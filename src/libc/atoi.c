/* Imported from emoose/re4 @ feb6805b (src/game/atoi.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/stdlib/atoi.c */
#include "newlib_local.h"

/* String to int, base 10. */
int atoi(const char *s)
{
    return (int)strtol(s, NULL, 10);
}
