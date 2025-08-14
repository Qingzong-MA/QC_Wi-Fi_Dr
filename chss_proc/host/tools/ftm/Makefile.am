AM_CFLAGS = -Wall \
            -g -O0 \
            $(DIAG_CFLAGS)

AM_CPPFLAGS = -Wall \
            -g -O0 \
            $(DIAG_CFLAGS)

if DEBUG
AM_CFLAGS += -DDEBUG
AM_CPPFLAGS += -DDEBUG
endif

requiredlibs = -lrt $(DIAG_LIBS)

if USE_GLIB
AM_CFLAGS += -DUSE_GLIB $(GLIB_CFLAGS)
AM_CPPFLAGS += -DUSE_GLIB $(GLIB_CFLAGS)
requiredlibs += $(GLIB_LIBS)
endif

#By default build for MDM_LE
AM_CFLAGS += -DMDM_LE
AM_CPPFLAGS += -DMDM_LE

c_sources = ftm_wlan_main.c ftm_wlan.c shared/Socket.c os.c shared/nl80211.c shared/libtcmd.c

AM_CFLAGS += -DLIBNL_2 -DWLAN_API_NL80211
ftmdaemon_SOURCES = $(c_sources)
ftmdaemon_LDADD = -ldl $(requiredlibs) -lnl-3 -lnl-genl-3
bin_PROGRAMS = ftmdaemon
