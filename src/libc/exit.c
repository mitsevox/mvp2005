/* Imported from emoose/re4 @ feb6805b (src/game/exit.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* newlib 1.8.2 libc/stdlib/exit.c */
#include "newlib_stdio.h"

/* Runs the atexit handlers and the stdio cleanup, then _exit. */
void exit(int code)
{
    register struct _atexit *p;
    register int n;

    for (p = _REENT->_atexit; p; p = p->_next)
        for (n = p->_ind; --n >= 0;)
            (*p->_fns[n])();

    if (_REENT->__cleanup)
        (*_REENT->__cleanup)(_REENT);
    _exit(code);
}
