/* Decompiled for this project (no public source). Nintendo Dolphin SDK virtual memory library,
 * vm.a(VMMapping.o): which ARAM page backs each virtual page. Names: config/GV4E69/linked_names.tsv. */
#include <dolphin.h>

#include "__vm.h"

/* Index of a virtual page in sVirtualToARAMLUT: 8192 pages of 4 KB cover 32 MB. */
#define VM_LUT_INDEX(addr) (((addr) >> 12) & 0x1FFF)

static u32 sARAMPageCursor;
static u32 sAllocatedARAM;
/* Per virtual page: the ARAM address backing it (0 = not allocated); the top bit is set once
 * the page has been written out to ARAM. */
static u32* sVirtualToARAMLUT;
/* Per ARAM page: the virtual address it backs, 0 when free. */
static u32* sARAMToVirtualLUT;

/* Gives the virtual range virtualAddr..+size a backing ARAM page for each 4 KB, taking free pages
 * round-robin from the VM's ARAM range. Returns FALSE, allocating nothing, when size would take
 * the total past the ARAM given to VMInit. */
BOOL VMAlloc(u32 virtualAddr, u32 size) {
    u32 firstPage;
    u32 endPage;
    u32 offset;
    u32 addr;

    firstPage = __VMGetARAMStart() >> 12;
    endPage = firstPage + (__VMGetARAMSize() >> 12);
    if (sARAMPageCursor < firstPage) {
        sARAMPageCursor = firstPage;
    }
    if (sAllocatedARAM + size > __VMGetARAMSize()) {
        return FALSE;
    }
    for (offset = 0; offset < size; offset += 0x1000) {
        addr = virtualAddr + offset;
        do {
            if (++sARAMPageCursor >= endPage) {
                sARAMPageCursor = firstPage;
            }
        } while (sARAMToVirtualLUT[sARAMPageCursor] != 0);
        sARAMToVirtualLUT[sARAMPageCursor] = addr;
        sVirtualToARAMLUT[VM_LUT_INDEX(addr)] = sARAMPageCursor << 12;
        sAllocatedARAM += 0x1000;
    }
    return TRUE;
}

/* The ARAM address backing virtualAddr's page; halts the game if it was never allocated. */
u32 __VMTranslateVMPageToARAMPage(u32 virtualAddr) {
    u32 aramAddr = sVirtualToARAMLUT[VM_LUT_INDEX(virtualAddr)] & 0x7FFFFFFF;

    if (aramAddr) {
        return aramAddr;
    }
    __VMMappingErrorAlert(virtualAddr);
    return 0;
}

BOOL __VMIsPageMapped(u32 virtualAddr) {
    return (sVirtualToARAMLUT[VM_LUT_INDEX(virtualAddr)] & 0x7FFFFFFF) != 0;
}

/* Formats the "not allocated" message into a local buffer (it is never shown) and halts. */
void __VMMappingErrorAlert(u32 virtualAddr) {
    char message[1024];

    sprintf(message, "Virtual address (%x) has not been allocated. Call VMAlloc on virtual address ranges before using them.", virtualAddr);
    PPCHalt();
}

/* Marks virtualAddr's page as written out, so the next fault copies it back from ARAM. */
void __VMSetPageInARAM(u32 virtualAddr) {
    sVirtualToARAMLUT[VM_LUT_INDEX(virtualAddr)] |= 0x80000000;
}

BOOL __VMIsPageInARAM(u32 virtualAddr) {
    return sVirtualToARAMLUT[VM_LUT_INDEX(virtualAddr)] >> 31;
}

/* Takes the 32 KB virtual-to-ARAM table from the bottom of the arena and clears it. */
void __VMAllocVirtualToARAMLUT(void) {
    u32 i;
    void* ptr;
    u8* arenaLo;

    arenaLo = ptr = OSGetArenaLo();
    sVirtualToARAMLUT = ptr;
    arenaLo += 0x2000 * 4;
    OSSetArenaLo(arenaLo);
    for (i = 0; i < 0x2000 * 4; i += 4) {
        *(u32*)((u8*)sVirtualToARAMLUT + i) = 0;
    }
}

/* Takes the 16 KB ARAM-to-virtual table from the bottom of the arena and clears it. */
void __VMAllocARAMToVirtualLUT(void) {
    u32 i;
    void* ptr;
    u8* arenaLo;

    arenaLo = ptr = OSGetArenaLo();
    sARAMToVirtualLUT = ptr;
    arenaLo += 0x1000 * 4;
    OSSetArenaLo(arenaLo);
    for (i = 0; i < 0x1000 * 4; i += 4) {
        *(u32*)((u8*)sARAMToVirtualLUT + i) = 0;
    }
}
