// geomgroup.cpp: GeomGroup, the collision shape that holds other shapes (a tree of Geoms).
// Name: EA's path string "/mvp2004/source/common/geomlib/geomgroup.cpp" (the asserts' __FILE__).
// The asserts' __LINE__ values are EA's, set with #line.
#include "common/geomlib/geomgroup.h"

// Builds an empty group.
GeomGroup::GeomGroup() {
    mType = GEOM_GROUP;
    mNumChildren = 0;
    mChildren = 0;
}

// Frees the children and the array (through Release).
GeomGroup::~GeomGroup() {
    Release();
}

// Deletes every child and the child array, leaving an empty group.
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

// Makes this group a copy of src: its Geom properties, then a clone of each child at scale,
// each clone's parent set to this group.
void GeomGroup::CopyFrom(const GeomGroup* src, const float* scale) {
    CopyProperties(src);
    AllocChildren(src->mNumChildren);
    for (int i = 0; i < src->mNumChildren; i++) {
        Child(i) = src->mChildren[i]->Clone(scale);
        Child(i)->mParent = this;
    }
}

// Sets each child to the matching child of src (a group) scaled by scale. Loops over src's
// children, so this group needs at least as many.
void GeomGroup::SetScaled(const Geom* src, const float* scale) {
#line 118
    GEOM_ASSERT(src->mType == GEOM_GROUP);
    const GeomGroup* group = (const GeomGroup*)src;
    for (int i = 0; i < group->mNumChildren; i++)
        Child(i)->SetScaled(group->mChildren[i], scale);
}

// Returns a new group whose children are clones of these at scale.
Geom* GeomGroup::Clone(const float* scale) {
    GeomGroup* copy = new GeomGroup;
#line 136
    GEOM_ASSERT(copy != 0);
    copy->CopyFrom(this, scale);
    return copy;
}

// Transforms every child, recomputes the group's bounds from theirs and marks the group
// unprepared.
void GeomGroup::Transform(const float* matrix, bool keepPrevious) {
    for (int i = 0; i < mNumChildren; i++)
        mChildren[i]->Transform(matrix, keepPrevious);
    UpdateBounds();
    mPrepared = false;
}

// Sets mBounds to the box around every child's bounds. Needs at least one child.
void GeomGroup::UpdateBounds() {
    mBounds = mChildren[0]->mBounds;
    for (int i = 1; i < mNumChildren; i++)
        mBounds.Enclose(mChildren[i]->mBounds);
}

// Only sets mPrepared: a group has no lazily built data of its own (the same body as Geom's).
void GeomGroup::Prepare() {
    mPrepared = true;
}
