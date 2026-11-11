/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright (c) 2026 Fred Horch. Typed, detached journal terminal launcher.
 */
#include <tam.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static char *program(const char *directory, const char *name) {
    if (!directory || directory[0] != '/') return NULL;
    tam_str_t path = tam_str_new(directory);
    path = tam_str_cat_printf(path, "/%s", name);
    char *result = strdup(path); tam_str_free(path);
    return result;
}

int main(int argc, char **argv) {
    if (argc > 4) { fputs("Usage: tam-launch-journal [add] [--date YYYY-MM-DD]\n", stderr); return 2; }
    int add = 0, date = 0;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "add") && !add) add = 1;
        else if (!strcmp(argv[i], "--date") && !date && i+1 < argc && strlen(argv[i+1]) == 10) {
            const char *s = argv[++i];
            for (int j = 0; j < 10; ++j)
                if ((j == 4 || j == 7) ? s[j] != '-' : (s[j] < '0' || s[j] > '9')) return 2;
            date = 1;
        } else return 2;
    }
    if (tam_bundle_guard(NULL)) return 1;
    const char *bin = getenv("TAMLINUX_BIN"), *home = getenv("HOME");
    char *fallback = home ? program(home, ".local/bin") : NULL;
    if (!bin || !*bin) bin = fallback;
    char *launcher = program(bin, "tam-launch-tui"), *journal = program(bin, "tam-journal");
    if (!journal || access(journal, X_OK)) { free(journal); journal = program(fallback, "tam-journal"); }
    if (!launcher || !journal || access(launcher, X_OK) || access(journal, X_OK)) {
        fputs("tam-launch-journal: the selected package needs tam-journal and tam-launch-tui.\n", stderr);
        free(fallback); free(launcher); free(journal); return 1;
    }
    char *args[9] = {launcher, "--app-id=org.tamlinux.journal", journal};
    for (int i = 1; i < argc; ++i) args[i+2] = argv[i];
    int pipefd[2];
    if (pipe2(pipefd, O_CLOEXEC)) return 1;
    pid_t child = fork();
    if (child < 0) { close(pipefd[0]); close(pipefd[1]); return 1; }
    if (!child) {
        close(pipefd[0]);
        int error = 0;
        if (setsid() < 0) error = errno;
        int nullfd = open("/dev/null", O_RDWR);
        if (nullfd < 0) error = errno;
        if (!error) {
            for (int i = 0; i < 3; ++i) if (dup2(nullfd, i) < 0) error = errno;
            if (nullfd > 2) close(nullfd);
        }
        if (!error) { execv(launcher, args); error = errno; }
        (void)write(pipefd[1], &error, sizeof error); _exit(127);
    }
    close(pipefd[1]); int error = 0; ssize_t n;
    do { n = read(pipefd[0], &error, sizeof error); } while (n < 0 && errno == EINTR);
    close(pipefd[0]); free(fallback); free(launcher); free(journal);
    if (n != 0) { fprintf(stderr, "tam-launch-journal: launch failed: %s\n", strerror(error ? error : EIO)); return 1; }
    return 0;
}
