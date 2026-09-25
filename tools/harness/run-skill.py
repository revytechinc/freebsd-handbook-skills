#!/usr/bin/env python3
"""Have a small model follow one skill on one disposable test machine, then
check the result independently.

    tools/harness/run-skill.py skills/<chapter>/<task> <target> [--no-reset]

Steps:
  1. Reset the target to its clean snapshot (the operator's reset command;
     the model never has host access), then run the skill's optional
     setup.sh (preconditions, such as pkg being installed).
  2. Run the model with the skill text and exactly one tool, run_on_target
     (target_mcp.py), from an empty directory, with no other context.
  3. Run the skill's own verify.sh on the target, independently of the model.
     The model's opinion of its own success is never the result. A skill that
     only reports something (a search, a query) also has answer.sh: it prints
     the true answer, computed on the target independently of the model, and
     every line it prints must appear in the model's final message.
  4. Write the transcript and verdict under .work/runs/ (private: run logs
     contain details of the test infrastructure).

Targets are described in the private file .work/targets.json:

  {"hbvm151": {"release": "15.1-RELEASE",
               "ssh": "ssh -F /path/.work/ssh_config 192.0.2.71",
               "reset": ["ssh", "adminhost", "doas", "..."]}}

If the skill directory has a file named "reboots", the skill may end by
scheduling a reboot (shutdown -r +1). The harness then waits for the machine to
go down and come back with its marker before running verify.sh.

If the skill directory has test-inputs.txt, its lines (such as
"PACKAGE=nginx-lite") are given to the model as the skill's inputs, the way a
person asking for the task would give them.

A skill that only reports something is marked with a "report-only" file and
has answer.sh instead of verify.sh. Its true answer is computed BEFORE the
model runs; after the run it must be unchanged (the model must not have
altered what it reports on) and must be an exact line of the final message.

A run is VERIFIED only when ALL hold: the model finished normally and said
DONE (not FAILED, not NOT DONE), the skill's verify.sh passes afterwards, and,
if the skill has answer.sh, the model's final message contains its answer.
verify.sh is also run once BEFORE the model: if it already passes, the result
is recorded as VERIFIED-NO-OP (exit 3), so a skill whose end state existed from the
start is never mistaken for one the model achieved.

Exit status:
  0  verified: the model said DONE and verify.sh passed, and the end state did
     NOT exist before the run (the model brought it about);
  3  verified, but the end state existed both before and after the run. The
     harness cannot tell whether the model changed nothing or undid and redid
     the work; confirm from the command log that the skill was a no-op;
  1  not verified (the model did not say DONE, or verify.sh failed);
  2  the run itself could not be carried out (infrastructure: reset, setup,
     ssh, the model process crashing, any timeout, or verify.sh exiting with
     anything other than 0 or 1).

verify.sh must exit 0 (verified) or 1 (not verified). Any other status,
including ssh's own 255, is treated as a failure of the run, not a verdict.
"""
import json, os, re, shlex, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, ".work")
MODEL = os.environ.get("HB_MODEL", "claude-haiku-4-5-20251001")
BUDGET = os.environ.get("HB_BUDGET_USD", "2.00")
MODEL_TIMEOUT = int(os.environ.get("HB_MODEL_TIMEOUT", "3600"))

SYSTEM = """You are operating one FreeBSD test machine. The ONLY way to act on it is
the run_on_target tool, which runs one shell command as root on that machine.

You are given a skill: step-by-step instructions for one task. Follow it exactly:
- Do the steps in order. Run exactly the commands it gives.
- After each command, compare the output with what the skill says to expect,
  and follow the skill's decision table for what you see.
- Do not improvise, skip steps, or add steps the skill does not contain.
- If the skill says to stop and report, stop and report.
- If a tool result says TRANSPORT ERROR or TRANSPORT LOST, stop and report it:
  that is a problem with the test setup, not with the skill.
When you finish, the LAST line of your final message must be exactly one word
on its own: DONE if every step and the skill's Verify step matched, otherwise
FAILED (and, above that line, name the step where it went wrong)."""


class HarnessError(Exception):
    """A problem with the test set-up found after the model ran: the run is
    recorded (result.json) as a harness error, never as a verdict."""


def die(msg, code=2):
    print(f"run-skill: {msg}", file=sys.stderr)
    sys.exit(code)


def load_target(name):
    path = os.path.join(WORK, "targets.json")
    try:
        with open(path) as f:
            targets = json.load(f)
    except (OSError, ValueError) as e:
        die(f"cannot read {path}: {e}")
    if name not in targets:
        die(f"unknown target {name!r}; known: {sorted(targets)}")
    return targets[name]


def ssh_run(target, command, timeout=600):
    argv = shlex.split(target["ssh"]) + [command]
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)


def wait_for(target, name, limit=600):
    t0 = time.monotonic()
    while time.monotonic() - t0 < limit:
        try:
            p = ssh_run(target, "cat /etc/hbskills-target", timeout=30)
            if p.returncode == 0 and p.stdout.strip() == name:
                return True
        except subprocess.TimeoutExpired:
            pass
        time.sleep(5)
    return False


def reset(target, name):
    cmd = target.get("reset")
    if not cmd:
        die(f"target {name} has no reset command; refusing to run on a dirty machine")
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        die(f"reset of {name} timed out after 900s; check that the host running the "
            "reset command is reachable and that the VM or jail stops cleanly")
    if p.returncode != 0:
        die(f"reset of {name} failed: {p.stderr.strip()[-300:]}")
    if not wait_for(target, name):
        die(f"{name} did not come back with its marker after the reset")


def run_model(skill_text, inputs, target, name, log_path, transcript_path):
    mcp = {"mcpServers": {"target": {
        "type": "stdio", "command": sys.executable,
        "args": [os.path.join(ROOT, "tools", "harness", "target_mcp.py")],
        "env": {"TARGET_SSH": target["ssh"], "TARGET_NAME": name, "TARGET_LOG": log_path}}}}
    with tempfile.TemporaryDirectory(prefix="hb-model-") as empty:
        cfg = os.path.join(empty, "mcp.json")
        with open(cfg, "w") as f:
            json.dump(mcp, f)
        prompt = ("Here is the skill to follow on the test machine. Follow it exactly.\n\n"
                  "=== SKILL ===\n" + skill_text + "\n=== END OF SKILL ===")
        if inputs:
            prompt += "\n\nUse these values for the skill's inputs:\n" + inputs
        argv = ["claude", "-p", "--model", MODEL, "--setting-sources", "", "--tools", "",
                "--mcp-config", cfg, "--strict-mcp-config",
                "--allowedTools", "mcp__target__run_on_target", "--permission-mode", "dontAsk",
                "--max-budget-usd", BUDGET, "--output-format", "stream-json", "--verbose",
                "--system-prompt", SYSTEM, prompt]
        with open(transcript_path, "w") as out:
            try:
                p = subprocess.run(argv, cwd=empty, stdin=subprocess.DEVNULL, stdout=out,
                                   stderr=subprocess.PIPE, text=True, timeout=MODEL_TIMEOUT)
                return p.returncode, p.stderr[-2000:]
            except subprocess.TimeoutExpired:
                return None, f"model did not finish within {MODEL_TIMEOUT}s"


def model_error(transcript_path):
    """The API error the model run ended with (rate or usage limit, ...), or ""."""
    msg = ""
    if not os.path.isfile(transcript_path):
        return msg
    with open(transcript_path) as f:
        for line in f:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "result" and ev.get("is_error"):
                msg = f"{ev.get('api_error_status') or ''} {ev.get('result') or ''}".strip()
    return msg


def final_text(transcript_path):
    """The model's final message, or None if the transcript has no result."""
    last = None
    with open(transcript_path) as f:
        for line in f:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "result":
                last = ev.get("result") or ""
    return last


# The verdict: some line STARTS with DONE (the prompt asks for it as the last
# line; any line is accepted, but FAILED or NOT DONE, in any case, anywhere
# vetoes it, except a zero tally such as "1 done, 0 failed"),
# allowing only known decoration
# before it (markdown "**DONE**", "## DONE", "- DONE", or a check mark
# "✅ **DONE**"; not "❌ DONE") and a summary
# after it ("**DONE** - all steps matched"). Case-sensitive: quoted command output is full of a lowercase
# "done" ("Extracting curl: ... done"), which is not a verdict.
DONE_LINE = re.compile("^[\\s*_`#>\u2705\u2714\u2713\ufe0f-]*DONE(?![\\w-])", re.M)


def said_done(text):
    """True when the model's final message has a line starting with DONE and says
    FAILED / NOT DONE nowhere. The whole message is read: models often write a
    summary after the verdict, and a fixed-size tail missed DONE."""
    # Any "failed" / "not done", in any case, vetoes: this can only reject a
    # correct run (e.g. one quoting "Failed to fetch"), never accept a bad one.
    # The one exception is a zero tally in a list of counts, as in
    # portupgrade's summary "1 done, 0 skipped and 0 failed", which models
    # quote and paraphrase ("1 done, 0 failed"), and its legend "!:failed":
    # ", 0 failed", "and 0 failed" and "!:failed" are removed before the
    # check. Anything else, including "1 failed", "exit=0 FAILED" or
    # "Step 0 failed", still vetoes.
    quoted = re.sub(r"(?:,|\band) 0 failed\b|!:failed\b", "", text, flags=re.I)
    if re.search(r"\bFAILED\b", quoted, re.I) or re.search(r"\bNOT\s+DONE\b", text, re.I):
        return False
    return bool(DONE_LINE.search(text))


def run_verify(target, verify):
    """Run verify.sh (or answer.sh) on the target over stdin; return the CompletedProcess.
    Not reaching the target (ssh exit 255, timeout) is an infrastructure
    failure, never a verdict about the skill."""
    try:
        with open(verify) as f:
            p = subprocess.run(shlex.split(target["ssh"]) + ["/bin/sh -s"], stdin=f,
                               capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        die("verify.sh timed out on the target; check that the target is up "
            "(ssh -F .work/ssh_config <address> true) and that verify.sh cannot hang")
    if p.returncode == 255:
        die(f"could not reach the target to run verify.sh ({p.stderr.strip()[-200:]}); "
            "check the gateway, the target VM or jail state, and .work/ssh_config")
    if p.returncode not in (0, 1):
        die(f"verify.sh exited {p.returncode}; it must exit 0 or 1. Fix verify.sh "
            f"(output: {(p.stdout + p.stderr).strip()[-200:]})")
    return p


def parse_args(argv):
    """(skill_dir, target_name, do_reset) from the command line, or die."""
    unknown = [f for f in argv if f.startswith("--") and f != "--no-reset"]
    if unknown:
        die(f"unknown option(s) {unknown}; the only option is --no-reset")
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        die(__doc__.split("\n\n")[1].strip())
    return os.path.abspath(args[0]), args[1], "--no-reset" not in argv


def prepare(target, name, skill_dir, do_reset):
    """Reset the target (unless told not to) and apply the skill's setup.sh.
    Preconditions the skill assumes are set up here, never by the model; if
    they cannot be met, the run is an infrastructure failure."""
    if do_reset:
        reset(target, name)
    elif not wait_for(target, name, limit=60):
        die(f"{name} is not reachable with its marker")
    setup = os.path.join(skill_dir, "setup.sh")
    if os.path.isfile(setup):
        try:
            with open(setup) as f:
                p = subprocess.run(shlex.split(target["ssh"]) + ["/bin/sh -s"], stdin=f,
                                   capture_output=True, text=True, timeout=1800)
        except subprocess.TimeoutExpired:
            die(f"setup.sh timed out on {name} after 1800s; check that the target can "
            "reach its package mirror through the gateway, and that setup.sh never waits for input")
        if p.returncode != 0:
            die(f"setup.sh failed on {name}: {(p.stdout + p.stderr).strip()[-400:]}")


def verdict(result):
    """(label, exit status) for a run in which the model finished."""
    before, after_ok = result["already_satisfied_before"], result["verify_exit"] == 0
    if not result["verified"]:
        broke = before and not after_ok
        return ("NOT VERIFIED (verify.sh passed BEFORE the run and failed after it: "
                "the run broke a working state)" if broke else "NOT VERIFIED"), 1
    if before:
        return "VERIFIED-NO-OP (end state already existed before the run)", 3
    return "VERIFIED", 0


def verify_word(result):
    if result.get("report_only"):
        return "report-only (no end state)"
    return "verify " + ("passed" if result["verify_exit"] == 0 else "FAILED")


def report(result, run_dir):
    """Write result.json, print the verdict, and return the exit status."""
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(result, f, indent=2)
    where = f"{result['skill']} on {result['target']} ({result['release']})"
    if not result["model_finished"]:
        print(f"RUN FAILED  {where}: the model did not finish (exit {result['model_exit']}): "
              f"{result['model_stderr'].strip()[-200:]}; run: {run_dir}")
        return 2
    label, code = verdict(result)
    answer = ""
    if result["expected_answer"]:
        answer = "; answer " + (f"MISSING {result['answer_missing']}" if result["answer_missing"] else "matched")
    print(f"{label}  {where}; model said {'DONE' if result['model_said_done'] else 'not DONE'}; "
          f"{verify_word(result)}{answer}; run: {run_dir}")
    return code


def answer_missing(expected, said):
    """Expected answer lines that are not a whole line of the model's final
    message. Markdown decoration around a line is ignored, but the line itself
    must match exactly: "RESULT: curl 8.22.0" does not match
    "RESULT: curl 8.22.0_1"."""
    lines = set()
    for l in (said or "").splitlines():
        l = re.sub(r"[*`]", "", l).strip()
        l = re.sub(r"^(?:[#>]+|[-+]|\d+[.)])\s*", "", l).strip()  # heading, quote, list marker
        lines.add(l.strip("_").strip())  # _emphasis_ at the ends only: names may contain "_"
    missing = [e for e in expected if e not in lines]
    # A hedged answer (the right RESULT: line plus a different one) is not an answer.
    labels = {e.split(":", 1)[0] + ":" for e in expected if ":" in e}
    others = sorted(l for l in lines if any(l.startswith(p) for p in labels) and l not in expected)
    return missing + [f"(also answered: {o})" for o in others]


BOOT_TOKEN = "/var/run/hbskills-boot-token"   # emptied at every boot (rc.d/cleanvar)


def boot_stamp(target, name):
    """Leave a random token in /var/run before the model runs. /var/run is
    emptied at boot, so a missing token proves a restart, independent of the
    clock (kern.boottime moves when the clock is stepped). Dies on failure."""
    token = os.urandom(8).hex()
    try:
        p = ssh_run(target, f"cat /etc/hbskills-target; echo {token} > {BOOT_TOKEN} && cat {BOOT_TOKEN}", timeout=30)
    except subprocess.TimeoutExpired:
        die(f"could not leave the boot token on {name} (timeout)")
    lines = p.stdout.splitlines()
    if p.returncode != 0 or len(lines) < 2 or lines[0].strip() != name or lines[1].strip() != token:
        die(f"could not leave the boot token on {name} (exit {p.returncode}): {p.stderr.strip()[-200:]}")
    return token


PROBE = ("cat /etc/hbskills-target; cat " + BOOT_TOKEN + " 2>/dev/null || echo GONE; "
         "if pgrep -x shutdown >/dev/null || [ -e /var/run/nologin ]; then echo PENDING; else echo IDLE; fi")


def probe_settled(target, name, token, scheduled):
    """One look at the target: "rebooted" (token gone, nothing pending),
    "idle" (token still there, no restart scheduled or pending), or "wait"."""
    try:
        p = ssh_run(target, PROBE, timeout=30)
    except subprocess.TimeoutExpired:
        return "wait"
    lines = [l.strip() for l in p.stdout.splitlines()]
    if p.returncode != 0 or len(lines) < 3 or lines[0] != name or lines[2] != "IDLE":
        return "wait"
    if lines[1] != token:
        return "rebooted"
    return "wait" if scheduled else "idle"


def restart_scheduled(log_path):
    """True when the command log shows a shutdown -r that ran successfully."""
    if not os.path.isfile(log_path):
        return False
    with open(log_path) as f:
        for line in f:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if (ev.get("event") == "end" and ev.get("command", "").lstrip().startswith("shutdown -r")
                    and "Shutdown at" in ev.get("stdout", "")):
                return True
    return False


def settle_reboot(target, name, reboots, booted_before, log_path):
    """For a skill that may restart the machine (shutdown -r +1): wait until it
    has either booted again (the boot token is gone) or, if no restart was
    scheduled, until nothing is pending. When a restart was scheduled, only a
    vanished boot token counts: a machine that still has it may be in the
    middle of shutting down. Returns "" when settled, otherwise
    why not; a machine that never comes back is the skill's failure, recorded
    as NOT VERIFIED, not a harness error."""
    if not reboots:
        return ""
    scheduled = restart_scheduled(log_path)
    if scheduled:
        time.sleep(90)  # shutdown -r +1: let the minute pass first
    t0 = time.monotonic()
    while time.monotonic() - t0 < 900:
        state = probe_settled(target, name, booted_before, scheduled)
        if state == "rebooted":
            time.sleep(20)  # let the new boot finish starting services
            return ""
        if state == "idle":
            return ""  # no restart asked for and none pending: verify.sh decides
        time.sleep(10)
    return f"the machine did not finish its restart within 900s (restart scheduled: {scheduled})"


def check_answer(target, name, answer, skill_text, said, verify_exit):
    """(expected, missing) answer lines; both empty when the skill has no
    answer.sh. answer.sh computes the true answer on the target without the
    model; each line must appear in the model's final message."""
    if not os.path.isfile(answer):
        return [], []
    a = run_verify(target, answer)
    if a.returncode == 0 and a.stdout.strip():
        expected = [l.strip() for l in a.stdout.splitlines() if l.strip()]
        copyable = [l for l in expected if l in skill_text]
        if copyable:
            raise HarnessError(f"the expected answer {copyable} appears word for word in the skill, so a model "
                               "could copy it without doing the task; use test inputs that differ from the skill's examples")
        return expected, answer_missing(expected, said)
    if verify_exit != 0:
        # The answer depends on state the model should have created, and
        # verify.sh already failed: a failed run, not a broken harness.
        note = ["(answer.sh could not compute an answer: verify.sh failed)"]
        return note, note
    raise HarnessError(f"answer.sh could not compute the answer on {name} although verify.sh passed "
                       f"(exit {a.returncode}): {(a.stdout + a.stderr).strip()[-200:]}; fix answer.sh")


def load_skill(skill_dir):
    """The skill's files: dict with text, verify path (None for a report-only
    skill), answer path, inputs, report_only and whether it may restart.
    A skill is report-only only when it says so with a "report-only" file."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    verify, answer = os.path.join(skill_dir, "verify.sh"), os.path.join(skill_dir, "answer.sh")
    report_only = os.path.isfile(os.path.join(skill_dir, "report-only"))
    if not os.path.isfile(skill_md):
        die(f"missing {skill_md}; add SKILL.md to the skill directory")
    with open(skill_md) as f:
        text = f.read()
    if "RESULT:" in text and not os.path.isfile(answer):
        die("the skill reports a RESULT: line but has no answer.sh to check it against; add answer.sh")
    if report_only:
        if not os.path.isfile(answer):
            die(f"{skill_dir} is marked report-only but has no answer.sh; add answer.sh")
        if os.path.isfile(verify) or os.path.isfile(os.path.join(skill_dir, "reboots")):
            die(f"{skill_dir} is marked report-only but also has verify.sh or reboots; "
                "a report-only skill changes nothing: remove one or the other")
        verify = None
    elif not os.path.isfile(verify):
        die(f"missing {verify}; add verify.sh, or mark a skill that only reports with a 'report-only' file and answer.sh")
    inputs_file = os.path.join(skill_dir, "test-inputs.txt")
    inputs = ""
    if os.path.isfile(inputs_file):
        with open(inputs_file) as f:
            inputs = f.read().strip()
    return {"dir": skill_dir, "text": text, "verify": verify, "answer": answer, "inputs": inputs,
            "report_only": report_only, "reboots": os.path.isfile(os.path.join(skill_dir, "reboots"))}


def answer_now(target, name, answer, skill_text):
    """Run answer.sh for a report-only skill; its answer lines. Dies if it
    cannot compute one (the machine was prepared by setup.sh, so that is a
    test-setup problem) or if the answer appears word for word in the skill."""
    a = run_verify(target, answer)
    lines = [l.strip() for l in a.stdout.splitlines() if l.strip()]
    if a.returncode != 0 or not lines:
        die(f"answer.sh could not compute the answer on {name} before the run (exit {a.returncode}): "
            f"{(a.stdout + a.stderr).strip()[-200:]}; fix answer.sh or setup.sh")
    copyable = [l for l in lines if l in skill_text]
    if copyable:
        die(f"the expected answer {copyable} appears word for word in the skill; use test inputs "
            "that differ from the skill's examples")
    return lines


def run_report_only(skill, target, said, expected):
    """For a report-only skill: the answer computed before the run must still
    hold after it (the model must not have changed what it reports on), and
    must be in the model's final message."""
    a = run_verify(target, skill["answer"])
    after = [l.strip() for l in a.stdout.splitlines() if l.strip()]
    missing = answer_missing(expected, said)
    if a.returncode != 0 or after != expected:
        missing = missing + [f"(the machine changed during the run: answer.sh now exits {a.returncode} with {after})"]
    return missing


def run_once(skill, target, name, run_dir, stamp, expected_before):
    """Run the model on the target and check the result; returns the result dict."""
    log_path, transcript = os.path.join(run_dir, "commands.jsonl"), os.path.join(run_dir, "transcript.jsonl")
    booted_before = boot_stamp(target, name) if skill["reboots"] else None
    rc, err = run_model(skill["text"], skill["inputs"], target, name, log_path, transcript)
    err = ((err or "") + " " + model_error(transcript)).strip()
    said = final_text(transcript)
    model_ok = rc == 0 and said is not None
    done = model_ok and said_done(said)
    unsettled = settle_reboot(target, name, skill["reboots"], booted_before, log_path)
    if skill["report_only"]:
        missing = run_report_only(skill, target, said, expected_before)
        return {"model_exit": rc, "model_stderr": err, "model_finished": model_ok, "model_said_done": done,
                "verify_exit": None, "verify_stdout": "(report-only skill: no end state to check)",
                "verify_stderr": "", "expected_answer": expected_before, "answer_missing": missing,
                "verified": done and not missing}
    if unsettled:
        after = subprocess.CompletedProcess([], 1, stdout=f"FAIL: {unsettled}", stderr="")
    else:
        after = run_verify(target, skill["verify"])  # independent of the model
    try:
        expected, missing = check_answer(target, name, skill["answer"], skill["text"], said, after.returncode)
    except HarnessError as e:
        with open(os.path.join(run_dir, "result.json"), "w") as f:
            json.dump({"skill": os.path.relpath(skill["dir"], ROOT), "target": name, "time_utc": stamp,
                       "harness_error": str(e), "verified": False}, f, indent=2)
        die(f"{e}; run: {run_dir}")
    return {"model_exit": rc, "model_stderr": err, "model_finished": model_ok, "model_said_done": done,
            "verify_exit": after.returncode, "verify_stdout": after.stdout[-4000:],
            "verify_stderr": after.stderr[-2000:], "expected_answer": expected, "answer_missing": missing,
            "verified": done and after.returncode == 0 and not missing}


def main():
    skill_dir, name, do_reset = parse_args(sys.argv[1:])
    skill = load_skill(skill_dir)
    target = load_target(name)
    prepare(target, name, skill_dir, do_reset)
    if skill["report_only"]:
        # Nothing to check before, but the true answer is taken now, before the model.
        before = subprocess.CompletedProcess([], 1, "", "")
        expected_before = answer_now(target, name, skill["answer"], skill["text"])
    else:
        before, expected_before = run_verify(target, skill["verify"]), None
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = os.path.join(WORK, "runs", f"{stamp}-{os.path.basename(skill_dir)}-{name}")
    os.makedirs(run_dir)
    result = {"skill": os.path.relpath(skill_dir, ROOT), "target": name, "release": target.get("release"),
              "model": MODEL, "time_utc": stamp, "inputs": skill["inputs"], "report_only": skill["report_only"],
              "already_satisfied_before": before.returncode == 0, "verify_before": before.stdout[-1000:]}
    result.update(run_once(skill, target, name, run_dir, stamp, expected_before))
    sys.exit(report(result, run_dir))


if __name__ == "__main__":
    main()
