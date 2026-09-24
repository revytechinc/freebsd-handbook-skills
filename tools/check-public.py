#!/usr/bin/env python3
"""Refuse to publish addresses, personal data or private hostnames.

Checks the files staged for commit (or the files given as arguments) and exits
non-zero if any of them contains:

  - an IPv4 or IPv6 address that is not in a documentation range
    (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32, 3fff::/20),
    a private or special-purpose range (10/8, 172.16/12, 192.168/16,
    100.64/10, 127/8, 169.254/16, fe80::/10, fc00::/7, ::1, 0.0.0.0,
    255.255.255.255, multicast), or a netmask-shaped value (255.x.x.x);
  - a MAC address other than the RFC 7042 documentation block 00:00:5e:00:53:xx;
  - an e-mail address outside example.org / example.com / example.net, other
    than a few named FreeBSD project role addresses;
  - a name listed in the private deny file (.publish-deny, one entry per line,
    git-ignored so the list itself is never published).

Usage:  tools/check-public.py                    # the STAGED content (what will be committed)
        tools/check-public.py FILE...            # given files, as they are on disk
        tools/check-public.py --all              # every tracked file (used by CI)
        add --no-deny-list where the private deny list is not available (CI)
"""
import ipaddress, os, re, subprocess, sys

# The ranges below are the allow-list this checker exists to enforce: they are
# documentation and private ranges, never real hosts.
ALLOWED_NETS = [ipaddress.ip_network(n) for n in (
    "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24",          # documentation, RFC 5737
    "2001:db8::/32", "3fff::/20",                                  # documentation, RFC 3849 / 9637
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",  # NOSONAR python:S1313 -- private ranges (allow-list)
    "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",  # NOSONAR python:S1313 -- special-purpose (allow-list)
    "0.0.0.0/8", "255.255.255.255/32", "224.0.0.0/4",  # NOSONAR python:S1313 -- special-purpose (allow-list)
    # 0.0.0.0/8 ("this network", RFC 1122) is never routed. It must stay /8:
    # IPv4-compatible IPv6 such as C++ "::abs" (read as ::ab) maps into it.
    "::1/128", "::/128", "fe80::/10", "fc00::/7", "ff00::/8")]
ALLOWED_MAIL_DOMAINS = ("example.org", "example.com", "example.net")
# The FreeBSD project's public role addresses (never individual people's).
ALLOWED_MAIL_ADDRESSES = ("freebsd-questions@freebsd.org", "security-officer@freebsd.org",
                          "secteam@freebsd.org", "doc@freebsd.org", "ports@freebsd.org",
                          "bugmeister@freebsd.org", "webmaster@freebsd.org")
DOC_MAC_PREFIXES = ("00:00:5e:00:53:", "00-00-5e-00-53-")          # RFC 7042

# The lookahead lets a sentence end right after an address ("... 192.0.2.1.")
# while still refusing to match inside a longer dotted number.
IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/\d{1,2})?(?!\w|\.\d)")
MAX_ADDR = 45  # longest textual IPv6 address
# Anything that could be IPv6: a run of hex digits and colons with at least two
# colons. ipaddress decides whether it really is one.
# (dots included, for an embedded IPv4 tail such as ::ffff:192.0.2.1)
IPV6_CANDIDATE = re.compile(r"(?<![\w.])([0-9A-Fa-f:.]{2,})(?:/\d{1,3})?")
# GitHub Actions workflow commands ("::error::msg", "::warning file=x::msg")
# start with "::e" and similar, which parse as IPv6 addresses. The line is NOT
# rewritten (rewriting split real addresses such as "2a00::1" that sit in the
# parameters); an IPv6 candidate is skipped only when it starts exactly at a
# command token. The names are listed, not matched as any word, because a
# generic word would match hex groups. The lookbehind stops the "::" at the end
# of a real address ("2001:db8::add") from being read as a command.
ANNOTATION = re.compile(
    r"(?<![0-9A-Fa-f:])::(?:error|warning|notice|debug|group|endgroup|add-mask|stop-commands|echo"
    r"|add-matcher|remove-matcher|set-output|save-state|add-path|set-env)(?=[\s:])")
MAC = re.compile(r"(?<![\w:-])((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})(?![\w:-])")
MAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = "tools/check-public.py"   # its own allow-list would trip it; skipped by exact path only
DENY_FILE = ".publish-deny"      # must never be committed


def git_names(*args):
    out = subprocess.run(["git", "-C", ROOT, *args, "-z"], capture_output=True, check=True).stdout
    return [n.decode("utf-8", "surrogateescape") for n in out.split(b"\0") if n]


def staged_blob(name):
    """The staged content of name (what the commit will contain), or None."""
    p = subprocess.run(["git", "-C", ROOT, "show", f":{name}"], capture_output=True)
    return p.stdout.decode("utf-8", errors="replace") if p.returncode == 0 else None


def disk_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def deny_patterns(required):
    p = os.path.join(ROOT, ".publish-deny")
    if not os.path.exists(p):
        if required:
            print("check-public: .publish-deny (the private name list) is missing; "
                  "pass --no-deny-list to run without it", file=sys.stderr)
            sys.exit(2)
        return []
    with open(p) as f:
        return [re.compile(re.escape(l.strip()), re.I) for l in f if l.strip() and not l.startswith("#")]


def is_allowed_ip(text):
    """True when text is not an address, or is an address we may publish."""
    text = text.split("%")[0]
    if "." in text and ":" not in text:  # IPv4: ipaddress rejects leading zeros, so drop them
        text = ".".join(str(int(o)) for o in text.split("."))
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return True
    if ip.version == 4 and text.startswith("255."):
        return True  # a netmask, not a host
    if any(ip in n for n in ALLOWED_NETS):
        return True
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped  # ::ffff:a.b.c.d is judged by its IPv4 address
    elif ip.version == 6 and ip in ipaddress.ip_network("::/96"):
        # Deprecated IPv4-compatible form (RFC 4291 2.5.5.1), never routed, and
        # also what C++ "::abs" parses as. Judge it by its IPv4 part, so
        # "::192.0.2.1" is still caught.
        ip = ipaddress.ip_address(int(ip))
    return any(ip in n for n in ALLOWED_NETS)


def trim_to_address(cand):
    """The candidate pattern also takes in what follows an address: a full stop
    ("... 2001:db8::1."), a colon ("2001:db8::1: note"), or the "::" closing a
    CI annotation and the hex letters after it ("2001:db8::1::bad" reads as
    "...::1::ba"). If the whole candidate does not parse, use the longest prefix
    ending just before a ':' or '.' that does. If none does, the candidate is
    returned unchanged and is then not treated as an address. Known gap: an
    address whose last group runs straight into a hex letter ("...::8888a")
    has no such prefix and is missed."""
    for end in range(len(cand), 1, -1):
        if end < len(cand) and cand[end] not in ".:":
            continue
        probe = cand[:end]
        if probe.count(":") < 2:
            break
        try:
            ipaddress.ip_address(probe)
            return probe
        except ValueError:
            continue
    return cand


def ip_problems(line):
    commands = {m.start() for m in ANNOTATION.finditer(line)}
    found = [f"public IPv4 address {m.group(0)}" for m in IPV4.finditer(line)
             if not is_allowed_ip(m.group(1))]
    for m in IPV6_CANDIDATE.finditer(line):
        if m.start() in commands:
            continue  # "::error" and the like, not an address
        cand = m.group(1)
        cand = cand.lstrip(":") if cand.startswith(":") and not cand.startswith("::") else cand
        cand = trim_to_address(cand)
        if cand.count(":") >= 2 and not MAC.fullmatch(cand) and not is_allowed_ip(cand):
            found.append(f"public IPv6 address {m.group(0)}")
    return found


def mac_problems(line):
    return [f"hardware (MAC) address {m.group(1)}" for m in MAC.finditer(line)
            if not m.group(1).lower().startswith(DOC_MAC_PREFIXES)]


def mail_problems(line):
    out = []
    for m in MAIL.finditer(line):
        dom = m.group(1).lower()
        if IPV4.fullmatch(dom):
            continue  # user@<IPv4> is an ssh destination; the IP check judges the address
        if m.group(0).lower() in ALLOWED_MAIL_ADDRESSES:
            continue
        if not any(dom == d or dom.endswith("." + d) for d in ALLOWED_MAIL_DOMAINS):
            out.append(f"e-mail address {m.group(0)}")
    return out


def deny_problems(line, deny):
    return ["private name matching the deny list" for pat in deny if pat.search(line)]


def check(content, deny):
    if content is None:
        return [(0, "could not read this file, so it could not be checked")]
    problems = []
    for n, line in enumerate(content.splitlines(), 1):
        for what in ip_problems(line) + mac_problems(line) + mail_problems(line) + deny_problems(line, deny):
            problems.append((n, what))
    return problems


FLAGS = ("--all", "--no-deny-list")


def targets(argv):
    """(display name, content) for everything to check."""
    unknown = [a for a in argv if a.startswith("--") and a not in FLAGS]
    if unknown:
        print(f"check-public: unknown option(s) {unknown}; known: {list(FLAGS)}", file=sys.stderr)
        sys.exit(2)
    if "--all" in argv:
        names = git_names("ls-files")
        if not names:
            print("check-public: --all found no tracked files; refusing to report clean", file=sys.stderr)
            sys.exit(2)
        return [(n, disk_text(os.path.join(ROOT, n))) for n in names]
    paths = [a for a in argv if not a.startswith("--")]
    if paths:
        return [(os.path.relpath(os.path.abspath(p), ROOT), disk_text(p)) for p in paths]
    return [(n, staged_blob(n)) for n in git_names("diff", "--cached", "--name-only", "--diff-filter=ACMR")]


def main():
    argv = sys.argv[1:]
    deny = deny_patterns(required="--no-deny-list" not in argv)
    files = targets(argv)
    bad = 0
    for name, content in files:
        if os.path.basename(name) == DENY_FILE:
            print(f"{name}: the private deny list must never be committed")
            bad += 1
            continue
        if name == SELF:
            continue
        for n, what in check(content, deny):
            print(f"{name}:{n}: {what}")
            bad += 1
    if bad:
        print(f"check-public: {bad} problem(s); replace them with documentation "
              "addresses / example.org before committing", file=sys.stderr)
        sys.exit(1)
    print(f"check-public: {len(files)} file(s) clean")


if __name__ == "__main__":
    # Exit 1 means "found problems" and nothing else: a crash must not look
    # like findings (CI prints different advice for each), so it exits 2.
    try:
        main()
    except Exception:  # noqa: BLE001 -- any crash; SystemExit passes through
        import traceback
        traceback.print_exc()
        sys.exit(2)
