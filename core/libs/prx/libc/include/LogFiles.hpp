#pragma once
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <string>
#include <system_error>

// File management shared by runtimes; no operating-system headers or APIs.
namespace RuntimeLogFiles {
inline std::string Timestamp() {
    using namespace std::chrono;
    const auto now = floor<milliseconds>(system_clock::now());
    const auto day = floor<days>(now);
    const year_month_day date{day};
    const hh_mm_ss clock{now - day};
    char stamp[40];
    std::snprintf(stamp, sizeof(stamp), ".%04d%02u%02uT%02lld%02lld%02lld%03lldZ",
        int(date.year()), unsigned(date.month()), unsigned(date.day()),
        static_cast<long long>(clock.hours().count()), static_cast<long long>(clock.minutes().count()),
        static_cast<long long>(clock.seconds().count()), static_cast<long long>(clock.subseconds().count()));
    return stamp;
}

inline bool Archive(const std::filesystem::path& source, const std::filesystem::path& base) {
    std::error_code error;
    if (!std::filesystem::exists(source, error)) return !error;
    const auto stamp = Timestamp();
    for (unsigned i = 0; i < 10000; ++i) {
        auto target = base;
        target += stamp + (i ? "." + std::to_string(i) : "");
        // Creating a new link cannot overwrite an existing archive, even if another
        // process archives at the same instant. Copy without overwrite on other volumes.
        std::filesystem::create_hard_link(source, target, error);
        if (error == std::errc::file_exists) continue;
        if (error) {
            error.clear();
            std::filesystem::copy_file(source, target, std::filesystem::copy_options::none, error);
            if (error == std::errc::file_exists) continue;
            if (error) return false;
        }
        std::filesystem::remove(source, error);
        return !error;
    }
    return false;
}

inline std::filesystem::path Prepare(const std::filesystem::path& root, const std::filesystem::path& name, bool runtimeLaunch = false) {
    std::error_code error;
    const auto directory = root / "logs";
    std::filesystem::create_directories(directory, error);
    if (error) return {};
    const auto current = directory / name;
    if (runtimeLaunch) {
        if (const char* prepared = std::getenv("RYGT_LOG_DIRECTORY")) {
            if (std::filesystem::equivalent(directory, prepared, error) && !error)
                return current; // The launcher has already rotated and opened this session.
            error.clear();
        }
    }
    auto legacyBase = current;
    legacyBase += ".legacy";
    if (!Archive(root / name, legacyBase) || !Archive(current, current)) return {};
    return current;
}
}
