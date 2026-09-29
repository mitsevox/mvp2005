/* Imported from emoose/re4 @ feb6805b (src/game/writer.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/reent/writer.c */
#include "newlib_stdio.h"

/* Reentrant write(): calls the system write and stores errno in the reent. */
long _write_r(struct _reent *ptr, int fd, const void *buf, size_t cnt)
{
    long ret;

    errno = 0;
    if ((ret = write(fd, buf, cnt)) == -1 && errno != 0)
        ptr->_errno = errno;
    return ret;
}
