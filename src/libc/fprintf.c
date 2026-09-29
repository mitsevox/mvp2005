/* Imported from emoose/re4 @ feb6805b (src/game/fprintf.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdio/fprintf.c */
#include "newlib_stdio.h"

/* printf to a stream (vfprintf); used by the debug log through stdout. */
int fprintf(FILE *fp, const char *fmt, ...)
{
    int ret;
    va_list ap;

    va_start(ap, fmt);
    ret = vfprintf(fp, fmt, ap);
    va_end(ap);
    return ret;
}
