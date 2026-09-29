/* Imported from emoose/re4 @ feb6805b (include/dolphin/db.h), based on doldecomp/dolsdk2004. Dolphin SDK header. */
#ifndef _DOLPHIN_DB_H_
#define _DOLPHIN_DB_H_

#include <dolphin/types.h>
#include <dolphin/db/DBInterface.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OS_DBINTERFACE_ADDR 0x00000040

BOOL DBIsDebuggerPresent(void);
void DBPrintf(char* str, ...);

#ifdef __cplusplus
}
#endif

#endif // _DOLPHIN_DB_H_
