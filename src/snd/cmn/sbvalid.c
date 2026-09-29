/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/sbvalid.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "snd/cmn/sndcmn.h"

int SNDBANKI_valid(int bhandle) {
    if (bhandle < 0 || bhandle >= sndgs.sso.set.maxbanks) {
        return -8;
    }

    if (sndgs.banklist[bhandle].phdr == NULL) {
        return -8;
    }

    if (sndgs.banklist[bhandle].locked != 0) {
        return -18;
    }

    return 0;
}
