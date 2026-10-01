// realmem.h: EA's memory API; MEM_copy's signature is retained in the NFS MW/HP maps.
// This header name is reconstructed from the realcore module convention.
#ifndef REALMEM_H
#define REALMEM_H
void MEM_copy(void* destination, const void* source, int size);
#endif
