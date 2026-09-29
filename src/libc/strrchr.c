/* Imported from emoose/re4 @ feb6805b (src/game/strrchr.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/string/strrchr.c */
#include "newlib_local.h"

/* Last occurrence of character i in s, NULL when absent. */
char *strrchr(const char *s, int i)
{
    const char *last = NULL;
    char c = i;

    while (*s) {
        if (*s == c) {
            last = s;
        }
        s++;
    }

    if (*s == c) {
        last = s;
    }

    return (char *)last;
}
