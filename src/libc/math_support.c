/* Imported from emoose/re4 @ feb6805b (src/game/math_support.c). newlib 1.8.2 as built into SN ProDG's libc. */
/* SN ProDG libc: floor/fmod/log/log10 for vfprintf's floating-point conversion, built from the
 * fdlibm sources (newlib 1.8.2 libm) under sn_ names so that printf does not pull in libm.
 * MVP's .sdata2 (0x806EFC60..0x806EFCE0) shows it is one file: log10 has only ivln10, log10_2hi and
 * log10_2lo of its own and shares log's two54 and zero, so e_log10.c's body is written out here
 * instead of included (re4's include duplicates those two constants). */
#define floor sn_floor
#define __ieee754_fmod sn_fmod
#define __ieee754_log sn_log
#define __ieee754_log10 sn_log10

#include "../libm/fdlibm/s_floor.c"
#include "../libm/fdlibm/e_fmod.c"
#include "../libm/fdlibm/e_log.c"

/* newlib 1.8.2 libm/math/e_log10.c, less the two54 and zero it shares with e_log.c above */
static const double
ivln10     =  4.34294481903251816668e-01, /* 0x3FDBCB7B, 0x1526E50E */
log10_2hi  =  3.01029995663611771306e-01, /* 0x3FD34413, 0x509F6000 */
log10_2lo  =  3.69423907715893078616e-13; /* 0x3D59FEF3, 0x11F12B36 */

double __ieee754_log10(double x)
{
	double y,z;
	__int32_t i,k,hx;
	__uint32_t lx;

	EXTRACT_WORDS(hx,lx,x);

        k=0;
        if (hx < 0x00100000) {                  /* x < 2**-1022  */
            if (((hx&0x7fffffff)|lx)==0)
                return -two54/zero;             /* log(+-0)=-inf */
            if (hx<0) return (x-x)/zero;        /* log(-#) = NaN */
            k -= 54; x *= two54; /* subnormal number, scale up x */
	    GET_HIGH_WORD(hx,x);
        }
	if (hx >= 0x7ff00000) return x+x;
	k += (hx>>20)-1023;
	i  = ((__uint32_t)k&0x80000000)>>31;
        hx = (hx&0x000fffff)|((0x3ff-i)<<20);
        y  = (double)(k+i);
	SET_HIGH_WORD(x,hx);
	z  = y*log10_2lo + ivln10*__ieee754_log(x);
	return  z+y*log10_2hi;
}
