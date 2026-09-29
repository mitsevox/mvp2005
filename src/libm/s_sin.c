/* SN ProDG libm (newlib 1.8.2 fdlibm): sin() (double, argument reduction + kernel). Compiled as C, as SN built its libm: a C
 * build keeps the file's unreferenced static consts in .sdata2, and MVP's .sdata2 has them in
 * link order (the re4 units' .cpp wrappers drop them; docs/sdk.md). re4 has no s_sin. */
#include "fdlibm/s_sin.c"
