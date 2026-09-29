/* Decompiled for this project (no public source). Nintendo Dolphin SDK virtual memory library,
 * vmbase.a(VMBase.o): the hardware side of virtual memory. It owns the CPU's hashed page table,
 * maps the 32 MB virtual window 0x7E000000..0x80000000 through segment register 7, and patches
 * the DSI and ISI exception vectors so page faults in that window reach vm.a's handler.
 * Built with the same CodeWarrior as vm.a. Names: config/GV4E69/linked_names.tsv. */
#include <dolphin.h>
#include <dolphin/os.h>

#include "__vm.h"

/* Low-memory words the OS keeps: the current context's physical and virtual addresses. */
#define OS_CURRENTCONTEXT_PADDR 0x00C0
#define OS_CURRENTCONTEXT 0x00D4

/* Invalidates the instruction-cache block holding p (isync first). Written for this decomp: the
 * binary inlines it at every patch site. */
static inline void ICBI(register void* p) {
    register int zero = 0;
    asm {
        isync
        icbi p, zero
    }
}

void __VMBASEInvalidateTLBEntry(register u32 virtualAddr);
void __VMBASESetVirtualAddr(u32 physPage, u32 virtualAddr);
void __VMBASESetPageLocked(u32 physPage, BOOL locked);
void __VMBASESetPageFaultHandler(void (*handler)(u32));
/* Takes the page table from the arena: from the next 64 KB boundary (a whole 64 KB further on
 * when the arena is already aligned), 64 KB long. Then clears it. */
void __VMBASEInitPageTable(void);
/* Takes the 4 KB lock table (one byte per main-memory page) from the arena and clears it. */
void __VMBASEInitLockedPageTable(void);
/* Takes the 16 KB reverse table (one word per main-memory page) from the arena and clears it. */
void __VMBASEInitReversePageTable(void);
/* Clears every page-table entry, writes the table out of the data cache and flushes the TLB. */
void __VMBASEInvalidatePageTable(void);
void __VMBASEInvalidateLockedPageTable(void);
void __VMBASEInvalidateReversePageTable(void);
/* The page-table entry for virtualAddr: the low 10 bits of the page number pick the 64-byte group,
 * the next 3 bits the entry in it. So each of the 8192 virtual pages has exactly one slot. */
u32* __VMBASEGetPTE(u32 virtualAddr);
/* The inverse of __VMBASEGetPTE: the virtual address a page-table entry maps. */
u32 __VMBASEGetPTEVirtualAddr(u32* pte);
/* Drops all 64 TLB congruence classes (tlbie on 64 pages 4 KB apart). */
void __VMBASEInvalidateEntireTLB(void);
/* Saves SDR1 and segment register 7, points segment 7 at VSID 0 and SDR1 at our page table
 * (keeping the old table-size mask), then switches over in real mode. */
void __VMBASESetupVMRegisters(void);
void __VMBASESetMSRAndSDR1(register u32 msr, register u32 sdr1, register u32 unused);
void __VMBASESetMSRAndSDR1_RealMode(void);
void __VMBASESetMSRAndSDR1_Done(void);
void __VMBASEDSIExceptionHandler_Service(void);
void __VMBASEISIExceptionHandler_Service(void);
/* Patches the DSI (0x300) and ISI (0x400) exception vectors: the first instruction of each
 * becomes a branch to our handler, the instruction it replaces is copied into the handler, and
 * the handler's last slot becomes a branch back to the vector's second instruction. So faults
 * outside the VM window still reach the OS's own handler. */
void __VMBASESetupExceptionHandlers(void);
void __VMBASEDSIExceptionHandler(void);
void __VMBASEDSIExceptionHandler_OriginalInstruction(void);
void __VMBASEDSIExceptionHandler_SetBranchBack(void);
/* Runs the page-fault handler for the faulting data address on a fresh context, then resumes. */
void __VMBASEDSIServiceException(OSContext* context, u32 dar);
void __VMBASEISIExceptionHandler(void);
void __VMBASEISIExceptionHandler_OriginalInstruction(void);
void __VMBASEISIExceptionHandler_SetBranchBack(void);
/* Runs the page-fault handler for the faulting instruction address, then resumes. */
void __VMBASEISIServiceException(OSContext* context);

/* SDR1 and segment register 7 as they were before VMBASEInit changed them. */
static u32 sSavedSDR1;
static u32 sSavedSR7;
static BOOL sInitialized;
/* vm.a's page-in function, called with the faulting address. */
static void (*sPageFaultHandler)(u32);
/* Per main-memory page: nonzero while the page may not be replaced. */
static u8* sLockedPageTable;
/* Per main-memory page: the virtual address mapped to it, 0 when free. */
static u32* sReversePageTable;
/* The 64 KB hashed page table: 8192 entries of two words, 64 KB aligned. */
static u32* sPageTable;

/* Sets up virtual memory once: records the page-fault handler, takes the page table, lock table
 * and reverse table from the arena (in the order that wastes least space before the 64 KB-aligned
 * page table), patches the exception vectors and switches the MMU over. Later calls do nothing. */
void VMBASEInit(void (*pageFaultHandler)(u32)) {
    BOOL enabled;
    u32 slack;

    if (!sInitialized) {
        enabled = OSDisableInterrupts();
        sInitialized = TRUE;
        __VMBASESetPageFaultHandler(pageFaultHandler);
        slack = 0x10000 - ((u32)OSGetArenaLo() & 0xFFFF);
        if (slack >= 0x5000) {
            __VMBASEInitLockedPageTable();
            __VMBASEInitReversePageTable();
            __VMBASEInitPageTable();
        } else if (slack >= 0x4000) {
            __VMBASEInitReversePageTable();
            __VMBASEInitPageTable();
            __VMBASEInitLockedPageTable();
        } else if (slack >= 0x1000) {
            __VMBASEInitLockedPageTable();
            __VMBASEInitPageTable();
            __VMBASEInitReversePageTable();
        } else {
            __VMBASEInitPageTable();
            __VMBASEInitLockedPageTable();
            __VMBASEInitReversePageTable();
        }
        __VMBASESetupExceptionHandlers();
        __VMBASESetupVMRegisters();
        __VMBASEInvalidateEntireTLB();
        OSRestoreInterrupts(enabled);
    }
}

/* Maps the page of virtualAddr to the main-memory page at physAddr (index physPage), valid and
 * with its referenced and changed bits clear, and records the mapping in the reverse table. */
void VMBASESetPageTableEntry(u32 virtualAddr, u32 physAddr, u32 physPage) {
    u32* pte;
    BOOL enabled;

    pte = __VMBASEGetPTE(virtualAddr);
    enabled = OSDisableInterrupts();
    pte[0] = 0x80000000 | ((virtualAddr >> 22) & 0x3F);
    pte[1] = physAddr & 0x0FFFF000;
    DCStoreRange(pte, 8);
    __VMBASEInvalidateTLBEntry(virtualAddr);
    __VMBASESetVirtualAddr(physPage, virtualAddr);
    OSRestoreInterrupts(enabled);
}

/* Unmaps the page of virtualAddr and frees and unlocks main-memory page physPage. */
void VMBASEClearPageTableEntry(u32 virtualAddr, u32 physPage) {
    BOOL enabled;
    u32* pte;

    enabled = OSDisableInterrupts();
    pte = __VMBASEGetPTE(virtualAddr);
    pte[0] = 0;
    pte[1] = 0;
    DCStoreRange(pte, 8);
    __VMBASEInvalidateTLBEntry(virtualAddr);
    __VMBASESetVirtualAddr(physPage, 0);
    __VMBASESetPageLocked(physPage, FALSE);
    OSRestoreInterrupts(enabled);
}

BOOL __VMBASEIsPageValid(u32 virtualAddr) {
    return __VMBASEGetPTE(virtualAddr)[0] >> 31;
}

/* The page-table entry's referenced bit: the CPU sets it when the page is accessed. */
BOOL __VMBASEIsPageReferenced(u32 virtualAddr) {
    return (__VMBASEGetPTE(virtualAddr)[1] >> 8) & 1;
}

/* The page-table entry's changed bit: the CPU sets it when the page is written. */
BOOL __VMBASEIsPageChanged(u32 virtualAddr) {
    return (__VMBASEGetPTE(virtualAddr)[1] >> 7) & 1;
}

/* Sets or clears the referenced bit of the page of virtualAddr. */
void VMBASESetPageReferenced(u32 virtualAddr, BOOL referenced) {
    BOOL enabled;
    u32* pte;

    enabled = OSDisableInterrupts();
    pte = __VMBASEGetPTE(virtualAddr);
    if (referenced) {
        pte[1] |= 0x100;
    } else {
        pte[1] &= ~0x100;
    }
    DCStoreRange(&pte[1], 4);
    __VMBASEInvalidateTLBEntry(virtualAddr);
    OSRestoreInterrupts(enabled);
}

/* Drops the TLB entry for the page of virtualAddr. */
asm void __VMBASEInvalidateTLBEntry(register u32 virtualAddr) {
    nofralloc
    rlwinm r0, virtualAddr, 0, 14, 19
    tlbsync
    tlbie r0
    blr
}

/* The main-memory page backing virtualAddr, as a cached (0x80000000-based) address. */
u32 __VMBASEGetPhysicalAddr(u32 virtualAddr) {
    return (u32)OSPhysicalToCached(__VMBASEGetPTE(virtualAddr)[1] & 0x0FFFF000);
}

u32 __VMBASEGetVirtualAddr(u32 physPage) {
    return sReversePageTable[physPage];
}

void __VMBASESetVirtualAddr(u32 physPage, u32 virtualAddr) {
    sReversePageTable[physPage] = virtualAddr;
}

BOOL __VMBASEIsPageLocked(u32 physPage) {
    return sLockedPageTable[physPage];
}

void __VMBASESetPageLocked(u32 physPage, BOOL locked) {
    if (locked) {
        sLockedPageTable[physPage] = TRUE;
    } else {
        sLockedPageTable[physPage] = FALSE;
    }
}

void __VMBASESetPageFaultHandler(void (*handler)(u32)) {
    sPageFaultHandler = handler;
}

/* Takes the page table from the arena: from the next 64 KB boundary (a whole 64 KB further on
 * when the arena is already aligned), 64 KB long. Then clears it. */
void __VMBASEInitPageTable(void) {
    u32 arenaLo = (u32)OSGetArenaLo();

    sPageTable = (u32*)(arenaLo + 0x10000 - (arenaLo & 0xFFFF));
    OSSetArenaLo((u8*)sPageTable + 0x10000);
    __VMBASEInvalidatePageTable();
}

/* Takes the 4 KB lock table (one byte per main-memory page) from the arena and clears it. */
void __VMBASEInitLockedPageTable(void) {
    sLockedPageTable = OSGetArenaLo();
    OSSetArenaLo(sLockedPageTable + 0x1000);
    __VMBASEInvalidateLockedPageTable();
}

/* Takes the 16 KB reverse table (one word per main-memory page) from the arena and clears it. */
void __VMBASEInitReversePageTable(void) {
    sReversePageTable = OSGetArenaLo();
    OSSetArenaLo(sReversePageTable + 0x1000);
    __VMBASEInvalidateReversePageTable();
}

/* Clears every page-table entry, writes the table out of the data cache and flushes the TLB. */
void __VMBASEInvalidatePageTable(void) {
    BOOL enabled;
    u32 i;

    enabled = OSDisableInterrupts();
    for (i = 0; i < 0x10000; i += 8) {
        *(u32*)((u8*)sPageTable + i) = 0;
        *(u32*)((u8*)sPageTable + i + 4) = 0;
    }
    DCStoreRange(sPageTable, 0x10000);
    __VMBASEInvalidateEntireTLB();
    OSRestoreInterrupts(enabled);
}

void __VMBASEInvalidateLockedPageTable(void) {
    u32 i;

    for (i = 0; i < 0x1000; i++) {
        *(u8*)((u8*)sLockedPageTable + i) = FALSE;
    }
}

void __VMBASEInvalidateReversePageTable(void) {
    u32 i;

    for (i = 0; i < 0x1000 * 4; i += 4) {
        *(u32*)((u8*)sReversePageTable + i) = 0;
    }
}

/* Calls storePage with the virtual address of every valid page whose changed bit is set, then
 * clears that bit. Used by vm.a to write every dirty page back to ARAM. */
void VMBASEStoreAllPages(void (*storePage)(u32)) {
    u32 i;
    BOOL enabled;
    u32* pte;

    enabled = OSDisableInterrupts();
    for (i = 0; i < 0x2000; i++) {
        pte = &sPageTable[i * 2];
        if ((pte[0] & 0x80000000) && (pte[1] & 0x80)) {
            storePage(__VMBASEGetPTEVirtualAddr(pte));
            pte[1] &= ~0x80;
            DCStoreRangeNoSync(&pte[1], 4);
        }
    }
    PPCSync();
    __VMBASEInvalidateEntireTLB();
    OSRestoreInterrupts(enabled);
}

/* The page-table entry for virtualAddr: the low 10 bits of the page number pick the 64-byte group,
 * the next 3 bits the entry in it. So each of the 8192 virtual pages has exactly one slot. */
u32* __VMBASEGetPTE(u32 virtualAddr) {
    return (u32*)((u32)sPageTable | ((virtualAddr >> 6) & 0xFFC0) | ((virtualAddr >> 19) & 0x38));
}

/* The inverse of __VMBASEGetPTE: the virtual address a page-table entry maps. */
u32 __VMBASEGetPTEVirtualAddr(u32* pte) {
    u32 offset = (u32)pte - (u32)sPageTable;

    return 0x7E000000 | ((offset << 19) & 0x01C00000) | ((offset << 6) & 0x003FF000);
}

/* Drops all 64 TLB congruence classes (tlbie on 64 pages 4 KB apart). */
void __VMBASEInvalidateEntireTLB(void) {
    register u32 addr;
    int i;

    addr = 0;
    asm { tlbsync }
    for (i = 0; i < 64; i++) {
        asm { tlbie addr }
        addr += 0x1000;
    }
}

/* Saves SDR1 and segment register 7, points segment 7 at VSID 0 and SDR1 at our page table
 * (keeping the old table-size mask), then switches over in real mode. */
void __VMBASESetupVMRegisters(void) {
    register u32 sr7;
    register u32 zero;
    register u32 msr;
    register u32 sdr1;

    zero = 0;
    asm {
        mfsr sr7, 7
        mtsr 7, zero
    }
    sSavedSR7 = sr7;
    asm {
        mfmsr msr
        mfsdr1 sdr1
    }
    sSavedSDR1 = sdr1;
    sdr1 = (sdr1 & 0xFFFF) + ((u32)sPageTable & 0x7FFF0000);
    __VMBASESetMSRAndSDR1(msr & ~0x30, sdr1, 0);
}

/* Drops to real mode with msr, loads SDR1 = sdr1, then returns with translation back on.
 * The caller passes 0 in the third argument register; nothing reads it. */
asm void __VMBASESetMSRAndSDR1(register u32 msr, register u32 sdr1, register u32 unused) {
    nofralloc
    mtsrr1 msr
    lis r5, __VMBASESetMSRAndSDR1_RealMode@ha
    addi r5, r5, __VMBASESetMSRAndSDR1_RealMode@l
    clrlwi r5, r5, 1
    mtsrr0 r5
    rfi
entry __VMBASESetMSRAndSDR1_RealMode
    sync
    mtsdr1 sdr1
    sync
    mfmsr r3
    ori r3, r3, 0x30
    mtsrr1 r3
    lis r5, __VMBASESetMSRAndSDR1_Done@ha
    addi r5, r5, __VMBASESetMSRAndSDR1_Done@l
    mtsrr0 r5
    rfi
entry __VMBASESetMSRAndSDR1_Done
    nop
    blr
}

/* Patches the DSI (0x300) and ISI (0x400) exception vectors: the first instruction of each
 * becomes a branch to our handler, the instruction it replaces is copied into the handler, and
 * the handler's last slot becomes a branch back to the vector's second instruction. So faults
 * outside the VM window still reach the OS's own handler. */
void __VMBASESetupExceptionHandlers(void) {
    u32* addr;

    {
        u32 original;
        u32 offset;
        u32 back;

        original = *(u32*)OSPhysicalToCached(0x300);
        offset = OSCachedToPhysical(__VMBASEDSIExceptionHandler);
        offset -= 0x300;
        *(u32*)OSPhysicalToCached(0x300) = 0x48000000 | offset;
        DCFlushRangeNoSync(OSPhysicalToCached(0x300), 4);
        __sync();
        ICBI(OSPhysicalToCached(0x300));
        addr = (u32*)__VMBASEDSIExceptionHandler_OriginalInstruction;
        *addr = original;
        DCFlushRangeNoSync(addr, 4);
        __sync();
        ICBI(addr);
        addr = (u32*)__VMBASEDSIExceptionHandler_SetBranchBack;
        back = OSCachedToPhysical(addr);
        back -= 0x304;
        *addr = 0x48000000 | (-back & 0x03FFFFFF);
        DCFlushRangeNoSync(addr, 4);
        __sync();
        ICBI(addr);
    }
    {
        u32 original;
        u32 offset;
        u32 back;

        original = *(u32*)OSPhysicalToCached(0x400);
        offset = OSCachedToPhysical(__VMBASEISIExceptionHandler);
        offset -= 0x400;
        *(u32*)OSPhysicalToCached(0x400) = 0x48000000 | offset;
        DCFlushRangeNoSync(OSPhysicalToCached(0x400), 4);
        __sync();
        ICBI(OSPhysicalToCached(0x400));
        addr = (u32*)__VMBASEISIExceptionHandler_OriginalInstruction;
        *addr = original;
        DCFlushRangeNoSync(addr, 4);
        __sync();
        ICBI(addr);
        addr = (u32*)__VMBASEISIExceptionHandler_SetBranchBack;
        back = OSCachedToPhysical(addr);
        back -= 0x404;
        *addr = 0x48000000 | (-back & 0x03FFFFFF);
        DCFlushRangeNoSync(addr, 4);
        __sync();
        ICBI(addr);
    }
}

/* Data-access fault vector. A fault with DAR in 0x7E000000..0x80000000 and DSISR saying no page
 * entry was found saves the context and goes to __VMBASEDSIServiceException with translation
 * on; anything else runs the displaced vector instruction and branches back to the OS. */
asm void __VMBASEDSIExceptionHandler(void) {
    nofralloc
    mtsprg 0, r4
    mtsprg 1, r5
    mtsprg 2, r6
    mfcr r4
    mtsprg 3, r4
    mfdar r5
    li r6, 0x7E
    slwi r6, r6, 24
    cmplw r5, r6
    blt @notvm
    mfdar r5
    li r6, 0x80
    slwi r6, r6, 24
    cmplw r5, r6
    bge @notvm
    mfdsisr r5
    rlwinm r6, r5, 0, 1, 1
    cmplwi r6, 0
    beq @notvm
    mfsprg r4, 3
    mtcrf 0xFF, r4
    mfsprg r4, 0
    mfsprg r5, 1
    mfsprg r6, 2
    mtsprg 0, r4
    lwz r4, OS_CURRENTCONTEXT_PADDR
    stw r3, OS_CONTEXT_R3(r4)
    mfsprg r3, 0
    stw r3, OS_CONTEXT_R4(r4)
    stw r5, OS_CONTEXT_R5(r4)
    lhz r3, OS_CONTEXT_STATE(r4)
    ori r3, r3, OS_CONTEXT_STATE_EXC
    sth r3, OS_CONTEXT_STATE(r4)
    mfcr r3
    stw r3, OS_CONTEXT_CR(r4)
    mflr r3
    stw r3, OS_CONTEXT_LR(r4)
    mfctr r3
    stw r3, OS_CONTEXT_CTR(r4)
    mfxer r3
    stw r3, OS_CONTEXT_XER(r4)
    mfsrr0 r3
    stw r3, OS_CONTEXT_SRR0(r4)
    mfsrr1 r3
    stw r3, OS_CONTEXT_SRR1(r4)
    mr r5, r3
    mfmsr r3
    ori r3, r3, 0x30
    mtsrr1 r3
    lwz r3, OS_CURRENTCONTEXT
    lis r5, __VMBASEDSIExceptionHandler_Service@ha
    addi r5, r5, __VMBASEDSIExceptionHandler_Service@l
    mtsrr0 r5
    rfi
@notvm:
    mfsprg r4, 3
    mtcrf 0xFF, r4
    mfsprg r4, 0
    mfsprg r5, 1
    mfsprg r6, 2
entry __VMBASEDSIExceptionHandler_OriginalInstruction
    nop
entry __VMBASEDSIExceptionHandler_SetBranchBack
    nop
entry __VMBASEDSIExceptionHandler_Service
    OS_EXCEPTION_SAVE_GPRS(r3)
    mfdar r4
    b __VMBASEDSIServiceException
}

/* Runs the page-fault handler for the faulting data address on a fresh context, then resumes. */
void __VMBASEDSIServiceException(OSContext* context, u32 dar) {
    OSContext exceptionContext;

    OSClearContext(&exceptionContext);
    OSSetCurrentContext(&exceptionContext);
    sPageFaultHandler(dar);
    OSSetCurrentContext(context);
    OSLoadContext(context);
}

/* Instruction-fetch fault vector: the same as the DSI one, testing SRR0 and SRR1 instead. */
asm void __VMBASEISIExceptionHandler(void) {
    nofralloc
    mtsprg 0, r4
    mtsprg 1, r5
    mtsprg 2, r6
    mfcr r4
    mtsprg 3, r4
    mfsrr0 r5
    li r6, 0x7E
    slwi r6, r6, 24
    cmplw r5, r6
    blt @notvm
    mfsrr0 r5
    li r6, 0x80
    slwi r6, r6, 24
    cmplw r5, r6
    bge @notvm
    mfsrr1 r5
    rlwinm r6, r5, 0, 1, 1
    cmplwi r6, 0
    beq @notvm
    mfsprg r4, 3
    mtcrf 0xFF, r4
    mfsprg r4, 0
    mfsprg r5, 1
    mfsprg r6, 2
    mtsprg 0, r4
    lwz r4, OS_CURRENTCONTEXT_PADDR
    stw r3, OS_CONTEXT_R3(r4)
    mfsprg r3, 0
    stw r3, OS_CONTEXT_R4(r4)
    stw r5, OS_CONTEXT_R5(r4)
    lhz r3, OS_CONTEXT_STATE(r4)
    ori r3, r3, OS_CONTEXT_STATE_EXC
    sth r3, OS_CONTEXT_STATE(r4)
    mfcr r3
    stw r3, OS_CONTEXT_CR(r4)
    mflr r3
    stw r3, OS_CONTEXT_LR(r4)
    mfctr r3
    stw r3, OS_CONTEXT_CTR(r4)
    mfxer r3
    stw r3, OS_CONTEXT_XER(r4)
    mfsrr0 r3
    stw r3, OS_CONTEXT_SRR0(r4)
    mfsrr1 r3
    stw r3, OS_CONTEXT_SRR1(r4)
    mr r5, r3
    mfmsr r3
    ori r3, r3, 0x30
    mtsrr1 r3
    lwz r3, OS_CURRENTCONTEXT
    lis r5, __VMBASEISIExceptionHandler_Service@ha
    addi r5, r5, __VMBASEISIExceptionHandler_Service@l
    mtsrr0 r5
    rfi
@notvm:
    mfsprg r4, 3
    mtcrf 0xFF, r4
    mfsprg r4, 0
    mfsprg r5, 1
    mfsprg r6, 2
entry __VMBASEISIExceptionHandler_OriginalInstruction
    nop
entry __VMBASEISIExceptionHandler_SetBranchBack
    nop
entry __VMBASEISIExceptionHandler_Service
    OS_EXCEPTION_SAVE_GPRS(r3)
    b __VMBASEISIServiceException
}

/* Runs the page-fault handler for the faulting instruction address, then resumes. */
void __VMBASEISIServiceException(OSContext* context) {
    OSContext exceptionContext;

    OSClearContext(&exceptionContext);
    OSSetCurrentContext(&exceptionContext);
    sPageFaultHandler(context->srr0);
    OSSetCurrentContext(context);
    OSLoadContext(context);
}
