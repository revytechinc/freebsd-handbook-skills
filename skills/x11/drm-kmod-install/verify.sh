#!/bin/sh
# Independent check for x11/drm-kmod-install (test input MODULE=i915kms).
# A drm-NN-kmod package (from drm-kmod, or built from the ports tree) is
# installed. If its kernel modules were built for the running
# kernel, i915kms is in kld_list and its file is in /boot/modules; if not
# (the end-of-life 14.x releases get modules built for 14.4), i915kms must
# NOT be in kld_list: loading a module built for another kernel can panic.
# Exit 0 when verified, 1 otherwise.
p=$(pkg query '%n' | grep -E '^drm-[0-9]+-kmod$' | head -1)
[ -n "$p" ] || { echo "FAIL: no drm-NN-kmod package installed"; exit 1; }
built=$(pkg query '%v' "$p" | sed -e 's/[_,].*//' -e 's/.*\.//')
kernel=$(uname -K)
case "$built" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) echo "FAIL: cannot read the build version of $p ('$built')"; exit 1 ;; esac
case "$kernel" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) echo "FAIL: cannot read the kernel version ('$kernel')"; exit 1 ;; esac
# kld_list as rc.d/kld reads it (rc.conf and rc.conf.d/kld).
l=$(sh -c '. /etc/rc.subr && load_rc_config kld && echo "kld_list=$kld_list"') || { echo "FAIL: cannot read kld_list"; exit 1; }
case "$l" in kld_list=*) ;; *) echo "FAIL: cannot read kld_list: $l"; exit 1 ;; esac
inlist=no
for m in ${l#kld_list=}; do m=${m##*/}; m=${m%.ko}; [ "$m" = i915kms ] && inlist=yes; done
inloader=no
# Test grep's output, not its status: a missing file in the list makes the
# status 2 even when another file matches.
[ -n "$(grep -lsiE '^[[:space:]]*i915kms_load[[:space:]]*=[[:space:]]*"?yes' /boot/loader.conf /boot/loader.conf.local /boot/loader.conf.d/*.conf)" ] && inloader=yes
if [ "$built" = "$kernel" ]; then
    [ "$inlist" = yes ] || { echo "FAIL: $p matches the kernel ($kernel) but i915kms is not in kld_list"; exit 1; }
    [ -f /boot/modules/i915kms.ko ] || { echo "FAIL: /boot/modules/i915kms.ko missing"; exit 1; }
    echo "OK: $p built for $kernel; i915kms in kld_list"
else
    [ "$inlist" = no ] && [ "$inloader" = no ] || { echo "FAIL: $p was built for $built, the kernel is $kernel, yet i915kms is set to load (kld_list or loader.conf)"; exit 1; }
    echo "OK: $p built for $built, kernel $kernel: installed, correctly not enabled"
fi
