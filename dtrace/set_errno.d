#! /usr/sbin/dtrace -s

::set_errno:entry
/curpsinfo->pr_ppid == $2 && arg0 == $1/
{
    stack();
    ustack();
}
