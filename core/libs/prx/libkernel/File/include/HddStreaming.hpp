#pragma once
#include <cstdlib>
#include <cstdio>
#include <cstring>

namespace File {
// A cache hint only: no private data cache, I/O reordering or completion changes.
static inline bool HddStreamingEnabled() {
#ifdef _WIN32
    static const bool enabled = [] {
        const char* value = std::getenv("RYGT_HDD_STREAMING");
        const bool on = value && std::strcmp(value, "1") == 0;
        if (on) std::fprintf(stderr, "[file] HDD read-ahead enabled for read-only game data (experimental)\n");
        return on;
    }();
    return enabled;
#else
    return false;
#endif
}
static inline bool IsStreamingGamePath(const char* path) {
    return path && (std::strncmp(path, "/app0/", 6) == 0 ||
                    std::strncmp(path, "/patch0/", 8) == 0);
}
}
