#!/usr/bin/env python3
"""Run a skill's verify.sh on an installed system through its serial console.

For skills done at a console (the FreeBSD installer), the independent check
cannot use ssh: the freshly installed system has no key for the harness. This
script attaches to the VM's console (`ssh HOST doas vm console VM`), waits for
the installed system's login prompt, logs in as root with the password the
test inputs gave the installer, types verify.sh into a file there, checks
its sha256, runs it with /bin/sh, and reads its output and exit status back
between markers.

Usage: HBV_ROOTPW=... console_verify.py HOST VM VERIFY_SH
(the password comes from the environment rather than the command line; it is
a throwaway test value, also in test-inputs.txt and the run's logs).
Exit status: that of verify.sh (0 or 1); 3 if the console showed a shell
instead of a login prompt, or root's password was refused (the machine is not
in the state the skill leaves it in: a verdict);
2 if the console or the markers failed, or anything unexpected happened (an
infrastructure failure, never a verdict).

verify.sh must not contain "~" (cu(1) on the host treats "~" at the start of
a line as a command) and must not contain the marker words."""
import hashlib, os, re, secrets, sys, time

import pexpect

# The markers carry a fresh random part each run, so text on the machine
# (a host name, say, echoed in a failure message) cannot forge them.
NONCE = secrets.token_hex(8)
BEGIN, END, EOF_WORD = f"HBV_BEGIN_{NONCE}", f"HBV_END_{NONCE}", "HBV_EOF_7f3a"


def fail(msg):
    sys.stderr.write(f"console_verify: {msg}\n")
    sys.exit(2)


def wait_for_login(c):
    """Wait (up to 10 minutes, the installed system may still be booting) for
    a login prompt. The only key sent is a bare Enter, which at a login
    prompt just prints it again. Nothing else is typed to get there: no
    Ctrl-C, no "exit". Typed into a shell the model left open (in the
    installer, say), those would move the installer on, and the verifier
    would finish the installation for the model."""
    c.expect([r"Connected", pexpect.TIMEOUT, pexpect.EOF], timeout=10)
    time.sleep(2)  # ssh must have its terminal in raw mode before any key
    t0, shells = time.monotonic(), 0
    while time.monotonic() - t0 < 600:
        c.send("\r")
        i = c.expect([r"login: ", r"[#$>] $", pexpect.TIMEOUT, pexpect.EOF], timeout=20)
        if i == 0:
            return
        # A shell prompt twice in a row (a boot message could end like one).
        shells = shells + 1 if i == 1 else 0
        if shells == 2:
            sys.stderr.write("console_verify: the console shows a shell prompt, not a login prompt\n")
            sys.exit(3)
        if i == 3:
            fail("console connection ended while waiting for the login prompt")
    fail("no login prompt on the installed system within 10 minutes")


def login_root(c, pw):
    c.sendline("root")
    i = c.expect([r"Password:", r"# $", pexpect.TIMEOUT], timeout=30)
    if i == 1:
        # No password asked for: root has none, so the skill did not set it.
        sys.stderr.write("console_verify: root logged in without a password\n")
        sys.exit(3)
    if i == 2:
        fail("no password prompt after typing root")
    c.sendline(pw)
    i = c.expect([r"# $", r"Login incorrect", pexpect.TIMEOUT], timeout=60)
    if i == 1:
        sys.stderr.write("console_verify: root's password was refused\n")
        sys.exit(3)
    if i == 2:
        fail("no shell prompt after logging in as root")
    # Line editing off, so each typed line is echoed as it is (libedit scrolls
    # long lines sideways, and the echo would not contain the text).
    c.send("set +E +V\r")
    c.expect([r"# $", pexpect.TIMEOUT], timeout=20)


def type_line(c, line):
    """Type one line and wait for its echo (typed all at once, the tty's input
    queue, about 1 KB, overflowed and dropped the rest)."""
    c.send(line + "\r")
    tail = line.strip()[-24:]
    if tail and c.expect_exact([tail, pexpect.TIMEOUT], timeout=20) != 0:
        fail(f"the console did not echo a line of verify.sh: {tail!r}")


def run_script(c, script):
    """Copy the script into a file on the machine, check its sha256 against
    the local copy (a line lost on the way would silently skip a check), then
    run it; return (exit status, output)."""
    text = script.rstrip() + "\n"
    want = hashlib.sha256(text.encode()).hexdigest()
    type_line(c, f"cat > /tmp/hbv_7f3a.sh <<'{EOF_WORD}'")
    for line in text.rstrip("\n").split("\n"):
        type_line(c, line)
    type_line(c, EOF_WORD)
    # The markers are printed by commands typed on ONE line, so nothing typed
    # later can be interleaved with the script's output.
    type_line(c, f'[ "$(sha256 -q /tmp/hbv_7f3a.sh)" = {want} ] && echo {BEGIN} && '
                 f'sh /tmp/hbv_7f3a.sh; echo {END} $?; rm -f /tmp/hbv_7f3a.sh')
    i = c.expect([rf"\n{BEGIN}", rf"\n{END} (\d+)", pexpect.TIMEOUT], timeout=60)
    if i == 1:
        fail("verify.sh did not arrive intact on the machine (checksum differs)")
    if i == 2:
        fail("no answer from the machine after typing verify.sh")
    if c.expect([rf"\n{END} (\d+)\r?\n", pexpect.TIMEOUT], timeout=600) != 0:
        fail("verify.sh did not finish within 10 minutes")
    rc = int(c.match.group(1))
    out = c.before.replace("\r", "")
    lines = [l for l in out.split("\n") if l.strip()]
    return rc, "\n".join(lines).strip()


def main():
    if len(sys.argv) != 4:
        fail("usage: HBV_ROOTPW=... console_verify.py HOST VM VERIFY_SH")
    host, vm, path = sys.argv[1:]
    pw = os.environ.get("HBV_ROOTPW", "")
    # The password is typed at the start of a line on cu(1) on the VM host:
    # "~" there would be a cu command (~! runs a shell on the host).
    if not re.fullmatch(r"[!-}]{1,128}", pw) or "~" in pw:
        fail("HBV_ROOTPW must be 1 to 128 printable characters, no spaces, no '~'")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}", host):
        fail(f"refusing console host {host!r}: a host name only")
    if not re.fullmatch(r"hbinst[a-z0-9]{1,20}", vm):
        fail(f"refusing VM {vm!r}: only disposable installer VMs (hbinst...)")
    script = open(path).read()
    if "~" in script or any(w in script for w in (BEGIN, END, EOF_WORD)):
        fail("verify.sh must not contain '~' or the marker words")
    c = pexpect.spawn("ssh", ["-tt", "-o", "BatchMode=yes", "--", host, "doas", "vm", "console", vm],
                      timeout=30, encoding="utf-8", codec_errors="replace")
    wait_for_login(c)
    try:
        login_root(c, pw)
        rc, out = run_script(c, script)
    finally:
        # Log out on every path, so no root shell is left on the console.
        c.send("\x03\rexit\r")
        time.sleep(1)
        c.close(force=True)
    sys.stdout.write(out + "\n")
    if rc not in (0, 1):
        # A syntax error (2) or a missing command (127) is a broken check,
        # not a verdict, as on the ssh path.
        fail(f"verify.sh exited {rc}; it must exit 0 or 1")
    sys.exit(rc)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, pexpect.ExceptionPexpect) as e:
        fail(f"{type(e).__name__}: {e}")
