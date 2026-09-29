/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/sballoc.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "./sndcmn.h"

int SNDBANKI_alloc() {
    int i;

    for (i = 0; i < sndgs.sso.set.maxbanks; i++) {
        if (sndgs.banklist[i].phdr == NULL) {
            return i;
        }
    }

    return -9;
}

TAGGEDPATCH *SNDBANKI_getppatch(BANKVER5 *pb, int patnum) {
    if (patnum >= pb->numpatches) return NULL;

    if (pb->patch[patnum] == NULL) {
        return NULL;
    }

    return reinterpret_cast<TAGGEDPATCH *>((int)&pb->patch[patnum] + (int)pb->patch[patnum]);
}
