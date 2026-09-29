/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/sstgetpv.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "./sndcmn.h"

int SNDSTRM_getprogvol(int sndstreamhandle) {
    SNDSTREAMCHANNEL *pssc = SNDSTRMI_getstreamptr(sndstreamhandle);

    int vol = -8;
    if (pssc == 0) {
        return vol;
    }

    vol = SNDCTRL_getprogvol(pssc->shandle);
    if (vol >= 0) {
        return vol;
    }

    // MVP's SND scales to 0..127, as SNDCTRL_getprogvol does; nfsmw's returns the raw 0..1 float.
    return SNDI_ftoifast(pssc->sourceChannelState[0].vol * 127.0f);
}
