// Shared EAGL colour and verbosity types from the disc libmatd.a DWARF.
// Offsets cite InstanceCrowd.o; allocator overloads without recorded bodies are omitted.
#ifndef EAGL_BASE_H
#define EAGL_BASE_H

namespace EAGL {

// Per-class log verbosity (0x5644).
class VerbosityControl {
public:
    int mBaseVerbosity;        // 0x0
    int mDefaultBaseVerbosity; // 0x4
    int mInitialized;          // 0x8

    static const int sUninitializedVerbosity;
};

// A packed colour (0x2C93).
struct Colour {
    unsigned int c; // 0x0

    // Signature retained at .debug 0x2FA7; body confirmed by viewport initialization.
    Colour(unsigned long colour) : c(colour) {}
};

} // namespace EAGL

#endif
