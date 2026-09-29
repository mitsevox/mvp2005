/* libgcc (GCC 2.95.3 libgcc2.c, as in SN ProDG's libgcc.a), section L_eh: the exception-handling
 * runtime. MVP links only __default_terminate, __terminate and the static per-thread context setup
 * (eh_context_initialize, eh_context_static); the linker dropped the rest but kept the file's data,
 * including SN's "Hook _register_malloc" message. re4's wrapper (src/lib/_eh.c) adds three heap-hook
 * statics that MVP's .bss has no room for, so this one is the plain section. */
#define L_eh
#include "libgcc2.c"
