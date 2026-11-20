#include "../native/providers/display/DisplayLog.hpp"
#include "Logger.hpp" // exact Aquamarine private logger header supplied with -I
#include <chrono>
#include <filesystem>
#include <fstream>
#include <thread>

// Compile with Aquamarine's matching src/backend/Logger.cpp and -laquamarine
// -lhyprutils. Never opens DRM, a compositor socket or an input device.
// All errors are synthetic. The native sink samples its own emission clocks.
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    Tamlinux::CDisplayLog sink;
    if (!sink.open(argv[1])) return 3;
    Aquamarine::CLogger backend;
    backend.m_logFn = [&](Aquamarine::eBackendLogLevel level, std::string message) {
        const int priority = level == Aquamarine::AQ_LOG_ERROR ? 3 : 7;
        sink.write("aquamarine", priority, message);
    };
    sink.write("hyprland", 7, "synthetic-debug-must-not-appear");
    backend.log(Aquamarine::AQ_LOG_DEBUG, "synthetic-backend-debug-must-not-appear");
    if (!sink.write("hyprland", 3, "synthetic-error-ordinary")) return 4;
    backend.log(Aquamarine::AQ_LOG_ERROR, "synthetic-error-backend output=TEST crtc=0");
    const auto firstSize = std::filesystem::file_size(argv[1]);
    // Both records must already be readable while both loggers are alive.
    std::ifstream file(argv[1]);
    std::string content{std::istreambuf_iterator<char>(file), {}};
    if (!firstSize || content.find("synthetic-error-backend") == std::string::npos || content.find("must-not-appear") != std::string::npos) return 5;
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    backend.log(Aquamarine::AQ_LOG_ERROR, "synthetic-error-backend-later output=TEST crtc=0");
    sink.write("aquamarine", 6, "synthetic-connector-transition output=TEST", true);
    sink.write("hyprland", 4, std::string(8000, 'x') + "\ninjected-line");
    std::fprintf(stderr, "probe: file readable before destruction bytes=%zu\n", firstSize);
    return 0;
}
