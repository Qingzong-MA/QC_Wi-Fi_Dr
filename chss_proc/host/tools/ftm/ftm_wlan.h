/*==========================================================================

                     FTM WLAN Header File

Description
  The header file includes enums, struct definitions for WLAN FTM packets

# Copyright (c) 2010-2011, 2014 by Qualcomm Technologies, Inc.
# All Rights Reserved.
# Qualcomm Technologies Proprietary and Confidential.

===========================================================================*/

/*===========================================================================

                         Edit History


when       who       what, where, why
--------   ---       ----------------------------------------------------------
07/11/11   karthikm  Created header file to include enums, struct for WLAN FTM
                     for Atheros support
========================================================================*/

#ifndef  FTM_WLAN_H_
#define  FTM_WLAN_H_



#include <sys/types.h>

#ifndef NULL
#define NULL    0
#endif
#ifndef FALSE
#define FALSE   0
#endif
#ifndef TRUE
#define TRUE    1
#endif

#define FTM_WLAN_CMD_CODE 22
#define DIAGPKT_COMMON_OP_CONTENT_START    16

#define MAX_FILE_PATH_SIZE    128
#define MAX_FTM_BDF_TX_SIZE   1024

/* TODO: For LE platforms only - need to extend it for BE platform too*/
#define cpu32_to_le32(buf, val)     \
    do { \
            buf[0] = val & 0xff;            \
            buf[1] = (val >> 8) & 0xff;     \
            buf[2] = (val >> 16) & 0xff;    \
            buf[3] = (val >> 24) & 0xff;    \
    } while(0)

/* TODO: For LE platforms only - need to extend it for BE platform too*/
#define le_to_cpu16(buf, uint16_val)                                   \
    do {                                                                   \
            uint16_val = (buf[0] | buf[1] << 8);  \
    } while(0)

/* TODO: For LE platforms only - need to extend it for BE platform too*/
#define le_to_cpu32(buf, uint32_val)                                   \
    do {                                                                   \
            uint32_val = (buf[0] | buf[1] << 8 | buf[2] << 16 | buf[3] << 24); \
    } while(0)

extern char g_ifname[];

/* Various ERROR CODES supported by the FTM WLAN module*/
typedef enum {
    FTM_ERR_CODE_PASS = 0,
    FTM_ERR_CODE_IOCTL_FAIL,
    FTM_ERR_CODE_SOCK_FAIL,
    FTM_ERR_CODE_UNRECOG_FTM
}FTM_WLAN_LOAD_ERROR_CODES;

typedef enum {
    FTM_ERR_CODE_INVALID_PARAMETER = 2,
}FTM_WLAN_COMMON_OPS_ERROR_CODES;


#define CONFIG_HOST_TCMD_SUPPORT  1
#define AR6000_IOCTL_SUPPORTED    1

#define ATH_MAC_LEN               6




typedef enum {
    FTM_WLAN_COMMON_OP,
    FTM_WLAN_BDF_GET_MAX_TRANSFER_SIZE,
    FTM_WLAN_BDF_READ,
    FTM_WLAN_BDF_WRITE,
    FTM_WLAN_BDF_GET_FNAMEPATH,
    FTM_WLAN_BDF_SET_FNAMEPATH,
    FTM_WLAN_CMD_CODE_MAX
}FTM_WLAN_CMD;

typedef enum {
    WLAN_BDF_READ_SUCCESS,
    WLAN_BDF_READ_FAILED,
    WLAN_BDF_WRITE_SUCCESS,
    WLAN_BDF_WRITE_FAILED,
    WLAN_BDF_INVALID_SIZE = 5,
    WLAN_BDF_BAD_OFFSET,
    WLAN_BDF_FILE_OPEN_FAIL,
    WLAN_BDF_FILE_SEEK_FAIL,
    WLAN_BDF_FILE_STAT_FAIL,
    WLAN_BDF_PATH_GET_SUCCESS,
    WLAN_BDF_PATH_GET_FAILED,
    WLAN_BDF_PATH_SET_SUCCESS,
    WLAN_BDF_PATH_SET_FAILED,
    WLAN_BDF_ERR_CODE_MAX
}FTM_WLAN_ERROR_CODES;

#ifdef WIN_AP_HOST
#define PACKED_STRUCT __attribute__((__packed__))
#else
#define PACKED_STRUCT __attribute__((packed))
#endif

#pragma pack(push,1)

/*FTM WLAN request type*/

typedef struct
{
    uint8_t                               cmd_code;
    uint8_t                               subsys_id;
    uint16_t                              subsys_cmd_code;
    uint16_t                              cmd_id;
    uint16_t                              cmd_data_len;
    uint16_t                              cmd_rsp_pkt_size;
    union {
        struct {
             uint16_t                     rsvd;
             uint8_t                      rsvd1;
             uint8_t                      rsvd2;
             uint8_t                      rsvd3;
             uint8_t                      wlandeviceno;
             uint8_t                      data[0];
        } common_ops;
        struct {
             uint8_t                       rsvd[6];
             uint8_t                       data[0];
        } get_max_transfer_size;
        struct {
            uint32_t                      offset;
            uint8_t                       rsvd[2];
            uint8_t                       data[0];
        } read_file;
        struct {
            uint16_t                      size;
            uint8_t                       append_flag;
            uint8_t                       rsvd[3];
            uint8_t                       data[0];
        } write_file;
        struct {
            uint8_t                       rsvd[6];
            uint8_t                       data[0];
        } get_fname;
        struct {
            uint8_t                       rsvd[6];
            uint8_t                       data[0];
        } set_fname;
    }cmd;
} ftm_wlan_req_pkt_type;

/*FTM WLAM response type */
typedef struct
{
    struct {
        uint8_t                               cmd_code;
        uint8_t                               subsys_id;
        uint16_t                              subsys_cmd_code;
        uint16_t                              cmd_id;
        uint16_t                              cmd_data_len;
        uint16_t                              cmd_rsp_pkt_size;
    } common_header;
    union {
        struct {
            uint16_t                             rsvd;
            uint32_t                             result;  /* error_code */
            uint8_t                              data[0]; /*rxReport*/
        } common_ops;
        struct {
            uint16_t                              result; /*error_code*/
            uint8_t                               rsvd[4];
            uint16_t                              max_size;
        } get_max_transfer_size;
        struct {
            uint8_t                               result; /*error_code*/
            uint16_t                              size;
            uint8_t                               bytes_remaining[3];
            uint8_t                               data[0];
        } read_file;
        struct {
            uint8_t                               result;
            uint8_t                               rsvd[5];
            uint8_t                               data[0];
        } write_file;
        struct {
            uint8_t                              result;
            uint8_t                              rsvd[5];
            uint8_t                              data[0];
        } get_fname;
        struct {
            uint8_t                              result;
            uint8_t                              rsvd[5];
            uint8_t                              data[0];
        } set_fname;
        struct {
            uint16_t                             win_cmd_specific;
            uint16_t                             data_len;
            uint8_t                              rsvd;
            uint8_t                              wlandeviceno;
            uint8_t                              data[0];
        } win_resp;
    }cmd;
} ftm_wlan_rsp_pkt_type;

void ftm_wlan_dispatch(ftm_wlan_req_pkt_type *wlan_ftm_pkt, unsigned int pkt_len, ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata);

#ifdef WIN_AP_HOST
void setBoardDataCaptureFlag (int flag);
void setDeviceId(int id);
extern ftm_wlan_rsp_pkt_type *win_bt_mac_flash_write(
       ftm_wlan_req_pkt_type *wlan_ftm_pkt,
       int pkt_len);

extern ftm_wlan_rsp_pkt_type *win_host_handle_fw_resp (void *data, uint32_t data_len);
extern ftm_wlan_rsp_pkt_type *win_host_handle_bdf_req(
       ftm_wlan_req_pkt_type *wlan_ftm_pkt, int pkt_len);
#endif


#endif /* FTM_WLAN_H_ */
