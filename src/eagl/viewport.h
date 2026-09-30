// viewport.h: EAGL viewport declarations from libmatd.a's InstanceCrowd.o DWARF.
// In progress: declarations include only the members used by recovered viewport code.
#ifndef EAGL_VIEWPORT_H
#define EAGL_VIEWPORT_H

#include "realcore/realmath.h"
#include <dolphin/mtx.h>

namespace EAGL {
// Current view-matrix storage; ViewPort::gpViewMatrix points here in the retail data.
extern MATRIX4 gViewMatrix;
// EAGL transform layout: disc InstanceCrowd.o .debug 0xE12D, 64 bytes, MATRIX4 at zero.
struct Transform {
    MATRIX4 m; // 0x00
    // The matrix-reference constructor signature is inferred from the 64-byte copy call.
    Transform(const MATRIX4& matrix);
    void TransformPoint(const COORD3& source, COORD3& destination) const;
};
class ViewPort;
}

namespace EAGLInternal {

// Disc InstanceCrowd.o .debug 0xF419 names both enum values.
enum ProjectionType { PERSPECTIVE = 0, ORTHOGRAPHIC = 1 };

// Perspective angles and camera-space depth limits.
struct VPFrustum {
    float mFOV;       // 0x00
    float mAspect;    // 0x04
    float mNearPlane; // 0x08
    float mFarPlane;  // 0x0C
};

// Side-plane coefficients retain the viewport's clipping adjustments.
struct VPCullData {
    float mLeftTan;     // 0x00
    float mLeftSin;     // 0x04
    float mRightTan;    // 0x08
    float mRightSin;    // 0x0C
    float mTopTan;      // 0x10
    float mTopSin;      // 0x14
    float mBottomTan;   // 0x18
    float mBottomSin;   // 0x1C
    float mLeftScale;   // 0x20
    float mRightScale;  // 0x24
    float mTopScale;    // 0x28
    float mBottomScale; // 0x2C
};

// In progress: unused regions are reserved at their proven DWARF offsets.
struct ViewPortPrivate {
    char mPad00[4];                 // 0x00
    ProjectionType mProjectionType; // 0x04
    char mPad08[4];                 // 0x08
    MATRIX4 mProjectionMatrix;      // 0x0C
    MATRIX4 mViewMatrix;            // 0x4C
    MATRIX4 mViewProjectionMatrix;  // 0x8C
    char mPadCC[0x18];              // 0xCC
    VPFrustum mFrustum;             // 0xE4
    char mPadF4[0x18];              // 0xF4
    VPCullData mCullData;           // 0x10C
    char mPad13C[0x10];             // 0x13C
    Mtx44 mProjection;             // 0x14C
    char mPad18C[0x14];             // 0x18C
};
}

namespace EAGL {
// In progress: camera projection and visibility state; remaining methods are unrecovered.
class ViewPort {
public:
    char mPad00[0x0C];         // 0x00
    EAGLInternal::ViewPortPrivate mPrivate; // 0x0C

    void SetPerspective(float fov, float aspect, float nearPlane, float farPlane);
    int TestSphere(const COORD3& centre, float radius) const;
};
}

#endif
