#!/usr/bin/env python3
"""Regression tests for the safety tooling. No network, no test machine.

    python3 tools/tests/test_tools.py

Covers:
  - target_mcp.parse(): how a command's result is classified from the start and
    end markers (ran / failed / timed out / never started / connection lost).
  - run-skill.said_done(): reading the model's DONE / FAILED verdict.
  - check-public.py: that planted addresses, MACs, e-mail addresses are caught
    and that legitimate text is not.
"""
import contextlib, importlib.util, io, os, shutil, subprocess, sys, tempfile, time
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
failures = 0


def expect(name, cond, detail=""):
    global failures
    print(f"{'PASS' if cond else 'FAIL'} {name}{'' if cond else '  ' + detail}")
    failures += 0 if cond else 1


def load_harness():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as log:
        os.environ.update(TARGET_SSH="ssh root@192.0.2.10", TARGET_NAME="unit", TARGET_LOG=log.name)
    spec = importlib.util.spec_from_file_location("target_mcp", os.path.join(TOOLS, "harness", "target_mcp.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # module level only checks config; nothing connects
    return mod


def test_parse():
    m = load_harness()
    S, E, now = m.START, m.END, time.monotonic()
    cases = [
        ("clean output", f"{S}\nhello\n\n{E} 0\n", ("ran", 0, "hello\n")),
        ("login-shell noise before the marker", f"Welcome!\n{S}\nhello\n\n{E} 0\n", ("ran", 0, "hello\n")),
        ("output without trailing newline", f"{S}\nabc\n{E} 0\n", ("ran", 0, "abc")),
        ("empty output", f"{S}\n\n{E} 0\n", ("ran", 0, "")),
        ("failed command", f"{S}\n\n{E} 1\n", ("ran", 1, "")),
        ("never started", "ssh: connect refused\n", ("transport_error", 255, None)),
        ("connection lost", f"{S}\npartial\n", ("transport_lost", 255, None)),
        ("command's own exit 124", f"{S}\n\n{E} 124\n", ("ran", 124, "")),
    ]
    for name, out, (kind, status, want) in cases:
        k, s, o, _ = m.parse(out, "", 255, now)
        expect(f"parse: {name}", k == kind and s == status and (want is None or o == want),
               f"got kind={k} status={s} out={o!r}")
    k, *_ = m.parse(f"{S}\n\n{E} 124\n", "", 0, now - m.TIMEOUT)
    expect("parse: real timeout", k == "timed_out", f"got {k}")


def test_logging():
    m = load_harness()
    # log() reports success and failure explicitly.
    expect("log: returns True when written", m.log({"event": "unit"}) is True)
    saved = m.LOG
    m.LOG = "/nonexistent-dir/log.jsonl"
    expect("log: returns False when it cannot write", m.log({"event": "unit"}) is False)
    m.LOG = saved
    # A command is never run when its start entry cannot be logged.
    real_log, real_call = m.log, m.remote_call
    ran = []
    m.remote_call = lambda *a, **k: ran.append(a) or ("", "", 0)
    m.log = lambda entry: False
    r = m.run("true")
    expect("run: nothing runs without a start log entry", r["kind"] == "harness_error" and not ran, str(r))
    # A result whose end entry cannot be logged is marked, and shown as an error.
    m.log = lambda entry: entry.get("event") == "start"
    m.remote_call = lambda *a, **k: (f"{m.START}\nok\n\n{m.END} 0\n", "", 0)
    r = m.run("true")
    body, is_error = m.render(r)
    expect("run: unlogged result is marked", r.get("unlogged") is True and "could NOT be written" in r["stderr"], str(r))
    expect("render: unlogged result is an error", is_error is True, body)
    m.log, m.remote_call = real_log, real_call  # leave the module as it was


def test_said_done():
    spec = importlib.util.spec_from_file_location("run_skill", os.path.join(TOOLS, "harness", "run-skill.py"))
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)  # module level defines only; main() is not run
    summary = "\n".join(f"{i}. step {i} matched" for i in range(60))
    cases = [
        ("plain DONE", "All steps matched.\n\nDONE", True),
        ("markdown **DONE**", "Verified.\n\n**DONE**", True),
        ("DONE followed by a long summary", "**DONE**\n\n" + summary, True),
        ("**DONE** followed by text on the same line", "Checked.\n\n**DONE** - All steps completed.", True),
        ("cross mark before DONE", "❌ DONE", False),
        ("unchecked box before DONE", "- [ ] DONE", False),
        ("emoji before DONE", "Summary:\n\n✅ **DONE** - All steps completed.", True),
        ("DONE - summary", "---\n\nDONE - All steps matched the expected behavior.", True),
        ("lowercase done in quoted output only", "Extracting curl-8.22.0: .......... done\nexit=0", False),
        ("DONE inside a sentence only", "I am DONE with step 2 and stopped.", False),
        ("FAILED", "Step 3 did not match.\n\nFAILED at step 3", False),
        ("NOT DONE", "**NOT DONE**", False),
        ("DONE line but FAILED elsewhere", "FAILED at step 2, retried.\n\nDONE", False),
        ("DONE line but lowercase failed elsewhere", "Step 3 failed, but it is installed.\n\nDONE", False),
        ("empty", "", False),
    ]
    for name, text, want in cases:
        expect(f"said_done: {name}", rs.said_done(text) is want)
    exp = ["RESULT: curl 8.22.0"]
    answers = [
        ("exact line", "Done.\n\nRESULT: curl 8.22.0\n\nDONE", True),
        ("bold line", "**RESULT: curl 8.22.0**\nDONE", True),
        ("in backticks", "`RESULT: curl 8.22.0`", True),
        ("bold label only", "**RESULT:** curl 8.22.0", True),
        ("as a list item", "- RESULT: curl 8.22.0", True),
        ("as a numbered item", "4. RESULT: curl 8.22.0", True),
        ("underscore emphasis", "__RESULT: curl 8.22.0__", True),
        ("hedged with a second answer", "RESULT: curl 8.22.0\nRESULT: curl 8.22.0_1", False),
        ("hedged with not available", "RESULT: curl 8.22.0\nRESULT: curl not available", False),
        ("longer version", "RESULT: curl 8.22.0_1", False),
        ("inside a sentence", "I think RESULT: curl 8.22.0 is right", False),
        ("absent", "DONE", False),
    ]
    for name, text, ok in answers:
        expect(f"answer check: {name}", (rs.answer_missing(exp, text) == []) is ok)
    base = {"already_satisfied_before": False, "verify_exit": 0, "verified": True}
    expect("verdict: verified", rs.verdict(base) == ("VERIFIED", 0))
    expect("verdict: answer missing is not verified", rs.verdict({**base, "verified": False})[1] == 1)
    expect("verdict: pre-existing end state", rs.verdict({**base, "already_satisfied_before": True})[1] == 3)


def test_gateway():
    spec = importlib.util.spec_from_file_location(
        "run_skill_gw", os.path.join(TOOLS, "harness", "run-skill.py"))
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)  # module level defines only; main() is not run
    fake = "sk-PLANTED-1"
    tmp = tempfile.mkdtemp(prefix="gw-")
    saved_path = os.environ.get("PATH")
    try:
        # 1. redact(): a key is replaced throughout, the header is fixed-cased,
        #    and text with no secret is left untouched.
        expect("redact: repeated key replaced",
               rs.redact(f"abc {fake} def {fake} gh", [fake])
               == f"abc [REDACTED] def [REDACTED] gh")
        expect("redact: bearer header, any case -> fixed",
               rs.redact("authorization: bearer xyz", [])
               == "Authorization: Bearer [REDACTED]")
        expect("redact: no secret unchanged",
               rs.redact("just text, no key here", [fake]) == "just text, no key here")

        # 2. dgx_gateway_env(): the key file is read and the six variables set;
        #    any provider selector already in the environment is dropped.
        key_file = os.path.join(tmp, "key")
        with open(key_file, "w") as f:
            f.write(fake + "\n")
        with patch.object(rs, "DGX_KEY_FILE", key_file), \
                patch.dict(os.environ, {
                    "CLAUDE_CODE_USE_BEDROCK": "1",
                    "CLAUDE_CODE_USE_VERTEX": "1",
                    "CLAUDE_CODE_USE_FOUNDRY": "1"}, clear=False):
            env = rs.dgx_gateway_env()
            expect("dgx: token read from key file", env["ANTHROPIC_AUTH_TOKEN"] == fake)
            expect("dgx: base url is the fixed DGX_URL", env["ANTHROPIC_BASE_URL"] == rs.DGX_URL)
            expect("dgx: api key empty", env["ANTHROPIC_API_KEY"] == "")
            expect("dgx: sonnet alias default", env["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "default")
            expect("dgx: haiku alias default", env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "default")
            expect("dgx: small_fast alias default", env["ANTHROPIC_SMALL_FAST_MODEL"] == "default")
            expect("dgx: bedrock selector dropped", "CLAUDE_CODE_USE_BEDROCK" not in env)
            expect("dgx: vertex selector dropped", "CLAUDE_CODE_USE_VERTEX" not in env)
            expect("dgx: foundry selector dropped", "CLAUDE_CODE_USE_FOUNDRY" not in env)

        # 3. dgx_gateway_env() stops (die raises SystemExit) when the key is
        #    empty or unreadable, and the message carries no key.
        empty_file = os.path.join(tmp, "empty")
        open(empty_file, "w").close()
        with patch.object(rs, "DGX_KEY_FILE", empty_file):
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                try:
                    rs.dgx_gateway_env()
                    stopped_empty = False
                except SystemExit as exc:
                    stopped_empty = exc.code not in (0, None)
            expect("dgx: empty key file stops", stopped_empty)
            expect("dgx: empty key message no key", fake not in buf.getvalue())

        missing_file = os.path.join(tmp, "missing")
        with patch.object(rs, "DGX_KEY_FILE", missing_file):
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                try:
                    rs.dgx_gateway_env()
                    stopped_missing = False
                except SystemExit as exc:
                    stopped_missing = exc.code not in (0, None)
            expect("dgx: missing key file stops", stopped_missing)
            expect("dgx: missing key message no key", fake not in buf.getvalue())

        # 4. model_argv_env() and recorded_model() for each HB_GATEWAY value.
        with patch.object(rs, "HB_GATEWAY", ""):
            model_arg, env = rs.model_argv_env()
            expect("argv: empty gw returns (MODEL, None)", (model_arg, env) == (rs.MODEL, None))
            expect("recorded: empty gw returns MODEL", rs.recorded_model() == rs.MODEL)
        with patch.object(rs, "HB_GATEWAY", "dgx"):
            with patch.object(rs, "DGX_KEY_FILE", key_file):
                model_arg, env = rs.model_argv_env()
                expect("argv: dgx returns (sonnet, dict)", model_arg == "sonnet" and isinstance(env, dict))
                expect("argv: dgx env carries the token", env.get("ANTHROPIC_AUTH_TOKEN") == fake)
                expect("recorded: dgx returns DGX_MODEL", rs.recorded_model() == rs.DGX_MODEL)
        with patch.object(rs, "HB_GATEWAY", "bogus"):
            try:
                rs.model_argv_env()
                stopped_bogus = False
            except SystemExit as exc:
                stopped_bogus = exc.code not in (0, None)
            expect("argv: bogus gw stops", stopped_bogus)

        # 5. run_claude() with a fake 'claude' on PATH. The script emits the
        #    key on stdout and in an Authorization header, then exec's sleep so
        #    it holds no pipe (the timeout path can then read EOF at once).
        bin_dir = os.path.join(tmp, "bin")
        sleep_bin = shutil.which("sleep") or "/bin/sleep"
        os.makedirs(bin_dir)
        script = os.path.join(bin_dir, "claude")
        with open(script, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("echo '{\"k\":\"%s\"}'\n" % fake)
            f.write('echo "Authorization: Bearer %s" >&2\n' % fake)
            # Absolute path: the test puts only bin_dir first on PATH. stdout and
            # stderr stay open, as with the real claude: a child that closes them
            # and then hangs leaves TimeoutExpired with no output to redact.
            f.write('exec %s "${SLEEP_SECONDS:-0}" </dev/null\n' % sleep_bin)
        os.chmod(script, 0o700)
        transcript_path = os.path.join(tmp, "transcript.jsonl")

        mode = {"v": "gateway"}

        def fake_argv_env():
            if mode["v"] == "gateway":
                return ("sonnet", dict(os.environ, ANTHROPIC_AUTH_TOKEN=fake))
            return ("x", None)

        def read_transcript():
            with open(transcript_path) as f:
                return f.read()

        def fresh_run(label):
            # Each run must write its own transcript: a file left by the
            # previous run would let a path that writes nothing pass.
            if os.path.exists(transcript_path):
                os.remove(transcript_path)
            result = rs.run_claude("prompt", "cfg", "tool", tmp, transcript_path)
            expect(f"claude: {label} transcript written", os.path.exists(transcript_path))
            return result

        with patch.object(rs, "model_argv_env", fake_argv_env), \
                patch.object(rs, "MODEL_TIMEOUT", 2), \
                patch.dict(os.environ, {"PATH": bin_dir +
                                        (os.pathsep + saved_path if saved_path else "")}):
            # gateway, sleep 0: redacted everywhere, no key survives.
            mode["v"] = "gateway"
            with patch.dict(os.environ, {"SLEEP_SECONDS": "0"}):
                rc, text = fresh_run("gw sleep0")
                t = read_transcript()
                expect("claude: gw sleep0 rc 0", rc == 0)
                expect("claude: gw sleep0 transcript no key", fake not in t)
                expect("claude: gw sleep0 transcript has [REDACTED]", "[REDACTED]" in t)
                expect("claude: gw sleep0 text no key", fake not in text)
                expect("claude: gw sleep0 text has [REDACTED]", "[REDACTED]" in text)

            # gateway, sleep 30: times out, transcript and message still redacted.
            mode["v"] = "gateway"
            with patch.dict(os.environ, {"SLEEP_SECONDS": "30"}):
                rc, text = fresh_run("gw sleep30")
                t = read_transcript()
                expect("claude: gw sleep30 rc None", rc is None)
                expect("claude: gw sleep30 text starts",
                       text.startswith(f"model did not finish within 2s"))
                expect("claude: gw sleep30 transcript no key", fake not in t)
                expect("claude: gw sleep30 transcript has [REDACTED]", "[REDACTED]" in t)
                expect("claude: gw sleep30 text no key", fake not in text)
                expect("claude: gw sleep30 text has [REDACTED]", "[REDACTED]" in text)

            # default, sleep 0: unchanged path, the key is left in the transcript.
            mode["v"] = "default"
            with patch.dict(os.environ, {"SLEEP_SECONDS": "0"}):
                rc, text = fresh_run("default sleep0")
                t = read_transcript()
                expect("claude: default sleep0 rc 0", rc == 0)
                expect("claude: default sleep0 transcript has key", fake in t)

            # default, sleep 30: times out with the plain message.
            mode["v"] = "default"
            with patch.dict(os.environ, {"SLEEP_SECONDS": "30"}):
                rc, text = fresh_run("default sleep30")
                expect("claude: default sleep30 rc None", rc is None)
                expect("claude: default sleep30 text exact",
                       text == "model did not finish within 2s")

            # The atomic-write temp files are always moved into place: none left.
            leftovers = [n for n in os.listdir(tmp) if n.startswith(".transcript-redact-")]
            expect("claude: no redact temp files left", leftovers == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_checker(text, *flags):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(text)
    p = subprocess.run([sys.executable, os.path.join(TOOLS, "check-public.py"), "--no-deny-list", *flags, f.name],
                       capture_output=True, text=True)
    os.unlink(f.name)
    return p.returncode, p.stdout + p.stderr


def test_checker():
    # The planted values are assembled at run time so this file itself contains
    # no public address, MAC or personal e-mail (the checker scans it too).
    pub4, pub6, mac, mail = ".".join(["8"] * 4), ":".join(["2a01", "4f8", "", "1"]), ":".join(["0c", "de", "ad", "be", "ef", "01"]), "@".join(["someone", "gmail.com"])
    must_fail = {
        "public IPv4": f"server {pub4}",
        "public IPv4 ending a sentence": f"Point it at {pub4}.",
        "public IPv4 with leading zeros": "at " + ".".join(["093", "184", "216", "34"]),
        "public IPv6": f"addr {pub6}",
        "public IPv6 after a colon": f"inet6:{pub6}",
        "IPv4-mapped public address": f"::ffff:{pub4}",
        "real MAC address": f"ether {mac}",
        "personal e-mail": f"mail {mail}",
        "personal freebsd.org e-mail": "mail " + "@".join(["a-committer", "freebsd.org"]),
        "ssh to a public address": f"ssh root@{pub4}",
        "public IPv6 followed by letters": f"addr {pub6}x",
        "public IPv4 hidden in a CI annotation parameter": f"::error file={pub4}::bad",
        "public IPv4 inside a CI annotation message": f"::notice {pub4}::x",
        "public IPv4 in IPv4-compatible IPv6 form": f"route ::{pub4} here",
        "short public IPv6 as a CI annotation parameter": f"::warning {pub6.split(':')[0]}::1",
        "public IPv6 with a hex tail in a CI annotation": f"::error file={pub6.split(':')[0]}" + "::" + "dead" + ":beef",
        "public IPv6 in a CI annotation parameter": f"::error file={pub6}::bad",
        "public IPv6 at the end of a sentence": f"the address is {pub6}.",
        "public IPv6 before a colon": f"{pub6}: note",
        "public IPv6 ending in a CI command name": f"{pub6[:-3]}::add-path::x",
        "two public IPv6 addresses on one line": f"{pub6[:-3]}::beef and {pub6[:-3]}::cafe",
        "public IPv6 followed by underscore": f"addr {pub6}_old",
    }
    must_pass = {
        "documentation IPv4": "192.0.2.10 198.51.100.1/24 203.0.113.5",
        "documentation IPv6": "2001:db8::1/64 3fff:0:1::5/48",
        "private and special ranges": "10.0.0.1 192.168.1.1 172.16.0.1 fe80::1%em0 ::1 ff02::1",
        "netmask": "255.255.255.0",
        "version strings and times": "15.1-RELEASE 14.4.0 1.2.3.4.5 12:30:45",
        "example mail and role address": "user@example.org freebsd-questions@freebsd.org",
        "documentation MAC": "00:00:5e:00:53:01",
        "ssh to a documentation address": "ssh root@192.0.2.10",
        "IPv4-mapped localhost": "::ffff:127.0.0.1",
        "CI annotation syntax": 'echo "::error::Fork pull request" and "::warning::x"',
        "C++ scope operator": "return ::abs(x) + std::max(a, b);",
        "other CI commands": 'echo "::echo::on" "::add-matcher::m.json" "::remove-matcher owner=x::"',
    }
    for name, text in must_fail.items():
        rc, out = run_checker(text)
        expect(f"checker catches {name}", rc == 1, out.strip()[-120:])
    for name, text in must_pass.items():
        rc, out = run_checker(text)
        expect(f"checker allows {name}", rc == 0, out.strip()[-120:])
    rc, out = run_checker("x", "--bogus")
    expect("checker refuses an unknown option", rc == 2, out.strip()[-120:])


if __name__ == "__main__":
    test_parse()
    test_logging()
    test_checker()
    test_said_done()
    test_gateway()
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
