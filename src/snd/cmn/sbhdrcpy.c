/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/sbhdrcpy.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "snd/cmn/sndcmn.h"
#include <cstring>
int SNDbankheadercopy(void *pmem, int bhandle) {
    int memneeded;
    int rc = 0;

    memneeded = SNDbankheadersize(bhandle);
    if (memneeded < 0) {
        rc = memneeded;
        goto abort;
    }

    memmove(pmem, sndgs.banklist[bhandle].phdr, memneeded);
    sndgs.banklist[bhandle].phdr = reinterpret_cast<BANKVER5 *>(pmem);

abort:
    return rc;
}
