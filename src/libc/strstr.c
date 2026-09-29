/* Imported from emoose/re4 @ feb6805b (src/game/strstr.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/string/strstr.c */
#include "newlib_local.h"

/* First occurrence of lookfor in searchee, NULL when absent. */
char *strstr(const char *searchee, const char *lookfor)
{
    if (*searchee == 0) {
        if (*lookfor)
            return (char *)NULL;
        return (char *)searchee;
    }

    while (*searchee) {
        size_t i;
        i = 0;

        while (1) {
            if (lookfor[i] == 0) {
                return (char *)searchee;
            }

            if (lookfor[i] != searchee[i]) {
                break;
            }
            i++;
        }
        searchee++;
    }

    return (char *)NULL;
}
