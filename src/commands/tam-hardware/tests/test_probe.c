#define _POSIX_C_SOURCE 200809L

#include "format.h"
#include "probe.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int failures;

static void expect(int cond, const char *msg)
{
	if (!cond) {
		fprintf(stderr, "FAIL: %s\n", msg);
		failures++;
	}
}

int main(void)
{
	struct tam_hardware_report r;
	const char *root = "tests/fixtures/sysfs";
	const char *cpu = "tests/fixtures/cpu.txt";

	setenv("TAM_HARDWARE_SYSFS_ROOT", root, 1);
	setenv("TAM_HARDWARE_FIXTURE_CPU", cpu, 1);

	expect(tam_hardware_probe(&r) == 0, "probe ok");
	expect(strcmp(r.brand, "Fixture Ryzen Test CPU") == 0, "brand");
	expect(r.cores == 8, "cores");
	expect(r.logical_cpus == 16, "logical");
	expect(r.feature_count == 5, "feature count");
	expect(strcmp(r.features[0], "aes") == 0, "features sorted");
	expect(strcmp(r.product_name, "Fixture Product") == 0, "dmi product");
	expect(strcmp(r.board_name, "Fixture Board") == 0, "dmi board");
	expect(r.l3_kb == 8192, "l3");

	/* JSON must not mention serial */
	{
		char path[] = "/tmp/tam-hardware-test-XXXXXX";
		int fd = mkstemp(path);
		FILE *f;
		char buf[8192];
		size_t n;

		expect(fd >= 0, "mkstemp");
		f = fdopen(fd, "w+");
		expect(f != NULL, "fdopen");
		expect(tam_hardware_format_json(f, &r) == 0, "json");
		rewind(f);
		n = fread(buf, 1, sizeof(buf) - 1, f);
		buf[n] = '\0';
		fclose(f);
		unlink(path);
		expect(strstr(buf, "\"schema\":1") != NULL, "schema");
		expect(strstr(buf, "SECRET") == NULL, "no serial");
		expect(strstr(buf, "board_serial") == NULL, "no serial key");
	}

	if (failures) {
		fprintf(stderr, "%d failure(s)\n", failures);
		return 1;
	}
	puts("ok");
	return 0;
}
