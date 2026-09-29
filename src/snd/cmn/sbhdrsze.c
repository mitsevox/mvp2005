/* Imported from dbalatoni13/nfsmw @ 9ca26bc1 (src/Speed/Indep/Libs/snd/9/source/library/cmn/sbhdrsze.c). EA SND audio library (rwaudiocore), matched against NFS Most Wanted GC; CC0. */

#include "snd/cmn/sndcmn.h"
int SNDbankheadersize(int bhandle) {
    return sndgs.banklist[bhandle].phdr->hdrsize;
}
