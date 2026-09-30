// EAGL primitive-state vocabulary: state.o in the FIFA/UEFA libeaglSNz.a maps.
// Types and complete known layouts come from the disc DWARF; namespace placement of
// the GC enums follows their owning state class and is inferred.
#ifndef EAGL_STATE_H
#define EAGL_STATE_H

#include "eagl/base.h"

namespace EAGL {

enum GCCullDir { GCCullDirNA = 0, GCCullBack = 1, GCCullFront = 2 };
enum GCZWrites { GCZWritesNA = 0, GCZWritesEnable = 1, GCZWritesDisable = 2 };
enum GCVertexFormat {
    MatrixIndices = 1, Tex0MatIdx = 2, Tex1MatIdx = 4, Tex2MatIdx = 8,
    Tex3MatIdx = 16, Tex4MatIdx = 32, Tex5MatIdx = 64, Tex6MatIdx = 128, Tex7MatIdx = 256,
    Coordinates = 512, Normals = 1024, NormBinormTan = 2048, Colour0 = 4096, Colour1 = 8192,
    UV0 = 16384, UV1 = 32768, UV2 = 65536, UV3 = 131072, UV4 = 262144,
    UV5 = 524288, UV6 = 1048576, UV7 = 2097152,
};
enum GCVertexDataType { Direct = 1, Index8 = 2, Index16 = 3, Custom = -1 };
enum GCAttr {
    GCA_VA_PNMTXIDX = 0, GCA_VA_TEX0MTXIDX = 1, GCA_VA_TEX1MTXIDX = 2,
    GCA_VA_TEX2MTXIDX = 3, GCA_VA_TEX3MTXIDX = 4, GCA_VA_TEX4MTXIDX = 5,
    GCA_VA_TEX5MTXIDX = 6, GCA_VA_TEX6MTXIDX = 7, GCA_VA_TEX7MTXIDX = 8,
    GCA_VA_POS = 9, GCA_VA_NRM = 10, GCA_VA_CLR0 = 11, GCA_VA_CLR1 = 12,
    GCA_VA_TEX0 = 13, GCA_VA_TEX1 = 14, GCA_VA_TEX2 = 15, GCA_VA_TEX3 = 16,
    GCA_VA_TEX4 = 17, GCA_VA_TEX5 = 18, GCA_VA_TEX6 = 19, GCA_VA_TEX7 = 20,
    GCA_VA_POS_MTX_ARRAY = 21, GCA_VA_NRM_MTX_ARRAY = 22,
    GCA_VA_TEX_MTX_ARRAY = 23, GCA_VA_LIGHT_ARRAY = 24,
    GCA_VA_NBT = 25, GCA_VA_MAX_ATTR = 26, GCA_VA_NULL = 255,
};
enum GCCompCnt {
    GCCC_POS_XY = 0, GCCC_POS_XYZ = 1, GCCC_NRM_XYZ = 0, GCCC_NRM_NBT = 1,
    GCCC_NRM_NBT3 = 2, GCCC_CLR_RGB = 0, GCCC_CLR_RGBA = 1,
    GCCC_TEX_S = 0, GCCC_TEX_ST = 1,
};
enum GCCompType {
    GCCT_U8 = 0, GCCT_S8 = 1, GCCT_U16 = 2, GCCT_S16 = 3, GCCT_F32 = 4,
    GCCT_RGB565 = 0, GCCT_RGB8 = 1, GCCT_RGBX8 = 2, GCCT_RGBA4 = 3,
    GCCT_RGBA6 = 4, GCCT_RGBA8 = 5,
};

// Primitive-state cache, from .debug 0x96C4, with its nested State at 0x9723.
class GeoPrimStateExtension {
public:
    struct State {
        int mPrimitiveType;          // 0x00
        int mDepthTestMethod;        // 0x04
        int mBlendMode;              // 0x08
        int mAlphaCompareValue;      // 0x0C
        int mAlphaTestMethod;        // 0x10
        int mTransparencyMethod;     // 0x14
        int mGXBlendMode;            // 0x18
        int mGXBlendSrcFactor;       // 0x1C
        int mGXBlendDestFactor;      // 0x20
        int mGXBlendLogicOp;         // 0x24
        GCCullDir mCullDirection;    // 0x28
        GCZWrites mZWritesEnable;    // 0x2C
        int mAlphaTestEnable;        // 0x30
        int mCullEnable;             // 0x34
        int mAlphaUpdate;            // 0x38
    };
    State mState;                    // 0x00
    static VerbosityControl sVerbosityControl;
    static unsigned int gVertexFormat;
    static unsigned int gVertexDataType;
    static State gCurrentState;
    static bool gStateInitialized;
    static bool gCoPlanarZModeEnabled;
    static bool gCullClockwise;
    static bool gZWritesEnable;
    static bool gColourWritesEnable;
    static bool gShowReferenceTriangle;
    static const int DEFAULT_BASE_VERBOSITY;
    static void SetCurrentVertex(unsigned int format, unsigned int dataType);
    static void SetAttributeFormat(int formatnumber, GCAttr attribute, GCCompCnt count,
                                   GCCompType type, unsigned char frac);
};

} // namespace EAGL

#endif
