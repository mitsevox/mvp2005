// geomlib.h: GeomLib, EA's collision geometry library (C:/mvp2004/source/common/geomlib/).
// Name: EA's path string "/mvp2004/source/common/geomlib/geomlib.h" and "Initialising GeomLib".
// Only what the matched units use is declared here; the rest is filled in as units are matched.
#ifndef GEOMLIB_H
#define GEOMLIB_H

// The game-side services GeomLib calls through gGeomLibHost: GeomLib::Init stores the object it is
// given there and prints "Initialising GeomLib\n" through it.
class GeomLibHost {
public:
    int mHostData;  // 0x00
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
    GEOM_CONE = 5,
    GEOM_GROUP = 10,
};

// The surface a shape is made of ("Default", "Glass", "Rubber": set up by GeomLib::Init).
class GeomMaterial;
extern GeomMaterial gDefaultMaterial;
// What a new shape's mUserValue starts as.
extern int gGeomDefaultUserValue;

// An axis-aligned bounding box.
struct GeomBox {
    float mMin[4];  // 0x00 x, y, z
    float mMax[4];  // 0x10 x, y, z
    GeomBox& operator=(const GeomBox& box);

    // Grows the box to enclose box. The tests are written !(a <= b), which also takes box's value
    // when the old one is NaN; a plain a > b compiles to a different branch (ble, not cror/bso).
    void Enclose(const GeomBox& box) {
        if (!(mMin[0] <= box.mMin[0]))
            mMin[0] = box.mMin[0];
        if (!(mMin[1] <= box.mMin[1]))
            mMin[1] = box.mMin[1];
        if (!(mMin[2] <= box.mMin[2]))
            mMin[2] = box.mMin[2];
        if (!(mMax[0] >= box.mMax[0]))
            mMax[0] = box.mMax[0];
        if (!(mMax[1] >= box.mMax[1]))
            mMax[1] = box.mMax[1];
        if (!(mMax[2] >= box.mMax[2]))
            mMax[2] = box.mMax[2];
    }
};

// The base of every collision shape. The intersection tests are picked from a table by the two
// shapes' mType.
class Geom {
public:
    unsigned char mType;      // 0x00 GeomType
    unsigned char mUserTag;   // 0x01 zero when built, copied by CopyProperties; GeomLib never reads it
    unsigned char mActive;    // 0x02 Transform skips the shape when 0
    unsigned char mPrepared;  // 0x03 0 after Transform; the intersection tests call Prepare first
    Geom* mParent;            // 0x04 the GeomGroup holding this shape, or NULL
    int mUserValue;           // 0x08 gGeomDefaultUserValue when built, copied by CopyProperties
    GeomMaterial* mMaterial;  // 0x0C gDefaultMaterial when built
    char mPad10[0x20];
    GeomBox mBounds;          // 0x30 world-space bounds, recomputed by Transform
    char mPad50[0xC];
    // 0x5C vtable

    Geom() {
        Parent() = 0;
        UserValue() = gGeomDefaultUserValue;
        UserTag() = 0;
        mPrepared = false;
        Material() = &gDefaultMaterial;
        SetActive(true);
    }

    // Brings the shape's lazily built data up to date and sets mPrepared.
    virtual void Prepare();
    virtual ~Geom() {}
    // Frees what the shape owns.
    virtual void Release();
    // Makes a new copy of the shape scaled by scale.
    virtual Geom* Clone(const float* scale) = 0;
    // Sets the shape to src (a shape of the same type) scaled by scale.
    virtual void SetScaled(const Geom* src, const float* scale) = 0;
    // Moves the shape to world space by the 4x4 matrix and recomputes mBounds. When keepPrevious
    // is set, one shape type first copies part of its data aside (read as its previous position).
    virtual void Transform(const float* matrix, bool keepPrevious) = 0;

    Geom*& Parent();
    int& UserValue();
    unsigned char& UserTag();
    GeomMaterial*& Material();
    void SetActive(bool active);
    // Copies mUserValue, mMaterial and mUserTag from src.
    void CopyProperties(const Geom* src);

    static void* operator new(unsigned int size) { return gGeomLibHost->Alloc(size, gGeomAllocTag); }
    static void operator delete(void* block) { gGeomLibHost->Free(block); }
};

#endif
