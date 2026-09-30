// geomsphere.h: GeomSphere, the collision shape for a sphere. The folder is geomsphere.cpp's (EA's
// path string); this header's own path is not in the binary.
#ifndef GEOMSPHERE_H
#define GEOMSPHERE_H

#include "common/geomlib/geomray.h"

// A sphere shape. In progress (0x120..0x12F and 0x140..0x183 are not yet read).
class GeomSphere : public Geom {
public:
    GeomRay mRay;          // 0x60 what it is for is not yet read
    char mPad120[0x10];    // unknown: 0x120..0x12F, member count and types not read yet
    COORD4 mCenter;        // 0x130 GeomCone places its end spheres here
    char mPad140[0x44];    // unknown: 0x140..0x183, member count and types not read yet
    float mRadius;         // 0x184
    float mRadiusSq;       // 0x188 mRadius * mRadius

    GeomSphere() {
        mType = GEOM_SPHERE;
    }

    virtual void Prepare();
    virtual ~GeomSphere();
    virtual Geom* Clone(const COORD4* scale);
    virtual void SetScaled(const Geom* src, const COORD4* scale);
    virtual void Transform(const MATRIX4* matrix, bool keepPrevious);

    void SetRadius(float radius) {
        mRadius = radius;
        mRadiusSq = radius * radius;
    }
};

#endif
