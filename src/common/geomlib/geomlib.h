// geomlib.h: GeomLib, EA's collision geometry library.
// Name: EA's path string "C:/mvp2004/source/common/geomlib/geomlib.h" and "Initialising GeomLib".
// In progress: only what the matched units use is declared; the rest is filled in as units match.
#ifndef GEOMLIB_H
#define GEOMLIB_H

#include "realcore/realmath.h"

// The game-side services GeomLib calls through gGeomLibHost. In progress (the word at 0x00).
class GeomLibHost {
public:
    char mPad00[4];
    // 0x04 vtable
    virtual ~GeomLibHost();
    // Reports a failed check: cond false means the check at file:line failed.
    virtual void Assert(bool cond, const char* file, int line);
    virtual void Print(const char* text);
    // Allocates size bytes; tag names the allocation (GeomLib passes gGeomAllocTag).
    virtual void* Alloc(unsigned int size, const char* tag);
    virtual void Free(void* block);
};

extern GeomLibHost* gGeomLibHost;
// "X", the tag every GeomLib allocation passes to GeomLibHost::Alloc.
extern const char gGeomAllocTag[];

#define GEOM_ASSERT(cond) gGeomLibHost->Assert((cond), __FILE__, __LINE__)

// Geom::mType. Each shape's SetScaled asserts its source is of its own type.
enum GeomType {
    GEOM_RAY = 1,
    GEOM_SPHERE = 4,
    GEOM_CONE = 5,
    GEOM_GROUP = 10,
};

// The surface a shape is made of ("Default", "Glass", "Rubber" are set up at startup).
class GeomMaterial;
extern GeomMaterial gDefaultMaterial;
// What a new shape's mUserValue starts as.
extern int gGeomDefaultUserValue;

// An axis-aligned bounding box.
struct GeomBox {
    COORD4 mMin;  // 0x00
    COORD4 mMax;  // 0x10
    // MATCH: COORD4 has constructors, so without this Geom() calls the implicit GeomBox
    // constructor out of line (no such call in any Geom constructor); this one inlines to nothing.
    GeomBox() {}
    // MATCH: declared only; UpdateBounds calls the copy out of line (0x8035F4EC), and both the
    // implicit operator= and one defined here are inlined instead.
    GeomBox& operator=(const GeomBox& box);

    // Grows the box to enclose box.
    // MATCH: only !(a <= b) gives the cror/bso branch around each store; a < b and a > b branch
    // with ble/bge, and x = MIN(x, y) stores unconditionally.
    void Enclose(const GeomBox& box) {
        if (!(mMin.x <= box.mMin.x)) mMin.x = box.mMin.x;
        if (!(mMin.y <= box.mMin.y)) mMin.y = box.mMin.y;
        if (!(mMin.z <= box.mMin.z)) mMin.z = box.mMin.z;
        if (!(mMax.x >= box.mMax.x)) mMax.x = box.mMax.x;
        if (!(mMax.y >= box.mMax.y)) mMax.y = box.mMax.y;
        if (!(mMax.z >= box.mMax.z)) mMax.z = box.mMax.z;
    }

    // Sets the box to the one around a sphere (w is left as it was).
    void SetSphere(const COORD4& centre, float radius) {
        mMin.x = centre.x - radius;
        mMin.y = centre.y - radius;
        mMin.z = centre.z - radius;
        mMax.x = centre.x + radius;
        mMax.y = centre.y + radius;
        mMax.z = centre.z + radius;
    }

    // Grows the box to enclose a sphere. The same compare form as Enclose.
    void EncloseSphere(const COORD4& centre, float radius) {
        if (!(mMin.x <= centre.x - radius)) mMin.x = centre.x - radius;
        if (!(mMin.y <= centre.y - radius)) mMin.y = centre.y - radius;
        if (!(mMin.z <= centre.z - radius)) mMin.z = centre.z - radius;
        if (!(mMax.x >= centre.x + radius)) mMax.x = centre.x + radius;
        if (!(mMax.y >= centre.y + radius)) mMax.y = centre.y + radius;
        if (!(mMax.z >= centre.z + radius)) mMax.z = centre.z + radius;
    }
};

// A plane: the points p with n.x*p.x + n.y*p.y + n.z*p.z + d == 0 (a, b, c, d = n.x, n.y, n.z, d).
struct GeomPlane {
    float a, b, c, d;
    // MATCH: declared only; GeomCone calls all three out of line (0x8035F4E4, 0x8035F4A4,
    // 0x8035F47C), and defined ones here are inlined instead.
    GeomPlane();
    GeomPlane(float a, float b, float c, float d);
    GeomPlane& operator=(const GeomPlane& plane);
};

class GeomGroup;

// The base of every collision shape. In progress (0x10..0x2F and 0x50..0x5B are not yet read).
class Geom {
public:
    unsigned char mType;      // 0x00 GeomType
    unsigned char mUserTag;   // 0x01 zero when built, copied by CopyProperties; no reader found yet
    unsigned char mActive;    // 0x02 one shape's Transform skips its work when 0
    unsigned char mPrepared;  // 0x03 0 after Transform; set by Prepare
    GeomGroup* mParent;       // 0x04 the GeomGroup holding this shape, or NULL
    int mUserValue;           // 0x08 gGeomDefaultUserValue when built, copied by CopyProperties
    GeomMaterial* mMaterial;  // 0x0C gDefaultMaterial when built
    char mPad10[0x20];
    GeomBox mBounds;          // 0x30 the box around the shape, recomputed by Transform
    char mPad50[0xC];
    // 0x5C vtable

    // MATCH: Geom() is compiled before the accessors below are defined, so every constructor calls
    // them out of line; code after the definitions (GeomGroup::CopyFrom's Parent()) inlines them.
    // mPrepared has no accessor.
    Geom() {
        Parent() = 0;
        UserValue() = gGeomDefaultUserValue;
        UserTag() = 0;
        mPrepared = 0;
        Material() = &gDefaultMaterial;
        SetActive(true);
    }

    // Brings the shape up to date for the intersection tests (they call it while mPrepared is 0).
    virtual void Prepare();
    virtual ~Geom() {}
    // Frees what the shape owns.
    virtual void Release();
    // Makes a new copy of the shape scaled by scale.
    virtual Geom* Clone(const COORD4* scale) = 0;
    // Sets the shape to src (a shape of the same type) scaled by scale.
    virtual void SetScaled(const Geom* src, const COORD4* scale) = 0;
    // Moves the shape by matrix and recomputes mBounds. keepPrevious is a guessed name (T4 row).
    virtual void Transform(const MATRIX4* matrix, bool keepPrevious) = 0;

    GeomGroup*& Parent();
    int& UserValue();
    unsigned char& UserTag();
    GeomMaterial*& Material();
    void SetActive(bool active);
    // Gives this shape src's properties that are not geometry (what a clone inherits).
    void CopyProperties(const Geom* src);

    static void* operator new(unsigned int size) { return gGeomLibHost->Alloc(size, gGeomAllocTag); }
    static void operator delete(void* block) { gGeomLibHost->Free(block); }
};

inline GeomGroup*& Geom::Parent() { return mParent; }
inline int& Geom::UserValue() { return mUserValue; }
inline unsigned char& Geom::UserTag() { return mUserTag; }
inline GeomMaterial*& Geom::Material() { return mMaterial; }
inline void Geom::SetActive(bool active) { mActive = active; }

#endif
