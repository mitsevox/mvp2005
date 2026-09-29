/* Imported from emoose/re4 @ feb6805b (include/dolphin/gx/GXDispList.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _DOLPHIN_GX_GXDISPLIST_H_
#define _DOLPHIN_GX_GXDISPLIST_H_

#include <dolphin/types.h>

#ifdef __cplusplus
extern "C" {
#endif

void GXBeginDisplayList(void* list, u32 size);
u32 GXEndDisplayList(void);
void GXCallDisplayList(void* list, u32 nbytes);

#ifdef __cplusplus
}
#endif

#endif
