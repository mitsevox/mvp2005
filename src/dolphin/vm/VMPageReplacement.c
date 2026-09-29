/* Decompiled for this project (no public source). Nintendo Dolphin SDK virtual memory library,
 * vm.a(VMPageReplacement.o): which main-memory page a page fault evicts. Names: config/GV4E69/linked_names.tsv. */
#include <dolphin.h>

#include "__vm.h"

static u32 sCurrentPage;
static BOOL sFirstPass = TRUE;
static s32 sPolicy = 1;

/* Picks the main-memory page to reuse, by the current policy: 0 LRU, 1 random (the default,
 * nothing here changes it), anything else FIFO. */
u32 __VMGetPageToReplace(void) {
    if (sPolicy == 0) {
        return __VMPageReplacementLRU();
    } else if (sPolicy == 1) {
        return __VMPageReplacementRandom();
    } else {
        return __VMPageReplacementFIFO();
    }
}

/* Clock-style replacement. The first time round, pages are handed out in order. After that it
 * looks at the page under the clock hand: a page not mapped, or unlocked and neither referenced
 * nor changed, is taken. Otherwise its referenced bit is cleared and the sweep should go on round
 * the clock, but the "back where we started" test runs before the hand first moves, so it stops
 * at once: the page is taken if unlocked, else page 0. Either way the hand then moves on one. */
u32 __VMPageReplacementLRU(void) {
    u32 start;
    u32 page;
    s32 unreferencedChanged;
    s32 referencedUnchanged;
    s32 referencedChanged;
    u32 virtualAddr;
    BOOL referenced;
    BOOL changed;

    page = 0;
    start = sCurrentPage;
    unreferencedChanged = -1;
    referencedUnchanged = -1;
    referencedChanged = -1;
    if (!sFirstPass) {
        while (TRUE) {
            virtualAddr = __VMBASEGetVirtualAddr(sCurrentPage);
            if (virtualAddr && __VMBASEIsPageValid(virtualAddr)) {
                referenced = __VMBASEIsPageReferenced(virtualAddr);
                changed = __VMBASEIsPageChanged(virtualAddr);
                if (!referenced && !changed && !__VMBASEIsPageLocked(sCurrentPage)) {
                    page = sCurrentPage;
                    break;
                }
                if (!referenced && changed) {
                    if (unreferencedChanged < 0 && !__VMBASEIsPageLocked(sCurrentPage)) {
                        unreferencedChanged = sCurrentPage;
                    }
                } else if (referenced && !changed) {
                    if (referencedUnchanged < 0 && !__VMBASEIsPageLocked(sCurrentPage)) {
                        referencedUnchanged = sCurrentPage;
                    }
                } else if (referencedChanged < 0 && !__VMBASEIsPageLocked(sCurrentPage)) {
                    referencedChanged = sCurrentPage;
                }
                if (referenced) {
                    VMBASESetPageReferenced(virtualAddr, FALSE);
                }
                if (start == sCurrentPage) {
                    if (unreferencedChanged >= 0) {
                        page = unreferencedChanged;
                    } else if (referencedUnchanged >= 0) {
                        page = referencedUnchanged;
                    } else if (referencedChanged >= 0) {
                        page = referencedChanged;
                    }
                    break;
                }
                sCurrentPage++;
                if (sCurrentPage >= __VMGetMRAMPages()) {
                    sCurrentPage = 0;
                }
            } else {
                page = sCurrentPage;
                break;
            }
        }
    } else {
        page = start;
    }
    sCurrentPage++;
    if (sCurrentPage >= __VMGetMRAMPages()) {
        sFirstPass = FALSE;
        sCurrentPage = 0;
    }
    return page;
}

/* The first time round, pages are handed out in order; after that a random page (the time base
 * modulo the page count). Locked pages are skipped. */
u32 __VMPageReplacementRandom(void) {
    u32 page;

    do {
        if (sFirstPass) {
            page = sCurrentPage++;
            if (sCurrentPage >= __VMGetMRAMPages()) {
                sFirstPass = FALSE;
                sCurrentPage = 0;
            }
        } else {
            page = OSGetTick() % __VMGetMRAMPages();
        }
    } while (__VMBASEIsPageLocked(page));
    return page;
}

/* Hands out pages in order, wrapping round, skipping locked ones. */
u32 __VMPageReplacementFIFO(void) {
    u32 page;

    do {
        page = sCurrentPage++;
        if (sCurrentPage >= __VMGetMRAMPages()) {
            sFirstPass = FALSE;
            sCurrentPage = 0;
        }
    } while (__VMBASEIsPageLocked(page));
    return page;
}
