// geomgroup.h: GeomGroup, a collision shape made of other shapes (C:/mvp2004/source/common/geomlib/).
#ifndef GEOMGROUP_H
#define GEOMGROUP_H

#include "common/geomlib/geomlib.h"

// A shape that owns an array of child shapes; its bounds enclose theirs.
class GeomGroup : public Geom {
public:
    int mNumChildren;   // 0x60
    Geom** mChildren;   // 0x64 mNumChildren shapes, each owned by the group

    GeomGroup();
    virtual void Prepare();
    virtual ~GeomGroup();
    virtual void Release();
    virtual Geom* Clone(const float* scale);
    virtual void SetScaled(const Geom* src, const float* scale);
    virtual void Transform(const float* matrix, bool keepPrevious);

    void AllocChildren(int count);
    void CopyFrom(const GeomGroup* src, const float* scale);
    void UpdateBounds();

    // Matching note: CopyFrom and SetScaled reach their own children through this; written as
    // mChildren[i] there, the indexed load and store take their operands the other way round.
    Geom*& Child(int i) { return mChildren[i]; }
};

#endif
