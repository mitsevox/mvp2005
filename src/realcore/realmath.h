// realmath.h: EA's realmath types (librealmathz.a under realcore/ in FIFA 2005's and UEFA CL
// 2004-05's link maps; MVP links the same library, e.g. v3add at 0x804029B8).
// The type names are EA's (COORD3, COORD4, MATRIX4 in those maps' mangled names). No reference build here
// gives their layouts, so only what matched units read is declared, and the member names are ours.
// The inline constructors and operators are the ones geomlib's code shows inlined (each homes its
// float arguments on the stack under -ffloat-store); their spelling is ours.
#ifndef REALMATH_H
#define REALMATH_H

// A 3-component vector.
struct COORD3 {
    float x, y, z;

    COORD3() {}
    COORD3(float ax, float ay, float az) {
        x = ax;
        y = ay;
        z = az;
    }
};

// A 4-component vector.
struct COORD4 {
    float x, y, z, w;

    COORD4() {}
    COORD4(const COORD3& v, float aw) {
        x = v.x;
        y = v.y;
        z = v.z;
        w = aw;
    }
    COORD4(float ax, float ay, float az, float aw) {
        x = ax;
        y = ay;
        z = az;
        w = aw;
    }
    // Copies component by component (lfs/stfs), never as a block of words.
    COORD4& operator=(const COORD4& v) {
        x = v.x;
        y = v.y;
        z = v.z;
        w = v.w;
        return *this;
    }
};

inline COORD3 operator*(const COORD3& v, float s) {
    return COORD3(v.x * s, v.y * s, v.z * s);
}

inline COORD4 operator+(const COORD4& a, const COORD4& b) {
    return COORD4(a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w);
}

inline COORD4 operator-(const COORD4& a, const COORD4& b) {
    return COORD4(a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w);
}

inline COORD4 operator-(const COORD4& v) {
    return COORD4(-v.x, -v.y, -v.z, -v.w);
}

inline COORD4 operator*(const COORD4& v, float s) {
    return COORD4(v.x * s, v.y * s, v.z * s, v.w * s);
}

// A 4x4 transform: row i is m[i]; a vector is a row multiplied on the left (v * M).
struct MATRIX4 {
    float m[4][4];
};

inline COORD4 operator*(const COORD4& v, const MATRIX4& mat) {
    return COORD4(mat.m[0][0] * v.x + mat.m[1][0] * v.y + mat.m[2][0] * v.z + mat.m[3][0] * v.w,
                  mat.m[0][1] * v.x + mat.m[1][1] * v.y + mat.m[2][1] * v.z + mat.m[3][1] * v.w,
                  mat.m[0][2] * v.x + mat.m[1][2] * v.y + mat.m[2][2] * v.z + mat.m[3][2] * v.w,
                  mat.m[0][3] * v.x + mat.m[1][3] * v.y + mat.m[2][3] * v.z + mat.m[3][3] * v.w);
}

#endif
