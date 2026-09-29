/* newlib 1.8.2 libc/stdio/fclose.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). SN's streams have no malloc'd buffers, so nothing is
 * freed. */
#include "newlib_stdio.h"

/* Flushes a write stream, calls its close hook and marks the FILE free; EOF if either failed. */
int fclose(register FILE *fp)
{
    int r;

    if (fp == NULL)
        return 0; /* on NULL */

    CHECK_INIT(fp);

    if (fp->_flags == 0) /* not open! */
        return 0;
    r = fp->_flags & __SWR ? fflush(fp) : 0;
    if (fp->_close != NULL && (*fp->_close)(fp->_cookie) < 0)
        r = EOF;
    fp->_flags = 0; /* release this FILE for reuse */
    return r;
}
