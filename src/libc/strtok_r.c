/* newlib 1.8.2 libc/string/strtok_r.c (BSD strtok), as built into SN ProDG's libc (MVP links it, re4
 * does not; written here in the form of the other newlib units). */
#include "newlib_local.h"

/* Splits s into tokens separated by any of `delim`; the position is kept in *lasts between calls. */
char *strtok_r(register char *s, register const char *delim, char **lasts)
{
    register char *spanp;
    register int c, sc;
    char *tok;

    if (s == NULL && (s = *lasts) == NULL)
        return (NULL);

    /*
     * Skip (span) leading delimiters (s += strspn(s, delim), sort of).
     */
cont:
    c = *s++;
    for (spanp = (char *)delim; (sc = *spanp++) != 0;) {
        if (c == sc)
            goto cont;
    }

    if (c == 0) { /* no non-delimiter characters */
        *lasts = NULL;
        return (NULL);
    }
    tok = s - 1;

    /*
     * Scan token (scan for delimiters: s += strcspn(s, delim), sort of).
     * Note that delim must have one NUL; we stop if we see that, too.
     */
    for (;;) {
        c = *s++;
        spanp = (char *)delim;
        do {
            if ((sc = *spanp++) == c) {
                if (c == 0)
                    s = NULL;
                else
                    s[-1] = 0;
                *lasts = s;
                return (tok);
            }
        } while (sc != 0);
    }
    /* NOTREACHED */
}
