/* Imported from emoose/re4 @ feb6805b (src/game/vsprintf.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdio/vsprintf.c */
#include "newlib_stdio.h"

/* Formats an argument list into `str` through a string FILE. */
int vsprintf(char *str, const char *fmt, va_list ap)
{
    int ret;
    FILE f;

    f._flags = __SWR | __SSTR;
    f._bf._base = f._p = (unsigned char *)str;
    f._bf._size = f._w = INT_MAX;
    f._data = _REENT;
    ret = vfprintf(&f, fmt, ap);
    *f._p = 0;
    return ret;
}

/* SN adds vsnprintf to this object (not in newlib 1.8.2 or re4; EA's FIFA 2005 link map puts it in
 * libc.a(vsprintf.obj)). Decompiled from MVP: the string FILE is `size` bytes long, and a result
 * longer than `size` returns -1. */
int vsnprintf(char *str, size_t size, const char *fmt, va_list ap)
{
    int ret;
    FILE f;

    f._flags = __SWR | __SSTR;
    f._bf._base = f._p = (unsigned char *)str;
    f._bf._size = f._w = size;
    f._data = _REENT;
    ret = vfprintf(&f, fmt, ap);
    *f._p = 0;
    if (ret > size)
        ret = -1;
    return ret;
}
