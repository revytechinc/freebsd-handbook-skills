#!/bin/sh
# Independent check for ports/pkg-branch-latest: the package repository for
# this release (FreeBSD on 14.x, FreeBSD-ports on 15.x and later) uses the
# latest branch; on 14.x no stray FreeBSD-ports repository was added (the
# Handbook command's broken result); on 15.x and later FreeBSD-base is still
# defined and enabled. Exit 0 when verified, 1 otherwise.
out=$(pkg -vv 2>/dev/null) || { echo "FAIL: pkg -vv failed"; exit 1; }
field() { echo "$out" | awk -v r="  $1:" -v f="$2" 'index($0, r)==1 {s=1; next} /^  [A-Za-z-]+:/ {s=0} s && $1==f {print $3; exit}'; }
case "$(freebsd-version -u)" in
    14.*) repo=FreeBSD
          echo "$out" | grep -q '^  FreeBSD-ports:' && { echo "FAIL: a stray FreeBSD-ports repository exists on 14.x"; exit 1; }
          # 14.3 and later ship a FreeBSD-kmods repository; it must stay enabled.
          case "$(freebsd-version -u)" in 14.[0-2]-*) ;;
              *) [ "$(field FreeBSD-kmods enabled)" = "yes," ] || { echo "FAIL: FreeBSD-kmods is missing or not enabled"; exit 1; } ;;
          esac ;;
    *)    repo=FreeBSD-ports
          [ "$(field FreeBSD-base enabled)" = "yes," ] || { echo "FAIL: FreeBSD-base is missing or not enabled"; exit 1; } ;;
esac
[ "$(field "$repo" enabled)" = "yes," ] || { echo "FAIL: $repo is not enabled"; exit 1; }
url=$(field "$repo" url)
case "$url" in
    *'/latest",') echo "OK: $repo $url"; exit 0 ;;
    *) echo "FAIL: $repo url is '$url', not latest"; exit 1 ;;
esac
