/* Imported from emoose/re4 @ feb6805b (src/game/sscanf.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdio/sscanf.c */
#include "newlib_stdio.h"

extern size_t strlen(const char *);

/* Read function of the string FILE: always EOF (the string is the whole buffer). */
int eofread(void *cookie, char *buf, int len)
{
    return 0;
}

/* Parses `str` with a read-only string FILE through vfscanf. */
int sscanf(const char *str, const char *fmt, ...)
{
    int ret;
    va_list ap;
    FILE f;

    f._flags = __SRD;
    f._bf._base = f._p = (unsigned char *)str;
    f._bf._size = f._r = strlen(str);
    f._read = eofread;
    f._ub._base = NULL;
    f._lb._base = NULL;
    f._data = _REENT;
    va_start(ap, fmt);
    ret = __svfscanf(&f, fmt, ap);
    va_end(ap);
    return ret;
}
