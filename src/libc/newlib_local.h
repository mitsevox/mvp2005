/* Imported from emoose/re4 @ feb6805b (include/newlib_local.h). newlib 1.8.2 as built into SN ProDG's libc. */
/* Shared declarations for the newlib C units in src/libc/ (no libc headers ship with ProDG here). */
#ifndef NEWLIB_LOCAL_H
#define NEWLIB_LOCAL_H

typedef unsigned int size_t;

#ifndef NULL
#define NULL 0
#endif

/* ctype table (newlib's ctype_.c) */
extern const char _ctype_[];

#define _U 01
#define _L 02
#define _N 04
#define _S 010
#define _P 020
#define _C 040
#define _X 0100
#define _B 0200

#define isupper(c) ((_ctype_ + 1)[(unsigned)(c)] & _U)

#define ERANGE 34
#define LONG_MAX 2147483647L
#define LONG_MIN (-2147483647L - 1)
#define ULONG_MAX 4294967295UL

/* string */
extern char *strcpy(char *, const char *);

/* stdlib */
extern long strtol(const char *, char **, int);
extern double strtod(const char *, char **);

/* Word-at-a-time helpers shared by the string units. */
#define LBLOCKSIZE (sizeof(long))
#define DETECTNULL(X) (((X)-0x01010101) & ~(X)&0x80808080)
#define DETECTCHAR(X, MASK) (DETECTNULL(X ^ MASK))

#endif
