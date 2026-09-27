#!/bin/sh
# Independent check for basics/file-protect (test input
# FILE=/home/hbtest6/contract.txt): contract.txt has the flag sunlnk added to
# the flags it had, and its mode, owner and content are unchanged; no other
# file in the home has sunlnk; the securelevel is still -1; and the file
# really cannot be renamed (the same protection as removal).
# Exit 0 / 1.
F=/home/hbtest6/contract.txt
read -r f0 m0 o0 c0 < /var/db/hb-fileprot || { echo "FAIL: no values recorded by setup"; exit 1; }
s=$(stat -f '%Sf %Mp%Lp %Su:%Sg' "$F") || { echo "FAIL: contract.txt missing"; exit 1; }
read -r f m o <<EOT
$s
EOT
case "$f0" in -) want=sunlnk ;; *) want="sunlnk,$f0" ;; esac
[ "$f" = "$want" ] || { echo "FAIL: flags are '$f', expected '$want'"; exit 1; }
[ "$m $o" = "$m0 $o0" ] || { echo "FAIL: mode/owner now '$m $o', was '$m0 $o0'"; exit 1; }
[ "$(sha256 -q "$F")" = "$c0" ] || { echo "FAIL: content changed"; exit 1; }
l=$(find /home/hbtest6 -flags +sunlnk) || { echo "FAIL: find failed"; exit 1; }
[ "$l" = "$F" ] || { echo "FAIL: files with sunlnk: '$l'"; exit 1; }
[ "$(sysctl -n kern.securelevel)" = "-1" ] || { echo "FAIL: securelevel changed"; exit 1; }
if mv "$F" "$F.hbprobe" 2>/dev/null; then
    mv "$F.hbprobe" "$F"; echo "FAIL: contract.txt could be renamed"; exit 1
fi
echo "OK: contract.txt has sunlnk"; exit 0
