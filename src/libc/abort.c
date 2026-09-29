/* abort as built into SN ProDG's libc (MVP links it, re4 does not). Decompiled from MVP: SN's only calls
 * _exit(1), with no signal first, and _exit is called without a prototype and does not return. */

extern volatile void _exit();

/* Ends the program with status 1. */
void abort(void)
{
    _exit(1);
}
