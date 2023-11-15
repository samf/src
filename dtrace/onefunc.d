#! /usr/sbin/dtrace -s

#pragma D option flowindent

::$1:entry
/curpsinfo->pr_ppid == $2/
{
    self->t = 1;
}

:::entry
/self->t/
{
}

:::return
/self->t/
{
    trace(arg1);
}

::$1:return
/self->t/
{
    self->t = 0;
}
