/* Imported from emoose/re4 @ feb6805b (include/libc/stdlib.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _STDLIB_H_
#define _STDLIB_H_

#include <stddef.h>
#include <wchar.h>

#define RAND_MAX 32767

void srand(unsigned int seed);
int rand(void);
void abort(void);
void exit(int status);
size_t wcstombs(char *dest, const wchar_t *src, size_t max);

#ifdef __MWERKS__
#define abs(x) __abs(x)
#else
static inline int abs(int x)
{
    int mask = x >> 31;
    return (x + mask) ^ mask;
}
#endif

#endif
