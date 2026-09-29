/* Imported from emoose/re4 @ feb6805b (include/dolphin/os/OSResetSW.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _DOLPHIN_OSRESETSW_H_
#define _DOLPHIN_OSRESETSW_H_

#include <dolphin/types.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*OSResetCallback)(void);

OSResetCallback OSSetResetCallback(OSResetCallback callback);
BOOL OSGetResetSwitchState(void);
BOOL OSGetResetButtonState(void);

#ifdef __cplusplus
}
#endif

#endif
