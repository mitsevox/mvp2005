// transform.cpp: libeaglSNz.a(transform.o), named by the FIFA/UEFA maps.
// The open left edge is placed after TevStage's startup thunk (0x803DE3E8), at
// map-named BuildQuatTrans (0x803DE414); ExtractQuatTrans follows at 0x803DE51C.
// The right edge follows PreMult and precedes TextureRenderContext code (0x803E032C).
#include "eagl/transform.h"
#include "realcore/realmem.h"
#include <math.h>

namespace EAGL {

// Builds a quaternion rotation and the full supplied translation row.
void Transform::BuildQuatTrans(const COORD4* quaternion, const COORD4* translation) {
    float qx = quaternion->x;
    float qy = quaternion->y;
    float qz = quaternion->z;
    float qw = quaternion->w;
    float x2 = qx + qx;
    float y2 = qy + qy;
    float z2 = qz + qz;
    float xx = qx * x2;
    float xy = qx * y2;
    float xz = qx * z2;
    float yy = qy * y2;
    float yz = qy * z2;
    float zz = qz * z2;
    float wx = qw * x2;
    float wy = qw * y2;
    float wz = qw * z2;
    MATRIX3 rotation;
    rotation.m[0] = 1.0f - (yy + zz);
    rotation.m[1] = xy + wz;
    rotation.m[2] = xz - wy;
    rotation.m[3] = xy - wz;
    rotation.m[4] = 1.0f - (xx + zz);
    rotation.m[5] = yz + wx;
    rotation.m[6] = xz + wy;
    rotation.m[7] = yz - wx;
    rotation.m[8] = 1.0f - (xx + yy);
    m.m44[0][0] = rotation.m33[0][0];
    m.m44[0][1] = rotation.m33[0][1];
    m.m44[0][2] = rotation.m33[0][2];
    m.m44[1][0] = rotation.m33[1][0];
    m.m44[1][1] = rotation.m33[1][1];
    m.m44[1][2] = rotation.m33[1][2];
    m.m44[2][0] = rotation.m33[2][0];
    m.m44[2][1] = rotation.m33[2][1];
    m.m44[2][2] = rotation.m33[2][2];
    m.m[3] = 0.0f;
    m.m[7] = 0.0f;
    m.m[11] = 0.0f;
    m.m[12] = translation->x;
    m.m[13] = translation->y;
    m.m[14] = translation->z;
    m.m[15] = translation->w;
}

// Extracts a quaternion from the linear block and preserves all four translation coordinates.
void Transform::ExtractQuatTrans(COORD4* quaternion, COORD4* translation) const {
    MATRIX3 rotation;
    rotation.m[0] = m.m[0]; rotation.m[1] = m.m[1]; rotation.m[2] = m.m[2];
    rotation.m[3] = m.m[4]; rotation.m[4] = m.m[5]; rotation.m[5] = m.m[6];
    rotation.m[6] = m.m[8]; rotation.m[7] = m.m[9]; rotation.m[8] = m.m[10];
    float trace = rotation.m[0] + rotation.m[4] + rotation.m[8];
    float root;
    if (trace > 0.0f) {
        root = sqrtf(trace + 1.0f);
        quaternion->w = root * 0.5f;
        root = 0.5f / root;
        quaternion->x = (rotation.m[5] - rotation.m[7]) * root;
        quaternion->y = (rotation.m[6] - rotation.m[2]) * root;
        quaternion->z = (rotation.m[1] - rotation.m[3]) * root;
    } else {
        int largest = 0;
        if (rotation.m[4] > rotation.m[0]) largest = 4;
        if (rotation.m[8] > rotation.m[largest]) {
            root = sqrtf(rotation.m[8] - (rotation.m[0] + rotation.m[4]) + 1.0f);
            quaternion->z = root * 0.5f;
            if (root != 0.0f) root = 0.5f / root;
            quaternion->w = (rotation.m[1] - rotation.m[3]) * root;
            quaternion->x = (rotation.m[6] + rotation.m[2]) * root;
            quaternion->y = (rotation.m[7] + rotation.m[5]) * root;
        } else if (largest != 0) {
            root = sqrtf(rotation.m[4] - (rotation.m[8] + rotation.m[0]) + 1.0f);
            quaternion->y = root * 0.5f;
            if (root != 0.0f) root = 0.5f / root;
            quaternion->w = (rotation.m[6] - rotation.m[2]) * root;
            quaternion->z = (rotation.m[5] + rotation.m[7]) * root;
            quaternion->x = (rotation.m[1] + rotation.m[3]) * root;
        } else {
            root = sqrtf(rotation.m[0] - (rotation.m[4] + rotation.m[8]) + 1.0f);
            quaternion->x = root * 0.5f;
            if (root != 0.0f) root = 0.5f / root;
            quaternion->w = (rotation.m[5] - rotation.m[7]) * root;
            quaternion->y = (rotation.m[1] + rotation.m[3]) * root;
            quaternion->z = (rotation.m[6] + rotation.m[2]) * root;
        }
    }
    translation->x = m.m[12];
    translation->y = m.m[13];
    translation->z = m.m[14];
    translation->w = m.m[15];
}

// Transforms a position with implicit w = 1; permits identical input and output.
void Transform::TransformPoint(const COORD3& point, COORD3& result) const {
    if (&point != &result) {
        result.x = point.x * m.m[0] + point.y * m.m[4] + point.z * m.m[8] + m.m[12];
        result.y = point.x * m.m[1] + point.y * m.m[5] + point.z * m.m[9] + m.m[13];
        result.z = point.x * m.m[2] + point.y * m.m[6] + point.z * m.m[10] + m.m[14];
    } else {
        COORD3 transformed;
        transformed.x = point.x * m.m[0] + point.y * m.m[4] + point.z * m.m[8] + m.m[12];
        transformed.y = point.x * m.m[1] + point.y * m.m[5] + point.z * m.m[9] + m.m[13];
        transformed.z = point.x * m.m[2] + point.y * m.m[6] + point.z * m.m[10] + m.m[14];
        result = transformed;
    }
}

// Transforms a homogeneous position; permits identical input and output.
void Transform::TransformPoint(const COORD4& point, COORD4& result) const {
    if (&point != &result) {
        result.x = point.x * m.m[0] + point.y * m.m[4] + point.z * m.m[8] + point.w * m.m[12];
        result.y = point.x * m.m[1] + point.y * m.m[5] + point.z * m.m[9] + point.w * m.m[13];
        result.z = point.x * m.m[2] + point.y * m.m[6] + point.z * m.m[10] + point.w * m.m[14];
        result.w = point.x * m.m[3] + point.y * m.m[7] + point.z * m.m[11] + point.w * m.m[15];
    } else {
        COORD4 transformed;
        transformed.x = point.x * m.m[0] + point.y * m.m[4] + point.z * m.m[8] + point.w * m.m[12];
        transformed.y = point.x * m.m[1] + point.y * m.m[5] + point.z * m.m[9] + point.w * m.m[13];
        transformed.z = point.x * m.m[2] + point.y * m.m[6] + point.z * m.m[10] + point.w * m.m[14];
        transformed.w = point.x * m.m[3] + point.y * m.m[7] + point.z * m.m[11] + point.w * m.m[15];
        result = transformed;
    }
}

// Transforms strided position arrays. Zero stride means tightly packed COORD3 values.
// port: strides count bytes; input/output equality selects the in-place path for the entire array.
void Transform::TransformPoints(unsigned int count, const COORD3* points, int pointStride,
                                 COORD3* results, int resultStride) const {
    if (count == 0) return;
    if (pointStride == 0) pointStride = sizeof(COORD3);
    if (resultStride == 0) resultStride = sizeof(COORD3);
    if (points == results) {
        do {
            COORD3 transformed;
            transformed.x = points->x * m.m[0] + points->y * m.m[4] + points->z * m.m[8] + m.m[12];
            transformed.y = points->x * m.m[1] + points->y * m.m[5] + points->z * m.m[9] + m.m[13];
            transformed.z = points->x * m.m[2] + points->y * m.m[6] + points->z * m.m[10] + m.m[14];
            points = (const COORD3*)((const char*)points + pointStride);
            *results = transformed;
            results = (COORD3*)((char*)results + resultStride);
        } while (--count);
    } else {
        do {
            results->x = points->x * m.m[0] + points->y * m.m[4] + points->z * m.m[8] + m.m[12];
            results->y = points->x * m.m[1] + points->y * m.m[5] + points->z * m.m[9] + m.m[13];
            results->z = points->x * m.m[2] + points->y * m.m[6] + points->z * m.m[10] + m.m[14];
            points = (const COORD3*)((const char*)points + pointStride);
            results = (COORD3*)((char*)results + resultStride);
        } while (--count);
    }
}

} // namespace EAGL

// Multiplies homogeneous matrices in row-vector order. The output must not alias either input.
void MultMatrix(const MATRIX4* left, const MATRIX4* right, MATRIX4* result) {
    result->m44[0][0] = left->m44[0][0] * right->m44[0][0] + left->m44[0][1] * right->m44[1][0] + left->m44[0][2] * right->m44[2][0] + left->m44[0][3] * right->m44[3][0];
    result->m44[0][1] = left->m44[0][0] * right->m44[0][1] + left->m44[0][1] * right->m44[1][1] + left->m44[0][2] * right->m44[2][1] + left->m44[0][3] * right->m44[3][1];
    result->m44[0][2] = left->m44[0][0] * right->m44[0][2] + left->m44[0][1] * right->m44[1][2] + left->m44[0][2] * right->m44[2][2] + left->m44[0][3] * right->m44[3][2];
    result->m44[0][3] = left->m44[0][0] * right->m44[0][3] + left->m44[0][1] * right->m44[1][3] + left->m44[0][2] * right->m44[2][3] + left->m44[0][3] * right->m44[3][3];
    result->m44[1][0] = left->m44[1][0] * right->m44[0][0] + left->m44[1][1] * right->m44[1][0] + left->m44[1][2] * right->m44[2][0] + left->m44[1][3] * right->m44[3][0];
    result->m44[1][1] = left->m44[1][0] * right->m44[0][1] + left->m44[1][1] * right->m44[1][1] + left->m44[1][2] * right->m44[2][1] + left->m44[1][3] * right->m44[3][1];
    result->m44[1][2] = left->m44[1][0] * right->m44[0][2] + left->m44[1][1] * right->m44[1][2] + left->m44[1][2] * right->m44[2][2] + left->m44[1][3] * right->m44[3][2];
    result->m44[1][3] = left->m44[1][0] * right->m44[0][3] + left->m44[1][1] * right->m44[1][3] + left->m44[1][2] * right->m44[2][3] + left->m44[1][3] * right->m44[3][3];
    result->m44[2][0] = left->m44[2][0] * right->m44[0][0] + left->m44[2][1] * right->m44[1][0] + left->m44[2][2] * right->m44[2][0] + left->m44[2][3] * right->m44[3][0];
    result->m44[2][1] = left->m44[2][0] * right->m44[0][1] + left->m44[2][1] * right->m44[1][1] + left->m44[2][2] * right->m44[2][1] + left->m44[2][3] * right->m44[3][1];
    result->m44[2][2] = left->m44[2][0] * right->m44[0][2] + left->m44[2][1] * right->m44[1][2] + left->m44[2][2] * right->m44[2][2] + left->m44[2][3] * right->m44[3][2];
    result->m44[2][3] = left->m44[2][0] * right->m44[0][3] + left->m44[2][1] * right->m44[1][3] + left->m44[2][2] * right->m44[2][3] + left->m44[2][3] * right->m44[3][3];
    result->m44[3][0] = left->m44[3][0] * right->m44[0][0] + left->m44[3][1] * right->m44[1][0] + left->m44[3][2] * right->m44[2][0] + left->m44[3][3] * right->m44[3][0];
    result->m44[3][1] = left->m44[3][0] * right->m44[0][1] + left->m44[3][1] * right->m44[1][1] + left->m44[3][2] * right->m44[2][1] + left->m44[3][3] * right->m44[3][1];
    result->m44[3][2] = left->m44[3][0] * right->m44[0][2] + left->m44[3][1] * right->m44[1][2] + left->m44[3][2] * right->m44[2][2] + left->m44[3][3] * right->m44[3][2];
    result->m44[3][3] = left->m44[3][0] * right->m44[0][3] + left->m44[3][1] * right->m44[1][3] + left->m44[3][2] * right->m44[2][3] + left->m44[3][3] * right->m44[3][3];
}

namespace EAGL {

// Builds a rotation around a normalised axis. A zero angle produces identity without reading its length.
void Transform::BuildRotate(float degrees, float x, float y, float z) {
    float radians = DegToRad(degrees);
    if (radians == 0.0f) {
        m.m[0] = 1.0f;
        m.m[1] = 0.0f;
        m.m[2] = 0.0f;
        m.m[3] = 0.0f;
        m.m[4] = 0.0f;
        m.m[5] = 1.0f;
        m.m[6] = 0.0f;
        m.m[7] = 0.0f;
        m.m[8] = 0.0f;
        m.m[9] = 0.0f;
        m.m[10] = 1.0f;
        m.m[11] = 0.0f;
        m.m[12] = 0.0f;
        m.m[13] = 0.0f;
        m.m[14] = 0.0f;
        m.m[15] = 1.0f;
    } else {
        float sine = sinf(radians);
        float cosine = cosf(radians);
        float length = sqrtf(x * x + y * y + z * z);
        x /= length;
        y /= length;
        z /= length;
        float complement = 1.0f - cosine;
        float sineAxisX = sine * x;
        float sineAxisY = sine * y;
        float sineAxisZ = sine * z;
        m.m[0] = complement * x * x + cosine;
        m.m[1] = complement * x * y + sineAxisZ;
        m.m[2] = complement * x * z - sineAxisY;
        m.m[3] = 0.0f;
        m.m[4] = complement * y * x - sineAxisZ;
        m.m[5] = complement * y * y + cosine;
        m.m[6] = complement * y * z + sineAxisX;
        m.m[7] = 0.0f;
        m.m[8] = complement * z * x + sineAxisY;
        m.m[9] = complement * z * y - sineAxisX;
        m.m[10] = complement * z * z + cosine;
        m.m[11] = 0.0f;
        m.m[12] = 0.0f;
        m.m[13] = 0.0f;
        m.m[14] = 0.0f;
        m.m[15] = 1.0f;
    }
}

// Applies another transformation after this one.
void Transform::PostMult(const Transform& transform) {
    MATRIX4 result;
    MultMatrix(&m, &transform.m, &result);
    MEM_copy(&m, &result, sizeof(MATRIX4));
}

// Builds a diagonal scale, including the homogeneous coordinate's scale.
void Transform::BuildScale(float x, float y, float z, float w) {
    m.m[0] = x;
    m.m[1] = 0.0f;
    m.m[2] = 0.0f;
    m.m[3] = 0.0f;
    m.m[4] = 0.0f;
    m.m[5] = y;
    m.m[6] = 0.0f;
    m.m[7] = 0.0f;
    m.m[8] = 0.0f;
    m.m[9] = 0.0f;
    m.m[10] = z;
    m.m[11] = 0.0f;
    m.m[12] = 0.0f;
    m.m[13] = 0.0f;
    m.m[14] = 0.0f;
    m.m[15] = w;
}

// Builds an affine translation with an identity rotation.
void Transform::BuildTranslate(float x, float y, float z) {
    m.m[0] = 1.0f;
    m.m[1] = 0.0f;
    m.m[2] = 0.0f;
    m.m[3] = 0.0f;
    m.m[4] = 0.0f;
    m.m[5] = 1.0f;
    m.m[6] = 0.0f;
    m.m[7] = 0.0f;
    m.m[8] = 0.0f;
    m.m[9] = 0.0f;
    m.m[10] = 1.0f;
    m.m[11] = 0.0f;
    m.m[12] = x;
    m.m[13] = y;
    m.m[14] = z;
    m.m[15] = 1.0f;
}

// Resets the transformation to preserve every coordinate.
void Transform::BuildIdentity() {
    m.m[0] = 1.0f;
    m.m[1] = 0.0f;
    m.m[2] = 0.0f;
    m.m[3] = 0.0f;
    m.m[4] = 0.0f;
    m.m[5] = 1.0f;
    m.m[6] = 0.0f;
    m.m[7] = 0.0f;
    m.m[8] = 0.0f;
    m.m[9] = 0.0f;
    m.m[10] = 1.0f;
    m.m[11] = 0.0f;
    m.m[12] = 0.0f;
    m.m[13] = 0.0f;
    m.m[14] = 0.0f;
    m.m[15] = 1.0f;
}

} // namespace EAGL

// Expands a 3x3 linear block and a three-coordinate translation into an affine matrix.
void mload44(float* matrix, const float* linear, const float* translation) {
    matrix[0] = linear[0];
    matrix[1] = linear[1];
    matrix[2] = linear[2];
    matrix[3] = 0.0f;
    matrix[4] = linear[3];
    matrix[5] = linear[4];
    matrix[6] = linear[5];
    matrix[7] = 0.0f;
    matrix[8] = linear[6];
    matrix[9] = linear[7];
    matrix[10] = linear[8];
    matrix[11] = 0.0f;
    matrix[12] = translation[0];
    matrix[13] = translation[1];
    matrix[14] = translation[2];
    matrix[15] = 1.0f;
}

namespace EAGL {

// Builds a scaled Euler rotation in degrees and an affine translation.
void Transform::BuildSRT(float sx, float sy, float sz, float rx, float ry, float rz,
                         float tx, float ty, float tz) {
    rx /= 360.0f;
    ry /= 360.0f;
    rz /= 360.0f;
    float sinX = SinTurn(rx);
    float cosX = CosTurn(rx);
    float sinY = SinTurn(ry);
    float cosY = CosTurn(ry);
    float sinZ = SinTurn(rz);
    float cosZ = CosTurn(rz);
    m.m[0] = sx * cosY * cosZ;
    m.m[1] = sx * cosY * sinZ;
    m.m[2] = -sx * sinY;
    m.m[3] = 0.0f;
    m.m[4] = sy * (sinX * sinY * cosZ - cosX * sinZ);
    m.m[5] = sy * (sinX * sinY * sinZ + cosX * cosZ);
    m.m[6] = sy * sinX * cosY;
    m.m[7] = 0.0f;
    m.m[8] = sz * (cosX * sinY * cosZ + sinX * sinZ);
    m.m[9] = sz * (cosX * sinY * sinZ - sinX * cosZ);
    m.m[10] = sz * cosX * cosY;
    m.m[11] = 0.0f;
    m.m[12] = tx;
    m.m[13] = ty;
    m.m[14] = tz;
    m.m[15] = 1.0f;
}

// Separates the linear part and translation; both output pointers must be valid.
void Transform::ExtractRotTrans(MATRIX3* rotation, COORD3* translation) const {
    rotation->m33[0][0] = m.m44[0][0];
    rotation->m33[0][1] = m.m44[0][1];
    rotation->m33[0][2] = m.m44[0][2];
    rotation->m33[1][0] = m.m44[1][0];
    rotation->m33[1][1] = m.m44[1][1];
    rotation->m33[1][2] = m.m44[1][2];
    rotation->m33[2][0] = m.m44[2][0];
    rotation->m33[2][1] = m.m44[2][1];
    rotation->m33[2][2] = m.m44[2][2];
    translation->x = m.m[12];
    translation->y = m.m[13];
    translation->z = m.m[14];
}

void Transform::SetMatrix(const MATRIX4& matrix) {
    m = matrix;
}

// Uses the original inverse routine; a near-zero computed denominator leaves the output unchanged.
float Transform::Inverse(Transform& result) const {
    return Invert(*this, result);
}

// Keeps the source values available while the inverse routine writes this matrix.
float Transform::Inverse() {
    Transform source = *this;
    return Invert(source, *this);
}

// Supplies the transpose without requiring a separate output matrix.
void Transform::Transpose() {
    float saved;
    saved = m.m[1];
    m.m[1] = m.m[4];
    m.m[4] = saved;
    saved = m.m[2];
    m.m[2] = m.m[8];
    m.m[8] = saved;
    saved = m.m[3];
    m.m[3] = m.m[12];
    m.m[12] = saved;
    saved = m.m[6];
    m.m[6] = m.m[9];
    m.m[9] = saved;
    saved = m.m[7];
    m.m[7] = m.m[13];
    m.m[13] = saved;
    saved = m.m[11];
    m.m[11] = m.m[14];
    m.m[14] = saved;
}

// Exchanges rows and columns; permits source and result to be the same object.
void Transform::Transpose(const Transform& source, Transform& result) {
    MATRIX4 transposed;
    MATRIX4* destination = &result.m;
    if (&source == &result) destination = &transposed;
    destination->m44[0][0] = source.m.m44[0][0];
    destination->m44[0][1] = source.m.m44[1][0];
    destination->m44[0][2] = source.m.m44[2][0];
    destination->m44[0][3] = source.m.m44[3][0];
    destination->m44[1][0] = source.m.m44[0][1];
    destination->m44[1][1] = source.m.m44[1][1];
    destination->m44[1][2] = source.m.m44[2][1];
    destination->m44[1][3] = source.m.m44[3][1];
    destination->m44[2][0] = source.m.m44[0][2];
    destination->m44[2][1] = source.m.m44[1][2];
    destination->m44[2][2] = source.m.m44[2][2];
    destination->m44[2][3] = source.m.m44[3][2];
    destination->m44[3][0] = source.m.m44[0][3];
    destination->m44[3][1] = source.m.m44[1][3];
    destination->m44[3][2] = source.m.m44[2][3];
    destination->m44[3][3] = source.m.m44[3][3];
    if (&source == &result) result.m = transposed;
}

// Applies a diagonal scale after this transformation.
void Transform::AppendScale(float x, float y, float z, float w) {
    Transform scale;
    scale.BuildScale(x, y, z, w);
    PostMult(scale);
}

// Applies an axis rotation after the current transform.
void Transform::AppendRotate(float degrees, float x, float y, float z) {
    Transform rotation;
    rotation.BuildRotate(degrees, x, y, z);
    PostMult(rotation);
}

// Applies an affine translation after this transformation.
void Transform::AppendTranslate(float x, float y, float z) {
    Transform translation;
    translation.BuildTranslate(x, y, z);
    PostMult(translation);
}

// Snapshots the input before composing it after this transformation, allowing aliasing.
void Transform::AppendMatrix(const MATRIX4* matrix) {
    Transform appended;
    appended.m = *matrix;
    PostMult(appended);
}

// Applies a diagonal scale before this transformation.
void Transform::PrependScale(float x, float y, float z, float w) {
    Transform scale;
    scale.BuildScale(x, y, z, w);
    PreMult(scale);
}

// Snapshots the input before composing it before this transformation, allowing aliasing.
void Transform::PrependMatrix(const MATRIX4* matrix) {
    Transform prepended;
    prepended.m = *matrix;
    PreMult(prepended);
}

// Transforms a direction, excluding translation; permits in-place use.
void Transform::TransformVector(const COORD3& vector, COORD3& result) const {
    if (&vector != &result) {
        result.x = vector.x * m.m[0] + vector.y * m.m[4] + vector.z * m.m[8];
        result.y = vector.x * m.m[1] + vector.y * m.m[5] + vector.z * m.m[9];
        result.z = vector.x * m.m[2] + vector.y * m.m[6] + vector.z * m.m[10];
    } else {
        COORD3 transformed;
        transformed.x = vector.x * m.m[0] + vector.y * m.m[4] + vector.z * m.m[8];
        transformed.y = vector.x * m.m[1] + vector.y * m.m[5] + vector.z * m.m[9];
        transformed.z = vector.x * m.m[2] + vector.y * m.m[6] + vector.z * m.m[10];
        result = transformed;
    }
}

// Builds a scaled quaternion rotation and translation, without normalising the quaternion.
void Transform::BuildSQT(float sx, float sy, float sz, float qx, float qy, float qz, float qw,
                         float tx, float ty, float tz) {
    float x2 = qx + qx;
    float y2 = qy + qy;
    float z2 = qz + qz;
    float xx = qx * x2;
    float xy = qx * y2;
    float xz = qx * z2;
    float yy = qy * y2;
    float yz = qy * z2;
    float zz = qz * z2;
    float wx = qw * x2;
    float wy = qw * y2;
    float wz = qw * z2;
    m.m[0] = sx * (1.0f - (yy + zz));
    m.m[1] = sx * (xy + wz);
    m.m[2] = sx * (xz - wy);
    m.m[3] = 0.0f;
    m.m[4] = sy * (xy - wz);
    m.m[5] = sy * (1.0f - (xx + zz));
    m.m[6] = sy * (yz + wx);
    m.m[7] = 0.0f;
    m.m[8] = sz * (xz + wy);
    m.m[9] = sz * (yz - wx);
    m.m[10] = sz * (1.0f - (xx + yy));
    m.m[11] = 0.0f;
    m.m[12] = tx;
    m.m[13] = ty;
    m.m[14] = tz;
    m.m[15] = 1.0f;
}

// Builds an affine rotation and translation from quaternion components.
void Transform::BuildQT(float qx, float qy, float qz, float qw,
                        float tx, float ty, float tz) {
    float x2 = qx + qx;
    float y2 = qy + qy;
    float z2 = qz + qz;
    float xx = qx * x2;
    float xy = qx * y2;
    float xz = qx * z2;
    float yy = qy * y2;
    float yz = qy * z2;
    float zz = qz * z2;
    float wx = qw * x2;
    float wy = qw * y2;
    float wz = qw * z2;
    m.m[0] = 1.0f - (yy + zz);
    m.m[1] = xy + wz;
    m.m[2] = xz - wy;
    m.m[3] = 0.0f;
    m.m[4] = xy - wz;
    m.m[5] = 1.0f - (xx + zz);
    m.m[6] = yz + wx;
    m.m[7] = 0.0f;
    m.m[8] = xz + wy;
    m.m[9] = yz - wx;
    m.m[10] = 1.0f - (xx + yy);
    m.m[11] = 0.0f;
    m.m[12] = tx;
    m.m[13] = ty;
    m.m[14] = tz;
    m.m[15] = 1.0f;
}

// Applies the source transform before the supplied transform; the output must be distinct.
void Transform::PreMult(const Transform& transform, const Transform& source, Transform& result) {
    MultMatrix(&source.m, &transform.m, &result.m);
}

// Applies another transformation before this one.
void Transform::PreMult(const Transform& transform) {
    MATRIX4 result;
    MultMatrix(&transform.m, &m, &result);
    MEM_copy(&m, &result, sizeof(MATRIX4));
}

} // namespace EAGL
