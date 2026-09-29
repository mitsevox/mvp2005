/* Imported from emoose/re4 @ feb6805b (src/game/isspace.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib libc/ctype/isspace.c */
#include "newlib_local.h"

/* ctype table lookup for white space. */
int isspace(int c)
{
    return ((_ctype_ + 1)[c] & _S);
}
