/* newlib 1.8.2 libc/stdlib/rand.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). */
#include "newlib_stdio.h"

#define RAND_MAX 0x7fffffff

/* Seeds rand() for the calling reent. */
void srand(unsigned int seed)
{
    _REENT->_new._reent._rand_next = seed;
}

/* The ANSI linear congruential generator: next = next * 1103515245 + 12345, low 31 bits. */
int rand(void)
{
    return ((_REENT->_new._reent._rand_next = _REENT->_new._reent._rand_next * 1103515245 + 12345) & RAND_MAX);
}
