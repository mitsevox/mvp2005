/* newlib 1.8.2 libc/string/strtok.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). */
#include "newlib_stdio.h"

extern char *strtok_r(char *, const char *, char **);

/* strtok_r with the position kept in the calling reent. */
char *strtok(register char *s, register const char *delim)
{
    return strtok_r(s, delim, &(_REENT->_new._reent._strtok_last));
}
