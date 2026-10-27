#pragma once
#include "../../renderer/stdout_level.h"

namespace RuntimeStdoutLog {
inline bool Enabled(unsigned level = 1) {
    static const unsigned minimum = [] {
        try {
            return Common::Log::StdoutLevel::Read(std::filesystem::current_path() / "RyGT.ini");
        } catch (...) {
            return Common::Log::StdoutLevel::Default;
        }
    }();
    return Common::Log::StdoutLevel::Enabled(level, minimum);
}
}
