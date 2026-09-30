#!/usr/bin/env python3
"""Leave a ProDG object's vtables to the DOL's .data: link against them instead of placing them.

GCC 2.95 puts a class's vtable in its own `.gnu.linkonce.d._vt.<class>` section, and SN's ngcld
gathered those after every object's .data: all of MVP's vtables sit together at the end of .data
(0x806492A8..0x80686800), after the libraries' data. dtk splits each DOL section by address in
one link order, so a game unit (early in .text) cannot own a vtable (late in .data, after the
libraries) without a cycle. Until vtables get units of their own, the vtable stays in dtk's .data
asm, named in symbols.txt (`_vt.<class>`), and the object links against it:

  * every .gnu.linkonce.d.* section loses its ALLOC and WRITE flags, so the linker places nothing;
  * every symbol it defines becomes an undefined global reference, resolved by the asm's copy.

The object's code is unchanged. What the dropped copy held (the function pointers) is checked
by main.dol: OK, since the asm's vtable points at this object's functions by name.

usage: linkonce_data.py <object>
"""
import struct
import sys

PREFIX = b".gnu.linkonce.d."
SHF_WRITE = 0x1
SHF_ALLOC = 0x2
SHT_SYMTAB = 2
STB_GLOBAL = 1
STT_SECTION = 3


def main():
    path = sys.argv[1]
    elf = bytearray(open(path, "rb").read())
    if elf[:4] != b"\x7fELF" or elf[4] != 1 or elf[5] != 2:
        sys.exit(f"{path}: not a 32-bit big-endian ELF")
    shoff, = struct.unpack_from(">I", elf, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from(">HHH", elf, 0x2E)

    def header(i):
        return shoff + i * shentsize

    str_off, = struct.unpack_from(">I", elf, header(shstrndx) + 0x10)

    def name(i):
        start = str_off + struct.unpack_from(">I", elf, header(i))[0]
        return bytes(elf[start:elf.index(b"\0", start)])

    dropped = set()
    for i in range(shnum):
        if name(i).startswith(PREFIX):
            flags, = struct.unpack_from(">I", elf, header(i) + 0x08)
            struct.pack_into(">I", elf, header(i) + 0x08, flags & ~(SHF_WRITE | SHF_ALLOC))
            dropped.add(i)
    if not dropped:
        return
    for i in range(shnum):
        sh_type, = struct.unpack_from(">I", elf, header(i) + 0x04)
        if sh_type != SHT_SYMTAB:
            continue
        off, size = struct.unpack_from(">II", elf, header(i) + 0x10)
        entsize, = struct.unpack_from(">I", elf, header(i) + 0x24)
        for sym in range(off, off + size, entsize):
            info = elf[sym + 12]
            shndx, = struct.unpack_from(">H", elf, sym + 14)
            if shndx in dropped and info & 0xF != STT_SECTION:
                struct.pack_into(">II", elf, sym + 4, 0, 0)  # value, size
                elf[sym + 12] = (STB_GLOBAL << 4) | (info & 0xF)
                struct.pack_into(">H", elf, sym + 14, 0)  # SHN_UNDEF
    open(path, "wb").write(elf)


if __name__ == "__main__":
    main()
