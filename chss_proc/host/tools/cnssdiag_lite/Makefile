CC := $(ATH_CROSS_COMPILE_TYPE)gcc
TARGET_TYPE ?= AR9888
TARGET_VERS ?= v2


CSOURCE = cld-fwlog-netlink.c parser.c nan-parser.c cld-diag-parser.c
OBJS = $(notdir $(CSOURCE:.c=.o))

CINCLUDE = -I/usr/include/libnl3
CFLAGS = -Wall -g3 $(CINCLUDE) -DNO_DIAG_SUPPORT
LIBS = -lnl-3 -lnl-genl-3 -lrt -lpthread -lbsd
# LIBS = -lnl-3 -lrt -lpthread
LDFLAGS = $(LIBS)

%.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@ 

all: $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o cnss_diag

# all:
#     $(CC) -g3 -Wall -Werror -Wno-unused-parameter \
#         cld-fwlog-netlink.c parser.c nan-parser.c cld-diag-parser.c -o cnss_diag
#
#


clean:
	rm -f cnss_diag $(OBJS)
