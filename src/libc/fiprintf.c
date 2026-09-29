/* newlib 1.8.2 libc/stdio/fiprintf.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of fprintf.c). */
#include "newlib_stdio.h"

extern int vfiprintf(FILE *, const char *, va_list);

/* fprintf without floating point (vfiprintf); __assert reports through it. */
int fiprintf(FILE *fp, const char *fmt, ...)
{
    int ret;
    va_list ap;

    va_start(ap, fmt);
    ret = vfiprintf(fp, fmt, ap);
    va_end(ap);
    return ret;
}
