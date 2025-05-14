#include <stdlib.h>
#include <stdio.h>
#include <bsd/string.h>

#define SHELL_PATH "/usr/bin/bash"
#define SCRIPT_PATH "/usr/sbin/qca-dump-umh.sh"
#define CMDS_SIZE 128

int main(int argc, char* argv[]) {
	char commands[CMDS_SIZE];

	strlcpy(commands, SHELL_PATH, CMDS_SIZE);
	strlcat(commands, " ", CMDS_SIZE);
	strlcat(commands, SCRIPT_PATH, CMDS_SIZE);
	strlcat(commands, " ", CMDS_SIZE);
	strlcat(commands, argv[1], CMDS_SIZE);

	printf("commands: %s\n", commands);
	system(commands);

	return 0;
}
