/* newlib 1.8.2 libc/stdio/flags.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). */
#include "newlib_stdio.h"

/* newlib's <sys/fcntl.h> and <errno.h> values */
#define O_RDONLY 0
#define O_WRONLY 1
#define O_RDWR 2
#define O_APPEND 0x0008
#define O_CREAT 0x0200
#define O_TRUNC 0x0400
#define EINVAL 22

/*
 * Return the (stdio) flags for a given mode.  Store the flags
 * to be passed to an open() syscall through *optr.
 * Return 0 on error.
 */
int __sflags(struct _reent *ptr, register char *mode, int *optr)
{
    register int ret, m, o;

    switch (mode[0]) {
    case 'r': /* open for reading */
        ret = __SRD;
        m = O_RDONLY;
        o = 0;
        break;

    case 'w': /* open for writing */
        ret = __SWR;
        m = O_WRONLY;
        o = O_CREAT | O_TRUNC;
        break;

    case 'a': /* open for appending */
        ret = __SWR | __SAPP;
        m = O_WRONLY;
        o = O_CREAT | O_APPEND;
        break;

    default: /* illegal mode */
        ptr->_errno = EINVAL;
        return (0);
    }
    if (mode[1] == '+' || mode[2] == '+') {
        ret = __SRW;
        m = O_RDWR;
    }
    *optr = m | o;
    return ret;
}
