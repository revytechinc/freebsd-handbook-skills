#!/bin/sh
# The true RESULT line for KEYWORD=crontab (not the skill's example). It is
# fixed, not read from the database the run built, so a wrong or
# self-derived result line cannot agree with itself. (Folders left unindexed
# are caught by verify.sh, which checks each folder's database.) On a freshly reset test machine (no
# packages installed) every release above has exactly the two base-system
# pages crontab(1) and crontab(5) matching "crontab", in that order.
echo "RESULT: crontab(1); crontab(5)"
