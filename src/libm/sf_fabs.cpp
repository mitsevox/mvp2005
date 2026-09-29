/* SN ProDG libm (newlib 1.8.2 fdlibm): fabsf(). Compiled as C++ through this wrapper, as in
 * emoose/re4 (src/lib/sf_fabs.cpp): g++ drops folded static consts defined in an included file
 * and keeps tables in small data, which is what SN's libm has. */
#include "fdlibm/sf_fabs.c"
