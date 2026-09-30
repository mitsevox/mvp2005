// viewport.h: EAGL's viewport (libeaglSNz.a, FIFA 2005 and UEFA CL 04-05 maps). The file name is
// ours. Every layout here is EA's, from the DWARF in the disc's libmatd.a (all 25 objects agree;
// .debug offsets are InstanceCrowd.o's, tools/research/dwarf_lookup.py). That DWARF does not say
// whether a type was declared as a struct or a class, or which members were private, and it
// leaves out member functions that are not inline, so the methods declared are the ones the
// matched code needs, with names recovered from maps or explicitly reconstructed below.
// Left out on purpose: the inline
// operator new, new[], delete and delete[] overloads the DWARF lists on most EAGL classes (EA's
// allocator macro; their bodies are not recorded) and ViewPort's inline GetStack/SetStack.
#ifndef EAGL_VIEWPORT_H
#define EAGL_VIEWPORT_H

#include "realcore/realmath.h"
#include "eagl/base.h"
#include "eagl/rendercontext.h"

namespace EAGL {

class ViewPort;
class RenderContextBase;
class RenderContextExtensionBase;

// Clear-mask values from disc .debug 0x1A246; namespace confirmed by map signature.
enum ClearFlags { CLEAR_CURRENT = 1, CLEAR_Z = 2, CLEAR_STENCIL = 4 };

// EAGL's own float constant; libmatd.a's unoptimised objects each keep a copy
// (_4EAGL.HALFPI_F in .rodata), optimised code folds it into a literal.
static const float HALFPI_F = 1.57079632679489661923f;

// The per-object extension slot every EAGL object starts with (0xEE96).
struct ViewPortExtension {
    ViewPort* mpBaseObject; // 0x0

    ViewPortExtension(ViewPort* baseObject);
    ~ViewPortExtension();

    static VerbosityControl sVerbosityControl;
    static float gProjectionValues[7];
    static ViewPort* gpFirstViewPort;
    static const int DEFAULT_BASE_VERBOSITY;
};

// A matrix wrapper for transforming points (0xE12D).
class Transform {
public:
    // 0xE171; values 0, 4, 8 (what they index is not recorded).
    enum Axis {
        X_AXIS = 0,
        Y_AXIS = 4,
        Z_AXIS = 8,
    };

    MATRIX4 m; // 0x0

    // Out of line at 0x803DFA2C. That it is a constructor taking the matrix by reference is a
    // guess from the call: it copies 64 bytes from its second argument into its first.
    Transform(const MATRIX4& matrix);
    // At 0x803DED40 (transform.o in the FIFA and UEFA maps).
    void TransformPoint(const COORD3& point, COORD3& result) const;
    void AppendMatrix(const MATRIX4* matrix);
};

// The current view matrix. The pointer ViewPort::gpViewMatrix (0x8062C280) holds its address and
// IsSphereInView reads it directly; its name is a guess.
extern MATRIX4 gViewMatrix;
// Backing matrix for ViewPort::gpModelViewMatrix; address identified from its pointer/use.
extern MATRIX4 gModelViewMatrix;

} // namespace EAGL

// The namespace of the VP* types and ProjectionType is not recorded; EAGLInternal, beside
// ViewPortPrivate that holds them, is a guess.
namespace EAGLInternal {

// 0xF419.
enum ProjectionType {
    PERSPECTIVE = 0,
    ORTHOGRAPHIC = 1,
};

// The viewport's rectangle and depth range (0xF463).
struct VPGeometry {
    float mOriginX; // 0x00
    float mOriginY; // 0x04
    float mWidth;   // 0x08
    float mHeight;  // 0x0C
    float mNearZ;   // 0x10
    float mFarZ;    // 0x14
};

// The current projection settings, shared by perspective and orthographic views (0xF580).
struct VPFrustum {
    float mFOV;       // 0x00
    float mAspect;    // 0x04
    float mNearPlane; // 0x08
    float mFarPlane;  // 0x0C
};

// Clip-space scale, shear and translation (0xF64C).
struct VPClipData {
    float mScaleX; // 0x00
    float mScaleY; // 0x04
    float mShearX; // 0x08
    float mShearY; // 0x0C
    float mTransX; // 0x10
    float mTransY; // 0x14
};

// The four side planes of the view frustum for sphere culling (0xF76B). Each plane is kept as the
// tangent of its angle and the sine of the angle's complement; the scales widen or narrow
// each side of the view.
struct VPCullData {
    float mLeftTan;     // 0x00
    float mLeftSin;     // 0x04
    float mRightTan;    // 0x08
    float mRightSin;    // 0x0C
    float mTopTan;      // 0x10
    float mTopSin;      // 0x14
    float mBottomTan;   // 0x18
    float mBottomSin;   // 0x1C
    float mLeftScale;   // 0x20
    float mRightScale;  // 0x24
    float mTopScale;    // 0x28
    float mBottomScale; // 0x2C
};

// The viewport's state (0xEFCF).
class ViewPortPrivate {
public:
    EAGL::RenderContextBase* mpRenderContext; // 0x000
    ProjectionType mProjectionType;           // 0x004
    EAGL::Colour mBackgroundColour;           // 0x008
    MATRIX4 mProjectionMatrix;                // 0x00C
    MATRIX4 mViewMatrix;                      // 0x04C
    MATRIX4 mViewProjectionMatrix;            // 0x08C
    VPGeometry mGeometry;                     // 0x0CC
    VPFrustum mFrustum;                       // 0x0E4
    VPClipData mClipData;                     // 0x0F4
    VPCullData mCullData;                     // 0x10C
    unsigned int mClipOriginX;                // 0x13C
    unsigned int mClipOriginY;                // 0x140
    unsigned int mClipWidth;                  // 0x144
    unsigned int mClipHeight;                 // 0x148
    float mProjection[4][4];                  // 0x14C, the matrix given to GX
    bool mAmActive;                           // 0x18C
    bool mFullScreen;                         // 0x190
    bool mUseForFontDraws;                    // 0x194
    EAGL::ViewPort* mNextVP;                  // 0x198
    EAGL::ViewPort* mpBaseObject;             // 0x19C

    static EAGL::Colour gScreenColour;
    ViewPortPrivate(EAGL::ViewPort* baseObject);
    void ReBegin();
    void EnactFogSettings();
};

} // namespace EAGLInternal

namespace EAGL {

// A camera's view of the scene (0xE87F).
class ViewPort {
public:
    ViewPortExtension EXTENSION_OBJ;               // 0x0
    ViewPort* mNextInStack;                        // 0x4
    int mflag_automatic_bounding_sphere_check;     // 0x8
    EAGLInternal::ViewPortPrivate mPrivate;        // 0xC

    static const MATRIX4* gpViewMatrix;
    static const MATRIX4* gpProjectionMatrix;
    static const MATRIX4* gpViewProjectionMatrix;
    static const MATRIX4* gpModelMatrix;
    static const MATRIX4* gpModelViewMatrix;
    static const MATRIX4* gpModelViewProjectionMatrix;
    static VerbosityControl sVerbosityControl;
    static const int DEFAULT_BASE_VERBOSITY;

    void SetPerspective(float fov, float aspect, float nearPlane, float farPlane);
    // Returns 0 or 1; bool (4 bytes on this target) over int is a guess from the Is name.
    bool IsSphereInView(const COORD3& centre, float radius);
    void GetShape(float& originX, float& originY, float& width, float& height,
                  float& nearZ, float& farZ) const;
    void SetOrthographic(float aspect, float nearPlane, float farPlane);
    void SetOrthographicScreenSpace(float nearPlane, float farPlane);
    void SetViewMatrix(const MATRIX4& matrix);
    void BeginView();
    void EndView();
    void ClearViewPort(ClearFlags flags);
    void SetShape(float originX, float originY, float width, float height,
                  float nearZ, float farZ);
    // Name is read from the field returned; const qualification is a guess.
    EAGLInternal::ProjectionType GetProjectionType() const;
};

} // namespace EAGL

#endif
