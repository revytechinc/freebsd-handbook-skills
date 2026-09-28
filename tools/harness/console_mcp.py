#!/usr/bin/env python3
"""Minimal MCP stdio server exposing ONE tool: type keys on the serial console
of a disposable installer VM, and read the screen back.

It is the console counterpart of target_mcp.py, for skills that are carried
out at a console rather than in a shell (the FreeBSD installer). The model
under test gets this tool and no built-in tools.

The console is reached as `ssh VMHOST doas vm console VMNAME`, which runs
cu(1) on the VM host. cu treats "~" at the start of a line as a command to
itself (~! even starts a shell ON THE HOST), so this server refuses any key
text that contains "~" and any character that is not printable. Only
printable characters and the named keys reach the console. (<PgUp> and
<PgDn> send "~" as the last byte of an escape sequence, never at the start
of a line.)

The screen is kept in a terminal emulator (pyte) for the whole session, so
every reply shows the full current screen, not just new output. Text shown in
reverse video or on a coloured background (the highlighted menu item or button
in the installer) is marked with « and ».

The arrow keys are sent in the form a VT100 in keypad ("application") mode
sends (ESC O A...), which is what the installer's menus expect once the
terminal type vt100 is chosen; the ESC [ A form made the installer read a
lone Escape and quit.

Configuration (environment):

  CONSOLE_HOST   the VM host's name, as given to ssh (letters, digits, "."
                 and "-" only)
  CONSOLE_VM     the VM's name; must start with "hbinst" (disposable
                 installer VMs only)
  CONSOLE_LOG    required: every key sequence and the resulting screen are
                 appended here (JSON lines)
  PYTHONPATH     must let Python import pyte and pexpect

Named keys: <Enter> <Tab> <BTab> <Space> <Esc> <Up> <Down> <Left> <Right>
<Backspace> <Home> <End> <PgUp> <PgDn> <F1>..<F4>."""
import json, os, re, sys, time

import pexpect
import pyte

HOST = os.environ.get("CONSOLE_HOST", "").strip()
VM = os.environ.get("CONSOLE_VM", "").strip()
LOG = os.environ.get("CONSOLE_LOG", "")
COLS, ROWS = 80, 25
QUIET = 2.0       # seconds without output that count as "the screen has settled"
MAX_WAIT = 120.0  # longest a single call waits for the screen to settle

KEYS = {
    "Enter": "\r", "Tab": "\t", "BTab": "\x1b[Z", "Space": " ", "Esc": "\x1b",
    "Up": "\x1bOA", "Down": "\x1bOB", "Right": "\x1bOC", "Left": "\x1bOD",
    "Backspace": "\x7f", "Home": "\x1b[H", "End": "\x1b[F",
    "PgUp": "\x1b[5~", "PgDn": "\x1b[6~",
    "F1": "\x1bOP", "F2": "\x1bOQ", "F3": "\x1bOR", "F4": "\x1bOS",
}
TOKEN = re.compile(r"<(" + "|".join(KEYS) + r")>")


def die(msg):
    sys.stderr.write(f"console_mcp: {msg}\n")
    sys.exit(2)


if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}", HOST):
    die("CONSOLE_HOST must be the VM host's name (letters, digits, '.' and '-')")
if not re.fullmatch(r"hbinst[a-z0-9]{1,20}", VM):
    die(f"CONSOLE_VM must be a disposable installer VM named hbinst..., got {VM!r}")
if not LOG:
    die("CONSOLE_LOG is required: every run must leave an evidence trail")

screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)
child = None


def log(entry):
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except OSError as e:
        sys.stderr.write(f"console_mcp: cannot write log {LOG}: {e}\n")
        return False


def attach():
    global child
    child = pexpect.spawn("ssh", ["-tt", "-o", "BatchMode=yes", "--", HOST, "doas", "vm", "console", VM], timeout=5)


def pump(settle=QUIET, limit=MAX_WAIT):
    """Read console output into the screen until it has been quiet for `settle`
    seconds ("settled"), or `limit` seconds have passed ("limit"); "ended" if
    the connection closed."""
    end = time.monotonic() + limit
    last = time.monotonic()
    while time.monotonic() < end:
        try:
            data = child.read_nonblocking(65536, timeout=0.5)
            stream.feed(data)
            last = time.monotonic()
        except pexpect.TIMEOUT:
            if time.monotonic() - last >= settle:
                return "settled"
        except pexpect.EOF:
            return "ended"
    return "limit"


def render():
    """The screen as text; runs of highlighted cells wrapped in « and »."""
    lines = []
    for y in range(ROWS):
        row = screen.buffer[y]
        out, hl = [], False
        for x in range(COLS):
            ch = row[x]
            on = bool(ch.reverse) or ch.bg not in ("default", "black")
            if on != hl:
                out.append("\u00ab" if on else "\u00bb")
                hl = on
            out.append(ch.data)
        if hl:
            out.append("\u00bb")
        lines.append("".join(out).rstrip())
    return "\n".join(lines).rstrip("\n")


MAX_KEYS = 1024


def translate(keys):
    """Key text -> bytes to send, or an error string."""
    if len(keys) > MAX_KEYS:
        return None, f"at most {MAX_KEYS} characters of keys per call"
    if "~" in keys:
        return None, "the character ~ is not allowed (it controls the console connection)"
    out, pos = [], 0
    for m in TOKEN.finditer(keys):
        out.append(keys[pos:m.start()])
        out.append(KEYS[m.group(1)])
        pos = m.end()
    out.append(keys[pos:])
    raw = "".join(out)
    plain = TOKEN.sub("", keys)
    if not all(c.isprintable() for c in plain):
        return None, "control characters are only allowed as named keys such as <Enter>"
    return raw, None


TOOL = {
    "name": "console",
    "description": ("Type keys on the FreeBSD installer's console and get the screen back (80x25). "
                    "Printable text is typed as is; named keys: <Enter> <Tab> <BTab> <Space> <Esc> "
                    "<Up> <Down> <Left> <Right> <Backspace> <Home> <End> <PgUp> <PgDn> <F1>..<F4>. "
                    "Highlighted text on the screen is shown between « and ». "
                    "Send an empty string to just wait and read the screen (up to 2 minutes)."),
    "inputSchema": {
        "type": "object",
        "properties": {"keys": {"type": "string", "description": "Keys to type, e.g. \"<Down><Enter>\" or \"myhost<Enter>\"."}},
        "required": ["keys"],
    },
}


def call(keys):
    raw, err = translate(keys)
    if err:
        if not log({"event": "refused", "keys": keys, "reason": err}):
            return "the evidence log could not be written", True
        return err, True
    if not child.isalive():
        return "the console connection has ended; nothing more can be typed", True
    if not log({"event": "keys", "keys": keys}):
        return "the evidence log could not be written; nothing was typed", True
    try:
        if raw:
            child.send(raw)
        state = pump()
    except OSError as e:
        return f"the console connection failed ({e}); nothing more can be typed", True
    shown = render()
    if not log({"event": "screen", "keys": keys, "screen": shown, "state": state}):
        return "the evidence log could not be written; the keys were typed but the screen is not recorded", True
    if state == "ended":
        return shown + "\n(harness: the console connection ended; nothing more can be typed)", True
    if state == "limit":
        shown += "\n(harness: the screen was still changing after 2 minutes)"
    return shown, False


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    attach()
    state = pump(settle=3, limit=20)
    if state == "ended":
        die("the console connection ended at once (is the VM running, or is its console in use?)")
    # What the console showed before the model's first call goes in the log
    # too (the installer's first question may already be on the screen).
    if not log({"event": "screen", "keys": "", "screen": render(), "state": state}):
        die("the evidence log could not be written")
    for line in sys.stdin:
        try:
            req = json.loads(line)
        except ValueError:
            continue
        rid, method = req.get("id"), req.get("method")
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": req.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}}, "serverInfo": {"name": "console", "version": "1"}}})
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": rid, "result": {"tools": [TOOL]}})
        elif method == "tools/call":
            p = req.get("params", {})
            if p.get("name") != "console":
                send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool"}})
                continue
            text, is_err = call(str(p.get("arguments", {}).get("keys", "")))
            send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}], "isError": is_err}})
        elif rid is not None:
            send({"jsonrpc": "2.0", "id": rid, "result": {}})
    # Let go of the console at once, so the verifier can attach to it.
    child.close(force=True)


if __name__ == "__main__":
    main()
