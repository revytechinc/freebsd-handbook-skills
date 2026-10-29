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
import base64, contextlib, hashlib, http.server, importlib.util, io, json, os, select, shutil, socket, ssl, subprocess, sys, tempfile, threading, time, types
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
        # 6. gateway_backend(): the concrete model read from the gateway's
        #    model/info, or "unknown" on any failure. The key passed in (fake)
        #    is the only thing the server is not shown; it must not appear in
        #    any value gateway_backend returns.
        with_default = {"data": [
            {"model_name": "default", "litellm_params": {"model": "openai/ornith-1.5-35b-a3b"}},
            {"model_name": "default-mlapointe",
             "litellm_params": {"model": "openai/ornith-1.5-35b-a3b"}}]}
        without_default = {"data": [
            {"model_name": "default", "litellm_params": {"model": "openai/ornith-1.5-35b-a3b"}}]}

        # A threaded 127.0.0.1 server whose body and status are set before each
        # request, so the five cases run against a real HTTP round trip.
        class _InfoServer(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(self.server.status_code)
                self.send_header("Content-Type", "application/json")
                body = self.server.body_bytes
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass  # keep the test output quiet

        def start_info_server():
            srv = http.server.HTTPServer(("127.0.0.1", 0), _InfoServer)
            srv.status_code = 200
            srv.body_bytes = json.dumps(with_default).encode("utf-8")
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            return srv

        srv = start_info_server()
        try:
            with patch.object(rs, "DGX_URL",
                              f"http://127.0.0.1:{srv.server_address[1]}"):
                # a) the JSON that has default-mlapointe -> its model.
                srv.status_code = 200
                srv.body_bytes = json.dumps(with_default).encode("utf-8")
                got = rs.gateway_backend(fake)
                expect("backend: known model returned",
                       got == "openai/ornith-1.5-35b-a3b", repr(got))
                # b) the key is only a request header; it never returns.
                expect("backend: key never appears in return", fake not in got, repr(got))

                # c) a list without default-mlapointe -> unknown.
                srv.body_bytes = json.dumps(without_default).encode("utf-8")
                expect("backend: alias absent -> unknown",
                       rs.gateway_backend(fake) == "unknown")

                # d) HTTP 500 -> unknown.
                srv.status_code = 500
                srv.body_bytes = b"boom"
                expect("backend: HTTP 500 -> unknown",
                       rs.gateway_backend(fake) == "unknown")

                # e) non-JSON body -> unknown.
                srv.status_code = 200
                srv.body_bytes = b"this is not json"
                expect("backend: non-JSON body -> unknown",
                       rs.gateway_backend(fake) == "unknown")
        finally:
            srv.shutdown()
            srv.server_close()
    # f) after_model(): "backend" and its alias go right after "model", and
        #    are appended at the end when there is no "model" key.
        ordered = rs.after_model({"skill": "s", "model": "openai/x", "time_utc": "t"}, "openai/backend")
        keys = list(ordered.keys())
        expect("after_model: fields right after model",
                keys == ["skill", "model", "backend", "backend_alias", "time_utc"], keys)
        expect("after_model: alias recorded", ordered["backend_alias"] == rs.GATEWAY_BACKEND_NAME)
        # Without backend_after, the "after" and "changed" keys are absent.
        expect("after_model: no backend_after or backend_changed when not passed",
                "backend_after" not in ordered and "backend_changed" not in ordered, list(ordered.keys()))
        appended = rs.after_model({"skill": "s", "time_utc": "t"}, "openai/backend")
        expect("after_model: fields appended when no model",
                list(appended.keys())[-2:] == ["backend", "backend_alias"], list(appended.keys()))

        # f2) With backend_after it goes right after the alias, plus
        #      "backend_changed" (False when equal, True when the run moved the
        #      alias). This is recorded only; it never alters the verdict.
        equal = rs.after_model({"skill": "s", "model": "openai/x", "time_utc": "t"},
                               "openai/backend", "openai/backend")
        expect("after_model: equal backend, order after alias",
               list(equal.keys()) == ["skill", "model", "backend", "backend_alias", "backend_after",
                                      "backend_changed", "time_utc"], list(equal.keys()))
        expect("after_model: equal backend, value recorded", equal["backend_after"] == "openai/backend")
        expect("after_model: equal backend, changed False", equal["backend_changed"] is False)
        moved = rs.after_model({"skill": "s", "model": "openai/x", "time_utc": "t"},
                               "openai/backend", "openai/other")
        expect("after_model: moved backend, value recorded", moved["backend_after"] == "openai/other")
        expect("after_model: moved backend, changed True", moved["backend_changed"] is True)
        expect("after_model: moved backend, order after alias",
               list(moved.keys())[-5:] == ["backend", "backend_alias", "backend_after",
                                           "backend_changed", "time_utc"], list(moved.keys()))

        # g) current_backend(): None unless the run routes over the gateway;
        #    an empty key gives "unknown" without a request.
        with patch.object(rs, "HB_GATEWAY", ""):
            expect("current_backend: None when gateway empty", rs.current_backend() is None)
        with patch.object(rs, "HB_GATEWAY", "dgx"), \
                patch.object(rs, "dgx_gateway_env", return_value={"ANTHROPIC_AUTH_TOKEN": fake}), \
                patch.object(rs, "gateway_backend", return_value="openai/backend") as gb:
            expect("current_backend: routes over dgx",
                   rs.current_backend() == "openai/backend" and gb.call_args.args == (fake,))
        with patch.object(rs, "HB_GATEWAY", "dgx"), \
                patch.object(rs, "dgx_gateway_env", return_value={"ANTHROPIC_AUTH_TOKEN": ""}), \
                patch.object(rs, "gateway_backend") as gb2:
            expect("current_backend: empty key unknown without request",
                   rs.current_backend() == "unknown" and gb2.call_count == 0)

        # h) a 302 redirect is not followed: the request ends "unknown" and the
        #    target's handler is never reached, so the key is never copied.
        class _RedirectServer(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/info":
                    self.server.second_hits += 1
                    body = json.dumps(with_default).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:%d/info" % self.server.server_address[1])
                self.end_headers()
                self.wfile.write(b"")
            def log_message(self, *a): pass  # keep the test output quiet
        rsrv = http.server.HTTPServer(("127.0.0.1", 0), _RedirectServer)
        rsrv.second_hits = 0
        threading.Thread(target=rsrv.serve_forever, daemon=True).start()
        try:
            with patch.object(rs, "DGX_URL", f"http://127.0.0.1:{rsrv.server_address[1]}"):
                got = rs.gateway_backend(fake)
                expect("backend: 302 redirect -> unknown", got == "unknown", repr(got))
                expect("backend: redirect target never reached", rsrv.second_hits == 0, str(rsrv.second_hits))
        finally:
            rsrv.shutdown()
            rsrv.server_close()

        # i) a body shorter than Content-Length raises IncompleteRead, caught as "unknown".
        class _ShortBodyServer(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "100")
                self.end_headers()
                self.wfile.write(b'{"data": []}')
            def log_message(self, *a): pass  # keep the test output quiet
        ssrv = http.server.HTTPServer(("127.0.0.1", 0), _ShortBodyServer)
        threading.Thread(target=ssrv.serve_forever, daemon=True).start()
        try:
            with patch.object(rs, "DGX_URL", f"http://127.0.0.1:{ssrv.server_address[1]}"):
                expect("backend: too-long Content-Length -> unknown",
                        rs.gateway_backend(fake) == "unknown", repr(rs.gateway_backend(fake)))
        finally:
            ssrv.shutdown()
            ssrv.server_close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def load_harness_mod(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generate_certs(tmp):
    """CA + server cert via openssl (argument list, no shell). The server cert
    carries IP:127.0.0.1 as a SAN, like the masters' certificates carry their
    address, so the bridge's full check (CA and hostname) passes. Both certs
    carry the key usage extensions the client's default verification policy
    requires."""
    ca_key = os.path.join(tmp, "ca.key")
    ca_pem = os.path.join(tmp, "ca.pem")
    srv_key = os.path.join(tmp, "server.key")
    srv_csr = os.path.join(tmp, "server.csr")
    srv_crt = os.path.join(tmp, "server.crt")
    ext = os.path.join(tmp, "v3.cnf")
    openssl = ["openssl"]
    # The client verifies the server cert with its default policy, so the CA
    # must carry the key usage extensions that make it a usable signing CA.
    subprocess.run(openssl + ["req", "-x509", "-newkey", "rsa:2048", "-nodes",
                              "-keyout", ca_key, "-out", ca_pem, "-days", "1",
                              "-subj", "/CN=Test Console CA",
                              "-addext", "basicConstraints=critical,CA:TRUE",
                              "-addext", "keyUsage=critical,digitalSignature,keyCertSign,cRLSign"],
                   check=True, capture_output=True)
    subprocess.run(openssl + ["req", "-newkey", "rsa:2048", "-nodes",
                              "-keyout", srv_key, "-out", srv_csr,
                              "-subj", "/CN=vmm-console"], check=True, capture_output=True)
    # The end-entity cert needs digitalSignature + keyEncipherment and the
    # serverAuth EKU, or verification fails ("CA cert does not include key
    # usage extension") even though the bridge turned hostname checking off.
    with open(ext, "w") as f:
        f.write("[v3_req]\n")
        f.write("basicConstraints=CA:FALSE\n")
        f.write("keyUsage=critical,digitalSignature,keyEncipherment\n")
        f.write("extendedKeyUsage=serverAuth\n")
        f.write("subjectAltName=IP:127.0.0.1\n")
    subprocess.run(openssl + ["x509", "-req", "-in", srv_csr, "-CA", ca_pem,
                              "-CAkey", ca_key, "-CAcreateserial", "-out", srv_crt,
                              "-days", "1", "-extfile", ext, "-extensions", "v3_req"],
                   check=True, capture_output=True)
    return ca_pem, srv_crt, srv_key


class FakeWS(threading.Thread):
    """One-connection TLS websocket server. On connect it does the handshake,
    sends b"login: " and a ping, echoes each binary frame it receives, and sends
    a close once it has seen b"quit\r". With reject_status the handshake fails
    (e.g. 403) and no websocket is opened. build_frame/read_frame are reused from
    the bridge so the test speaks the exact same wire format.

    run() finishes when the connection closes; closed is set at that point."""

    def __init__(self, vmod, server_pem, server_key, reject_status=None):
        super().__init__(daemon=True)
        self.vmod = vmod
        self.server_pem = server_pem
        self.server_key = server_key
        self.reject_status = reject_status
        self.port = 0
        self.pong = threading.Event()
        self.bound = threading.Event()
        self.seen = []
        self.closed = threading.Event()
        self.count = 0
        self._lock = threading.Lock()

    def run(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(self.server_pem, self.server_key)
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        self.port = srv.getsockname()[1]
        self.bound.set()
        srv.listen(1)
        try:
            raw, _ = srv.accept()
            with self._lock:
                self.count += 1
            # The real server is TLS from the first byte, so wrap the accepted
            # socket in TLS BEFORE the handshake, then read the upgrade request
            # and reply over that same TLS connection (as the bridge does). A
            # rejected connection replies 4xx over TLS and is done: it is never
            # served as a websocket.
            conn = ctx.wrap_socket(raw, server_side=True)
            try:
                if not self.handshake(conn):
                    self.serve(conn)
            finally:
                conn.close()
        finally:
            srv.close()
            self.closed.set()

    def handshake(self, conn):
        # Read the upgrade request over the (already TLS-wrapped) connection.
        # Returns True if the connection was rejected (4xx); then the handshake
        # is over and serve() must not run.
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                return False
            data += chunk
        key = None
        for line in data.decode("latin-1").split("\r\n"):
            if line[:18].lower() == "sec-websocket-key:":
                key = line.split(":", 1)[1].strip()
        if self.reject_status is not None:
            conn.sendall(f"HTTP/1.1 {self.reject_status}\r\n\r\n".encode())
            return True
        # Any bytes after the blank line belong to the first websocket frame;
        # the client parses them from its own buffer, so we need only the accept.
        digest = hashlib.sha1((key + self.vmod.GUID).encode(), usedforsecurity=False).digest()  # nosec B324 -- RFC 6455 accept value # nosemgrep: home.mlapointe..config.scan-tools.rules.semgrep.python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 -- RFC 6455 accept value # NOSONAR -- RFC 6455 accept value
        accept = base64.b64encode(digest).decode()
        resp = ("HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n")
        conn.sendall(resp.encode())
        return False

    def serve(self, conn):
        conn.sendall(self.vmod.build_frame(self.vmod.OP_BINARY, b"login: "))
        conn.sendall(self.vmod.build_frame(self.vmod.OP_PING, b"ping"))
        # read_frame parses from this buffer (which carries bytes it read past a
        # full frame) so nothing the server sends is dropped.
        buf = b""
        while True:
            opcode, payload, buf = self.vmod.read_frame(conn, buf)
            if opcode is None:
                break
            if opcode == self.vmod.OP_PONG:
                self.pong.set()
            elif opcode == self.vmod.OP_PING:
                conn.sendall(self.vmod.build_frame(self.vmod.OP_PONG, payload))
            elif opcode == self.vmod.OP_CLOSE:
                break
            elif opcode == self.vmod.OP_BINARY:
                conn.sendall(self.vmod.build_frame(self.vmod.OP_BINARY, payload))
                with self._lock:
                    self.seen.append(payload)
        self.closed.set()


def write_grant_script(tmp):
    """A script that prints the grant URL then the CA path, one per line."""
    path = os.path.join(tmp, "grant.py")
    with open(path, "w") as f:
        f.write("import sys\nprint(sys.argv[1])\nprint(sys.argv[2])\n")
    return path


class _Noop:
    """Stand-in for pyte.Screen / pyte.ByteStream, so we can import console_mcp.py
    (and test its argv builder) without the terminal-emulator package installed."""

    def __init__(self, *args, **kwargs):
        pass


def _run_bridge_code(vmm_console, grant_cmd, timeout=10):
    """Run the bridge with no stdin; return its exit code, or None if it timed
    out, so a hang becomes a failing check rather than a silent pass."""
    try:
        proc = subprocess.run([sys.executable, vmm_console, "--grant-cmd", grant_cmd],
                              input=b"", capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return proc.returncode


def _read_bridge(vmm_console, grant_cmd, stdin_data, timeout=10):
    """Run the bridge with stdin kept open, reading stdout until the echo (which
    contains "quit\\r") or the client exits. Returns a small result object holding
    returncode, stdout and the stderr bytes the bridge wrote (or None on timeout).
    Keeping stdin open until the echo is seen stops the client from exiting on EOF
    before it has relayed, pinged and echoed. The stderr is read by a side thread
    so its pipe cannot fill and block the client while we read stdout."""
    proc = subprocess.Popen([sys.executable, vmm_console, "--grant-cmd", grant_cmd],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    err_chunks = []

    def read_stderr():
        for chunk in iter(lambda: proc.stderr.read(1), b""):
            err_chunks.append(chunk)

    err_reader = threading.Thread(target=read_stderr, daemon=True)
    err_reader.start()

    proc.stdin.write(stdin_data)
    proc.stdin.flush()
    out = b""
    # A healthy relay writes the echo and we return as soon as "quit\\r" appears.
    # A broken relay writes nothing, so bound the read with select() (so read(1)
    # cannot block forever) plus a wall-clock deadline; the test fails fast
    # instead of hanging on a bridge that emits no stdout.
    deadline = time.monotonic() + 3
    while b"quit\r" not in out:
        if time.monotonic() > deadline:
            break
        ready, _, _ = select.select([proc.stdout], [], [], 0.2)
        if proc.stdout not in ready:
            continue
        # os.read on the descriptor: a buffered read(1) would pull more into
        # Python's buffer, which select() then cannot see.
        chunk = os.read(proc.stdout.fileno(), 4096)
        if not chunk:
            break
        out += chunk
    proc.stdin.close()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        err_reader.join(timeout=2)
        return None
    err_reader.join(timeout=timeout + 1)
    err = b"".join(err_chunks)
    return types.SimpleNamespace(returncode=proc.returncode, stdout=out, stderr=err)


def test_vmm_console():
    """The bridge, pointed at a fake TLS websocket, relays the console, pongs a
    ping, and exits 0; it refuses bad URLs, a 403 handshake, and makes no
    connection attempt for a bad URL."""
    vmod = load_harness_mod("vmm_console", "harness/vmm_console.py")

    # An untrusted server cannot make the bridge read an unbounded frame: a
    # header declaring more than MAX_FRAME bytes is refused before any read.
    class _NoBytes:
        def recv(self, _n):
            return b""
    huge = bytes([0x82, 127]) + (vmod.MAX_FRAME + 1).to_bytes(8, "big")
    try:
        vmod.read_frame(_NoBytes(), huge)
        refused = False
    except ValueError:
        refused = True
    expect("vmm: a frame over MAX_FRAME is refused", refused)

    # A grant URL with a CR/LF or space is refused before any connection, so it
    # cannot split the upgrade request line.
    for bad_url in ("https://127.0.0.1:1/console/t\r\nX-Evil: 1", "https://127.0.0.1:1/console/a b"):
        try:
            vmod.validate_url(bad_url)
            refused = False
        except SystemExit as exc:
            refused = exc.code not in (0, None)
        expect(f"vmm: refuses grant URL {bad_url[-12:]!r}", refused)
    vmm_console = os.path.join(TOOLS, "harness", "vmm_console.py")
    with tempfile.TemporaryDirectory() as tmp:
        ca_pem, server_pem, server_key = generate_certs(tmp)
        grant_py = write_grant_script(tmp)

        # Happy path: a 101 handshake relays "login: ", echoes stdin, pongs, closes.
        srv = FakeWS(vmod, server_pem, server_key)
        srv.start()
        srv.bound.wait(timeout=5)
        grant_cmd = (f"python3 {grant_py} "
                     f"https://127.0.0.1:{srv.port}/console/ticket {ca_pem}")
        result = _read_bridge(vmm_console, grant_cmd, b"type this\r\nquit\r")
        expect("vmm: exits after the server closes", result is not None, "timed out")
        if result is not None:
            expect("vmm: exits 0 after the server's close", result.returncode == 0,
                   f"rc={result.returncode} err={result.stderr[-160:]!r}")
            expect("vmm: receives 'login: ' then the echo of what was typed",
                   b"login: " in result.stdout and b"type this\r\n" in result.stdout,
                   f"stdout={result.stdout!r}")
        expect("vmm: the server got a pong", srv.pong.wait(timeout=5))

        # A bad URL costs no connection: the bridge refuses before it connects.
        bad_srv = FakeWS(vmod, server_pem, server_key)
        bad_srv.start()
        bad_srv.bound.wait(timeout=5)
        bad = (f"http://127.0.0.1:{bad_srv.port}/console/ticket",
               f"https://127.0.0.1:{bad_srv.port}/no-console/ticket")
        for url in bad:
            code = _run_bridge_code(vmm_console, f"python3 {grant_py} {url} {ca_pem}", timeout=10)
            expect("vmm: http scheme / wrong path exits non-zero", code not in (0, None),
                   f"code={code}")
            expect("vmm: no connection attempt for a bad URL", bad_srv.count == 0,
                   f"count={bad_srv.count}")

        # A non-101 handshake also fails, but the client did connect.
        reject = FakeWS(vmod, server_pem, server_key, reject_status="403 Forbidden")
        reject.start()
        reject.bound.wait(timeout=5)
        code = _run_bridge_code(vmm_console,
                                f"python3 {grant_py} https://127.0.0.1:{reject.port}/console/ticket {ca_pem}",
                                timeout=10)
        expect("vmm: HTTP 403 instead of 101 exits non-zero", code not in (0, None),
               f"code={code}")
        expect("vmm: the client did connect for a 403", reject.count == 1,
               f"count={reject.count}")

        srv.join(timeout=5)
        bad_srv.join(timeout=5)
        reject.join(timeout=5)


def test_console_argv():
    """With CONSOLE_TRANSPORT unset, console_mcp still builds the same ssh argv
    as before. pyte is only the terminal emulator, so stub it to import the
    module without that dependency."""
    try:
        import pyte  # noqa: F401
    except ImportError:
        sys.modules["pyte"] = types.SimpleNamespace(Screen=_Noop, ByteStream=_Noop)
    mod = load_harness_mod("console_mcp", "harness/console_mcp.py")
    want = ["-tt", "-o", "BatchMode=yes", "--", "host.example.com", "doas", "vm", "console", "hbinst0"]
    with patch.object(mod, "HOST", "host.example.com"), patch.object(mod, "VM", "hbinst0"), \
            patch.object(mod, "LOG", os.path.join(tempfile.gettempdir(), "x.jsonl")), patch.object(mod, "TRANSPORT", ""):
        expect("console: default transport still builds the ssh argv", mod.ssh_argv() == want)
        with patch.object(mod.pexpect, "spawn", return_value=object()) as sp:
            mod.attach()
        expect("console: default transport spawns ssh with that argv",
               sp.call_args.args == ("ssh", want), f"{sp.call_args}")
    # The vmm transport keeps the safety checks: an evidence log and a
    # disposable installer VM name are still required.
    for label, vm, log in (("no log", "hbt151u", ""), ("wrong VM name", "hbvm140", os.path.join(tempfile.gettempdir(), "x.jsonl"))):
        with patch.object(mod, "VM", vm), patch.object(mod, "LOG", log), \
                patch.object(mod, "TRANSPORT", "vmm"), \
                patch.dict(os.environ, {"CONSOLE_GRANT_CMD": "true"}), \
                patch.object(mod.pexpect, "spawn", return_value=object()) as sp:
            try:
                mod.attach()
                refused = False
            except SystemExit as exc:
                refused = exc.code not in (0, None)
        expect(f"console: vmm refuses {label}", refused and sp.call_count == 0)


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
    test_vmm_console()
    test_console_argv()
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
