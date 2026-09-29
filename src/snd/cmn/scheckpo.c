/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/scheckpo.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */
#include "snd/sndo.h"

void SNDI_checkplayopts(SNDPLAYOPTS *pspo) {
    if (pspo->timemult > 0x2000) {
        pspo->timemult = 0x2000;
        return;
    }
    if (pspo->timemult < 0x800) {
        pspo->timemult = 0x800;
    }
}
