#pragma once

#include <cstdio>
#include <ctime>
#include <fcntl.h>
#include <format>
#include <mutex>
#include <string>
#include <string_view>
#include <unistd.h>
#include <sys/stat.h>

// Small shared emission sink for Hyprland and its Aquamarine callback.
// No DRM, compositor or systemd dependency: the exact sink is tested in isolation.
namespace Tamlinux {
    class CDisplayLog {
      public:
        ~CDisplayLog() {
            if (m_file)
                std::fclose(m_file);
        }
        bool open(const std::string& path) {
            std::lock_guard guard(m_mutex);
            const int       fd = ::open(path.c_str(), O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK, 0600);
            if (fd < 0)
                return false;
            struct stat metadata{};
            if (::fstat(fd, &metadata) || !S_ISREG(metadata.st_mode)) {
                ::close(fd);
                return false;
            }
            FILE* file = ::fdopen(fd, "a");
            if (!file) {
                ::close(fd);
                return false;
            }
            if (m_file)
                std::fclose(m_file);
            m_file = file;
            return true;
        }
        // Lower priorities are more severe. State events are a small allowlist;
        // trace/frame/cursor/input logs never enter this production sink.
        bool write(std::string_view component, int priority, std::string_view message, bool state = false) {
            if (priority > 4 && !state)
                return true;
            std::lock_guard guard(m_mutex);
            timespec        wall{}, mono{};
            if (clock_gettime(CLOCK_REALTIME, &wall) || clock_gettime(CLOCK_MONOTONIC, &mono))
                return false;
            std::string body(message.substr(0, 3500));
            for (char& c : body)
                if (static_cast<unsigned char>(c) < 32 || c == 127)
                    c = ' ';
            const auto record = std::format("wall_ns={} monotonic_ns={} component={} severity={} pid={} {}{}\n", wall.tv_sec * 1'000'000'000LL + wall.tv_nsec,
                                            mono.tv_sec * 1'000'000'000LL + mono.tv_nsec, component, priority, getpid(), body, message.size() > body.size() ? " [truncated]" : "");
            // The journal stream consumes the priority prefix; the retained file
            // gets identical payload clocks, sampled once before either write.
            const auto stream  = std::format("<{}>{}", priority, record);
            const bool out     = std::fwrite(stream.data(), 1, stream.size(), stdout) == stream.size();
            const bool flushed = std::fflush(stdout) == 0;
            bool       file    = true;
            if (m_file) {
                file = std::fwrite(record.data(), 1, record.size(), m_file) == record.size();
                file = std::fflush(m_file) == 0 && file;
            }
            return out && flushed && file;
        }

      private:
        std::mutex m_mutex;
        FILE*      m_file = nullptr;
    };
}
