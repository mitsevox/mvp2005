/* SN ProDG libm (newlib 1.8.2 fdlibm): __ieee754_rem_pio2: reduce an argument modulo pi/2 (double). Compiled as C++ through this wrapper, as in
 * emoose/re4 (src/lib/e_rem_pio2.cpp): g++ drops folded static consts defined in an included file
 * and keeps tables in small data, which is what SN's libm has. */
#include "fdlibm/e_rem_pio2.c"
