/* Link script for SN's ngcld (GNU syntax). dtk copies it to build/GV4E69/ldscript.lcf.
   Each output section is pinned to its address in the original DOL. The small-data bases are the
   values the original entry code loads into r13 and r2 (0x80003108..0x80003114). */
ENTRY(__start)
SECTIONS
{
  _SDA_BASE_ = 0x806F69C0;
  _SDA2_BASE_ = 0x807069C0;
  .init     0x80003100 : { *(.init) }
  .text     0x800034A0 : { *(.text) }
  .ctordtor 0x805A2BC0 : { *(.ctordtor) }
  .rodata   0x805A2DA0 : { *(.rodata) }
  .data     0x8060F120 : { *(.data) }
  .bss      0x80686860 : { *(.bss) }
  .sdata    0x806EE9C0 : { *(.sdata) }
  .sbss     0x806EF380 : { *(.sbss) }
  .sdata2   0x806EFC40 : { *(.sdata2) }
}
