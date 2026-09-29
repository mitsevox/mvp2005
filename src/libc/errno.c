/* Imported from emoose/re4 @ feb6805b (src/game/errno.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/errno/errno.c. The SN build also defines the plain `errno' the syscall stubs
 * (closer, readr, ...) use; as a common symbol the linker placed it last in .sbss. */
#include "newlib_stdio.h"

int errno;

/* Address of the reentrant errno (the newlib errno macro expands to *__errno()). */
int *__errno()
{
    return &_REENT->_errno;
}
