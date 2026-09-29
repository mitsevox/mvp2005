/* Imported from emoose/re4 @ feb6805b (src/game/strcpy.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/string/strcpy.c */
#include "newlib_local.h"

#define UNALIGNED(X, Y) (((long)X & (sizeof(long) - 1)) | ((long)Y & (sizeof(long) - 1)))

/* Copies src0 (with its terminator) to dst0. */
char *strcpy(char *dst0, const char *src0)
{
    char *dst = dst0;
    const char *src = src0;
    long *aligned_dst;
    const long *aligned_src;

    if (!UNALIGNED(src, dst)) {
        aligned_dst = (long *)dst;
        aligned_src = (long *)src;
        while (!DETECTNULL(*aligned_src)) {
            *aligned_dst++ = *aligned_src++;
        }
        dst = (char *)aligned_dst;
        src = (char *)aligned_src;
    }

    while (*dst++ = *src++)
        ;
    return dst0;
}
