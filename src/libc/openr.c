/* newlib 1.8.2 libc/reent/openr.c, as built into SN ProDG's libc (MVP has it, re4 does not link it;
 * written here in the form of re4's closer.c/readr.c). */
#include "newlib_stdio.h"

extern int open(const char *, int, ...);

/* Reentrant open(): calls SN's open and stores errno in the reent. */
int _open_r(struct _reent *ptr, const char *file, int flags, int mode)
{
    int ret;

    errno = 0;
    if ((ret = open(file, flags, mode)) == -1 && errno != 0)
        ptr->_errno = errno;
    return ret;
}
