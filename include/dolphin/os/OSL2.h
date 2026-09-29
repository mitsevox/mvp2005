/* Imported from emoose/re4 @ feb6805b (include/dolphin/os/OSL2.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _DOLPHIN_OSL2_H_
#define _DOLPHIN_OSL2_H_

#include <dolphin/types.h>

#ifdef __cplusplus
extern "C" {
#endif

void L2Enable(void);
void L2Disable(void);
void L2GlobalInvalidate(void);
void L2SetDataOnly(BOOL dataOnly);
void L2SetWriteThrough(BOOL writeThrough);

#ifdef __cplusplus
}
#endif

#endif
