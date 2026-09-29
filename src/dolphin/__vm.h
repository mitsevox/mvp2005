/* Nintendo Dolphin SDK virtual memory library (vm.a and vmbase.a): declarations for this decomp.
 * Nintendo's own header is not public; this one is reconstructed. Function names come from EA
 * GameCube builds with symbols where they name the function (config/GV4E69/linked_names.tsv),
 * otherwise they are read from the code (T3). */
#ifndef _DOLPHIN_VM_INTERNAL_H_
#define _DOLPHIN_VM_INTERNAL_H_

#include <dolphin/types.h>

/* Called after every page-in with the faulting address, the main-memory page used, its index,
 * the time the swap took in microseconds and whether a dirty page was written back first. */
typedef void (*VMLogStatsCallback)(u32 virtualAddr, u32 physicalAddr, u32 pageNumber, u32 pageMissLatency, BOOL pageSwappedOut);

/* VM.c */
void VMInit(u32 mramSize, u32 aramStart, u32 aramSize);
void VMSetLogStatsCallback(VMLogStatsCallback callback);
u32 __VMGetMRAMPages(void);
u32 __VMGetARAMSize(void);
u32 __VMGetARAMStart(void);
void __VMAllocMRAMSwapSpace(void);
void __VMSwapPageIn(u32 virtualAddr);
void __VMSwapPageOut(u32 virtualAddr);
void VMStoreAllPages(void);

/* VMPageReplacement.c */
u32 __VMGetPageToReplace(void);
u32 __VMPageReplacementLRU(void);
u32 __VMPageReplacementRandom(void);
u32 __VMPageReplacementFIFO(void);

/* VMMapping.c */
BOOL VMAlloc(u32 virtualAddr, u32 size);
u32 __VMTranslateVMPageToARAMPage(u32 virtualAddr);
BOOL __VMIsPageMapped(u32 virtualAddr);
void __VMMappingErrorAlert(u32 virtualAddr);
void __VMSetPageInARAM(u32 virtualAddr);
BOOL __VMIsPageInARAM(u32 virtualAddr);
void __VMAllocVirtualToARAMLUT(void);
void __VMAllocARAMToVirtualLUT(void);

/* vmbase.a (VMBase.o, still asm) */
void VMBASEInit(void (*pageFaultHandler)(u32 virtualAddr));
void VMBASESetPageTableEntry(u32 virtualAddr, u32 physAddr, u32 physPage);
void VMBASEClearPageTableEntry(u32 virtualAddr, u32 physPage);
BOOL __VMBASEIsPageValid(u32 virtualAddr);
BOOL __VMBASEIsPageReferenced(u32 virtualAddr);
BOOL __VMBASEIsPageChanged(u32 virtualAddr);
void VMBASESetPageReferenced(u32 virtualAddr, BOOL referenced);
u32 __VMBASEGetPhysicalAddr(u32 virtualAddr);
u32 __VMBASEGetVirtualAddr(u32 physPage);
BOOL __VMBASEIsPageLocked(u32 physPage);
void VMBASEStoreAllPages(void (*storePage)(u32 virtualAddr));

/* ar.c (not in ar.h) */
u16 __ARGetInterruptStatus(void);
void __ARClearInterrupt(void);

#endif
