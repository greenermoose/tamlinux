#include <hyprutils/cli/Logger.hpp>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <string>
#include <cstdio>
#include <thread>

// Isolated Hyprutils logger probe; never connects to DRM or a compositor.
// Build with: c++ -std=c++23 native-display-logging.cpp -lhyprutils -pthread
// Pass a new scratch file path. Stdout can be routed through systemd-cat;
// these are synthetic probe errors, not reports of a real display fault.
// Sample both emission-time clocks in the payload so the common logger's
// native timestamp and buffering can be compared with the journal envelope.
using namespace Hyprutils::CLI;

static std::string sample(const char* marker) {
    timespec mono{};
    clock_gettime(CLOCK_MONOTONIC, &mono);
    const auto wall = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    return std::format("synthetic-display-probe {} wall_ns={} monotonic_ns={}", marker, wall,
                       int64_t(mono.tv_sec) * 1'000'000'000 + mono.tv_nsec);
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    CLogger logger;
    logger.setEnableColor(false);
    logger.setEnableStdout(true);
    logger.setTime(true);
    logger.setLogLevel(LOG_WARN);
    if (!logger.setOutputFile(argv[1])) return 3;
    CLoggerConnection backend(logger);
    backend.setName("aquamarine");
    backend.setLogLevel(LOG_WARN);
    logger.log(LOG_DEBUG, sample("debug-ordinary"));
    backend.log(LOG_DEBUG, sample("debug-backend"));
    logger.log(LOG_ERR, sample("error-ordinary"));
    backend.log(LOG_ERR, sample("error-backend"));
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    backend.log(LOG_ERR, sample("error-backend-later"));
    // File content while this process is still alive tests buffering too.
    FILE* file = fopen(argv[1], "r");
    if (!file) return 4;
    char buffer[4096];
    const auto size = fread(buffer, 1, sizeof(buffer), file);
    fclose(file);
    fprintf(stderr, "probe file bytes before logger destruction=%zu\n", size);
}
