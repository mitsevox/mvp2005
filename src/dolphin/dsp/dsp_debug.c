/* Imported from emoose/re4 @ feb6805b (src/lib/dsp_debug.c), based on doldecomp/dolsdk2004. Nintendo Dolphin SDK 2004 Patch 1, dsp library; names are Nintendo's. */
#include <dolphin/dsp.h>

#include "__dsp.h"

void __DSP_debug_printf(const char* fmt, ...) {}

DSPTaskInfo* __DSPGetCurrentTask(void) {
    return __DSP_curr_task;
}
