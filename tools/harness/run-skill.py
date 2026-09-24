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
     The model's opinion of its own success is never the result.
  4. Write the transcript and verdict under .work/runs/ (private: run logs
     contain details of the test infrastructure).

Targets are described in the private file .work/targets.json:

  {"hbvm151": {"release": "15.1-RELEASE",
               "ssh": "ssh -F /path/.work/ssh_config 192.0.2.71",
               "reset": ["ssh", "adminhost", "doas", "..."]}}

A run is VERIFIED only when BOTH hold: the model finished normally and said
DONE (not FAILED, not NOT DONE), AND the skill's verify.sh passes afterwards.
verify.sh is also run once BEFORE the model: if it already passes, the result
is recorded as "already satisfied", so a skill whose end state existed from the
start is never mistaken for one the model achieved.

Exit status: 0 verified, 1 not verified (the model did not say DONE, or
verify.sh failed), 2 the run itself could not be carried out (infrastructure:
reset, setup, the model process crashing or timing out).
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
When you finish, say DONE if every step and the skill's Verify step matched,
otherwise say FAILED and name the step where it went wrong."""


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
    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    if p.returncode != 0:
        die(f"reset of {name} failed: {p.stderr.strip()[-300:]}")
    if not wait_for(target, name):
        die(f"{name} did not come back with its marker after the reset")


def run_model(skill_text, target, name, log_path, transcript_path):
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


def said_done(text):
    """True when the model's final message reports DONE and not FAILED.
    Models decorate the word (**DONE**, `DONE`), so match it as a word."""
    tail = text[-400:].upper()
    if re.search(r"\bFAILED\b", tail) or re.search(r"\bNOT\s+DONE\b", tail):
        return False
    return bool(re.search(r"\bDONE\b", tail))


def run_verify(target, verify):
    """Run verify.sh on the target over stdin; return the CompletedProcess."""
    with open(verify) as f:
        return subprocess.run(shlex.split(target["ssh"]) + ["/bin/sh -s"], stdin=f,
                              capture_output=True, text=True, timeout=900)


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
        with open(setup) as f:
            p = subprocess.run(shlex.split(target["ssh"]) + ["/bin/sh -s"], stdin=f,
                               capture_output=True, text=True, timeout=1800)
        if p.returncode != 0:
            die(f"setup.sh failed on {name}: {(p.stdout + p.stderr).strip()[-400:]}")


def report(result, run_dir):
    """Write result.json, print the verdict, and return the exit status."""
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(result, f, indent=2)
    where = f"{result['skill']} on {result['target']} ({result['release']})"
    if not result["model_finished"]:
        print(f"RUN FAILED  {where}: the model did not finish (exit {result['model_exit']}): "
              f"{result['model_stderr'].strip()[-200:]}; run: {run_dir}")
        return 2
    label = "VERIFIED" if result["verified"] else "NOT VERIFIED"
    note = " (end state already existed before the run)" if result["already_satisfied_before"] else ""
    print(f"{label}{note}  {where}; model said {'DONE' if result['model_said_done'] else 'not DONE'}; "
          f"verify {'passed' if result['verify_exit'] == 0 else 'FAILED'}; run: {run_dir}")
    return 0 if result["verified"] else 1


def main():
    skill_dir, name, do_reset = parse_args(sys.argv[1:])
    skill_md, verify = os.path.join(skill_dir, "SKILL.md"), os.path.join(skill_dir, "verify.sh")
    for p in (skill_md, verify):
        if not os.path.isfile(p):
            die(f"missing {p}")
    target = load_target(name)
    prepare(target, name, skill_dir, do_reset)

    before = run_verify(target, verify)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = os.path.join(WORK, "runs", f"{stamp}-{os.path.basename(skill_dir)}-{name}")
    os.makedirs(run_dir)
    log_path, transcript = os.path.join(run_dir, "commands.jsonl"), os.path.join(run_dir, "transcript.jsonl")

    with open(skill_md) as f:
        rc, err = run_model(f.read(), target, name, log_path, transcript)
    said = final_text(transcript)
    model_ok = rc == 0 and said is not None
    done = model_ok and said_done(said)
    after = run_verify(target, verify)  # independent of the model
    result = {
        "skill": os.path.relpath(skill_dir, ROOT), "target": name, "release": target.get("release"),
        "model": MODEL, "time_utc": stamp, "model_exit": rc, "model_stderr": err,
        "model_finished": model_ok, "model_said_done": done,
        "already_satisfied_before": before.returncode == 0, "verify_before": before.stdout[-1000:],
        "verify_exit": after.returncode, "verify_stdout": after.stdout[-4000:], "verify_stderr": after.stderr[-2000:],
        "verified": done and after.returncode == 0,
    }
    sys.exit(report(result, run_dir))


if __name__ == "__main__":
    main()
