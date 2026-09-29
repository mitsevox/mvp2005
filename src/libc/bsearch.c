/* newlib 1.8.2 libc/stdlib/bsearch.c, as built into SN ProDG's libc (MVP links it, re4 does not; written
 * here in the form of the other newlib units). */
#include "newlib_local.h"

/* Binary search of a sorted array of nmemb elements of `size` bytes; the match, or NULL. */
void *bsearch(const void *key, const void *base, size_t nmemb, size_t size, int (*compar)(const void *, const void *))
{
    void *current;
    size_t lower = 0;
    size_t upper = nmemb;
    size_t index;
    int result;

    if (nmemb == 0 || size == 0)
        return NULL;

    while (lower < upper) {
        index = (lower + upper) / 2;
        current = (void *)(((char *)base) + (index * size));

        result = compar(key, current);

        if (result < 0)
            upper = index;
        else if (result > 0)
            lower = index + 1;
        else
            return current;
    }

    return NULL;
}
