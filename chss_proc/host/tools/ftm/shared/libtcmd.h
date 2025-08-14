/*
* Copyright (c) 2011-2012 Qualcomm Atheros Inc. All Rights Reserved.
* Qualcomm Atheros Proprietary and Confidential.
*/

#ifndef _LIBTCMD_H_
#define _LIBTCMD_H_

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <stdint.h>
#include <stdbool.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <net/if.h>
#include <signal.h>
#include <time.h>
#ifndef CONFIG_AR6002_REV6
#include <stdarg.h>
#endif

#define A_ERR(ret, args...)	{		\
				printf(args);	\
				exit(ret);	\
				}
#define A_DBG(args...) fprintf(stderr, args);

#define TCMD_TIMEOUT 16 /* s */
#define UNUSED(x) (void)(x)

#ifndef CONFIG_AR6002_REV6
enum tcmd_ep {
	/* Returns the supported ath11k testmode interface version in
	 * ATH11K_TM_ATTR_VERSION. Always guaranteed to work. User space
	 * uses this to verify it's using the correct version of the
	 * testmode interface
	 */
	EP_TM_CMD_GET_VERSION = 0,

	/* The command used to transmit a WMI command to the firmware and
	 * the event to receive WMI events from the firmware. Without
	 * struct wmi_cmd_hdr header, only the WMI payload. Command id is
	 * provided with ATH11K_TM_ATTR_WMI_CMDID and payload in
	 * ATH11K_TM_ATTR_DATA.
	 */
	EP_TM_CMD_WMI = 1,

	/* Boots the UTF firmware, the netdev interface must be down at the
	 * time.
	 */
	EP_TM_CMD_TESTMODE_START = 2,

	/* Shuts down the UTF firmware and puts the driver back into OFF
	 * state.
	 */
	EP_TM_CMD_TESTMODE_STOP = 3,


	/* The command used to transmit a FTM WMI command to the firmware
	 * and the event to receive WMI events from the firmware.The data
	 * received  only contain the payload, Need to add the tlv
	 * header and send the cmd to fw with commandid WMI_PDEV_UTF_CMDID.
	 */
	EP_TM_CMD_WMI_FTM_SEGMENTED = 4,
};
#endif

struct tcmd_cfg {
	char iface[100];
	void (*rx_cb)(void *buf, int len);
#ifndef CONFIG_AR6002_REV6
	uint32_t ep;
#endif
#ifdef WLAN_API_NL80211
/* XXX: eventually default to libnl-2.0 API */
#ifdef LIBNL_2
#define nl_handle nl_sock
#endif
	struct nl_handle *nl_handle;
	int nl_id;
#endif
	struct sigevent sev;
	timer_t timer;
	bool timeout;
//} tcmd_cfg;
} ;

/* WLAN API */
#ifdef WLAN_API_NL80211
#include "nl80211_drv.h"
#endif

/* send tcmd in buffer buf of length len. resp == true if a response by the FW
 * is required.  Returns: 0 on success, -ETIMEOUT on timeout
 */
int tcmd_tx(void *buf, int len, bool resp);

/* Initialize tcmd transport layer on given iface. Call given rx_cb on tcmd
 * response */
int tcmd_tx_init(char *iface, void (*rx_cb)(void *buf, int len));
#ifndef CONFIG_AR6002_REV6
/* same as above, but takes optional testmode endpoint (e.g. WMI vs. TCMD) */
int tcmd_init(char *iface, void (*rx_cb)(void *buf, int len), ...);
#endif
int tcmd_tx_start( void );
int tcmd_tx_stop( void );
#endif /* _LIBTCMD_H_ */
