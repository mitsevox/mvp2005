// Shared EAGL rendering context declarations, from the disc libmatd.a DWARF.
// Offsets cite InstanceCrowd.o. Known data/static members are complete; unrecovered
// out-of-line methods and allocator overloads without recorded bodies are omitted.
#ifndef EAGL_RENDERCONTEXT_H
#define EAGL_RENDERCONTEXT_H

#include "eagl/base.h"
#include <dolphin/gx/GXStruct.h>
#include <dolphin/gx/GXEnum.h>
#include <dolphin/gx/GXManage.h>
#include <dolphin/os/OSMessage.h>

namespace EAGL {
class ViewPort;
class RenderContextBase;
class RenderContext;
class TextureRenderContext;
class Device;
class GCBuffer;
class TAR;

// Render-context overrides, retained in disc DWARF at 0x67EA..0x699E.
// Their namespace is inferred from the owning EAGL extension class.
enum FilterModeOverride { FMO_NOOVERRIDE = -1, FMO_POINT = 1, FMO_BILINEAR = 2, FMO_ANISOTROPIC = 3 };
enum AlphaWritesOverride { AWO_NOOVERRIDE = -1, AWO_ALPHAWRITESDISABLED = 1, AWO_ALPHAWRITESENABLED = 2 };
enum MipMapModeOverride { MMMO_NOOVERRIDE = -1, MMMO_OFF = 0, MMMO_NEAREST = 1, MMMO_LINEAR = 2 };
enum AnisotropyOverride { AO_ANISO_1 = 0, AO_ANISO_2 = 1, AO_ANISO_4 = 2 };
enum FogTableMode { FTM_NONE = 0, FTM_LINEAR = 2, FTM_EXP = 4, FTM_EXP2 = 5, FTM_REVEXP = 6, FTM_REVEXP2 = 7 };

// Fog state and render-state overrides (.debug 0x6101). The deleting destructor at
// 0x803D9BAC installs this type's vptr at 0x1C; other out-of-line methods are absent.
class RenderContextExtensionBase {
public:
    bool mFogEnable;                          // 0x00
    float mFogStartZ;                         // 0x04
    float mFogEndZ;                           // 0x08
    FogTableMode mFogType;                    // 0x0C
    Colour mFogColour;                        // 0x10
    bool mFogRangeAdjust;                     // 0x14
    RenderContextBase* mpBaseObject;          // 0x18

    static VerbosityControl sVerbosityControl;
    static bool gEnableDestinationAlpha;
    static bool gVisibilityTestStarted;
    static float gOverrideMipmapLODBias;
    static FilterModeOverride gOverrideFilterMode;
    static AlphaWritesOverride gOverrideAlphaWrites;
    static bool gConstDestAlphaEnable;
    static unsigned char gConstDestAlphaValue;
    static MipMapModeOverride gOverrideMipMapMode;
    static AnisotropyOverride gOverrideMaxAniso;
    static const int DEFAULT_BASE_VERBOSITY;
    virtual ~RenderContextExtensionBase();    // compiler vptr at 0x1C
};

// Screen-context extension, including every retained member/static (.debug 0x60D6).
class RenderContextExtension : public RenderContextExtensionBase {
public:
    RenderContextExtension(RenderContext* context);
    RenderContext* mpBaseObject; // 0x20
    GXGamma mGamma;              // 0x24
    static VerbosityControl sVerbosityControl;
    static unsigned char gDoScreenClear;
    static bool gIsDebugTokenEnabled;
    static GCBuffer* gVolatileBuffers[2];
    static unsigned int gVolatileBufferSize;
    static int gCurrentVolatileBuffer;
    static bool gDataStuffing;
    static const int DEFAULT_BASE_VERBOSITY;
};

// In progress: no disc DWARF for the texture-context extension. Its constructor at
// 0x803E081C proves the shared base; the containing context places its private state at 0x3C.
class TextureRenderContextExtension : public RenderContextExtensionBase {
public:
    TextureRenderContextExtension(TextureRenderContext* context);
    char mPad20[0xC]; // 0x20..0x2B: derived member names and complete types not recovered.
};

} // namespace EAGL

namespace EAGLInternal {

// Render-context discriminator and shared state (disc .debug 0x6E07 and 0x6E67).
// Their namespace is not recorded. The deleting destructor at 0x803D99F0 installs
// this type's vptr at 0x10; other out-of-line methods are absent from the debug records.
enum DerivedContextType {
    RCT_RENDERCONTEXT = 0,
    RCT_TEXTURERENDERCONTEXT = 1,
};

class RenderContextPrivateBase {
public:
    EAGL::RenderContextBase* mNextRC;          // 0x00
    EAGL::RenderContextBase* mpBaseObject;     // 0x04
    EAGL::ViewPort* mpCurrentViewPort;         // 0x08
    EAGL::ViewPort* mFirstViewPort;            // 0x0C

    virtual ~RenderContextPrivateBase();      // compiler vptr at 0x10
    void SetCurrentViewPort(EAGL::ViewPort* viewPort);
};

// Screen-context platform state (.debug 0x747E); inherited fields are in the shared base.
class RenderContextPrivate : public RenderContextPrivateBase {
public:
    // Nested callback typedef and breakpoint state (.debug 0x7F53 and 0x7F80).
    typedef void (*GPBreakCallback)(unsigned int);
    struct GPBreak {
        volatile void* mBreakAddress; // 0x0
        unsigned int mToken;         // 0x4
        GPBreakCallback mCallback;   // 0x8
        static volatile bool gBreakSet;
    };
    GXRenderModeObj* mRenderMode; // 0x14
    EAGL::RenderContext* mpBaseObject; // 0x18
    float mScreenWidth; // 0x1C
    float mScreenHeight; // 0x20
    int mColourDepth; // 0x24
    int mZBufferDepth; // 0x28
    int mDesiredVIWidth; // 0x2C
    int mDesiredVIHeight; // 0x30
    int mDesiredVIXOrigin; // 0x34
    int mDesiredVIYOrigin; // 0x38
    unsigned int mFbSize; // 0x3C
    GXRenderModeObj mRenderModeObj; // 0x40
    void* mFifoBuffer; // 0x7C
    void* mFrameBuffer; // 0x80
    volatile int mFirstFrame; // 0x84
    GXFifoObj* mFifoObj; // 0x88
    unsigned int mFifoSize; // 0x8C
    void* mLastWritePtr; // 0x90
    EAGL::TAR* mBlurTexture; // 0x94
    float mBlurAmount; // 0x98
    bool mBlurOk; // 0x9C
    bool mBlurHalfSize; // 0xA0
    bool mSyncOnVBL; // 0xA4
    bool mCullClockwise; // 0xA8
    bool mZWritesEnable; // 0xAC
    bool mDitherEnable; // 0xB0
    static volatile unsigned int gWaitForGPULoops;
    static volatile unsigned int gFIFOFullLoops;
    static float gCyclesPerIdleLoop;
    static int gBeginEndNestLevel;
    static volatile bool gEndFrameProcessed;
    static volatile unsigned short gCurrentToken;
    static unsigned short gBreakToken;
    static int gBreakTokenCount;
    static volatile unsigned short gLastToken;
    static volatile unsigned int gFrameCycles;
    static volatile unsigned int gLastCycleCount;
    static unsigned int gCPUFrequency;
    static volatile bool gDrawsDone;
    static volatile bool gUseVSyncCallback;
    static bool gEnableDebugTrap;
    static int gVSyncCallbackRefCount;
    static OSMessageQueue gMessageQueue;
    static void* gMessages[]; // DWARF records a nonconstant array bound.
    static GXRenderModeObj* gRenderMode;
    static unsigned short gOverScanYAdjust;
    static bool gFrameBuffersInitialized;
    static volatile bool gWaitingForEndFrameToken;
    static volatile unsigned short gPixPassedZTest[4096];
    static volatile unsigned short gPixSubmitted[4096];
    static volatile char gVisibilityValid[4096];
    static GPBreak gGPBreaklist[128];
    static volatile int gGPBreakPointHead;
    static volatile int gGPBreakPointTail;
};

// In progress: disc DWARF has no complete texture-private definition. Its constructor at
// 0x803E08B8 proves this base; no derived data member is accessed by the recovered viewport.
class TextureRenderContextPrivate : public RenderContextPrivateBase {
public:
    float GetPhysicalXOffset() const;
};

} // namespace EAGLInternal

namespace EAGL {

// Shared render-context header (disc .debug 0x6C66). GCC places the virtual-table pointer
// after these members, at 0x0C. The destructor name is retained in the FIFA and UEFA maps.
class RenderContextBase {
public:
    RenderContextExtensionBase& EXTENSION_OBJ;               // 0x00
    const EAGLInternal::DerivedContextType mObjectType;        // 0x04
    EAGLInternal::RenderContextPrivateBase& mPrivate;          // 0x08

    static VerbosityControl sVerbosityControl;
    static const int DEFAULT_BASE_VERBOSITY;
    // Virtual order confirmed by the base and derived context vtables.
    virtual void BeginFrame() = 0;
    virtual void EndFrame() = 0;
    virtual void GetSize(float& width, float& height) const = 0;
    virtual ~RenderContextBase();                            // compiler vptr at 0x0C
    ViewPort* GetCurrentViewPort() const;
};

// Display render target (.debug 0x701E), including every retained member/static.
class RenderContext : public RenderContextBase {
public:
    RenderContext(Device* device);
    RenderContextExtension EXTENSION_OBJ; // 0x10
    EAGLInternal::RenderContextPrivate mPrivate; // 0x38
    Device* mDevice; // 0xEC
    static VerbosityControl sVerbosityControl;
    static unsigned int gCurrentFrameNumber;
    static const int DEFAULT_BASE_VERBOSITY;
};

// In progress: no complete disc DWARF. Constructor 0x803E09B4 places these two owned
// subobjects at 0x10 and 0x3C; remaining derived members are not accessed here.
class TextureRenderContext : public RenderContextBase {
public:
    TextureRenderContext(Device* device);
    TextureRenderContextExtension EXTENSION_OBJ; // 0x10
    EAGLInternal::TextureRenderContextPrivate mPrivate; // 0x3C
};

// External six-instruction query at 0x803D9E3C; reconstructed name.
bool IsScreenClearEnabled();

} // namespace EAGL

#endif
