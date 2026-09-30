/* SN ProDG's libgcc.a(eabi.o): GCC 2.95's PowerPC EABI register save and restore helpers, which
 * are hand-written assembly in GCC's own source (gcc/config/rs6000/eabi.asm). Names from EA
 * reference builds (config/GV4E69/linked_names.tsv).
 *
 * A function that saves its callee-saved registers out of line points r11 at the top of its
 * register save area and calls _savegpr_N to store rN..r31 below it; _restgpr_N loads them back.
 * Each entry falls through to the next, so one routine serves every first register. The rest of
 * eabi.o (__eabi, the float helpers and the _x exit variants) is dead-stripped by the linker. */

.include "macros.inc"

.text
.balign 4

.fn _savegpr_14, global
	stw r14, -0x48(r11)
.sym _savegpr_15, global
	stw r15, -0x44(r11)
.sym _savegpr_16, global
	stw r16, -0x40(r11)
.sym _savegpr_17, global
	stw r17, -0x3c(r11)
.sym _savegpr_18, global
	stw r18, -0x38(r11)
.sym _savegpr_19, global
	stw r19, -0x34(r11)
.sym _savegpr_20, global
	stw r20, -0x30(r11)
.sym _savegpr_21, global
	stw r21, -0x2c(r11)
.sym _savegpr_22, global
	stw r22, -0x28(r11)
.sym _savegpr_23, global
	stw r23, -0x24(r11)
.sym _savegpr_24, global
	stw r24, -0x20(r11)
.sym _savegpr_25, global
	stw r25, -0x1c(r11)
.sym _savegpr_26, global
	stw r26, -0x18(r11)
.sym _savegpr_27, global
	stw r27, -0x14(r11)
.sym _savegpr_28, global
	stw r28, -0x10(r11)
.sym _savegpr_29, global
	stw r29, -0xc(r11)
.sym _savegpr_30, global
	stw r30, -0x8(r11)
.sym _savegpr_31, global
	stw r31, -0x4(r11)
	blr
.endfn _savegpr_14

.fn _restgpr_14, global
	lwz r14, -0x48(r11)
.sym _restgpr_15, global
	lwz r15, -0x44(r11)
.sym _restgpr_16, global
	lwz r16, -0x40(r11)
.sym _restgpr_17, global
	lwz r17, -0x3c(r11)
.sym _restgpr_18, global
	lwz r18, -0x38(r11)
.sym _restgpr_19, global
	lwz r19, -0x34(r11)
.sym _restgpr_20, global
	lwz r20, -0x30(r11)
.sym _restgpr_21, global
	lwz r21, -0x2c(r11)
.sym _restgpr_22, global
	lwz r22, -0x28(r11)
.sym _restgpr_23, global
	lwz r23, -0x24(r11)
.sym _restgpr_24, global
	lwz r24, -0x20(r11)
.sym _restgpr_25, global
	lwz r25, -0x1c(r11)
.sym _restgpr_26, global
	lwz r26, -0x18(r11)
.sym _restgpr_27, global
	lwz r27, -0x14(r11)
.sym _restgpr_28, global
	lwz r28, -0x10(r11)
.sym _restgpr_29, global
	lwz r29, -0xc(r11)
.sym _restgpr_30, global
	lwz r30, -0x8(r11)
.sym _restgpr_31, global
	lwz r31, -0x4(r11)
	blr
.endfn _restgpr_14

