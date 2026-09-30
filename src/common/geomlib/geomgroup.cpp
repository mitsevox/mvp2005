// geomgroup.cpp: GeomGroup, the collision shape made of other shapes (a tree of Geoms).
// Name: EA's path string "/mvp2004/source/common/geomlib/geomgroup.cpp" (the asserts' __FILE__).
// The asserts' __LINE__ values are EA's, set with #line.
// Extent (the map's edges are open): from the constructor at 0x802E313C, right after
// GeomCone::PointOnAxis, to Prepare at 0x802E3770 (vtable slot 1), the highest-addressed function
// _vt.9GeomGroup (0x80664B18) holds; UpdateBounds, before it, is called by Transform.
// fn_802E377C after it sets gGeomLibHost, so it is not GeomGroup's.
#include "common/geomlib/geomgroup.h"

// Builds an empty group.
GeomGroup::GeomGroup() {
    mType = GEOM_GROUP;
    mNumChildren = 0;
    mChildren = 0;
}

// Frees the children with the group.
GeomGroup::~GeomGroup() {
    Release();
}

// Frees what the group owns (its children and the array), leaving it empty.
void GeomGroup::Release() {
    for (int i = 0; i < mNumChildren; i++) {
        delete mChildren[i];
        mChildren[i] = 0;
    }
    mNumChildren = 0;
    delete[] mChildren;
    mChildren = 0;
}

// Makes room for count children (count must be at least 1), all NULL. Does not free an old array.
void GeomGroup::AllocChildren(int count) {
#line 75 "/mvp2004/source/common/geomlib/geomgroup.cpp"
    GEOM_ASSERT(count > 0);
    mNumChildren = count;
    mChildren = new Geom*[count];
#line 80
    GEOM_ASSERT(mChildren != 0);
    for (int i = 0; i < count; i++)
        mChildren[i] = 0;
}

// Makes this empty group a copy of src at scale, owning clones of src's children.
void GeomGroup::CopyFrom(const GeomGroup* src, const COORD4* scale) {
    CopyProperties(src);
    AllocChildren(src->mNumChildren);
    for (int i = 0; i < src->mNumChildren; i++) {
        Child(i) = src->mChildren[i]->Clone(scale);
        Child(i)->Parent() = this;
    }
}

// Sets each child to src's matching child at scale. This group needs at least as many
// children as src (a group).
void GeomGroup::SetScaled(const Geom* src, const COORD4* scale) {
#line 118
    GEOM_ASSERT(src->mType == GEOM_GROUP);
    const GeomGroup* group = (const GeomGroup*)src;
    for (int i = 0; i < group->mNumChildren; i++)
        Child(i)->SetScaled(group->mChildren[i], scale);
}

// Returns a new group whose children are clones of these at scale.
Geom* GeomGroup::Clone(const COORD4* scale) {
    GeomGroup* copy = new GeomGroup;
#line 136
    GEOM_ASSERT(copy != 0);
    copy->CopyFrom(this, scale);
    return copy;
}

// Moves every child by matrix; the group's bounds follow its children.
void GeomGroup::Transform(const MATRIX4* matrix, bool keepPrevious) {
    for (int i = 0; i < mNumChildren; i++)
        mChildren[i]->Transform(matrix, keepPrevious);
    UpdateBounds();
    mPrepared = 0;
}

// Fits mBounds around the children's bounds. Needs at least one child.
void GeomGroup::UpdateBounds() {
    mBounds = mChildren[0]->mBounds;
    for (int i = 1; i < mNumChildren; i++)
        mBounds.Enclose(mChildren[i]->mBounds);
}

// A group has nothing of its own to prepare (the same body as Geom's).
void GeomGroup::Prepare() {
    mPrepared = 1;
}
