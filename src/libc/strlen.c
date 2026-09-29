/* Imported from emoose/re4 @ feb6805b (src/game/strlen.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/string/strlen.c */
#include "newlib_local.h"

#define UNALIGNED(X) ((long)X & (LBLOCKSIZE - 1))

/* Length of a string. */
size_t strlen(const char *str)
{
    const char *start = str;
    unsigned long *aligned_addr;

    if (!UNALIGNED(str)) {
        aligned_addr = (unsigned long *)str;
        while (!DETECTNULL(*aligned_addr))
            aligned_addr++;
        str = (char *)aligned_addr;
    }

    while (*str)
        str++;
    return str - start;
}
