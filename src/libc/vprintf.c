/* Imported from emoose/re4 @ feb6805b (src/game/vprintf.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdio/vprintf.c */
#include "newlib_stdio.h"

/* vfprintf onto stdout. */
int vprintf(const char *fmt, va_list ap)
{
    return vfprintf(_stdout_r(_REENT), fmt, ap);
}
