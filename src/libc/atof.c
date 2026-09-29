/* Imported from emoose/re4 @ feb6805b (src/game/atof.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/stdlib/atof.c */
#include "newlib_local.h"

/* String to double. */
double atof(const char *s)
{
    return strtod(s, NULL);
}
