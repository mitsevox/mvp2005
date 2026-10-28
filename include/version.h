#ifndef INCLUDE_VERSION_H
#define INCLUDE_VERSION_H

/* Version differences between targets.
 *
 * Every target has one define, VERSION_<ID>: the target id upper-cased with `-` and `.` replaced
 * by `_` (GAME01-rev0 gives VERSION_GAME01_REV0). configure.py passes it for the target being
 * built; tools/targets.py derives it; nothing stores it.
 *
 * A difference lives in the shared source under `#if VERSION_<ID>`. A condition is a boolean
 * expression of VERSION_ tokens and the group macros below, with !, && and || only, and it names
 * the targets it includes: a branch a target listed later would take (`#if !VERSION_<ID>`, or the
 * `#else` of a chain) covers every target not named, so tools/versions.py warns about it while two
 * targets are listed and fails from the third. Never compare BUILD_VERSION numerically: it is
 * defined for dtk-template and never read.
 *
 * A group is defined here, by hand, when two or more targets share a difference, for example:
 *   #define REGION_USA (VERSION_GAME01_REV0 || VERSION_GAME01_REV1)
 * Nothing else goes in this file. tools/versions.py reads these groups to show what one target
 * compiles (`view`, `diff`) and rejects unknown tokens (`check`).
 */

#endif
