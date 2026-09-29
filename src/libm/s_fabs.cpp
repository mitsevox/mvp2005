/* SN ProDG libm (newlib 1.8.2 fdlibm): fabs(). Compiled as C++ through this wrapper, as in
 * emoose/re4 (src/lib/s_fabs.cpp): g++ drops folded static consts defined in an included file
 * and keeps tables in small data, which is what SN's libm has. */
#include "fdlibm/s_fabs.c"
