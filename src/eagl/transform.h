// transform.h: EAGL's matrix wrapper, named in FIFA/UEFA's libeaglSNz.a(transform.o).
// Layout from all 25 libmatd.a DWARF objects, InstanceCrowd.o .debug 0xE12D.
// Inline allocator overloads are omitted: their bodies are not retained.
#ifndef EAGL_TRANSFORM_H
#define EAGL_TRANSFORM_H

#include "realcore/realmath.h"

// Global matrix multiplication helper named by the FIFA and UEFA maps.
void MultMatrix(const MATRIX4* left, const MATRIX4* right, MATRIX4* result);

namespace EAGL {

// A row-vector transformation, including its homogeneous coordinate.
class Transform {
public:
    enum Axis { X_AXIS = 0, Y_AXIS = 4, Z_AXIS = 8 }; // .debug 0xE171
    MATRIX4 m; // 0x0; .debug 0xE14B

    // Name and reference signature are inferred from the matrix-copy caller.
    void SetMatrix(const MATRIX4& matrix);
    void BuildScale(float x, float y, float z, float w);
    void BuildTranslate(float x, float y, float z);
    void BuildIdentity();
    void BuildRotate(float degrees, float x, float y, float z);
    void AppendRotate(float degrees, float x, float y, float z);
    void BuildSRT(float sx, float sy, float sz, float rx, float ry, float rz,
                  float tx, float ty, float tz);
    void BuildQT(float qx, float qy, float qz, float qw, float tx, float ty, float tz);
    void BuildSQT(float sx, float sy, float sz, float qx, float qy, float qz, float qw,
                  float tx, float ty, float tz);
    void BuildQuatTrans(const COORD4* quaternion, const COORD4* translation);
    void ExtractQuatTrans(COORD4* quaternion, COORD4* translation) const;
    void ExtractRotTrans(MATRIX3* rotation, COORD3* translation) const;
    void TransformPoint(const COORD3& point, COORD3& result) const;
    void TransformPoint(const COORD4& point, COORD4& result) const;
    void TransformPoints(unsigned int count, const COORD3* points, int pointStride,
                         COORD3* results, int resultStride) const;
    void TransformVector(const COORD3& vector, COORD3& result) const;
    void PostMult(const Transform& transform);
    void PreMult(const Transform& transform);
    static void PreMult(const Transform& transform, const Transform& source, Transform& result);
    void AppendScale(float x, float y, float z, float w);
    void AppendTranslate(float x, float y, float z);
    void AppendMatrix(const MATRIX4* matrix);
    void PrependScale(float x, float y, float z, float w);
    void PrependMatrix(const MATRIX4* matrix);
    void Transpose();
    static void Transpose(const Transform& source, Transform& result);
    static float Invert(const Transform& source, Transform& result);
    // Overload name, const qualification and float returns are guesses from wrapper calls.
    float Inverse(Transform& result) const;
    float Inverse();
};

} // namespace EAGL
#endif
