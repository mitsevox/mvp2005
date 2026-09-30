// viewport.cpp: libeaglSNz.a(viewport.o) in the FIFA 2005 and UEFA CL 04-05 maps; the file name
// is theirs. EAGL's viewport: projection setup, sphere culling and the view stack. In progress:
// the functions not written here stay in asm. ReBegin at 0x803E1F0C (size 0x60 in both maps) is
// followed by the global initializer at 0x803E1F6C, registered at 0x805A2CF8 in the constructor
// list and calling this unit's static initializer at 0x803E1B54. It ends at 0x803E1F98, where
// both maps place the next object's ViewPort constructor in viewport_cmn.o. Those two final
// functions bound the unit; the global initializer still stays in asm. The object's .data
// and .bss (the gp* matrix pointers from 0x8062C280, the matrices from 0x806AA990) are not
// split out: constructed-global placement and part of the .data ownership remain unresolved.
#include "eagl/viewport.h"
#include "eagl/state.h"
#include <dolphin/gx/GXLighting.h>
#include <dolphin/gx/GXTev.h>
#include <dolphin/gx/GXCull.h>
#include <dolphin/gx/GXGeometry.h>
#include <dolphin/gx/GXFrameBuffer.h>
#include <dolphin/gx/GXVert.h>
#include <dolphin/gx/GXTransform.h>
#include <dolphin/gx/GXPixel.h>
#include <dolphin/mtx.h>
#include <dolphin/vi.h>
#include <math.h>
#include <string.h>

using namespace EAGL;
using namespace EAGLInternal;

// Fits the viewport's visible rectangle to its render target and adjusts its culling planes.
void ViewPort::SetShape(float originX, float originY, float width, float height,
                       float nearZ, float farZ) {
    mPrivate.mGeometry.mOriginX = originX;
    mPrivate.mGeometry.mOriginY = originY;
    mPrivate.mGeometry.mWidth = width;
    mPrivate.mGeometry.mHeight = height;
    mPrivate.mGeometry.mNearZ = nearZ;
    mPrivate.mGeometry.mFarZ = farZ;
    mPrivate.mClipOriginX = 0;
    mPrivate.mClipOriginY = 0;
    mPrivate.mClipWidth = (unsigned int)width;
    mPrivate.mClipHeight = (unsigned int)height;

    COORD2 topLeft, bottomRight;
    topLeft.x = originX;
    topLeft.y = originY;
    bottomRight.x = originX + width;
    bottomRight.y = originY + height;
    float targetWidth, targetHeight;
    mPrivate.mpRenderContext->GetSize(targetWidth, targetHeight);

    if (topLeft.x < 0.0f) topLeft.x = 0.0f;
    if (topLeft.y < 0.0f) topLeft.y = 0.0f;
    if (bottomRight.x < 0.0f) bottomRight.x = 0.0f;
    if (bottomRight.y < 0.0f) bottomRight.y = 0.0f;
    if (topLeft.x > targetWidth) topLeft.x = targetWidth;
    if (topLeft.y > targetHeight) topLeft.y = targetHeight;
    if (bottomRight.x > targetWidth) bottomRight.x = targetWidth;
    if (bottomRight.y > targetHeight) bottomRight.y = targetHeight;
    if (topLeft.x == 0.0f && topLeft.y == 0.0f &&
        bottomRight.x == targetWidth && bottomRight.y == targetHeight)
        mPrivate.mFullScreen = true;
    else
        mPrivate.mFullScreen = false;

    float visibleWidth = bottomRight.x - topLeft.x;
    float visibleHeight = bottomRight.y - topLeft.y;
    if ((visibleWidth == width && visibleHeight == height) ||
        visibleWidth * visibleHeight == 0.0f) {
        mPrivate.mCullData.mLeftScale = 1.0f;
        mPrivate.mCullData.mRightScale = 1.0f;
        mPrivate.mCullData.mTopScale = 1.0f;
        mPrivate.mCullData.mBottomScale = 1.0f;
    } else {
        float halfWidth = width * 0.5f;
        float halfHeight = height * 0.5f;
        float centreX = originX + halfWidth;
        float centreY = originY + halfHeight;
        mPrivate.mCullData.mLeftScale = (centreX - topLeft.x) / halfWidth;
        mPrivate.mCullData.mRightScale = (bottomRight.x - centreX) / halfWidth;
        mPrivate.mCullData.mTopScale = (centreY - topLeft.y) / halfHeight;
        mPrivate.mCullData.mBottomScale = (bottomRight.y - centreY) / halfHeight;
    }
    if (GetProjectionType() == PERSPECTIVE)
        SetPerspective(mPrivate.mFrustum.mFOV, mPrivate.mFrustum.mAspect,
                       mPrivate.mFrustum.mNearPlane, mPrivate.mFrustum.mFarPlane);
}

// Sets a perspective projection, uploads it to GX and rebuilds the culling planes. fov is the
// horizontal field of view in degrees: the SDK matrix is built for a square view and its y scale is
// then multiplied by aspect (width over height). near and far are camera-space distances.
void ViewPort::SetPerspective(float fov, float aspect, float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = fov;
    mPrivate.mFrustum.mAspect = aspect;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXPerspective(mPrivate.mProjection, fov, 1.0f, nearPlane, farPlane);
    mPrivate.mProjection[1][1] *= aspect;
    // GX's matrix is for column vectors, EA's for row vectors (v * M): copy it transposed.
    mPrivate.mProjectionMatrix.m44[0][0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m44[1][1] = mPrivate.mProjection[1][1];
    mPrivate.mProjectionMatrix.m44[2][0] = mPrivate.mProjection[0][2];
    mPrivate.mProjectionMatrix.m44[2][1] = mPrivate.mProjection[1][2];
    mPrivate.mProjectionMatrix.m44[2][2] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m44[2][3] = -1.0f;
    mPrivate.mProjectionMatrix.m44[3][0] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][1] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][2] = mPrivate.mProjection[2][3];
    mPrivate.mProjectionMatrix.m44[3][3] = 0.0f;
    GXSetProjection(mPrivate.mProjection, GX_PERSPECTIVE);
    mPrivate.mProjectionType = PERSPECTIVE;

    // Each side plane's angle from the view axis, widened or narrowed by that side's scale.
    float halfWidth = tanf(DegToRad(fov * 0.5f));
    float leftAngle = atanf(-halfWidth * mPrivate.mCullData.mLeftScale);
    float rightAngle = atanf(halfWidth * mPrivate.mCullData.mRightScale);
    float topAngle = atanf(halfWidth * mPrivate.mCullData.mTopScale / aspect);
    float bottomAngle = atanf(-halfWidth * mPrivate.mCullData.mBottomScale / aspect);
    mPrivate.mCullData.mLeftTan = tanf(leftAngle);
    mPrivate.mCullData.mLeftSin = sinf(HALFPI_F - leftAngle);
    mPrivate.mCullData.mRightTan = tanf(rightAngle);
    mPrivate.mCullData.mRightSin = sinf(HALFPI_F - rightAngle);
    mPrivate.mCullData.mTopTan = tanf(topAngle);
    mPrivate.mCullData.mTopSin = sinf(HALFPI_F - topAngle);
    mPrivate.mCullData.mBottomTan = tanf(bottomAngle);
    mPrivate.mCullData.mBottomSin = sinf(HALFPI_F - bottomAngle);
}

// Makes this camera current, suspending the previous view and enacting its matrices,
// visible rectangle, projection and fog on the render target.
void ViewPort::BeginView() {
    if (!ViewPortExtension::gpFirstViewPort)
        ViewPortExtension::gpFirstViewPort = this;
    if (mPrivate.mpRenderContext->GetCurrentViewPort() &&
        mPrivate.mpRenderContext->GetCurrentViewPort()->mPrivate.mAmActive) {
        mNextInStack = mPrivate.mpRenderContext->GetCurrentViewPort();
        ViewPort* previousStack = mNextInStack->mNextInStack;
        mNextInStack->EndView();
        mNextInStack->mNextInStack = previousStack;
    }
    // port: EA uses address 1 as the end-of-stack sentinel; it is never dereferenced.
    if (!mNextInStack)
        mNextInStack = (ViewPort*)1;
    mPrivate.mAmActive = true;
    mPrivate.mpRenderContext->mPrivate.SetCurrentViewPort(this);
    Transform viewProjection(mPrivate.mViewMatrix);
    viewProjection.AppendMatrix(&mPrivate.mProjectionMatrix);
    mPrivate.mViewProjectionMatrix = viewProjection.m;
    gViewMatrix = mPrivate.mViewMatrix;
    gModelViewMatrix = mPrivate.mViewMatrix;

    float targetWidth, targetHeight;
    float physicalXOffset = 0.0f;
    RenderContext* screenContext = 0;
    mPrivate.mpRenderContext->GetSize(targetWidth, targetHeight);
    if (mPrivate.mpRenderContext->mObjectType == RCT_RENDERCONTEXT)
        screenContext = (RenderContext*)mPrivate.mpRenderContext;
    else
        physicalXOffset = ((TextureRenderContext*)mPrivate.mpRenderContext)->mPrivate.GetPhysicalXOffset();
    if (screenContext && screenContext->mPrivate.mRenderMode->field_rendering)
        GXSetViewportJitter(mPrivate.mGeometry.mOriginX + physicalXOffset,
                            mPrivate.mGeometry.mOriginY, mPrivate.mGeometry.mWidth,
                            mPrivate.mGeometry.mHeight, mPrivate.mGeometry.mNearZ,
                            mPrivate.mGeometry.mFarZ, VIGetNextField());
    else
        GXSetViewport(mPrivate.mGeometry.mOriginX + physicalXOffset,
                      mPrivate.mGeometry.mOriginY, mPrivate.mGeometry.mWidth,
                      mPrivate.mGeometry.mHeight, mPrivate.mGeometry.mNearZ,
                      mPrivate.mGeometry.mFarZ);

    int right = (int)(mPrivate.mGeometry.mOriginX + mPrivate.mGeometry.mWidth);
    int bottom = (int)(mPrivate.mGeometry.mOriginY + mPrivate.mGeometry.mHeight);
    int left = (int)(mPrivate.mGeometry.mOriginX + mPrivate.mClipOriginX);
    int top = (int)(mPrivate.mGeometry.mOriginY + mPrivate.mClipOriginY);
    int clipRight = left + mPrivate.mClipWidth;
    int clipBottom = top + mPrivate.mClipHeight;
    if (left < 0) left = 0;
    if (top < 0) top = 0;
    if (right < targetWidth) targetWidth = right;
    if (bottom < targetHeight) targetHeight = bottom;
    if (clipRight < targetWidth) targetWidth = clipRight;
    if (clipBottom < targetHeight) targetHeight = clipBottom;
    GXSetScissor((unsigned int)(left + physicalXOffset), top,
                 (unsigned int)(targetWidth - left), (unsigned int)(targetHeight - top));
    if (mPrivate.mProjectionType == PERSPECTIVE)
        GXSetProjection(mPrivate.mProjection, GX_PERSPECTIVE);
    else
        GXSetProjection(mPrivate.mProjection, GX_ORTHOGRAPHIC);
    mPrivate.EnactFogSettings();
}

// Clears the viewport's selected colour/depth buffers, then restores its projection.
void ViewPort::ClearViewPort(ClearFlags flags) {
    // MATCH: this == gpFirstViewPort reverses the cmpw operands; the global-first
    // equality keeps the original comparison order.
    if (mPrivate.mFullScreen && ViewPortExtension::gpFirstViewPort == this &&
        (flags & (CLEAR_CURRENT | CLEAR_Z)) == (CLEAR_CURRENT | CLEAR_Z) && IsScreenClearEnabled()) {
        if (mPrivate.mBackgroundColour.c == ViewPortPrivate::gScreenColour.c)
            return;
        ViewPortPrivate::gScreenColour = mPrivate.mBackgroundColour;
        GXColor colour;
        memcpy(&colour, &ViewPortPrivate::gScreenColour, sizeof(colour));
        GXSetCopyClear(colour, 0xFFFFFF);
    }
    GXSetNumChans(1);
    GXSetTevOrder(GX_TEVSTAGE0, GX_TEXCOORD_NULL, GX_TEXMAP_NULL, GX_COLOR0A0);
    GXSetTevOp(GX_TEVSTAGE0, GX_PASSCLR);
    GeoPrimStateExtension::SetCurrentVertex(Coordinates | Colour0, Direct);
    GeoPrimStateExtension::SetAttributeFormat(5, GCA_VA_POS, GCCC_POS_XYZ, GCCT_F32, 0);
    GeoPrimStateExtension::SetAttributeFormat(5, GCA_VA_CLR0, GCCC_CLR_RGBA, GCCT_RGBA8, 0);
    GXSetCullMode(GX_CULL_NONE);
    Mtx44 clearProjection;
    C_MTXOrtho(clearProjection,
               mPrivate.mGeometry.mOriginY, mPrivate.mGeometry.mOriginY + mPrivate.mGeometry.mHeight,
               mPrivate.mGeometry.mOriginX, mPrivate.mGeometry.mOriginX + mPrivate.mGeometry.mWidth,
               0.0f, -1.0f);
    GXSetProjection(clearProjection, GX_ORTHOGRAPHIC);
    GXSetCurrentMtx(GX_IDENTITY);
    GXSetNumTexGens(0);
    GXSetNumTevStages(1);
    GXSetTevOp(GX_TEVSTAGE0, GX_PASSCLR);
    GXSetChanCtrl(GX_COLOR0A0, GX_FALSE, GX_SRC_REG, GX_SRC_VTX, GX_LIGHT_NULL, GX_DF_CLAMP, GX_AF_NONE);
    GXSetBlendMode(GX_BM_NONE, GX_BL_ONE, GX_BL_ZERO, GX_LO_COPY);
    GXSetAlphaCompare(GX_ALWAYS, 0, GX_AOP_OR, GX_ALWAYS, 0);
    GXSetZCompLoc(GX_FALSE);
    if (!(flags & CLEAR_CURRENT))
        GXSetColorUpdate(GX_FALSE);
    if (flags & CLEAR_Z)
        GXSetZMode(GX_TRUE, GX_ALWAYS, GX_TRUE);
    else
        GXSetZMode(GX_FALSE, GX_ALWAYS, GX_FALSE);
    GXBegin(GX_QUADS, GX_VTXFMT5, 4);
    GXPosition3f32(mPrivate.mGeometry.mOriginX, mPrivate.mGeometry.mOriginY, 1.0f - 1.0f / 8388608.0f);
    GXColor1u32(mPrivate.mBackgroundColour.c);
    GXPosition3f32(mPrivate.mGeometry.mOriginX + mPrivate.mGeometry.mWidth,
                  mPrivate.mGeometry.mOriginY, 1.0f - 1.0f / 8388608.0f);
    GXColor1u32(mPrivate.mBackgroundColour.c);
    GXPosition3f32(mPrivate.mGeometry.mOriginX + mPrivate.mGeometry.mWidth,
                  mPrivate.mGeometry.mOriginY + mPrivate.mGeometry.mHeight, 1.0f - 1.0f / 8388608.0f);
    GXColor1u32(mPrivate.mBackgroundColour.c);
    GXPosition3f32(mPrivate.mGeometry.mOriginX,
                  mPrivate.mGeometry.mOriginY + mPrivate.mGeometry.mHeight, 1.0f - 1.0f / 8388608.0f);
    GXColor1u32(mPrivate.mBackgroundColour.c);
    GXSetColorUpdate(GX_TRUE);
    if (mPrivate.mProjectionType == PERSPECTIVE)
        GXSetProjection(mPrivate.mProjection, GX_PERSPECTIVE);
    else
        GXSetProjection(mPrivate.mProjection, GX_ORTHOGRAPHIC);
    GeoPrimStateExtension::gStateInitialized = false;
}

// True unless the sphere is wholly outside the view: past the near or far plane, or, in a
// perspective view, outside a side plane. radius is in view space, not scaled. On each axis only
// the side the centre lies towards is tested.
bool ViewPort::IsSphereInView(const COORD3& centre, float radius) {
    COORD3 viewCentre;
    Transform viewTransform(gViewMatrix);
    viewTransform.TransformPoint(centre, viewCentre);

    // View space looks down -z: z + near is how far the centre lies on the camera side of the
    // near plane, and -(z + far) how far it lies beyond the far plane.
    float distance = viewCentre.z + mPrivate.mFrustum.mNearPlane;
    if (distance > radius)
        return false;
    distance = viewCentre.z + mPrivate.mFrustum.mFarPlane;
    if (-distance > radius)
        return false;

    if (mPrivate.mProjectionType == PERSPECTIVE) {
        distance = viewCentre.x + viewCentre.z * mPrivate.mCullData.mRightTan;
        if (distance > 0.0f) {
            distance *= mPrivate.mCullData.mRightSin;
            if (distance > radius)
                return false;
        } else {
            distance = viewCentre.x + viewCentre.z * mPrivate.mCullData.mLeftTan;
            if (distance < 0.0f) {
                distance *= -mPrivate.mCullData.mLeftSin;
                if (distance > radius)
                    return false;
            }
        }

        distance = viewCentre.y + viewCentre.z * mPrivate.mCullData.mTopTan;
        if (distance > 0.0f) {
            distance *= mPrivate.mCullData.mTopSin;
            if (distance > radius)
                return false;
        } else {
            distance = viewCentre.y + viewCentre.z * mPrivate.mCullData.mBottomTan;
            if (distance < 0.0f) {
                distance *= -mPrivate.mCullData.mBottomSin;
                if (distance > radius)
                    return false;
            }
        }
    }
    return true;
}

// Applies the render context's fog using this viewport's depth range and projection.
void ViewPortPrivate::EnactFogSettings() {
    if (mpRenderContext) {
        GXColor colour;
        memcpy(&colour, &mpRenderContext->EXTENSION_OBJ.mFogColour, sizeof(colour));
        if (mpRenderContext->EXTENSION_OBJ.mFogEnable) {
            GXSetFog((GXFogType)mpRenderContext->EXTENSION_OBJ.mFogType,
                     mpRenderContext->EXTENSION_OBJ.mFogStartZ,
                     mpRenderContext->EXTENSION_OBJ.mFogEndZ,
                     mFrustum.mNearPlane, mFrustum.mFarPlane, colour);
            if (mpRenderContext->EXTENSION_OBJ.mFogRangeAdjust) {
                GXFogAdjTable fogTable;
                GXInitFogAdjTable(&fogTable, (unsigned short)mGeometry.mWidth, mProjection);
                int centre = (int)(mGeometry.mOriginX + mGeometry.mWidth * 0.5f);
                if (centre < 0)
                    centre = 0;
                GXSetFogRangeAdj(GX_TRUE, centre, &fogTable);
            } else {
                GXSetFogRangeAdj(GX_FALSE, 0, 0);
            }
        } else {
            GXSetFog(GX_FOG_NONE, 0.0f, 0.0f, 0.0f, 0.0f, colour);
        }
    }
}

// Starts an inactive orthographic viewport with unset geometry and frustum values, and an
// identity GX projection.
ViewPortPrivate::ViewPortPrivate(ViewPort* baseObject)
    : mpRenderContext(0), mProjectionType(ORTHOGRAPHIC), mAmActive(false),
      mUseForFontDraws(false), mBackgroundColour(0), mNextVP(0), mpBaseObject(baseObject) {
    mGeometry.mOriginX = -1.0f;
    mGeometry.mOriginY = -1.0f;
    mGeometry.mWidth = -1.0f;
    mGeometry.mHeight = -1.0f;
    mGeometry.mNearZ = -1.0f;
    mGeometry.mFarZ = -1.0f;
    mFrustum.mFOV = -1.0f;
    mFrustum.mAspect = -1.0f;
    mFrustum.mNearPlane = -1.0f;
    mFrustum.mFarPlane = -1.0f;
    mProjection[0][0] = 1.0f;
    mProjection[0][1] = 0.0f;
    mProjection[0][2] = 0.0f;
    mProjection[0][3] = 0.0f;
    mProjection[1][0] = 0.0f;
    mProjection[1][1] = 1.0f;
    mProjection[1][2] = 0.0f;
    mProjection[1][3] = 0.0f;
    mProjection[2][0] = 0.0f;
    mProjection[2][1] = 0.0f;
    mProjection[2][2] = 1.0f;
    mProjection[2][3] = 0.0f;
    mProjection[3][0] = 0.0f;
    mProjection[3][1] = 0.0f;
    mProjection[3][2] = 0.0f;
    mProjection[3][3] = 1.0f;
}

// Reports the viewport rectangle and its depth range.
void ViewPort::GetShape(float& originX, float& originY, float& width, float& height,
                       float& nearZ, float& farZ) const {
    originX = mPrivate.mGeometry.mOriginX;
    originY = mPrivate.mGeometry.mOriginY;
    width = mPrivate.mGeometry.mWidth;
    height = mPrivate.mGeometry.mHeight;
    nearZ = mPrivate.mGeometry.mNearZ;
    farZ = mPrivate.mGeometry.mFarZ;
}

// Stores the view transform and refreshes the active viewport.
void ViewPort::SetViewMatrix(const MATRIX4& matrix) {
    mPrivate.mViewMatrix = matrix;
    if (mPrivate.mAmActive)
        mPrivate.ReBegin();
}

// Sets an orthographic view spanning -1..1 horizontally and -aspect..aspect vertically,
// with nearPlane and farPlane as camera-space distances, and uploads its projection to GX.
void ViewPort::SetOrthographic(float aspect, float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = 0.0f;
    mPrivate.mFrustum.mAspect = aspect;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXOrtho(mPrivate.mProjection, aspect, -aspect, -1.0f, 1.0f, nearPlane, farPlane);
    // GX's column-vector projection is transposed for EA's row-vector matrix.
    mPrivate.mProjectionMatrix.m44[0][0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m44[1][1] = mPrivate.mProjection[1][1];
    mPrivate.mProjectionMatrix.m44[2][0] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][1] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][2] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m44[2][3] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][0] = mPrivate.mProjection[0][3];
    mPrivate.mProjectionMatrix.m44[3][1] = mPrivate.mProjection[1][3];
    mPrivate.mProjectionMatrix.m44[3][2] = mPrivate.mProjection[2][3];
    mPrivate.mProjectionMatrix.m44[3][3] = 1.0f;
    mPrivate.mProjectionType = ORTHOGRAPHIC;
    GXSetProjection(mPrivate.mProjection, GX_ORTHOGRAPHIC);
}

// Sets a screen-space projection with the viewport's width and height, x right and y down,
// and uploads it to GX. nearPlane and farPlane set the camera-space depth range.
void ViewPort::SetOrthographicScreenSpace(float nearPlane, float farPlane) {
    mPrivate.mFrustum.mFOV = 0.0f;
    mPrivate.mFrustum.mAspect = 0.75f;
    mPrivate.mFrustum.mNearPlane = nearPlane;
    mPrivate.mFrustum.mFarPlane = farPlane;
    C_MTXOrtho(mPrivate.mProjection, 0.0f, mPrivate.mGeometry.mHeight,
               0.0f, mPrivate.mGeometry.mWidth, nearPlane, farPlane);
    // GX uses column vectors; EA's row-vector matrix is its transpose.
    mPrivate.mProjectionMatrix.m44[0][0] = mPrivate.mProjection[0][0];
    mPrivate.mProjectionMatrix.m44[1][1] = mPrivate.mProjection[1][1];
    mPrivate.mProjectionMatrix.m44[2][0] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][1] = 0.0f;
    mPrivate.mProjectionMatrix.m44[2][2] = mPrivate.mProjection[2][2];
    mPrivate.mProjectionMatrix.m44[2][3] = 0.0f;
    mPrivate.mProjectionMatrix.m44[3][0] = mPrivate.mProjection[0][3];
    mPrivate.mProjectionMatrix.m44[3][1] = mPrivate.mProjection[1][3];
    mPrivate.mProjectionMatrix.m44[3][2] = mPrivate.mProjection[2][3];
    mPrivate.mProjectionMatrix.m44[3][3] = 1.0f;
    mPrivate.mProjectionType = ORTHOGRAPHIC;
    GXSetProjection(mPrivate.mProjection, GX_ORTHOGRAPHIC);
}

// Associates the platform extension with its owning viewport.
ViewPortExtension::ViewPortExtension(ViewPort* baseObject) : mpBaseObject(baseObject) {}

// The extension owns no resources beyond its allocation.
ViewPortExtension::~ViewPortExtension() {}

// Ends this viewport and restores its preceding stacked view.
void ViewPort::EndView() {
    mPrivate.mpRenderContext->mPrivate.SetCurrentViewPort(0);
    mPrivate.mAmActive = false;
    // port: the stack uses pointer value 1 as a sentinel on this 32-bit target.
    if ((unsigned int)mNextInStack > 1)
        mNextInStack->BeginView();
    mNextInStack = 0;
}

// Restarts this viewport, restoring its preceding stacked view before beginning it again.
void ViewPortPrivate::ReBegin() {
    ViewPort* viewPort = mpBaseObject;
    viewPort->mPrivate.mpRenderContext->mPrivate.SetCurrentViewPort(0);
    viewPort->mPrivate.mAmActive = false;
    // port: the stack uses pointer value 1 as a sentinel on this 32-bit target.
    if ((unsigned int)viewPort->mNextInStack > 1)
        viewPort->mNextInStack->BeginView();
    viewPort->mNextInStack = 0;
    mpBaseObject->BeginView();
}
