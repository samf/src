#! /usr/sbin/dtrace -s

:::return
/curpsinfo->pr_ppid == $2 && arg1 == $1/
{
    stack();
    ustack();
}
