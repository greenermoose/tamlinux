#include "input.h"

#include <ctype.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static int read_byte(int fd, unsigned char *out)
{
	struct pollfd pfd = { .fd = fd, .events = POLLIN };
	ssize_t n;

	if (poll(&pfd, 1, -1) <= 0)
		return -1;
	n = read(fd, out, 1);
	if (n != 1)
		return -1;
	return 0;
}

static int read_byte_timeout(int fd, unsigned char *out, int ms)
{
	struct pollfd pfd = { .fd = fd, .events = POLLIN };
	ssize_t n;

	if (poll(&pfd, 1, ms) <= 0)
		return -1;
	n = read(fd, out, 1);
	if (n != 1)
		return -1;
	return 0;
}

int start_read_key(int fd, char *buf, size_t bufsz)
{
	unsigned char ch;
	unsigned char seq[16];
	size_t slen = 0;

	if (bufsz < 2)
		return -1;
	if (read_byte(fd, &ch) != 0)
		return -1;

	if (ch == '\r' || ch == '\n') {
		snprintf(buf, bufsz, "%s", START_KEY_ENTER);
		return 0;
	}
	if (ch == ' ') {
		snprintf(buf, bufsz, "%s", START_KEY_SPACE);
		return 0;
	}
	if (ch == '`') {
		snprintf(buf, bufsz, "%s", START_KEY_BACKTICK);
		return 0;
	}
	if (ch == 0x7f || ch == 0x08) {
		snprintf(buf, bufsz, "%s", START_KEY_BACKSPACE);
		return 0;
	}
	if (ch == 0x1b) {
		seq[slen++] = ch;
		if (read_byte_timeout(fd, &seq[slen], 50) != 0) {
			snprintf(buf, bufsz, "%s", START_KEY_ESC);
			return 0;
		}
		slen++;
		if (read_byte_timeout(fd, &seq[slen], 50) == 0)
			slen++;
		if (slen >= 3 && seq[0] == 0x1b && seq[1] == '[' &&
		    !(seq[slen - 1] == 'A' || seq[slen - 1] == 'B' ||
		      seq[slen - 1] == 'C' || seq[slen - 1] == 'D' ||
		      seq[slen - 1] == 'H' || seq[slen - 1] == 'F' ||
		      seq[slen - 1] == '~')) {
			while (slen < sizeof(seq)) {
				if (read_byte_timeout(fd, &seq[slen], 50) != 0)
					break;
				slen++;
				if (seq[slen - 1] == '~' || seq[slen - 1] == 'A' ||
				    seq[slen - 1] == 'B' || seq[slen - 1] == 'C' ||
				    seq[slen - 1] == 'D' || seq[slen - 1] == 'H' ||
				    seq[slen - 1] == 'F')
					break;
			}
		}
		if ((slen == 3 && seq[1] == '[' && seq[2] == 'A') ||
		    (slen == 3 && seq[1] == 'O' && seq[2] == 'A')) {
			snprintf(buf, bufsz, "%s", START_KEY_UP);
			return 0;
		}
		if ((slen == 3 && seq[1] == '[' && seq[2] == 'B') ||
		    (slen == 3 && seq[1] == 'O' && seq[2] == 'B')) {
			snprintf(buf, bufsz, "%s", START_KEY_DOWN);
			return 0;
		}
		if ((slen == 3 && seq[1] == '[' && seq[2] == 'C') ||
		    (slen == 3 && seq[1] == 'O' && seq[2] == 'C')) {
			snprintf(buf, bufsz, "%s", START_KEY_RIGHT);
			return 0;
		}
		if ((slen == 3 && seq[1] == '[' && seq[2] == 'H') ||
		    (slen == 3 && seq[1] == 'O' && seq[2] == 'H') ||
		    (slen == 4 && seq[1] == '[' && seq[2] == '1' && seq[3] == '~') ||
		    (slen == 4 && seq[1] == '[' && seq[2] == '7' && seq[3] == '~')) {
			snprintf(buf, bufsz, "%s", START_KEY_HOME);
			return 0;
		}
		if ((slen == 3 && seq[1] == '[' && seq[2] == 'F') ||
		    (slen == 3 && seq[1] == 'O' && seq[2] == 'F') ||
		    (slen == 4 && seq[1] == '[' && seq[2] == '4' && seq[3] == '~') ||
		    (slen == 4 && seq[1] == '[' && seq[2] == '8' && seq[3] == '~')) {
			snprintf(buf, bufsz, "%s", START_KEY_END);
			return 0;
		}
		if (slen == 4 && seq[1] == '[' && seq[2] == '5' && seq[3] == '~') {
			snprintf(buf, bufsz, "%s", START_KEY_PGUP);
			return 0;
		}
		if (slen == 4 && seq[1] == '[' && seq[2] == '6' && seq[3] == '~') {
			snprintf(buf, bufsz, "%s", START_KEY_PGDN);
			return 0;
		}
		if (slen == 4 && seq[1] == '[' && seq[2] == '3' && seq[3] == '~') {
			snprintf(buf, bufsz, "%s", START_KEY_DELETE);
			return 0;
		}
		snprintf(buf, bufsz, "%s", START_KEY_ESC);
		return 0;
	}
	if (isalpha(ch)) {
		buf[0] = (char)tolower(ch);
		buf[1] = '\0';
		return 0;
	}
	buf[0] = (char)ch;
	buf[1] = '\0';
	return 0;
}
