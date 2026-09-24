#!/usr/bin/env python3
"""Minimal MCP stdio server exposing ONE tool: run a shell command on a
disposable test machine (a throwaway VM or jail), and nowhere else.

The model under test gets this tool and no built-in tools, so it has no way to
act on the machine running the harness. The tool connects DIRECTLY to the test
machine with a key that exists only for that machine (the machine runs its own
sshd on its own address). It never goes through a real server's account, so
the worst the model can do is damage the throwaway machine, which is rolled
back from a snapshot afterwards.

Before any command runs, the server checks that the target is a disposable test
machine: the file /etc/hbskills-target must exist there and contain exactly
TARGET_NAME. Anything else (a typo, a real server) is refused at startup.

Configuration (environment):

  TARGET_SSH      argv to reach the test machine; must start with an ssh binary,
                  e.g. "ssh -i key -o BatchMode=yes root@192.0.2.10"
  TARGET_NAME     the name written in /etc/hbskills-target on that machine
  TARGET_LOG      required: every command and its full result are appended
                  here (JSON lines), so every result has an evidence trail
  TARGET_EXEC     optional remote prefix that runs one sh -c string
                  (default "/bin/sh -c")
  TARGET_TIMEOUT  optional: seconds per command (default 900)

Results keep apart failures that must never be confused:
  - transport_error: the command never started on the target (the start marker
    the target prints first is missing);
  - transport_lost: it started, but the connection ended before it finished
    (the end marker, printed on the target with the real exit status, is missing);
  - timed_out: timeout(1) on the target stopped it (exit 124 AND the full
    timeout elapsed; a command's own exit 124 is not this);
  - a non-zero exit_status from the end marker: it ran, finished and failed.

No dependencies beyond the Python standard library."""
import json, os, re, shlex, subprocess, sys, time

START = "__HB_TARGET_START__"
END = "__HB_TARGET_END__"
MARKER = "/etc/hbskills-target"
REPLY_LIMIT = 20000  # characters of stdout shown to the model; the log keeps all
ERR_LIMIT = 8000
SSH_ARG_OPTS = ("-o", "-i", "-p", "-l", "-F", "-J", "-b", "-c", "-D", "-E", "-e",
                "-L", "-m", "-O", "-Q", "-R", "-S", "-W", "-w")
LOCAL_RUN_OPTS = ("proxycommand", "localcommand", "permitlocalcommand")


def die(msg):
    sys.stderr.write(f"target_mcp: {msg}\n")
    sys.exit(2)


def ssh_options(argv):
    """Every -o option name in an ssh argv, in any spelling (-o X=y, -oX=y, -o 'X y')."""
    names = []
    for i, a in enumerate(argv[1:], 1):
        # The option can be attached to -o, or be the next argument, and its
        # name and value can be joined by "=" or by a space.
        if a.startswith("-o") and len(a) > 2:
            val = a[2:]
        elif argv[i - 1] == "-o":
            val = a
        else:
            continue
        names.append(re.split(r"[=\s]+", val.strip(), maxsplit=1)[0].lower())
    return names


# Destinations that mean "this machine"; refused, never bound to.
LOCAL_NAMES = ("localhost", "::1", "[::1]", "0.0.0.0", "::", "::ffff:127.0.0.1")  # nosec B104 -- a deny list, nothing binds here


def check_config(ssh, name, log_path):
    """Sanity checks against obviously wrong configurations. They cannot prove
    where ssh really goes (ssh config files can redirect it); the real guard is
    verify_target(), which refuses any machine without the test marker."""
    if not ssh or os.path.basename(ssh[0]) != "ssh":
        die(f"TARGET_SSH must start with an ssh binary, got {ssh!r}")
    bad = [o for o in ssh_options(ssh) if o in LOCAL_RUN_OPTS]
    if bad:
        die(f"TARGET_SSH must not set {bad[0]}: it can run commands locally")
    positional = [a for i, a in enumerate(ssh[1:], 1) if not a.startswith("-") and ssh[i - 1] not in SSH_ARG_OPTS]
    if len(positional) != 1:
        die(f"TARGET_SSH must name exactly one destination and no remote command, got {positional!r}")
    host = positional[0].split("@")[-1].lower()
    if host in LOCAL_NAMES or host.startswith("127.") or host == "127.1":
        die(f"TARGET_SSH points at this machine ({host})")
    if not name:
        die("TARGET_NAME is required (the contents of /etc/hbskills-target on the target)")
    if not log_path:
        die("TARGET_LOG is required: every run must leave an evidence trail")
    try:
        open(log_path, "a").close()
    except OSError as e:
        die(f"cannot open TARGET_LOG {log_path}: {e}")


SSH = shlex.split(os.environ.get("TARGET_SSH", ""))
NAME = os.environ.get("TARGET_NAME", "").strip()
LOG = os.environ.get("TARGET_LOG", "")
EXEC = os.environ.get("TARGET_EXEC", "/bin/sh -c").strip() or "/bin/sh -c"
try:
    TIMEOUT = int(os.environ.get("TARGET_TIMEOUT", "900"))
except ValueError:
    die("TARGET_TIMEOUT must be an integer")
check_config(SSH, NAME, LOG)

TOOL = {
    "name": "run_on_target",
    "description": "Run one shell command (sh syntax) as root on the FreeBSD test machine and "
                   "return its exit status, stdout and stderr. This is the only way to act on the machine.",
    "inputSchema": {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The shell command to run."}},
        "required": ["command"],
    },
}


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def log(entry):
    """Append to the evidence log; False if that failed."""
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except OSError as e:
        sys.stderr.write(f"target_mcp: cannot write log {LOG}: {e}\n")
        return False


def text(b):
    if b is None:
        return ""
    return b.decode("utf-8", errors="replace") if isinstance(b, bytes) else b


def remote_call(inner, limit):
    """Run one sh string on the target; return (stdout, stderr, status)."""
    remote = EXEC + " " + shlex.quote(inner)
    try:
        # stdin=DEVNULL: ssh must never read the MCP stream on our stdin (it
        # would swallow the model's pending requests).
        p = subprocess.run(SSH + [remote], stdin=subprocess.DEVNULL, capture_output=True, timeout=limit)
        return text(p.stdout), text(p.stderr), p.returncode
    except subprocess.TimeoutExpired as e:
        return text(e.stdout), text(e.stderr) + f"\n(harness: no reply after {limit}s)", None
    except Exception as e:  # never let a harness fault kill the server or hide a result
        return "", f"harness error: {e!r}", None


def verify_target():
    """Refuse to run anything unless the target proves it is a disposable test machine."""
    out, err, status = remote_call(f"cat {MARKER}", 60)
    if status != 0 or out.strip() != NAME:
        die(f"target is not the disposable test machine {NAME!r}: {MARKER} says {out.strip()!r} "
            f"(status {status}, {err.strip()[:200]!r}); refusing to run anything")
    sys.stderr.write(f"target_mcp: verified target {NAME!r} via {SSH!r}; log {LOG}\n")


def parse(out, err, status, began):
    """Classify a finished call from its start/end markers."""
    at = out.find(START + "\n")
    if at < 0:
        return "transport_error", status, out, err
    out = out[at + len(START) + 1:]  # anything before the marker is login-shell noise
    body, _, last = out.rstrip("\n").rpartition("\n")
    fields = last.split(" ")
    if len(fields) != 2 or fields[0] != END or not fields[1].isdigit():
        return "transport_lost", status, out, err
    status = int(fields[1])
    out = body  # the target printed <output>\n<END> <rc>: body is the output exactly
    # timeout(1) exits 124 when it fires (FreeBSD: even with -s KILL); a command
    # can also exit 124 itself. Only elapsed time tells them apart.
    if status == 124 and time.monotonic() - began >= TIMEOUT - 1:
        return "timed_out", status, out, err + f"\n(target: command stopped after {TIMEOUT}s by timeout(1))"
    return "ran", status, out, err


def run(command):
    # The target prints START, runs the command under timeout(1) (so the command
    # itself is killed on the target when time is up), then prints END and the
    # command's own exit status on a line of its own.
    inner = (f"printf '%s\\n' {START}; "
             f"timeout -s KILL {TIMEOUT} /bin/sh -c {shlex.quote(command)}; rc=$?; "
             f"printf '\\n%s %s\\n' {END} \"$rc\"")
    if not log({"event": "start", "command": command}):
        # No evidence trail, no command: a result nobody can check is not a result.
        return {"kind": "harness_error", "exit_status": None, "stdout": "",
                "stderr": f"the evidence log {LOG} could not be written; the command was NOT run"}
    began = time.monotonic()
    out, err, status = remote_call(inner, TIMEOUT + 60)
    kind, status, out, err = parse(out, err, status, began)
    res = {"kind": kind, "exit_status": status, "stdout": out, "stderr": err}
    if not log({"event": "end", "command": command, **res}):
        res["stderr"] += "\n(harness: this result could NOT be written to the evidence log)"
        res["unlogged"] = True
    return res


def clip(s, limit, label):
    return s if len(s) <= limit else f"({label} truncated to the last {limit} characters)\n" + s[-limit:]


def render(r):
    """The text the model sees, and whether it is an error."""
    err = clip(r["stderr"], ERR_LIMIT, "stderr")
    if r["kind"] == "harness_error":
        return f"HARNESS ERROR: {r['stderr']}", True
    if r["kind"] == "transport_error":
        return ("TRANSPORT ERROR: the start marker was never seen, so the command most likely did not "
                "start on the test machine (could not reach it).\n"
                f"exit_status: {r['exit_status']}\n--- stderr ---\n{err}"), True
    if r["kind"] == "transport_lost":
        return ("TRANSPORT LOST: the command started on the test machine but the connection ended "
                "before it finished; its result is unknown.\n--- stdout so far ---\n"
                f"{clip(r['stdout'], REPLY_LIMIT, 'stdout')}\n--- stderr ---\n{err}"), True
    return (f"exit_status: {r['exit_status']}\n--- stdout ---\n{clip(r['stdout'], REPLY_LIMIT, 'stdout')}\n"
            f"--- stderr ---\n{err}"), r["exit_status"] != 0 or r.get("unlogged", False)


def reply(rid, body, is_error):
    send({"jsonrpc": "2.0", "id": rid,
          "result": {"content": [{"type": "text", "text": body}], "isError": is_error}})


def handle(req):
    rid, method = req.get("id"), req.get("method")
    params = req.get("params") if isinstance(req.get("params"), dict) else {}
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "target", "version": "3"}}})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": rid, "result": {"tools": [TOOL]}})
    elif method == "tools/call":
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        command = args.get("command")
        if not isinstance(command, str) or not command.strip():
            reply(rid, "error: 'command' must be a non-empty string; nothing was run", True)
        else:
            reply(rid, *render(run(command)))
    elif method == "ping":
        send({"jsonrpc": "2.0", "id": rid, "result": {}})
    else:
        send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown method {method}"}})


def main():
    verify_target()
    for line in sys.stdin:
        try:
            req = json.loads(line)
        except ValueError:
            continue
        if isinstance(req, dict) and req.get("id") is not None:  # skip notifications
            handle(req)


if __name__ == "__main__":
    main()
