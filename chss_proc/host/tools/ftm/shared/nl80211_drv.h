/*
* Copyright (c) 2011-2012 Qualcomm Atheros Inc. All Rights Reserved.
* Qualcomm Atheros Proprietary and Confidential.
*/

#ifndef _NL80211_DRV_H_
#define _NL80211_DRV_H_

#include <netlink/genl/genl.h>
#include <netlink/genl/family.h>
#include <netlink/genl/ctrl.h>
#include <netlink/msg.h>
#include <netlink/attr.h>
#include <netlink/socket.h>
#include <linux/nl80211.h>

#include "shared/libtcmd.h"

/* copied from ath6kl */
enum ar6k_testmode_attr {
	__AR6K_TM_ATTR_INVALID	= 0,
	AR6K_TM_ATTR_CMD	= 1,
	AR6K_TM_ATTR_DATA	= 2,
	AR6K_TM_ATTR_STREAM_ID	= 3,

	/* keep last */
	__AR6K_TM_ATTR_AFTER_LAST,
	AR6K_TM_ATTR_MAX	= __AR6K_TM_ATTR_AFTER_LAST - 1
};

enum ath10k_tm_attr {
	__ATH10K_TM_ATTR_INVALID	= 0,
	ATH10K_TM_ATTR_CMD		= 1,
	ATH10K_TM_ATTR_DATA		= 2,
	ATH10K_TM_ATTR_WMI_CMDID	= 3,
	ATH10K_TM_ATTR_VERSION_MAJOR	= 4,
	ATH10K_TM_ATTR_VERSION_MINOR	= 5,
	ATH10K_TM_ATTR_WMI_OP_VERSION	= 6,

	/* keep last */
	__ATH10K_TM_ATTR_AFTER_LAST,
	ATH10K_TM_ATTR_MAX		= __ATH10K_TM_ATTR_AFTER_LAST - 1,
};

enum ar6k_testmode_cmd {
	AR6K_TM_CMD_TCMD		= 0,
	AR6K_TM_CMD_START		= 2,
	AR6K_TM_CMD_STOP		= 3,
#ifndef CONFIG_AR6002_REV6
	AR6K_TM_CMD_WMI_CMD		= 0xF000,
#endif
};

enum ath10k_testmode_cmd {
	/* Returns the supported ath10k testmode interface version in
	 * ATH10K_TM_ATTR_VERSION. Always guaranteed to work. User space
	 * uses this to verify it's using the correct version of the
	 * testmode interface */
	ATH10K_TM_CMD_GET_VERSION = 0,

	/* Boots the UTF firmware, the netdev interface must be down at the
	 * time. */
	ATH10K_TM_CMD_UTF_START = 1,

	/* Shuts down the UTF firmware and puts the driver back into OFF
	 * state. */
	ATH10K_TM_CMD_UTF_STOP = 2,

	/* The command used to transmit a WMI command to the firmware and
	 * the event to receive WMI events from the firmware. Without
	 * struct wmi_cmd_hdr header, only the WMI payload. Command id is
	 * provided with ATH10K_TM_ATTR_WMI_CMDID and payload in
	 * ATH10K_TM_ATTR_DATA.*/
	ATH10K_TM_CMD_WMI = 3,
};

enum ath11k_testmode_cmd {
	/* Returns the supported ath11k testmode interface version in
	 * ATH11K_TM_ATTR_VERSION. Always guaranteed to work. User space
	 * uses this to verify it's using the correct version of the
	 * testmode interface
	 */
	ATH11K_TM_CMD_GET_VERSION = 0,

	/* The command used to transmit a WMI command to the firmware and
	 * the event to receive WMI events from the firmware. Without
	 * struct wmi_cmd_hdr header, only the WMI payload. Command id is
	 * provided with ATH11K_TM_ATTR_WMI_CMDID and payload in
	 * ATH11K_TM_ATTR_DATA.
	 */
	ATH11K_TM_CMD_WMI = 1,

	/* Boots the UTF firmware, the netdev interface must be down at the
	 * time.
	 */
	ATH11K_TM_CMD_TESTMODE_START = 2,

	/* Shuts down the UTF firmware and puts the driver back into OFF
	 * state.
	 */
	ATH11K_TM_CMD_TESTMODE_STOP = 3,

	/* The command used to transmit a FTM WMI command to the firmware
	 * and the event to receive WMI events from the firmware.The data
	 * received  only contain the payload, Need to add the tlv
	 * header and send the cmd to fw with commandid WMI_PDEV_UTF_CMDID.
	 */
	ATH11K_TM_CMD_WMI_FTM = 4,
};

int nl80211_init(struct tcmd_cfg *cfg);
int nl80211_tcmd_pre_tx(struct tcmd_cfg *cfg);
int nl80211_tcmd_tx(struct tcmd_cfg *cfg, void *buf, int len);
int nl80211_tcmd_rx(struct tcmd_cfg *cfg);
int nl80211_tcmd_start(struct tcmd_cfg *cfg);
int nl80211_tcmd_stop(struct tcmd_cfg *cfg);
#ifndef CONFIG_AR6002_REV6
int nl80211_set_ep(uint32_t *driv_ep, enum tcmd_ep ep);
#endif
#endif /* _NL80211_DRV_H_ */
