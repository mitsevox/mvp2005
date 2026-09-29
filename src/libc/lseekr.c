/* Imported from emoose/re4 @ feb6805b (src/game/lseekr.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/reent/lseekr.c */
#include "newlib_stdio.h"

/* Reentrant lseek wrapper storing errno into the reent structure. */
off_t _lseek_r(struct _reent *ptr, int fd, off_t pos, int whence)
{
    off_t ret;

    errno = 0;
    if ((ret = lseek(fd, pos, whence)) == (off_t)-1 && errno != 0)
        ptr->_errno = errno;
    return ret;
}
