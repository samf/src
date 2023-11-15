#! /usr/sbin/dtrace -Fs

::dserv_ioctl:entry
{
    self->t = speculation();
}

:::entry
/self->t/
{
    speculate(self->t);
}

:::return
/self->t/
{
    speculate(self->t);
    trace(arg1);
}

syscall::ioctl:return
/self->t && arg1 == 0/
{
    discard(self->t);
}

syscall::ioctl:return
/self->t && arg1 != 0/
{
    commit(self->t);
}

syscall::ioctl:return
/self->t/
{
	self->t = 0;
}
