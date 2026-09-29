/* Decompiled for this project (no public source). Nintendo Dolphin SDK virtual memory library, vm.a(VM.o),
 * built with a newer CodeWarrior than the rest of the SDK. Names: config/GV4E69/linked_names.tsv. */
#include <dolphin.h>

#include "__vm.h"

static BOOL sInitialized;
static VMLogStatsCallback sLogStatsCallback;
static u32 sMRAMPages;
static u32 sARAMSize;
static u32 sMRAMSwapSpace;
static u32 sMRAMSize;
static u32 sARAMStart = 0x4000;

/* Sets up virtual memory once: mramSize bytes of main memory (taken from the arena) cache 4 KB
 * pages of the ARAM range starting at aramStart, aramSize bytes long. Later calls do nothing. */
void VMInit(u32 mramSize, u32 aramStart, u32 aramSize) {
    BOOL enabled;

    if (!sInitialized) {
        enabled = OSDisableInterrupts();
        sInitialized = TRUE;
        sARAMStart = aramStart;
        sARAMSize = aramSize;
        sMRAMSize = mramSize;
        sMRAMPages = mramSize >> 12;
        VMBASEInit(__VMSwapPageIn);
        __VMAllocVirtualToARAMLUT();
        __VMAllocARAMToVirtualLUT();
        __VMAllocMRAMSwapSpace();
        OSRestoreInterrupts(enabled);
    }
}

/* Sets the function called after every page-in (NULL for none). */
void VMSetLogStatsCallback(VMLogStatsCallback callback) {
    sLogStatsCallback = callback;
}

u32 __VMGetMRAMPages(void) {
    return sMRAMPages;
}

u32 __VMGetARAMSize(void) {
    return sARAMSize;
}

u32 __VMGetARAMStart(void) {
    return sARAMStart;
}

/* Takes the main-memory page cache (mramSize bytes) from the bottom of the arena. */
void __VMAllocMRAMSwapSpace(void) {
    sMRAMSwapSpace = (u32)OSGetArenaLo();
    OSSetArenaLo((void*)(sMRAMSwapSpace + sMRAMSize));
}

/* Page-fault handler: brings the 4 KB page holding virtualAddr into main memory. Picks a page to
 * replace, writes it back to ARAM first if it was changed, then copies the wanted page in from
 * ARAM (or leaves it as it is when it was never written out) and maps it. An address that was
 * never given to VMAlloc halts the game. */
void __VMSwapPageIn(u32 virtualAddr) {
    u32 physAddr;
    BOOL swappedOut;
    u32 page;
    BOOL arInterrupt;
    u32 physPage;
    u32 start;
    BOOL enabled;
    u32 oldVirtualAddr;

    start = OSTicksToMicroseconds(OSGetTime());
    page = virtualAddr & ~0xFFF;
    swappedOut = FALSE;
    physPage = __VMGetPageToReplace();
    physAddr = sMRAMSwapSpace + (physPage << 12);
    oldVirtualAddr = __VMBASEGetVirtualAddr(physPage);
    enabled = OSDisableInterrupts();
    while (ARGetDMAStatus()) {}
    arInterrupt = __ARGetInterruptStatus();
    if (oldVirtualAddr) {
        if (__VMBASEIsPageChanged(oldVirtualAddr)) {
            __VMSetPageInARAM(oldVirtualAddr);
            swappedOut = TRUE;
            DCFlushRange((void*)physAddr, 0x1000);
            ARStartDMA(ARAM_DIR_MRAM_TO_ARAM, physAddr, __VMTranslateVMPageToARAMPage(oldVirtualAddr), 0x1000);
            while (ARGetDMAStatus()) {}
        }
        VMBASEClearPageTableEntry(oldVirtualAddr, physPage);
    }
    if (__VMIsPageInARAM(page)) {
        ARStartDMA(ARAM_DIR_ARAM_TO_MRAM, physAddr, __VMTranslateVMPageToARAMPage(page), 0x1000);
        while (ARGetDMAStatus()) {}
        DCInvalidateRange((void*)physAddr, 0x1000);
        ICInvalidateRange((void*)physAddr, 0x1000);
    } else if (!__VMIsPageMapped(page)) {
        __VMMappingErrorAlert(page);
    }
    if (!arInterrupt) {
        __ARClearInterrupt();
    }
    VMBASESetPageTableEntry(page, physAddr, physPage);
    OSRestoreInterrupts(enabled);
    if (sLogStatsCallback) {
        sLogStatsCallback(virtualAddr, physAddr, physPage, (u32)OSTicksToMicroseconds(OSGetTime()) - start, swappedOut);
    }
}

/* Writes the resident page of virtualAddr back to its ARAM page and marks it as held in ARAM.
 * The page stays mapped. */
void __VMSwapPageOut(u32 virtualAddr) {
    u32 physAddr;
    BOOL arInterrupt;
    BOOL enabled;

    physAddr = __VMBASEGetPhysicalAddr(virtualAddr);
    enabled = OSDisableInterrupts();
    while (ARGetDMAStatus()) {}
    arInterrupt = __ARGetInterruptStatus();
    DCFlushRange((void*)physAddr, 0x1000);
    ARStartDMA(ARAM_DIR_MRAM_TO_ARAM, physAddr, __VMTranslateVMPageToARAMPage(virtualAddr), 0x1000);
    while (ARGetDMAStatus()) {}
    if (!arInterrupt) {
        __ARClearInterrupt();
    }
    OSRestoreInterrupts(enabled);
    __VMSetPageInARAM(virtualAddr);
}

/* Writes every changed resident page back to ARAM: vmbase walks the page table, calls
 * __VMSwapPageOut for each valid entry marked changed, and clears its changed bit. */
void VMStoreAllPages(void) {
    VMBASEStoreAllPages(__VMSwapPageOut);
}
