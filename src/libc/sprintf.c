/* Imported from emoose/re4 @ feb6805b (src/game/sprintf.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdio/sprintf.c */
#include "newlib_stdio.h"

/* Formats into `str` through a string FILE (no length limit). */
int sprintf(char *str, const char *fmt, ...)
{
    int ret;
    va_list ap;
    FILE f;

    f._flags = __SWR | __SSTR;
    f._bf._base = f._p = (unsigned char *)str;
    f._bf._size = f._w = INT_MAX;
    f._data = _REENT;
    va_start(ap, fmt);
    ret = vfprintf(&f, fmt, ap);
    va_end(ap);
    *f._p = 0;
    return (ret);
}
