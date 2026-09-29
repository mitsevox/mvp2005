/* libgcc (GCC 2.95.3 libgcc2.c, as in SN ProDG's libgcc.a), section L_pure: __pure_virtual, where a
 * call through a pure virtual vtable slot lands. In this build it only calls __terminate
 * (tconfig.h's inhibit_libc compiles the message write out). Wrapper as in emoose/re4 (src/lib/_pure.c). */
#define L_pure
#include "libgcc2.c"
