/* newlib 1.8.2 libc/stdlib/assert.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). */
#include "newlib_stdio.h"

extern int fiprintf(FILE *, const char *, ...);
extern void abort(void);

/* The assert() failure path: reports the expression, file and line on stderr and aborts. */
void __assert(const char *file, int line, const char *failedexpr)
{
    (void)fiprintf(_stderr_r(_REENT), "assertion \"%s\" failed: file \"%s\", line %d\n", failedexpr, file, line);
    abort();
    /* NOTREACHED */
}
