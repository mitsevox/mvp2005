/* newlib 1.8.2 libc/string/strcasecmp.c, as built into SN ProDG's libc (MVP links it, re4 does not;
 * written here in the form of the other newlib units). */
#include "newlib_local.h"

/* newlib's <ctype.h> tolower for GCC */
#define tolower(c) __extension__({ int __x = (c); isupper(__x) ? (__x - 'A' + 'a') : __x; })

/* Compares two strings ignoring ASCII case: <0, 0 or >0. */
int strcasecmp(const char *s1, const char *s2)
{
    while (*s1 != '\0' && tolower(*s1) == tolower(*s2)) {
        s1++;
        s2++;
    }

    return tolower(*(unsigned char *)s1) - tolower(*(unsigned char *)s2);
}
