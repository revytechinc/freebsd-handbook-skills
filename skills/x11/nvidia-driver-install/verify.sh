#!/bin/sh
# Independent check for x11/nvidia-driver-install. nvidia-drm-kmod is
# installed. If nvidia-kmod and the nvidia-drm-NN-kmod package were both
# built for the running kernel and carry the same driver version, nvidia-drm
# is in kld_list (as rc.d/kld reads it), its file in /boot/modules belongs to
# that package, and every loader file line setting hw.nvidiadrm.modeset says
# 1; otherwise nvidia-drm
# must be set to load nowhere (kld_list or a loader file).
# Exit 0 when verified, 1 otherwise.
pkg info -e nvidia-drm-kmod || { echo "FAIL: nvidia-drm-kmod not installed"; exit 1; }
k=$(uname -K)
case "$k" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) echo "FAIL: cannot read the kernel version ('$k')"; exit 1 ;; esac
dp=$(pkg query '%n' | grep -E '^nvidia-drm-[0-9]+-kmod$' | head -1)
[ -n "$dp" ] || { echo "FAIL: no nvidia-drm-NN-kmod package"; exit 1; }
ok=yes; d0=
for p in nvidia-kmod "$dp"; do
    v=$(pkg query '%v' "$p") || { echo "FAIL: cannot read $p"; exit 1; }
    b=$(echo "$v" | sed -e 's/[_,].*//' -e 's/.*\.//')
    d=$(echo "$v" | sed -e 's/[_,].*//' -e 's/\.[^.]*$//')
    case "$b" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) echo "FAIL: cannot read the build version of $p ('$v')"; exit 1 ;; esac
    [ "$b" = "$k" ] || ok=no
    [ -z "$d0" ] && d0=$d
    [ "$d" = "$d0" ] || ok=no
done
l=$(sh -c '. /etc/rc.subr && load_rc_config kld && echo "kld_list=$kld_list"') || { echo "FAIL: cannot read kld_list"; exit 1; }
case "$l" in kld_list=*) ;; *) echo "FAIL: cannot read kld_list: $l"; exit 1 ;; esac
inlist=no
for m in ${l#kld_list=}; do m=${m##*/}; m=${m%.ko}; [ "$m" = nvidia-drm ] && inlist=yes; done
inloader=no
[ -n "$(grep -lsiE '^[[:space:]]*nvidia[-_]drm_load[[:space:]]*=[[:space:]]*"?yes"?[[:space:]]*(#.*)?$' /boot/loader.conf /boot/loader.conf.local /boot/loader.conf.d/*.conf)" ] && inloader=yes
if [ "$ok" = yes ]; then
    [ "$inlist" = yes ] || { echo "FAIL: the modules match the kernel ($k) but nvidia-drm is not in kld_list"; exit 1; }
    o=$(pkg which -q /boot/modules/nvidia-drm.ko)
    case "$o" in "$dp"-[0-9]*) ;; *) echo "FAIL: /boot/modules/nvidia-drm.ko does not belong to $dp ('$o')"; exit 1 ;; esac
    # Every loader file the loader reads; a later one overrides an earlier one,
    # so every line that sets it must say 1.
    ms=$(grep -hE '^[[:space:]]*hw\.nvidiadrm\.modeset[[:space:]]*=' /boot/loader.conf /boot/loader.conf.local /boot/loader.conf.d/*.conf 2>/dev/null)
    [ -n "$ms" ] || { echo "FAIL: hw.nvidiadrm.modeset is not set in any loader file"; exit 1; }
    echo "$ms" | grep -qvE '=[[:space:]]*"?1"?[[:space:]]*(#.*)?$' && { echo "FAIL: a loader file sets hw.nvidiadrm.modeset to another value: $ms"; exit 1; }
    echo "OK: nvidia-kmod and $dp built for $k, driver $d0; nvidia-drm enabled with modeset"
else
    [ "$inlist" = no ] && [ "$inloader" = no ] || { echo "FAIL: the modules do not match the kernel ($k) or each other, yet nvidia-drm is set to load"; exit 1; }
    echo "OK: modules do not match kernel $k or each other: installed, correctly not enabled"
fi
