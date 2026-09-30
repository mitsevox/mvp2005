// geomcone.h: GeomCone, the collision shape for a capped cone. The folder is geomcone.cpp's (EA's
// path string); this header's own path is not in the binary.
#ifndef GEOMCONE_H
#define GEOMCONE_H

#include "common/geomlib/geomsphere.h"

// A cone cut off at two ends, with an end sphere at each end.
class GeomCone : public Geom {
public:
    GeomSphere mSpheres[2];  // 0x060 at the base and the top, with the radius of that end
    COORD4 mLocalBase;       // 0x378 the base centre before Transform
    COORD4 mLocalAxis;       // 0x388 the direction base to top before Transform
    float mLength;           // 0x398 base to top along the axis
    float mRadius[2];        // 0x39C at the base and at the top; the base one is the smaller
    float mRadiusSq[2];      // 0x3A4 mRadius squared
    float mCapRadius[2];     // 0x3AC mRadius when that end's mEndType is 2, else 0
    int mEndType[2];         // 0x3B4
    COORD4 mBase;            // 0x3BC the base centre, from Transform
    COORD4 mTop;             // 0x3CC the top centre
    COORD4 mAxis;            // 0x3DC the direction base to top
    COORD4 mApex;            // 0x3EC where the sides meet, beyond the base
    GeomPlane mBasePlane;    // 0x3FC through mBase, facing away from the top
    GeomPlane mTopPlane;     // 0x40C through mTop, facing away from the base
    float mApexToBase;       // 0x41C
    float mCosAngle;         // 0x420 the cosine of the half angle at the apex
    float mCosAngleSq;       // 0x424
    float mInvCosAngle;      // 0x428
    float mSinAngle;         // 0x42C the sine of the half angle
    float mSinAngleSq;       // 0x430
    float mSlope;            // 0x434 how fast the radius grows along the axis
    float mInvSlope;         // 0x438

    GeomCone() {
        mType = GEOM_CONE;
    }

    virtual ~GeomCone();
    virtual Geom* Clone(const COORD4* scale);
    virtual void SetScaled(const Geom* src, const COORD4* scale);
    virtual void Transform(const MATRIX4* matrix, bool keepPrevious);

    void CopySphereProperties();
    void CopyFrom(const GeomCone* src, const COORD4* scale);
    void Precompute();
    void PointOnAxis(float t, COORD4* out) const;

    void SetRadius(int end, float radius) {
        mRadius[end] = radius;
        mRadiusSq[end] = radius * radius;
        mSpheres[end].SetRadius(radius);
    }
};

#endif
