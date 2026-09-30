// geomgroup.h: GeomGroup, a collision shape made of other shapes. The folder is geomgroup.cpp's
// (EA's path string); this header's own path is not in the binary.
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
    virtual Geom* Clone(const COORD4* scale);
    virtual void SetScaled(const Geom* src, const COORD4* scale);
    virtual void Transform(const MATRIX4* matrix, bool keepPrevious);

    void AllocChildren(int count);
    void CopyFrom(const GeomGroup* src, const COORD4* scale);
    void UpdateBounds();

    // MATCH: CopyFrom and SetScaled need this accessor's base-first lwzx/stwx operand order;
    // AllocChildren, Release, Transform and UpdateBounds need mChildren[i]'s index-first order, so
    // they index directly.
    // It is not const, so a const source group's children are always read as src->mChildren[i].
    Geom*& Child(int i) { return mChildren[i]; }
};

#endif
