/* Imported from emoose/re4 @ feb6805b (src/game/fopen.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* SN ProDG replacement for newlib 1.8.2 libc/stdio/findfp.c and fopen.c: a static pool of 10 FILEs
 * instead of malloc'd glue. re4 links only snstd, _sn_sinit and _cleanup_r (plus an error stub
 * fopen); MVP's newer libc (libsn v62) has a working fopen, so __sfp, _fopen_r and fopen are
 * decompiled here from MVP (no source in re4). */
#include "newlib_stdio.h"

extern int __sflags(struct _reent *, const char *, int *);
extern int _open_r(struct _reent *, const char *, int, int);
extern int fseek(FILE *, long, int);

FILE _sn_iobf[10];
struct _glue _sn_stat_g;

/* Per-slot preset buffers for the FILE a __sfp search lands on (indexed 9 - slots left in its glue
 * block); a slot with no buffer stays unbuffered. Defined elsewhere in SN's libc (a zeroed table in
 * MVP, so every stream is unbuffered). */
extern struct __sbuf *_sn_iobuf;

/* Initialises one of the three standard FILEs (stdin/stdout/stderr) on the SN read/write/seek/close hooks. */
static void snstd(FILE *ptr, int flags, int file, struct _reent *data)
{
    ptr->_p = 0;
    ptr->_r = 0;
    ptr->_w = 0;
    ptr->_flags = flags;
    ptr->_file = file;
    ptr->_bf._base = 0;
    ptr->_lbfsize = 0;
    ptr->_cookie = ptr;
    ptr->_read = __sread;
    ptr->_write = __swrite;
    ptr->_seek = __sseek;
    ptr->_close = __sclose;
    ptr->_data = data;
}

/* First-use stdio init (CHECK_INIT): sets up stdin/stdout/stderr and the static 10-FILE pool glue. */
void _sn_sinit(struct _reent *s)
{
    /* make sure we clean up on exit */
    s->__cleanup = _cleanup_r; /* conservative */
    s->__sdidinit = 1;

    snstd(s->__sf + 0, __SRD, 0, s);
    snstd(s->__sf + 1, __SWR | __SLBF, 1, s);
    snstd(s->__sf + 2, __SWR | __SNBF, 2, s);

    s->__sglue._next = &_sn_stat_g;
    s->__sglue._niobs = 3;
    s->__sglue._iobs = s->__sf;
    _sn_stat_g._next = NULL;
    _sn_stat_g._niobs = 10;
    _sn_stat_g._iobs = _sn_iobf;
}

/* Finds a free FILE (flags 0) in the standard three or the static pool and resets it. There is no
 * malloc'd overflow as in newlib: the search does not stop until it finds one. */
FILE *__sfp(struct _reent *d)
{
    FILE *fp;
    int n;
    struct _glue *g;

    if (!d->__sdidinit)
        _sn_sinit(d);
    if (d->__sglue._next == NULL) {
        _sn_stat_g._next = NULL;
        _sn_stat_g._niobs = 10;
        _sn_stat_g._iobs = _sn_iobf;
        d->__sglue._next = &_sn_stat_g;
    }
    for (g = &d->__sglue;; g = g->_next) {
        for (fp = g->_iobs, n = g->_niobs; --n >= 0; fp++)
            if (fp->_flags == 0)
                goto found;
    }
found:
    fp->_flags = 1; /* reserve this slot; caller sets real flags */
    fp->_w = 0; /* nothing to read or write */
    fp->_r = 0;
    if (_sn_iobuf[9 - n]._size > 0 && _sn_iobuf[9 - n]._base != NULL) {
        fp->_bf = _sn_iobuf[9 - n];
        fp->_p = _sn_iobuf[9 - n]._base;
        fp->_flags = __SMBF | 1;
    } else {
        fp->_flags |= __SNBF;
        fp->_bf._base = fp->_p = fp->_nbuf;
        fp->_bf._size = 1;
    }
    fp->_lbfsize = 0; /* not line buffered */
    fp->_file = -1; /* no file */
    fp->_ub._base = NULL; /* no ungetc buffer */
    fp->_ub._size = 0;
    fp->_lb._base = NULL; /* no line buffer */
    fp->_lb._size = 0;
    fp->_data = d;
    return fp;
}

/* Reentrant fopen: parses the mode, takes a pool FILE and opens the file through SN's open(). */
FILE *_fopen_r(struct _reent *ptr, const char *file, const char *mode)
{
    FILE *fp;
    int f;
    int flags, oflags;

    if ((flags = __sflags(ptr, mode, &oflags)) == 0)
        return NULL;
    if ((fp = __sfp(ptr)) == NULL)
        return NULL;

    fp->_flags &= __SNBF; /* SN's; the flags are overwritten below once the open succeeds */
    if ((f = _open_r(fp->_data, file, oflags, 0666)) < 0) {
        fp->_flags = 0; /* release */
        return NULL;
    }

    fp->_file = f;
    fp->_flags = flags;
    fp->_cookie = (void *)fp;
    fp->_read = __sread;
    fp->_write = __swrite;
    fp->_seek = __sseek;
    fp->_close = __sclose;

    if (fp->_flags & __SAPP)
        fseek(fp, 0, SEEK_END);

    return fp;
}

/* fopen on the global reent (_impure_ptr). */
FILE *fopen(const char *file, const char *mode)
{
    return _fopen_r(_REENT, file, mode);
}

/* Exit-time stdio cleanup: flushes every open stream. */
void _cleanup_r(struct _reent *ptr)
{
    /* (void) _fwalk(fclose); */
    (void)_fwalk(ptr, fflush); /* `cheating' */
}
