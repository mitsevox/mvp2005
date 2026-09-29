/* Imported from emoose/re4 @ feb6805b (src/game/stdio.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdio/stdio.c */
#include "newlib_stdio.h"

/* Default FILE read: _read_r on the descriptor, tracking the offset (or dropping it on error). */
int __sread(void *cookie, char *buf, int n)
{
    register FILE *fp = (FILE *)cookie;
    register int ret;

    ret = _read_r(fp->_data, fp->_file, buf, n);

    /* If the read succeeded, update the current offset.  */

    if (ret >= 0)
        fp->_offset += ret;
    else
        fp->_flags &= ~__SOFF; /* paranoia */
    return ret;
}

/* Default FILE write: seeks to the end in append mode, then _write_r. */
int __swrite(void *cookie, char const *buf, int n)
{
    register FILE *fp = (FILE *)cookie;

    if (fp->_flags & __SAPP)
        (void)_lseek_r(fp->_data, fp->_file, (off_t)0, SEEK_END);
    fp->_flags &= ~__SOFF; /* in case O_APPEND mode is set */
    return _write_r(fp->_data, fp->_file, buf, n);
}

/* Default FILE seek: lseek, remembering the offset. */
fpos_t __sseek(void *cookie, fpos_t offset, int whence)
{
    register FILE *fp = (FILE *)cookie;
    register off_t ret;

    ret = _lseek_r(fp->_data, fp->_file, (off_t)offset, whence);
    if (ret == -1L)
        fp->_flags &= ~__SOFF;
    else {
        fp->_flags |= __SOFF;
        fp->_offset = ret;
    }
    return ret;
}

/* Default FILE close. */
int __sclose(void *cookie)
{
    FILE *fp = (FILE *)cookie;

    return _close_r(fp->_data, fp->_file);
}
