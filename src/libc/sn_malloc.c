/* Imported from emoose/re4 @ feb6805b (src/game/sn_malloc.c), changed to MVP's form below. */
/* SN ProDG libc stubs: the C heap functions only report the caller. In MVP's newer libc (libsn v62)
 * they stop the game through OSPanic instead of printing, with the caller's call instruction as the
 * address (link register - 4, read with mflr: GCC's __builtin_return_address reads the stack frame
 * instead), and keep no call counters (re4's copy has two). Only free() is linked; malloc, realloc
 * and calloc were dead-stripped with their messages kept, so their bodies here follow free's
 * (inferred, not checkable against the DOL). */
#include "newlib_stdio.h"

extern void OSPanic(const char *file, int line, const char *msg, ...);

/* Stub: the game never uses the C heap; stops with the caller's address. */
void *malloc(size_t n)
{
    register unsigned lr;

    asm volatile("mflr %0" : "=r"(lr));
    OSPanic(NULL, 0, "\n*** Library error ***\nAn external call has been made to 'malloc'\nCalling function address: 0x%X\nPlease See the ProDG manual\n",
            lr - 4);
    return NULL;
}

/* Stub: stops with the caller's address. */
void free(void *p)
{
    register unsigned lr;

    asm volatile("mflr %0" : "=r"(lr));
    OSPanic(NULL, 0, "\n*** Library error ***\nAn external call has been made to 'free'\nCalling function address: 0x%X\nPlease See the ProDG manual\n",
            lr - 4);
}

/* Stub: stops with the caller's address. */
void *realloc(void *p, size_t n)
{
    register unsigned lr;

    asm volatile("mflr %0" : "=r"(lr));
    OSPanic(NULL, 0, "\n*** Library error ***\nAn external call has been made to 'realloc'\nCalling function address: 0x%X\nPlease See the ProDG manual\n",
            lr - 4);
    return NULL;
}

/* Stub: stops with the caller's address. */
void *calloc(size_t n, size_t m)
{
    register unsigned lr;

    asm volatile("mflr %0" : "=r"(lr));
    OSPanic(NULL, 0, "\n*** Library error ***\nAn external call has been made to 'calloc'\nCalling function address: 0x%X\nPlease See the ProDG manual\n",
            lr - 4);
    return NULL;
}
