/* Imported from emoose/re4 @ feb6805b (src/game/memchr.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/string/memchr.c */
#include "newlib_local.h"

#define UNALIGNED(X) ((long)X & (LBLOCKSIZE - 1))
#define TOO_SMALL(LEN) ((LEN) < LBLOCKSIZE)

/* Finds the first byte equal to c in the block, scanning a word at a time when aligned; NULL when absent. */
void *memchr(const void *src_void, int c, size_t length)
{
    const unsigned char *src = (const unsigned char *)src_void;
    unsigned long *asrc;
    unsigned long buffer;
    unsigned long mask;
    unsigned char d;
    int i, j;

    d = c;

    /* If the size is small, or src is unaligned, then
       use the bytewise loop.  We can hope this is rare.  */
    if (!TOO_SMALL(length) && !UNALIGNED(src)) {
        /* The fast code reads the ASCII one word at a time and only
           performs the bytewise search on word-sized segments if they
           contain the search character, which is detected by XORing
           the word-sized segment with a word-sized block of the search
           character and then detecting for the presence of NULL in the
           result.  */
        asrc = (unsigned long *)src;
        mask = 0;
        for (i = 0; i < LBLOCKSIZE; i++)
            mask = (mask << 8) + d;

        while (length >= LBLOCKSIZE) {
            buffer = *asrc;
            buffer ^= mask;
            if (DETECTNULL(buffer)) {
                src = (unsigned char *)asrc;
                for (j = 0; j < LBLOCKSIZE; j++) {
                    if (*src == d)
                        return (void *)src;
                    src++;
                }
            }
            length -= LBLOCKSIZE;
            asrc++;
        }

        /* If there are fewer than LBLOCKSIZE characters left,
           then we resort to the bytewise loop.  */

        src = (unsigned char *)asrc;
    }

    while (length--) {
        if (*src == d)
            return (void *)src;
        src++;
    }

    return NULL;
}
