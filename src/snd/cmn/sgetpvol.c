/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/sgetpvol.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "sndcmn.h"

int SNDCTRL_getprogvol(int shandle) {
    int voice = SNDVOICEI_get(shandle);
    int vol;

    if (voice < 0)
        return -8;

    // MVP's SND returns the volume on the 0..127 scale; nfsmw's returns the raw 0..1 float.
    vol = SNDI_ftoifast(sndgs.chan[voice].programmedVol * 127.0f);

    return vol;
}
