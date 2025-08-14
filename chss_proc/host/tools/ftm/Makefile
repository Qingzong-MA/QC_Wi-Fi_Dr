LOCAL_PATH=$(shell pwd)
CC := $(ATH_CROSS_COMPILE_TYPE)gcc
TARGET_TYPE ?= AR9888
TARGET_VERS ?= v2

TARGET = ftm

#Sources to compile
SRCS := ftm_wlan_main.c ftm_wlan.c os.c
SRCS += shared/nl80211.c
SRCS += shared/Socket.c
SRCS += shared/libtcmd.c

INCLUDES += -I$(LOCAL_PATH)

OBJS = $(SRCS:.c=.o)

#TARGET_CFLAGS += -DCONFIG_FTM_WLAN -DDEBUG -DFTM_DEBUG -DWIN_AP_HOST
CFLAGS += -DDEBUG
CFLAGS += -MMD -O2 -Wall -g
CFLAGS += -fpie
CFLAGS += -DWLAN_API_NL80211 -DLIBNL_2 -I/usr/include/libnl3
#LDFLAGS += -L. -ltcmd
LDFLAGS += -L/lib/x86_64-linux-gnu -lnl-3 -lnl-genl-3 -lrt -lbsd
LDFLAGS += -pie

all :
	$(CC) -o $(TARGET) $(SRCS) $(INCLUDES) $(CFLAGS) $(LDFLAGS) -g3 -Wall

clean:
	rm -f $(OBJS) $(TARGET)
