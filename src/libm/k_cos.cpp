/* SN ProDG libm (newlib 1.8.2 fdlibm): __kernel_cos: cos on a reduced argument. Compiled as C++ through this wrapper, as in
 * emoose/re4 (src/lib/k_cos.cpp): g++ drops folded static consts defined in an included file
 * and keeps tables in small data, which is what SN's libm has. */
#include "fdlibm/k_cos.c"
