// viewport_projection.cpp: projection subset of libeaglsnz.a(viewport.o), placed by the FIFA/UEFA SN maps.
#include "viewport.h"
#include <dolphin/gx/GXTransform.h>
#include <math.h>

using namespace EAGL;
using namespace EAGLInternal;

// Sets the hardware projection and sphere-culling planes; fov is horizontal degrees.
// Aspect is effective width/height; near and far are camera-space distances.
void ViewPort::SetPerspective(float fov, float aspect, float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = fov;
    mPrivate.mFrustum.mAspect = aspect;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXPerspective(mPrivate.mProjection, fov, 1.0f, nearPlane, farPlane);
    mPrivate.mProjection[1][1] *= aspect;
    mPrivate.mProjectionMatrix.m[0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m[8] = mPrivate.mProjection[0][2];
    mPrivate.mProjectionMatrix.m[9] = mPrivate.mProjection[1][2];
    mPrivate.mProjectionMatrix.m[10] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m[11] = -1.0f;
    mPrivate.mProjectionMatrix.m[14] = mPrivate.mProjection[2][3];
    // MATCH: clearing entries 15,12,13 emits stores 13,15,12; index order emits 15,12,13.
    mPrivate.mProjectionMatrix.m[12] = 0.0f;
    mPrivate.mProjectionMatrix.m[13] = 0.0f;
    mPrivate.mProjectionMatrix.m[15] = 0.0f;
    mPrivate.mProjectionMatrix.m[5] = mPrivate.mProjection[1][1];
    GXSetProjection(mPrivate.mProjection, GX_PERSPECTIVE);
    mPrivate.mProjectionType = PERSPECTIVE;

    float halfWidth = tanf((fov * 0.5f) * (3.14159265358979323846f / 180.0f));
    float leftAngle = atanf(-halfWidth * mPrivate.mCullData.mLeftScale);
    float rightAngle = atanf(halfWidth * mPrivate.mCullData.mRightScale);
    float topAngle = atanf(halfWidth * mPrivate.mCullData.mTopScale / aspect);
    float bottomAngle = atanf(-halfWidth * mPrivate.mCullData.mBottomScale / aspect);
    mPrivate.mCullData.mLeftTan = tanf(leftAngle);
    mPrivate.mCullData.mLeftSin = sinf(3.14159265358979323846f / 2.0f - leftAngle);
    mPrivate.mCullData.mRightTan = tanf(rightAngle);
    mPrivate.mCullData.mRightSin = sinf(3.14159265358979323846f / 2.0f - rightAngle);
    mPrivate.mCullData.mTopTan = tanf(topAngle);
    mPrivate.mCullData.mTopSin = sinf(3.14159265358979323846f / 2.0f - topAngle);
    mPrivate.mCullData.mBottomTan = tanf(bottomAngle);
    mPrivate.mCullData.mBottomSin = sinf(3.14159265358979323846f / 2.0f - bottomAngle);
}
