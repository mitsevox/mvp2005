// realmath.h: EA's realmath types (librealmathz.a under realcore/ in FIFA 2005's and UEFA CL
// 2004-05's link maps; MVP links the same library, e.g. v3add at 0x804029B8).
// The type names are EA's (COORD4, MATRIX4 in those maps' mangled names). No reference build here
// gives their layouts, so only what matched units read is declared, and the member names are ours.
#ifndef REALMATH_H
#define REALMATH_H

// A 4-component vector.
struct COORD4 {
    float x, y, z, w;
};

// A 4x4 transform. Layout not declared until a matched unit reads its members.
struct MATRIX4;

#endif
