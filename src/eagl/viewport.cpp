// viewport.cpp: libeaglSNz.a(viewport.o) in the FIFA 2005 and UEFA CL 04-05 maps; the file name
// is theirs. EAGL's viewport: projection setup, sphere culling and the view stack. In progress:
// the functions not written here stay in asm. ReBegin at 0x803E1F0C (size 0x60 in both maps) is
// followed by the global initializer at 0x803E1F6C, registered at 0x805A2CF8 in the constructor
// list and calling this unit's static initializer at 0x803E1B54. It ends at 0x803E1F98, where
// both maps place the next object's ViewPort constructor in viewport_cmn.o. Those two final
// functions also stay in asm. The object's .data and .bss (the gp* matrix pointers
// from 0x8062C280, the matrices from 0x806AA990) are not split out: other EAGL objects use the
// same area and where viewport.o's part starts and ends is still open.
#include "eagl/viewport.h"
#include <dolphin/gx/GXTransform.h>
#include <dolphin/mtx.h>
#include <math.h>

using namespace EAGL;
using namespace EAGLInternal;

// Sets a perspective projection, uploads it to GX and rebuilds the culling planes. fov is the
// horizontal field of view in degrees: the SDK matrix is built for a square view and its y scale is
// then multiplied by aspect (width over height). near and far are camera-space distances.
void ViewPort::SetPerspective(float fov, float aspect, float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = fov;
    mPrivate.mFrustum.mAspect = aspect;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXPerspective(mPrivate.mProjection, fov, 1.0f, nearPlane, farPlane);
    mPrivate.mProjection[1][1] *= aspect;
    // GX's matrix is for column vectors, EA's for row vectors (v * M): copy it transposed.
    mPrivate.mProjectionMatrix.m44[0][0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m44[1][1] = mPrivate.mProjection[1][1];
    mPrivate.mProjectionMatrix.m44[2][0] = mPrivate.mProjection[0][2];
    mPrivate.mProjectionMatrix.m44[2][1] = mPrivate.mProjection[1][2];
    mPrivate.mProjectionMatrix.m44[2][2] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m44[2][3] = -1.0f;
    mPrivate.mProjectionMatrix.m44[3][0] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][1] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][2] = mPrivate.mProjection[2][3];
    mPrivate.mProjectionMatrix.m44[3][3] = 0.0f;
    GXSetProjection(mPrivate.mProjection, GX_PERSPECTIVE);
    mPrivate.mProjectionType = PERSPECTIVE;

    // Each side plane's angle from the view axis, widened or narrowed by that side's scale.
    float halfWidth = tanf(DegToRad(fov * 0.5f));
    float leftAngle = atanf(-halfWidth * mPrivate.mCullData.mLeftScale);
    float rightAngle = atanf(halfWidth * mPrivate.mCullData.mRightScale);
    float topAngle = atanf(halfWidth * mPrivate.mCullData.mTopScale / aspect);
    float bottomAngle = atanf(-halfWidth * mPrivate.mCullData.mBottomScale / aspect);
    mPrivate.mCullData.mLeftTan = tanf(leftAngle);
    mPrivate.mCullData.mLeftSin = sinf(HALFPI_F - leftAngle);
    mPrivate.mCullData.mRightTan = tanf(rightAngle);
    mPrivate.mCullData.mRightSin = sinf(HALFPI_F - rightAngle);
    mPrivate.mCullData.mTopTan = tanf(topAngle);
    mPrivate.mCullData.mTopSin = sinf(HALFPI_F - topAngle);
    mPrivate.mCullData.mBottomTan = tanf(bottomAngle);
    mPrivate.mCullData.mBottomSin = sinf(HALFPI_F - bottomAngle);
}

// True unless the sphere is wholly outside the view: past the near or far plane, or, in a
// perspective view, outside a side plane. radius is in view space, not scaled. On each axis only
// the side the centre lies towards is tested.
bool ViewPort::IsSphereInView(const COORD3& centre, float radius) {
    COORD3 viewCentre;
    Transform viewTransform(gViewMatrix);
    viewTransform.TransformPoint(centre, viewCentre);

    // View space looks down -z: z + near is how far the centre lies on the camera side of the
    // near plane, and -(z + far) how far it lies beyond the far plane.
    float distance = viewCentre.z + mPrivate.mFrustum.mNearPlane;
    if (distance > radius)
        return false;
    distance = viewCentre.z + mPrivate.mFrustum.mFarPlane;
    if (-distance > radius)
        return false;

    if (mPrivate.mProjectionType == PERSPECTIVE) {
        distance = viewCentre.x + viewCentre.z * mPrivate.mCullData.mRightTan;
        if (distance > 0.0f) {
            distance *= mPrivate.mCullData.mRightSin;
            if (distance > radius)
                return false;
        } else {
            distance = viewCentre.x + viewCentre.z * mPrivate.mCullData.mLeftTan;
            if (distance < 0.0f) {
                distance *= -mPrivate.mCullData.mLeftSin;
                if (distance > radius)
                    return false;
            }
        }

        distance = viewCentre.y + viewCentre.z * mPrivate.mCullData.mTopTan;
        if (distance > 0.0f) {
            distance *= mPrivate.mCullData.mTopSin;
            if (distance > radius)
                return false;
        } else {
            distance = viewCentre.y + viewCentre.z * mPrivate.mCullData.mBottomTan;
            if (distance < 0.0f) {
                distance *= -mPrivate.mCullData.mBottomSin;
                if (distance > radius)
                    return false;
            }
        }
    }
    return true;
}

// Reports the viewport rectangle and its depth range.
void ViewPort::GetShape(float& originX, float& originY, float& width, float& height,
                       float& nearZ, float& farZ) const {
    originX = mPrivate.mGeometry.mOriginX;
    originY = mPrivate.mGeometry.mOriginY;
    width = mPrivate.mGeometry.mWidth;
    height = mPrivate.mGeometry.mHeight;
    nearZ = mPrivate.mGeometry.mNearZ;
    farZ = mPrivate.mGeometry.mFarZ;
}

// Sets an orthographic view spanning -1..1 horizontally and -aspect..aspect vertically,
// with nearPlane and farPlane as camera-space distances, and uploads its projection to GX.
void ViewPort::SetOrthographic(float aspect, float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = 0.0f;
    mPrivate.mFrustum.mAspect = aspect;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXOrtho(mPrivate.mProjection, aspect, -aspect, -1.0f, 1.0f, nearPlane, farPlane);
    // GX's column-vector projection is transposed for EA's row-vector matrix.
    mPrivate.mProjectionMatrix.m44[0][0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m44[1][1] = mPrivate.mProjection[1][1];
    mPrivate.mProjectionMatrix.m44[2][0] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][1] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][2] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m44[2][3] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][0] = mPrivate.mProjection[0][3];
    mPrivate.mProjectionMatrix.m44[3][1] = mPrivate.mProjection[1][3];
    mPrivate.mProjectionMatrix.m44[3][2] = mPrivate.mProjection[2][3];
    mPrivate.mProjectionMatrix.m44[3][3] = 1.0f;
    mPrivate.mProjectionType = ORTHOGRAPHIC;
    GXSetProjection(mPrivate.mProjection, GX_ORTHOGRAPHIC);
}

// Sets a screen-space projection with the viewport's width and height, x right and y down,
// and uploads it to GX. nearPlane and farPlane set the camera-space depth range.
void ViewPort::SetOrthographicScreenSpace(float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = 0.0f;
    mPrivate.mFrustum.mAspect = 0.75f;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXOrtho(mPrivate.mProjection, 0.0f, mPrivate.mGeometry.mHeight,
               0.0f, mPrivate.mGeometry.mWidth, nearPlane, farPlane);
    // GX uses column vectors; EA's row-vector matrix is its transpose.
    mPrivate.mProjectionMatrix.m44[0][0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m44[1][1] = mPrivate.mProjection[1][1];
    mPrivate.mProjectionMatrix.m44[2][0] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][1] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][2] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m44[2][3] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][0] = mPrivate.mProjection[0][3];
    mPrivate.mProjectionMatrix.m44[3][1] = mPrivate.mProjection[1][3];
    mPrivate.mProjectionMatrix.m44[3][2] = mPrivate.mProjection[2][3];
    mPrivate.mProjectionMatrix.m44[3][3] = 1.0f;
    mPrivate.mProjectionType = ORTHOGRAPHIC;
    GXSetProjection(mPrivate.mProjection, GX_ORTHOGRAPHIC);
}
