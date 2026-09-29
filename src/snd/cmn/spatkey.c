/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/spatkey.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "./sndcmn.h"

int iSNDpatchkey(int chan, int *psetchan) {
    CHANPUB *pchan = &sndgs.chan[chan];
    int patchkey = pchan->patchkey;
    if (patchkey != 0) {
        (*psetchan)++;
        for (; *psetchan < sndgs.voicestotal; (*psetchan)++) {
            pchan = &sndgs.chan[*psetchan];
            if (pchan->patchkey == patchkey && pchan->status == 1 && pchan->handle >= 0) {
                return 1;
            }
        }
    } else if (*psetchan < 0) {
        *psetchan = chan;
        return 1;
    }

    return 0;

}
