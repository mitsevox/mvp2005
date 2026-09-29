/* Imported from emoose/re4 @ feb6805b (src/game/isdigit.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/ctype/isdigit.c */
#include "newlib_local.h"

/* ctype table lookup for '0'..'9'. */
int isdigit(int c)
{
    return ((_ctype_ + 1)[c] & _N);
}
