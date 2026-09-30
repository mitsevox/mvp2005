// realmath.h: EA's realmath types (librealmathz.a under realcore/ in FIFA 2005's and UEFA CL
// 2004-05's link maps; MVP links the same library, e.g. v3add at 0x804029B8).
// Layouts and member names come from the DWARF in the disc's libmatd.a (all 25 objects agree;
// offsets below are InstanceCrowd.o's .debug records, tools/research/dwarf_lookup.py).
// The file name is ours: that DWARF records no declaring header for these types.
#ifndef REALMATH_H
#define REALMATH_H

// Converts degrees to radians. EA's global float DegToRad(float deg) is in the libmatd.a DWARF
// (InstanceCrowd.o .debug 0x24CE, with a double overload and RadToDeg beside it); the body is
// ours, read from the single multiply by PI/180 that ViewPort::SetPerspective inlines.
inline float DegToRad(float deg) {
    return deg * (3.14159265358979323846f / 180.0f);
}

// A 3-component vector: typedef 0x219D2 of an unnamed 12-byte struct (0x17CE).
typedef struct {
    float x, y, z;
} COORD3;

// A 4-component vector, not built on COORD3.
// The DWARF (typedef 0x219ED) shows EA's COORD4 as an unnamed 16-byte struct (0x1E3C) of float
// x, y, z, w, so EA's COORD4 has no constructors. The constructors and operators below are the
// ones geomlib's matched code needs; they are not EA's form and geomlib is to be reworked onto
// the plain struct.
struct COORD4 {
    float x, y, z, w;

    COORD4() {}
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

// A 4x4 transform: row i is m44[i]; a vector is a row multiplied on the left (v * M).
// Union 0xE4A3 with typedef 0x21AFC of the same name: m is float[16], m44 is float[4][4].
typedef union MATRIX4 {
    float m[16];
    float m44[4][4];
} MATRIX4;

inline COORD4 operator*(const COORD4& v, const MATRIX4& mat) {
    return COORD4(mat.m44[0][0] * v.x + mat.m44[1][0] * v.y + mat.m44[2][0] * v.z + mat.m44[3][0] * v.w,
                  mat.m44[0][1] * v.x + mat.m44[1][1] * v.y + mat.m44[2][1] * v.z + mat.m44[3][1] * v.w,
                  mat.m44[0][2] * v.x + mat.m44[1][2] * v.y + mat.m44[2][2] * v.z + mat.m44[3][2] * v.w,
                  mat.m44[0][3] * v.x + mat.m44[1][3] * v.y + mat.m44[2][3] * v.z + mat.m44[3][3] * v.w);
}

#endif
