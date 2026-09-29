/* Imported from emoose/re4 @ feb6805b (src/game/tolower.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/ctype/tolower.c */
#include "newlib_local.h"

/* ASCII upper -> lower case. */
int tolower(int c)
{
    return isupper(c) ? (c) - 'A' + 'a' : c;
}
