#!/bin/sh
# Preconditions for basics/users-add (test input USER=hbtest1): no such user,
# no such group, no /home/hbtest1.
! pw usershow hbtest1 >/dev/null 2>&1 && ! pw groupshow hbtest1 >/dev/null 2>&1 && [ ! -e /home/hbtest1 ] && [ ! -e /var/mail/hbtest1 ] && [ ! -e /var/cron/tabs/hbtest1 ]
