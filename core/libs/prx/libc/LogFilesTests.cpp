#include "prx/libc/include/LogFiles.hpp"
#include "stdout_level.h"
#include <fstream>
#include <stdexcept>
#include <iostream>

static void Require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}

int main() {
    namespace fs = std::filesystem;
    using namespace Common::Log;
    Require(StdoutLevel::Names.size() == 5 && StdoutLevel::Parse("Critical") == 4, "Critical maps to Error");
    for (unsigned minimum = 0; minimum < StdoutLevel::Names.size(); ++minimum) {
        Require(StdoutLevel::Parse(StdoutLevel::Names[minimum]) == minimum, "severity parsing");
        for (unsigned message = 0; message < StdoutLevel::Names.size(); ++message)
            Require(StdoutLevel::Enabled(message, minimum) == (message >= minimum), "severity threshold");
    }
    Require(StdoutLevel::Parse("invalid") == 3 && StdoutLevel::Parse(" warning \r") == 3, "Warning default");
    const auto root = fs::temp_directory_path() / ("RyGT-portable-logs" + RuntimeLogFiles::Timestamp());
    Require(fs::create_directory(root), "unique test directory");
    try {
        Require(StdoutLevel::Read(root / "missing.ini") == 3, "missing setting default");
        { std::ofstream settings(root / "RyGT.ini"); settings << "game=test\nstdout_level= DEBUG\r\n"; }
        Require(StdoutLevel::Read(root / "RyGT.ini") == 1, "persisted threshold");
        for (const auto* name : {"stdout.log", "stderr.log", "setup.log"}) {
            { std::ofstream previous(root / name); previous << "legacy"; }
            auto path = RuntimeLogFiles::Prepare(root, name);
            Require(path == root / "logs" / name, "logs folder");
            Require(!fs::exists(root / name), "legacy migration");
            for (unsigned i = 0; i < 30; ++i) {
                { std::ofstream current(path); current << "session " << i; }
                path = RuntimeLogFiles::Prepare(root, name);
                Require(!path.empty(), "session rotation");
            }
            unsigned archived = 0;
            bool legacy = false;
            for (const auto& file : fs::directory_iterator(root / "logs")) {
                if (!file.path().filename().string().starts_with(std::string(name) + ".")) continue;
                ++archived;
                std::ifstream input(file.path()); std::string contents;
                std::getline(input, contents);
                legacy |= contents == "legacy";
            }
            Require(archived == 31 && legacy, "all archives retained without overwrite");
        }
        fs::remove_all(root);
    } catch (...) { fs::remove_all(root); throw; }
    std::cout << "PASS: portable severity gates, Warning default, config, folder creation, migration and rotation\n";
}
