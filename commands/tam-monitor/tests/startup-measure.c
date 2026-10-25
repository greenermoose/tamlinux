/* Linux startup-only measurement: compile this runner, pass an executable
 * path, and collect seven warm --help samples. Prints peak RSS KiB and wall ms.
 * Does not measure a live supervisor, PSS, hardware probing or cold-cache cost. */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int main(int argc, char **argv) {
 if (argc != 2) return 2;
 struct timespec a,b; struct rusage usage; int status;
 clock_gettime(CLOCK_MONOTONIC,&a);
 pid_t pid=fork();
 if (pid==0) { int fd=open("/dev/null",O_WRONLY); dup2(fd,1); close(fd); execl(argv[1],argv[1],"--help",(char*)0); _exit(127); }
 if (pid<0 || wait4(pid,&status,0,&usage)!=pid || !WIFEXITED(status) || WEXITSTATUS(status)) return 1;
 clock_gettime(CLOCK_MONOTONIC,&b);
 printf("%ld %.3f\n",usage.ru_maxrss,(b.tv_sec-a.tv_sec)*1000.0+(b.tv_nsec-a.tv_nsec)/1000000.0);
}
