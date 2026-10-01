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

// A 2-component vector: typedef 0x219B7 of an unnamed 8-byte struct (0x1184).
typedef struct {
    float x, y;
} COORD2;

// A 3-component vector: typedef 0x219D2 of an unnamed 12-byte struct (0x17CE).
typedef struct {
    float x, y, z;
} COORD3;

// A 4-component vector, not built on COORD3: typedef 0x219ED of an unnamed 16-byte struct
// (0x1E3C).
typedef struct {
    float x, y, z, w;
} COORD4;

// A 3x3 matrix: union 0x21A08 and typedef 0x21A95 in the same retained DWARF.
typedef union MATRIX3 {
    float m[9];
    float m33[3][3];
} MATRIX3;

// A 4x4 transform: row i is m44[i]; a vector is a row multiplied on the left (v * M).
// Union 0xE4A3 with typedef 0x21AFC of the same name: m is float[16], m44 is float[4][4].
typedef union MATRIX4 {
    float m[16];
    float m44[4][4];
} MATRIX4;

// C-style matrix loader retained as mload44(float*, const float*, const float*) in ff's map.
void mload44(float* matrix, const float* linear, const float* translation);

// Names reconstructed from the realmath routines' turn-based trigonometric contracts.
float SinTurn(float turns);
float CosTurn(float turns);

#endif
