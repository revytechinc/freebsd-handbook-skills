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
  - an e-mail address outside example.org / example.com / example.net and the
    FreeBSD project's own public addresses;
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
    "0.0.0.0/32", "255.255.255.255/32", "224.0.0.0/4",  # NOSONAR python:S1313 -- special-purpose (allow-list)
    "::1/128", "::/128", "fe80::/10", "fc00::/7", "ff00::/8")]
ALLOWED_MAIL_DOMAINS = ("example.org", "example.com", "example.net", "freebsd.org")
DOC_MAC_PREFIXES = ("00:00:5e:00:53:", "00-00-5e-00-53-")          # RFC 7042

IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/\d{1,2})?(?![\w.])")
MAX_ADDR = 45  # longest textual IPv6 address
# Anything that could be IPv6: a run of hex digits and colons with at least two
# colons. ipaddress decides whether it really is one.
# (dots included, for an embedded IPv4 tail such as ::ffff:192.0.2.1)
IPV6_CANDIDATE = re.compile(r"(?<![\w.])([0-9A-Fa-f:.]{2,})(?:/\d{1,3})?")
MAC = re.compile(r"(?<![\w:-])((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})(?![\w:-])")
MAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ("check-public.py", ".publish-deny")  # the checker's own allow-list and the deny list


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
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped  # ::ffff:a.b.c.d is judged by its IPv4 address
    return any(ip in n for n in ALLOWED_NETS)


def ip_problems(line):
    found = [f"public IPv4 address {m.group(0)}" for m in IPV4.finditer(line)
             if not is_allowed_ip(m.group(1))]
    for m in IPV6_CANDIDATE.finditer(line):
        cand = m.group(1).rstrip(".")  # a sentence may end right after an address
        cand = cand.lstrip(":") if cand.startswith(":") and not cand.startswith("::") else cand
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


def targets(argv):
    """(display name, content) for everything to check."""
    if "--all" in argv:
        return [(n, disk_text(os.path.join(ROOT, n))) for n in git_names("ls-files")]
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
        if os.path.basename(name) in SKIP:
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
    main()
