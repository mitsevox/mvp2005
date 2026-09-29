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
