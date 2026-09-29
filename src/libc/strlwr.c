/* newlib 1.8.2 libc/string/strlwr.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). */
#include "newlib_local.h"

/* newlib's <ctype.h> tolower for GCC */
#define tolower(c) __extension__({ int __x = (c); isupper(__x) ? (__x - 'A' + 'a') : __x; })

/* Lower-cases a string in place (ASCII) and returns it. */
char *strlwr(char *a)
{
    char *ret = a;

    while (*a != '\0') {
        if (isupper(*a))
            *a = tolower(*a);
        ++a;
    }

    return ret;
}
