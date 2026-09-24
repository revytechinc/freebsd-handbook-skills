#!/usr/bin/env python3
"""Regression tests for the safety tooling. No network, no test machine.

    python3 tools/tests/test_tools.py

Covers:
  - target_mcp.parse(): how a command's result is classified from the start and
    end markers (ran / failed / timed out / never started / connection lost).
  - check-public.py: that planted addresses, MACs, e-mail addresses are caught
    and that legitimate text is not.
"""
import importlib.util, os, subprocess, sys, tempfile, time

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
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
