/* Imported from emoose/re4 @ feb6805b (src/game/closer.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/reent/closer.c */
#include "newlib_stdio.h"

/* Reentrant close(): closes `fd` through the DVD file system stub, mirroring errno into the reent. */
int _close_r(struct _reent *ptr, int fd)
{
    int ret;

    errno = 0;
    if ((ret = close(fd)) == -1 && errno != 0)
        ptr->_errno = errno;
    return ret;
}
