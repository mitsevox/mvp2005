/* Imported from emoose/re4 @ feb6805b (src/game/readr.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/reent/readr.c */
#include "newlib_stdio.h"

/* Reentrant read(): calls the system read and stores errno in the reent. */
long _read_r(struct _reent *ptr, int fd, void *buf, size_t cnt)
{
    long ret;

    errno = 0;
    if ((ret = read(fd, buf, cnt)) == -1 && errno != 0)
        ptr->_errno = errno;
    return ret;
}
