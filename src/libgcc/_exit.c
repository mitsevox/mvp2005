/* Imported from emoose/re4 @ feb6805b (src/lib/_exit.c). SN ProDG's libgcc _exit. */
/* SN ProDG libgcc: _exit traps into the debugger with an illegal instruction. */
void _exit(int code)
{
    __asm__(".long 0");
}
