// geomray.h: GeomRay, the collision shape for a line segment. The folder is geomray.cpp's (EA's
// path string); this header's own path is not in the binary.
#ifndef GEOMRAY_H
#define GEOMRAY_H

#include "common/geomlib/geomlib.h"

// A ray shape. In progress (0x60..0xAF and 0xB4 are not yet read).
class GeomRay : public Geom {
public:
    char mPad60[0x50];   // unknown: 0x60..0xAF, member count and types not read yet
    float mLength;       // 0xB0 0 when built; SetScaled scales it by scale x
    char mPadB4[4];      // unknown: 0xB4..0xB7, member count and types not read yet
    float mMaxLength;    // 0xB8 1e7 when built
    float mInvMaxLength; // 0xBC 1 / mMaxLength

    GeomRay() {
        mType = GEOM_RAY;
        mLength = 0.0f;
        mMaxLength = 1e7f;
        mInvMaxLength = 1.0f / mMaxLength;
    }

    virtual void Prepare();
    virtual ~GeomRay();
    virtual Geom* Clone(const COORD4* scale);
    virtual void SetScaled(const Geom* src, const COORD4* scale);
    virtual void Transform(const MATRIX4* matrix, bool keepPrevious);
};

#endif
