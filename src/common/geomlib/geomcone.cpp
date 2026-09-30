// geomcone.cpp: GeomCone, the collision shape for a capped cone.
// Name: EA's path string "/mvp2004/source/common/geomlib/geomcone.cpp" (the asserts' __FILE__).
// The asserts' __LINE__ values are EA's, set with #line.
// Extent (the map's edges are open): from the destructor at 0x802E2218 (slot 2 of _vt.8GeomCone,
// 0x80664BD8), right after Geom::CopyProperties, to GeomGroup's constructor at 0x802E313C.
// Not yet exact: Precompute (agents/tried/); the unit is not linked.
#include "common/geomlib/geomcone.h"
#include <math.h>

// Frees the cone; its end spheres go with it.
GeomCone::~GeomCone() {
}

// Gives both end spheres this cone's user value and material.
void GeomCone::CopySphereProperties() {
    for (int i = 0; i < 2; i++) {
        mSpheres[i].UserValue() = UserValue();
        mSpheres[i].Material() = Material();
    }
}

// Makes this new cone a copy of src at scale: lengths scale by scale x, radii by scale y.
void GeomCone::CopyFrom(const GeomCone* src, const COORD4* scale) {
    CopyProperties(src);
    const COORD4& base = src->mLocalBase;
    // fake match: the dst alias and the block exist only to order loads and stores. Through the
    // reference dst the four loads come before the stores (the target's order); v4copy(&mLocalBase,
    // t) interleaves them (95.9%). Without the block around t, SetScaled scores 99.9 (t's stack slot
    // is not reused). The natural forms lose (agents/tried/realmath-COORD4.md).
    COORD4& dst = mLocalBase;
    {
        COORD4 t;
        v4set3(&t, v4scale3(base, scale->x), base.w);
        v4copy(&dst, t);
    }
    v4copy(&mLocalAxis, src->mLocalAxis);
    mLength = src->mLength * scale->x;
    SetRadius(0, src->mRadius[0] * scale->y);
    SetRadius(1, src->mRadius[1] * scale->y);
    mEndType[0] = src->mEndType[0];
    mEndType[1] = src->mEndType[1];
    CopySphereProperties();
}

// Sets the cone's base, length and radii to src's (a cone) at scale, as CopyFrom does.
void GeomCone::SetScaled(const Geom* src, const COORD4* scale) {
#line 74 "/mvp2004/source/common/geomlib/geomcone.cpp"
    GEOM_ASSERT(src->mType == GEOM_CONE);
    const GeomCone* cone = (const GeomCone*)src;
    const COORD4& base = cone->mLocalBase;
    // fake match: dst and the block as in CopyFrom.
    COORD4& dst = mLocalBase;
    {
        COORD4 t;
        v4set3(&t, v4scale3(base, scale->x), base.w);
        v4copy(&dst, t);
    }
    mLength = cone->mLength * scale->x;
    SetRadius(0, cone->mRadius[0] * scale->y);
    SetRadius(1, cone->mRadius[1] * scale->y);
}

// Returns a new cone that is a copy of this one at scale.
Geom* GeomCone::Clone(const COORD4* scale) {
    GeomCone* copy = new GeomCone;
#line 92
    GEOM_ASSERT(copy != 0);
    copy->CopyFrom(this, scale);
    return copy;
}

// Moves the cone by matrix, then refits everything the intersection tests read and the bounds
// (a box around both end spheres). keepPrevious is not used.
void GeomCone::Transform(const MATRIX4* matrix, bool keepPrevious) {
    v4copy(&mBase, v4mult(mLocalBase, *matrix));
    v4copy(&mAxis, v4mult(mLocalAxis, *matrix));
    v4copy(&mTop, v4add(mBase, v4scale(mAxis, mLength)));
    Precompute();
    mPrepared = 0;
    mBounds.SetSphere(mBase, mRadius[0]);
    mBounds.EncloseSphere(mTop, mRadius[1]);
}

// Works out the apex, the half angle and the end planes from the moved ends. The top radius must
// be larger than the base radius.
void GeomCone::Precompute() {
#line 132
    GEOM_ASSERT(mRadius[0] != mRadius[1]);
#line 133
    GEOM_ASSERT(mRadius[0] < mRadius[1]);
    mSlope = (mRadius[1] - mRadius[0]) / mLength;
    mInvSlope = 1.0f / mSlope;
    float apexToTop = mRadius[1] * mInvSlope;
    mApexToBase = apexToTop - mLength;
    float invSide = 1.0f / sqrtf(apexToTop * apexToTop + mRadiusSq[1]);
    mCosAngle = apexToTop * invSide;
    mSinAngle = mRadius[1] * invSide;
    mInvCosAngle = 1.0f / mCosAngle;
    mSinAngleSq = mSinAngle * mSinAngle;
    mCosAngleSq = mCosAngle * mCosAngle;
    v4copy(&mApex, v4sub(mBase, v4scale(mAxis, mApexToBase)));
    mBasePlane = PlaneThrough(v4neg(mAxis), mBase);
    mTopPlane = PlaneThrough(mAxis, mTop);
    v4copy(&mSpheres[0].mCenter, mBase);
    v4copy(&mSpheres[1].mCenter, mTop);
    if (mEndType[0] == 2)
        mCapRadius[0] = mRadius[0];
    else
        mCapRadius[0] = 0.0f;
    if (mEndType[1] == 2)
        mCapRadius[1] = mRadius[1];
    else
        mCapRadius[1] = 0.0f;
}

// Puts in out the point on the axis t / (mCosAngle * mSlope) beyond the apex, on the side away
// from the top (t == 0 gives mApex); raytocone.cpp's ray test uses it.
void GeomCone::PointOnAxis(float t, COORD4* out) const {
    // MATCH: along is declared before dist; declared in use order, the two float-store homes
    // swap (dist at 0xC, along at 0x10).
    float along;
    float dist = (t * mInvCosAngle + mRadius[1]) * mInvSlope;
    along = dist - mLength;
    v4copy(out, v4sub(mBase, v4scale(mAxis, along)));
}
