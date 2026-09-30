// viewport_cull.cpp: viewport.o in the FIFA/UEFA SN maps; this is a recovered subset.
#include "eagl/viewport.h"

// 0 rejects spheres outside the depth limits or perspective side planes; radius is unscaled.
int EAGL::ViewPort::TestSphere(const COORD3& centre, float radius) const {
    COORD3 viewCentre;
    Transform viewTransform(gViewMatrix);
    viewTransform.TransformPoint(centre, viewCentre);

    float distance = viewCentre.z + mPrivate.mFrustum.mNearPlane;
    if (distance > radius)
        return 0;
    // MATCH: -(z + farPlane) adds into f0 then negates into f13; keeping the far-plane
    // distance before reversing its sign retains f13 for both instructions.
    distance = viewCentre.z + mPrivate.mFrustum.mFarPlane;
    distance = -distance;
    if (distance > radius)
        return 0;

    if (mPrivate.mProjectionType == EAGLInternal::PERSPECTIVE) {
        distance = viewCentre.x + viewCentre.z * mPrivate.mCullData.mRightTan;
        if (distance > 0.0f) {
            distance *= mPrivate.mCullData.mRightSin;
            if (distance > radius)
                return 0;
        } else {
            distance = viewCentre.x + viewCentre.z * mPrivate.mCullData.mLeftTan;
            if (distance < 0.0f) {
                distance *= -mPrivate.mCullData.mLeftSin;
                if (distance > radius)
                    return 0;
            }
        }

        distance = viewCentre.y + viewCentre.z * mPrivate.mCullData.mTopTan;
        if (distance > 0.0f) {
            distance *= mPrivate.mCullData.mTopSin;
            if (distance > radius)
                return 0;
        } else {
            distance = viewCentre.y + viewCentre.z * mPrivate.mCullData.mBottomTan;
            if (distance < 0.0f) {
                distance *= -mPrivate.mCullData.mBottomSin;
                if (distance > radius)
                    return 0;
            }
        }
    }
    return 1;
}
