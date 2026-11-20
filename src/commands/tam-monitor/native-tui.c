#define _GNU_SOURCE
#include "native-tui.h"
#include "native-hw.h"
#include "native-preview.h"
#include <tam_display.h>
#include <tam_vt.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/signalfd.h>
#include <termios.h>
#include <unistd.h>

#define MAX_LINES 32
#define LINE_CAP 200

static const unsigned IDLE_PRESETS[] = {0, 1, 5, 10, 15, 30, 60};
static const size_t IDLE_PRESET_COUNT = sizeof(IDLE_PRESETS) / sizeof(IDLE_PRESETS[0]);

static void get_term_size(int *rows_out, int *cols_out)
{
    struct winsize ws = {0};
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_row > 0 && ws.ws_col > 0) {
        *rows_out = (int)ws.ws_row;
        *cols_out = (int)ws.ws_col;
    } else {
        *rows_out = 24;
        *cols_out = 80;
    }
}

static void render_frame(char lines[MAX_LINES][LINE_CAP], size_t line_count,
    int selected_row, int rows, int cols)
{
    char out[8192];
    size_t pos = 0;
    pos += (size_t)snprintf(out + pos, sizeof(out) - pos, "\x1b[H\x1b[2J");
    int max_rows = rows > 1 ? rows - 1 : 0;
    int max_cols = cols > 1 ? cols - 1 : 0;
    if (max_cols > LINE_CAP - 1) max_cols = LINE_CAP - 1;
    for (size_t r = 0; r < line_count && (int)r < max_rows && pos + 256 < sizeof(out); ++r) {
        char cleaned[LINE_CAP];
        tam_monitor_clean(lines[r], cleaned, sizeof(cleaned));
        if ((int)strlen(cleaned) > max_cols)
            cleaned[max_cols] = 0;
        if ((int)r == selected_row) {
            pos += (size_t)snprintf(out + pos, sizeof(out) - pos,
                "\x1b[%zu;1H\x1b[7m%s\x1b[0m", r + 1, cleaned);
        } else {
            pos += (size_t)snprintf(out + pos, sizeof(out) - pos,
                "\x1b[%zu;1H%s", r + 1, cleaned);
        }
    }
    (void)write(STDOUT_FILENO, out, pos);
}

enum key_code {
    KEY_NONE = 0,
    KEY_QUIT,
    KEY_UP_ITEM,
    KEY_DOWN_ITEM,
    KEY_REFRESH,
    KEY_PLUS,
    KEY_MINUS,
    KEY_BLANK_ALL,
    KEY_CYCLE_IDLE,
    KEY_KEEP_ONE,
    KEY_TOGGLE_ONE,
    KEY_WAKE_ALL,
    KEY_KEEP_SHELL
};

static enum key_code read_key(int fd)
{
    unsigned char ch = 0;
    if (read(fd, &ch, 1) != 1) return KEY_QUIT;
    if (ch == 'q' || ch == 'Q') return KEY_QUIT;
    if (ch == 'j' || ch == 'J') return KEY_DOWN_ITEM;
    if (ch == 'k' || ch == 'K') return KEY_UP_ITEM;
    if (ch == 'r' || ch == 'R') return KEY_REFRESH;
    if (ch == '+' || ch == '=') return KEY_PLUS;
    if (ch == '-') return KEY_MINUS;
    if (ch == 'b' || ch == 'B') return KEY_BLANK_ALL;
    if (ch == 'i' || ch == 'I') return KEY_CYCLE_IDLE;
    if (ch == 'o' || ch == 'O' || ch == '\r' || ch == '\n') return KEY_KEEP_ONE;
    if (ch == 'x' || ch == 'X') return KEY_TOGGLE_ONE;
    if (ch == 'w' || ch == 'W') return KEY_WAKE_ALL;
    if (ch == 's' || ch == 'S') return KEY_KEEP_SHELL;
    if (ch == 27) {
        struct pollfd pfd = {.fd = fd, .events = POLLIN};
        if (poll(&pfd, 1, 25) <= 0) return KEY_QUIT;
        unsigned char seq[2] = {0};
        if (read(fd, &seq[0], 1) != 1) return KEY_QUIT;
        if (seq[0] == '[' || seq[0] == 'O') {
            if (poll(&pfd, 1, 25) > 0 && read(fd, &seq[1], 1) == 1) {
                if (seq[1] == 'A') return KEY_UP_ITEM;
                if (seq[1] == 'B') return KEY_DOWN_ITEM;
            }
            return KEY_NONE;
        }
        return KEY_QUIT;
    }
    return KEY_NONE;
}

int tam_monitor_tui(void)
{
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO)) {
        fprintf(stderr, "tam-monitor: TUI requires a terminal; use list --json for noninteractive output\n");
        return 1;
    }
    struct termios saved_term = {0};
    if (tcgetattr(STDIN_FILENO, &saved_term) < 0) {
        fprintf(stderr, "tam-monitor: Cannot read terminal attributes: %s\n", strerror(errno));
        return 1;
    }

    struct tam_vt vt = {.fd = -1};
    struct tam_display_error vt_err = {0};
    bool has_console = (tam_vt_open(&vt, &vt_err) == TAM_DISPLAY_OK);
    struct tam_console_fb cfb = {0};
    bool has_cfb = false;
    if (has_console) {
        struct tam_display_error fb_err = {0};
        has_cfb = (tam_display_map_console_fb(vt.number, &cfb, &fb_err) == TAM_DISPLAY_OK);
    }

    struct termios raw = saved_term;
    raw.c_lflag &= ~(tcflag_t)(ICANON | ECHO);
    raw.c_cc[VMIN] = 1;
    raw.c_cc[VTIME] = 0;
    if (tcsetattr(STDIN_FILENO, TCSANOW, &raw) < 0) {
        tam_vt_close(&vt);
        fprintf(stderr, "tam-monitor: Cannot configure terminal attributes\n");
        return 1;
    }
    (void)write(STDOUT_FILENO, "\x1b[?1049h\x1b[?25l", 14);

    sigset_t mask, oldmask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGWINCH);
    sigaddset(&mask, SIGINT);
    sigaddset(&mask, SIGTERM);
    sigaddset(&mask, SIGHUP);
    sigprocmask(SIG_BLOCK, &mask, &oldmask);
    int sigfd = signalfd(-1, &mask, SFD_CLOEXEC | SFD_NONBLOCK);

    struct tam_monitor_info monitors[TAM_MONITOR_MAX_MONITORS];
    size_t count = 0, index = 0;
    char message[160] = "Ready";
    char err[160] = {0};
    if (tam_monitor_discover(true, monitors, TAM_MONITOR_MAX_MONITORS, &count, err, sizeof(err)) < 0) {
        tam_monitor_clean(err, message, sizeof(message));
    }

    int idle_sec = -1;
    int idle_min = -1;
    if (tam_monitor_console_idle_seconds(&idle_sec) == 0 && idle_sec >= 0 && idle_sec % 60 == 0)
        idle_min = idle_sec / 60;

    char prev_lines[MAX_LINES][LINE_CAP];
    memset(prev_lines, 0, sizeof(prev_lines));
    size_t prev_count = 0;
    int prev_selected = -2, prev_rows = -1, prev_cols = -1;
    int exit_code = 0;

    for (;;) {
        int rows = 24, cols = 80;
        get_term_size(&rows, &cols);
        char lines[MAX_LINES][LINE_CAP];
        memset(lines, 0, sizeof(lines));
        size_t lcount = 0;

        snprintf(lines[lcount++], LINE_CAP, "Tamlinux monitor control -- console / direct hardware");
        snprintf(lines[lcount++], LINE_CAP, "%s", "");

        int visible = rows - 17;
        if (visible < 1) visible = 1;
        size_t first = 0;
        if (count > 0 && index >= (size_t)visible)
            first = index - (size_t)visible + 1;

        for (size_t i = first; i < count && i < first + (size_t)visible && lcount < MAX_LINES - 14; ++i) {
            char b_str[32];
            if (monitors[i].brightness >= 0) snprintf(b_str, sizeof(b_str), "%d%%", monitors[i].brightness);
            else snprintf(b_str, sizeof(b_str), "unknown");
            snprintf(lines[lcount++], LINE_CAP, "%-20s %-12s brightness %s",
                monitors[i].id, monitors[i].connection, b_str);
        }
        if (count == 0) {
            snprintf(lines[lcount++], LINE_CAP, "No DRM connectors found");
        }
        int selected = (count > 0) ? (int)(2 + index - first) : -1;
        const struct tam_monitor_info *m = (count > 0) ? &monitors[index] : NULL;

        snprintf(lines[lcount++], LINE_CAP, "%s", "");
        snprintf(lines[lcount++], LINE_CAP, "%s", m ? m->identity : "");
        if (m) snprintf(lines[lcount++], LINE_CAP, "Brightness: %s", m->brightness_detail);
        else snprintf(lines[lcount++], LINE_CAP, "%s", "");
        if (has_console && has_cfb) {
            snprintf(lines[lcount++], LINE_CAP,
                "Targeted power: ready on tty%u (card%u fb%u %s %ux%u)",
                vt.number, cfb.card, cfb.fb_index, cfb.fb_name, cfb.width, cfb.height);
        } else if (has_console) {
            snprintf(lines[lcount++], LINE_CAP, "Targeted power: native DRM/KMS (tty%u)", vt.number);
        } else {
            snprintf(lines[lcount++], LINE_CAP, "Targeted power: requires foreground Linux text VT");
        }
        snprintf(lines[lcount++], LINE_CAP, "Mode / rotation / layout: targeted console routing via libtam-display");
        snprintf(lines[lcount++], LINE_CAP, "%s", "");
        snprintf(lines[lcount++], LINE_CAP, "%s",
            has_console ? "Console: ready" : "Console controls unavailable in a desktop terminal / tmux / SSH");
        if (idle_min >= 0)
            snprintf(lines[lcount++], LINE_CAP, "Console idle: %d min (0 = off)", idle_min);
        else
            snprintf(lines[lcount++], LINE_CAP, "Console idle: unknown (0 = off)");
        snprintf(lines[lcount++], LINE_CAP,
            "o keep selected (15s/session)  |  x blank/wake selected  |  w wake all");
        snprintf(lines[lcount++], LINE_CAP,
            "s keep selected + shell  |  b blank all (15s max)  |  i cycle console idle");
        snprintf(lines[lcount++], LINE_CAP,
            "+/- brightness  |  j/k/arrows select  |  r refresh  |  q quit");
        snprintf(lines[lcount++], LINE_CAP, "%s", "");
        tam_monitor_clean(message, lines[lcount++], LINE_CAP);

        bool changed = (lcount != prev_count || selected != prev_selected ||
                        rows != prev_rows || cols != prev_cols ||
                        memcmp(lines, prev_lines, sizeof(lines)) != 0);
        if (changed) {
            render_frame(lines, lcount, selected, rows, cols);
            memcpy(prev_lines, lines, sizeof(lines));
            prev_count = lcount;
            prev_selected = selected;
            prev_rows = rows;
            prev_cols = cols;
        }

        struct pollfd fds[2] = {
            {.fd = STDIN_FILENO, .events = POLLIN},
            {.fd = sigfd, .events = POLLIN}
        };
        int n = poll(fds, 2, -1);
        if (n < 0) {
            if (errno == EINTR) continue;
            break;
        }
        if (sigfd >= 0 && (fds[1].revents & POLLIN)) {
            struct signalfd_siginfo si;
            bool stop = false;
            while (read(sigfd, &si, sizeof(si)) == sizeof(si)) {
                if (si.ssi_signo == SIGWINCH) {
                    prev_rows = -1;
                } else {
                    if (si.ssi_signo == SIGINT) exit_code = 130;
                    stop = true;
                }
            }
            if (stop) break;
        }
        if (!(fds[0].revents & (POLLIN | POLLHUP | POLLERR))) continue;
        enum key_code key = read_key(STDIN_FILENO);
        if (key == KEY_QUIT) break;
        if (key == KEY_DOWN_ITEM && count > 0) {
            index = (index + 1) % count;
        } else if (key == KEY_UP_ITEM && count > 0) {
            index = (index + count - 1) % count;
        } else if (key == KEY_REFRESH) {
            if (tam_monitor_discover(true, monitors, TAM_MONITOR_MAX_MONITORS, &count, err, sizeof(err)) < 0) {
                tam_monitor_clean(err, message, sizeof(message));
            } else {
                if (count > 0 && index >= count) index = count - 1;
                snprintf(message, sizeof(message), "Ready");
            }
        } else if ((key == KEY_PLUS || key == KEY_MINUS) && m) {
            if (m->brightness < 0) {
                snprintf(message, sizeof(message), "Brightness unavailable; r retries detection");
            } else {
                int target = m->brightness + (key == KEY_MINUS ? -5 : 5);
                if (target < 1) target = 1;
                if (target > 100) target = 100;
                int actual = 0;
                if (tam_monitor_set_brightness(m->id, target, &actual, err, sizeof(err)) < 0) {
                    tam_monitor_clean(err, message, sizeof(message));
                } else {
                    monitors[index].brightness = actual;
                    snprintf(message, sizeof(message),
                        "Brightness verified: %d%% (r refreshes all monitors)", actual);
                }
            }
        } else if (key == KEY_BLANK_ALL || key == KEY_CYCLE_IDLE ||
                   key == KEY_KEEP_ONE || key == KEY_TOGGLE_ONE ||
                   key == KEY_WAKE_ALL || key == KEY_KEEP_SHELL) {
            if (!has_console) {
                snprintf(message, sizeof(message),
                    "Use a real foreground Linux text console for blanking and idle");
                continue;
            }
            if (key == KEY_BLANK_ALL) {
                if (tam_monitor_blank_console(15, &saved_term, err, sizeof(err)) != 0) {
                    tam_monitor_clean(err, message, sizeof(message));
                } else {
                    snprintf(message, sizeof(message), "Console restored (blanking is not a screen lock)");
                }
                (void)tcsetattr(STDIN_FILENO, TCSANOW, &raw);
                prev_rows = -1;
            } else if (key == KEY_CYCLE_IDLE) {
                unsigned next_val = 5;
                for (size_t i = 0; i < IDLE_PRESET_COUNT; ++i) {
                    if (idle_min == (int)IDLE_PRESETS[i]) {
                        next_val = IDLE_PRESETS[(i + 1) % IDLE_PRESET_COUNT];
                        break;
                    }
                }
                bool verified = false;
                struct tam_display_error ie = {0};
                if (tam_vt_idle_path(&vt, next_val, tam_monitor_consoleblank_path(), &verified, &ie) != TAM_DISPLAY_OK) {
                    tam_monitor_clean(ie.message, message, sizeof(message));
                } else {
                    idle_min = (int)next_val;
                    snprintf(message, sizeof(message), "%s",
                        verified ? "Console idle interval verified"
                                 : "Idle request sent; runtime interval readback unavailable");
                }
            } else if (key == KEY_WAKE_ALL) {
                struct tam_display_error we = {0};
                int rc = tam_monitor_supervisor_request(vt.number, "RESTORE", &we);
                tam_vt_wake(&vt, &we);
                if (rc > 0 && we.code) tam_monitor_clean(we.message, message, sizeof(message));
                else snprintf(message, sizeof(message), "All console monitors awake");
            } else if (key == KEY_KEEP_ONE && m) {
                struct tam_display_error ke = {0};
                char req[128];
                snprintf(req, sizeof(req), "KEEP %s", m->id);
                int rc = tam_monitor_supervisor_request(vt.number, req, &ke);
                if (rc >= 0) {
                    if (ke.code) tam_monitor_clean(ke.message, message, sizeof(message));
                    else snprintf(message, sizeof(message), "Keeping %s active in current session", m->id);
                } else {
                    if (tam_monitor_keep(m->card, m->connector, false, 15, 0) != 0)
                        snprintf(message, sizeof(message), "Targeted keep trial failed for %s", m->id);
                    else
                        snprintf(message, sizeof(message), "Bounded 15s keep trial completed for %s", m->id);
                    prev_rows = -1;
                }
            } else if (key == KEY_TOGGLE_ONE && m) {
                struct tam_display_error te = {0};
                char req[128];
                snprintf(req, sizeof(req), "TOGGLE %s", m->id);
                int rc = tam_monitor_supervisor_request(vt.number, req, &te);
                if (rc >= 0) {
                    if (te.code) tam_monitor_clean(te.message, message, sizeof(message));
                    else snprintf(message, sizeof(message), "Toggled %s (w wakes all)", m->id);
                } else {
                    const char *targets[1] = {m->connector};
                    if (tam_monitor_blank_monitors(m->card, targets, 1, 15, true, 0) != 0)
                        snprintf(message, sizeof(message), "Targeted blank trial failed for %s", m->id);
                    else
                        snprintf(message, sizeof(message), "Bounded 15s blank completed for %s", m->id);
                    prev_rows = -1;
                }
            } else if (key == KEY_KEEP_SHELL && m) {
                (void)write(STDOUT_FILENO, "\x1b[0m\x1b[?25h\x1b[?1049l", 18);
                (void)tcsetattr(STDIN_FILENO, TCSANOW, &saved_term);
                sigprocmask(SIG_SETMASK, &oldmask, NULL);
                int sh_rc = tam_monitor_keep(m->card, m->connector, true, 0, 0);
                sigprocmask(SIG_BLOCK, &mask, &oldmask);
                (void)tcsetattr(STDIN_FILENO, TCSANOW, &raw);
                (void)write(STDOUT_FILENO, "\x1b[?1049h\x1b[?25l", 14);
                snprintf(message, sizeof(message),
                    sh_rc == 0 ? "Keep shell ended; all console monitors restored"
                               : "Keep shell failed or ended with error");
                prev_rows = -1;
            }
        }
    }

    if (sigfd >= 0) close(sigfd);
    struct timespec zero = {0};
    while (sigtimedwait(&mask, NULL, &zero) >= 0) {}
    sigprocmask(SIG_SETMASK, &oldmask, NULL);
    (void)write(STDOUT_FILENO, "\x1b[0m\x1b[?25h\x1b[?1049l", 18);
    (void)tcsetattr(STDIN_FILENO, TCSANOW, &saved_term);
    tam_vt_close(&vt);
    return exit_code;
}
