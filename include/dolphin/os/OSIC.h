/* Imported from emoose/re4 @ feb6805b (include/dolphin/os/OSIC.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _DOLPHIN_OSIC_H_
#define _DOLPHIN_OSIC_H_

#ifdef __cplusplus
extern "C" {
#endif

void ICFlashInvalidate(void);
void ICEnable(void);
void ICDisable(void);
void ICFreeze(void);
void ICUnfreeze(void);
void ICBlockInvalidate(void *addr);
void ICSync(void);

#ifdef __cplusplus
}
#endif

#endif
