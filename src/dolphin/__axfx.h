/* Imported from emoose/re4 @ feb6805b (src/lib/__axfx.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _DOLPHIN_AX_INTERNAL_H_
#define _DOLPHIN_AX_INTERNAL_H_

#include <dolphin/axfx.h>

#ifdef __cplusplus
extern "C" {
#endif

extern void* (*__AXFXAlloc)(u32);
extern void (*__AXFXFree)(void*);

#ifdef __cplusplus
}
#endif

#endif
