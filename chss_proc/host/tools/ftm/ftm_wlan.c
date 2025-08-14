/*==========================================================================

                     FTM WLAN Source File

* Copyright (c) 2018 Qualcomm Technologies, Inc.
* All Rights Reserved.
* Confidential and Proprietary - Qualcomm Technologies, Inc.

===========================================================================*/


#include <stdint.h>
#include <assert.h>
#include <linux/nl80211.h>
#include "ftm_wlan.h"
#include "shared/libtcmd.h"
#include "ftm_dbg.h"
#include "testcmd.h"



//value 1 means read/write bdf in dpp, value -1 mean read/write bdf in systerm32\drivers folder
#define BDF_IN_DPP      1
#define BDF_IN_SYSTEM  -1
#define BDF_IN_NONE     0

char bdf_file[MAX_FILE_PATH_SIZE] = {'\0'};
int  gReadWriteBdf = BDF_IN_SYSTEM;
int ifs_init[32]  = {FALSE};

char g_ifname[IFNAMSIZ];

#define MAX_RSP_DATA_SIZ  3*1024
char rsp_data[MAX_RSP_DATA_SIZ];
int rsp_len;


TCMD_ID tcmd = TCMD_CONT_RX_ID;
uint32_t mode = 0;

extern void DispHexString2(unsigned char *pkt_buffer, int recvsize);

#if 0
void print_uchar_array(unsigned char *pkt_buffer, int recvsize)
{
  int i, j, k;

  for (i=0; i<recvsize; i+=16) {
    printf("[%4.4d] ",i);
    for (j=i, k=0; (k<16) && ((j+k)<recvsize); k++)
      printf("0x%2.2X ",(pkt_buffer[j+k])&0xFF);
    for (; (k<16 ); k++)
      printf("     ");
    printf(" ");
    for (j=i, k=0; (k<16) && ((j+k)<recvsize); k++)
      printf("%c",(pkt_buffer[j+k]>32)?pkt_buffer[j+k]:'.');
    printf("\n");
  }
  printf("\n");
}
#endif
/*===========================================================================
FUNCTION   isResponseNeeded

DESCRIPTION
   Do we need a response for the command

DEPENDENCIES
  NIL

RETURN VALUE
  boolean response required/not

SIDE EFFECTS
  NONE

===========================================================================*/
static bool isResponseNeeded(void *buf)
{
   bool respNeeded = false;

   tcmd = * ((uint32_t *) buf);
   mode = * ((uint32_t *) buf + 1);


/// Insert commands which need response
   switch (tcmd)
   {
   case TC_CMD_TLV_ID:
      respNeeded = true;
      break;
   case TCMD_CONT_RX_ID:
      switch (mode)
      {
         case TCMD_CONT_RX_REPORT:
         case TCMD_CONT_RX_GETMAC:
            respNeeded = true;
         break;
      }
      break;
   case TC_CMDS_ID:
      switch (mode)
      {
         case TC_CMDS_READTHERMAL:
         case TC_CMDS_EFUSEDUMP:
         case TC_CMDS_EFUSEWRITE:
         case TC_CMDS_OTPSTREAMWRITE:
         case TC_CMDS_OTPDUMP:
	    respNeeded = true; //TC_CMDS_EFUSEDUMP, TC_CMDS_EFUSEWRITE, TC_CMDS_OTPSTREAMWRITE, TC_CMDS_OTPDUMP, TC_CMDS_READTHERMAL
         break;
      }
      break;
   default:
      break;
   }

   if (respNeeded)
   {
      DPRINTF(FTM_DBG_INFO,"response needed\n");
   } else
      DPRINTF(FTM_DBG_INFO,"response NOT needed\n");

   return respNeeded;
}

/*===========================================================================
FUNCTION   ftm_wlan_tcmd_rx

DESCRIPTION
   Call back handler

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
void ftm_wlan_tcmd_rx(void *buf, int len)
{
   DPRINTF(FTM_DBG_INFO, "Data length %04d\n", len);
   //DispHexString2(buf, len);
   memcpy(rsp_data, buf, len);
   rsp_len = len;
}

/*===========================================================================
FUNCTION   ftm_wlan_common_op

DESCRIPTION
  Process ftm commands like load driver, Tx, Rx and few test commands

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
static void ftm_wlan_common_op(ftm_wlan_req_pkt_type *wlan_ftm_pkt, int pkt_len, ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{
    uint32_t err_code = FTM_ERR_CODE_PASS;
    ftm_wlan_rsp_pkt_type *rsp = respdata;
    uint16_t rsp_pkt_len = 0;
    unsigned char *returnBuf = NULL;
    uint32_t rsp_data_len = 0;
    int data_len = pkt_len - DIAGPKT_COMMON_OP_CONTENT_START;
    char ifname[IFNAMSIZ];
    bool resp = true;

    rsp_pkt_len = sizeof(rsp->common_header) + sizeof(rsp->cmd.common_ops);     

    if (data_len <= 0) {
        DPRINTF(FTM_DBG_ERROR, "Invalid data_len: %d\n", data_len);
        err_code = FTM_ERR_CODE_INVALID_PARAMETER;
        goto ftm_ops_out;
    }

    snprintf(ifname, sizeof(ifname), "%s", g_ifname);

    DPRINTF(FTM_DBG_TRACE, "\nftm_daemon: Request Packet.ops->data Dump:\n");
    DispHexString2((uint8_t*)(wlan_ftm_pkt->cmd.common_ops.data), data_len);

    if (!ifs_init[wlan_ftm_pkt->cmd.common_ops.wlandeviceno])
    {
        DPRINTF(FTM_DBG_TRACE, "Initializing Interface: %s\n", ifname);

        if (tcmd_tx_init(ifname, ftm_wlan_tcmd_rx))
        {
            DPRINTF(FTM_DBG_ERROR, "Couldn't init tcmd transport!\n");
            err_code = FTM_ERR_CODE_IOCTL_FAIL;
            goto ftm_ops_out;
        }

        DPRINTF(FTM_DBG_TRACE, "tcmd: Initialized Interface: %s\n", ifname);
        ifs_init[wlan_ftm_pkt->cmd.common_ops.wlandeviceno] = TRUE;

        int ret = tcmd_tx_start();
        DPRINTF(FTM_DBG_TRACE, "tcmd: tcmd_tx_start done, ret = %d\n", ret);
    }

    returnBuf = (unsigned char *)&rsp->cmd.common_ops.data;

    resp = isResponseNeeded( (void*)wlan_ftm_pkt->cmd.common_ops.data);
    //resp = true;

    if (tcmd_tx(wlan_ftm_pkt->cmd.common_ops.data, data_len, resp))
    {
        DPRINTF(FTM_DBG_ERROR, "TCMD tx failed !\n");
        err_code = FTM_ERR_CODE_IOCTL_FAIL;
        goto ftm_ops_out;
    }

    err_code = FTM_ERR_CODE_PASS;

ftm_ops_out:
    rsp ->common_header.cmd_id = FTM_WLAN_COMMON_OP;
    rsp ->cmd.common_ops.rsvd = 0;
    rsp ->cmd.common_ops.result = err_code;
    rsp_data_len = rsp_len;

    if (err_code == FTM_ERR_CODE_PASS) {
        rsp_pkt_len += (uint16_t)rsp_data_len;
    } else{
        rsp_pkt_len += 1;    //need to send atleast 1 byte of data to diag in case of read failure
        memset(rsp->cmd.common_ops.data, 0, 1);
    }
    rsp ->common_header.cmd_rsp_pkt_size = rsp_pkt_len;

    *nrespdata = rsp_pkt_len;

    memcpy(returnBuf, rsp_data, rsp_data_len);

    DPRINTF(FTM_DBG_TRACE, "\ncommon_op resp msg dump:\n");
    DispHexString2((uint8_t *)rsp, (int)rsp_pkt_len);

    return;
}

/*===========================================================================
FUNCTION  ftm_wlan_bdf_read

DESCRIPTION
  Read the data from bdf_file

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
static void ftm_wlan_bdf_read(ftm_wlan_req_pkt_type *wlan_ftm_read_pkt, ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{
    FILE *fp = NULL;
    unsigned char err_code;
    int ret;
    uint32_t file_size = 0;
    uint32_t size = 0;  /*actual number of bytes transferred in resp pkt*/
    char *buf = NULL;
    struct stat st;
    int byte_rem = 0;
    uint16_t rsp_pkt_size = 0;
    ftm_wlan_rsp_pkt_type *ftm_read_resp = respdata;


    rsp_pkt_size = sizeof(ftm_read_resp->common_header) + sizeof(ftm_read_resp->cmd.read_file);

    if ((fp = fopen( bdf_file, "rb") )== NULL) {
        DPRINTF(FTM_DBG_ERROR, " failed to open file: %s\n", bdf_file);
        err_code = WLAN_BDF_FILE_OPEN_FAIL;
        goto ftm_read_out;
    }

    /*get size of the file*/
    if (stat(bdf_file, &st) == 0)
        file_size = st.st_size;
    else {
        DPRINTF(FTM_DBG_ERROR, "Failed to get file size \n");
        err_code = WLAN_BDF_FILE_STAT_FAIL;
        goto ftm_read_out;
    }
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: %s file size is: %u\n", bdf_file, file_size);
    if (file_size <= wlan_ftm_read_pkt->cmd.read_file.offset) {
        DPRINTF(FTM_DBG_ERROR, " Bad offset \n");
        err_code = WLAN_BDF_BAD_OFFSET;
        goto ftm_read_out;
    }

    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: offset: %d\n", wlan_ftm_read_pkt->cmd.read_file.offset);
    ret = fseek(fp, wlan_ftm_read_pkt->cmd.read_file.offset, SEEK_SET);
    if (ret != 0) {
        DPRINTF(FTM_DBG_ERROR, "fseek failed \n");
        err_code = WLAN_BDF_FILE_SEEK_FAIL;
        goto ftm_read_out;
    }

    /*validate the size(number of bytes) to be read from file */
    if ((uint32_t)(wlan_ftm_read_pkt->cmd_rsp_pkt_size - rsp_pkt_size) > (file_size - wlan_ftm_read_pkt->cmd.read_file.offset)) {
        size = file_size - wlan_ftm_read_pkt->cmd.read_file.offset;
    } else
        size = wlan_ftm_read_pkt->cmd_rsp_pkt_size - rsp_pkt_size;
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: number of bytes to be read: %d\n", size);

    buf = (char *)malloc(size);
    if(!buf) {
        DPRINTF(FTM_DBG_ERROR, " failed to allocate buf memory \n");
        err_code = WLAN_BDF_READ_FAILED;
        goto ftm_read_out;
    }
    ret = (int)fread(buf, 1, size, fp);
    if (ret ==(signed)size || feof(fp)) {
        size = ret;
        err_code = WLAN_BDF_READ_SUCCESS;
        rsp_pkt_size += (uint16_t)size;
    } else {
        DPRINTF(FTM_DBG_ERROR, "ftm_daemon: fread failed\n");
        err_code = WLAN_BDF_READ_FAILED;
    }

ftm_read_out:

    if (err_code == WLAN_BDF_READ_SUCCESS) {
        ftm_read_resp->cmd.read_file.size = (uint16_t)size;
        byte_rem = file_size - (size + wlan_ftm_read_pkt->cmd.read_file.offset);
        DPRINTF(FTM_DBG_TRACE, "ftm_daemon: byte_rem: %d\n", byte_rem);
        memcpy(ftm_read_resp->cmd.read_file.bytes_remaining, &byte_rem, sizeof(ftm_read_resp->cmd.read_file.bytes_remaining));
        memcpy(ftm_read_resp->cmd.read_file.data, buf, size);
    } else{
        rsp_pkt_size += 1;         //need to send atleast 1 byte of data to diag in case of read failure
        memset(ftm_read_resp->cmd.read_file.data, 0, 1);
    }
    ftm_read_resp->common_header.cmd_id = FTM_WLAN_BDF_READ;
    ftm_read_resp->common_header.cmd_rsp_pkt_size = rsp_pkt_size;
    ftm_read_resp->cmd.read_file.result = err_code;
    *nrespdata = rsp_pkt_size;
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: read resp msg dump:\n");
    DispHexString2((uint8_t *)ftm_read_resp, (int)rsp_pkt_size);

    if (fp)
        fclose(fp);
    if (buf)
        free(buf);
    return;
}

/*===========================================================================
FUNCTION  ftm_wlan_bdf_write

DESCRIPTION
  Write the data received from application to bdf_file

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
static void ftm_wlan_bdf_write(ftm_wlan_req_pkt_type *wlan_ftm_write_pkt, ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{
    FILE *fp = NULL;
    unsigned char err_code;
    int ret;
    ftm_wlan_rsp_pkt_type *ftm_write_resp = respdata;
    uint16_t rsp_pkt_len;

    rsp_pkt_len = sizeof(ftm_write_resp->common_header) + sizeof(ftm_write_resp->cmd.write_file) + 1;

    if (wlan_ftm_write_pkt->cmd.write_file.size > MAX_FTM_BDF_TX_SIZE) {
        DPRINTF(FTM_DBG_ERROR, " INVALID BDF file size!\n");
        err_code = WLAN_BDF_INVALID_SIZE;
        goto ftm_write_out;
    }

    if (wlan_ftm_write_pkt->cmd.write_file.size == 0) {
        DPRINTF(FTM_DBG_ERROR, " Write BDF file size is 0!\n");
        err_code = WLAN_BDF_WRITE_SUCCESS;
        goto ftm_write_out;
    }

    if (!wlan_ftm_write_pkt->cmd.write_file.append_flag) {
        DPRINTF(FTM_DBG_TRACE, "ftm_daemon: bdf_file = %s open in write mode\n", bdf_file);
        fp = fopen(bdf_file, "wb");
    } else {
        DPRINTF(FTM_DBG_TRACE, "ftm_daemon: bdf_file = %s open in append mode\n", bdf_file);
        fp = fopen( bdf_file, "ab");
    }
    if (fp == NULL) {
        DPRINTF(FTM_DBG_ERROR, " failed to open file: %s\n", bdf_file);
        err_code = WLAN_BDF_FILE_OPEN_FAIL;
        goto ftm_write_out;
    }

    ret = (int)fwrite(&(wlan_ftm_write_pkt->cmd.write_file.data), 1, wlan_ftm_write_pkt->cmd.write_file.size, fp);
    if (ferror(fp)) {
        DPRINTF(FTM_DBG_ERROR, " failed to write %d\n", ret);
        err_code = WLAN_BDF_WRITE_FAILED;
    } else
        err_code = WLAN_BDF_WRITE_SUCCESS;

ftm_write_out:
    if (fp)
        fclose(fp);
    ftm_write_resp->common_header.cmd_id = FTM_WLAN_BDF_WRITE;
    ftm_write_resp->common_header.cmd_rsp_pkt_size = rsp_pkt_len;
    ftm_write_resp->cmd.write_file.result = err_code;
    memset(ftm_write_resp->cmd.write_file.rsvd, 0,
           sizeof(ftm_write_resp->cmd.write_file.rsvd));
    memset(ftm_write_resp->cmd.write_file.data, 0, 1);
    *nrespdata = rsp_pkt_len;
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: write resp msg dump:\n");
    DispHexString2((uint8_t *)ftm_write_resp, (int)rsp_pkt_len);

    return;
}

/*===========================================================================
FUNCTION  ftm_wlan_bdf_get_filename

DESCRIPTION
  Get bdf_file path

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
static void ftm_wlan_bdf_get_filename(ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{
    ftm_wlan_rsp_pkt_type *ftm_get_fname_resp = respdata;
    uint16_t rsp_pkt_len;
    int fname_len = 1;  //allocate 1 byte of data in case of error
    unsigned char err_code;

    rsp_pkt_len = sizeof(ftm_get_fname_resp->common_header) +  sizeof(ftm_get_fname_resp->cmd.get_fname);

    if (bdf_file[0] != '\0' && strlen(bdf_file) < MAX_FILE_PATH_SIZE)
    {
        fname_len = (int)strlen(bdf_file);
        DPRINTF(FTM_DBG_TRACE, "ftm_daemon: bdf_file is  %s\n", bdf_file);
        err_code = WLAN_BDF_PATH_GET_SUCCESS;
        memcpy(ftm_get_fname_resp->cmd.get_fname.data, bdf_file, fname_len);
    }
    else
    {
        DPRINTF(FTM_DBG_TRACE, "ftm_daemon: get_filename failed: bdf_file:%s fname_len: %zu\n", bdf_file, bdf_file[0]?strlen(bdf_file):0);
        err_code = WLAN_BDF_PATH_GET_FAILED;
        memset(ftm_get_fname_resp->cmd.get_fname.data, 0, 1);
    }
    rsp_pkt_len += (uint16_t)fname_len;

    ftm_get_fname_resp->common_header.cmd_id = FTM_WLAN_BDF_GET_FNAMEPATH;
    ftm_get_fname_resp->common_header.cmd_rsp_pkt_size = rsp_pkt_len;
    memset(ftm_get_fname_resp->cmd.get_fname.rsvd, 0, sizeof(ftm_get_fname_resp->cmd.get_fname.rsvd));
    ftm_get_fname_resp->cmd.get_fname.result = err_code;
    *nrespdata = rsp_pkt_len;
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: get_filename resp msg dump:\n");
    DispHexString2((uint8_t *)ftm_get_fname_resp, (int)rsp_pkt_len);

    return;
}

/*===========================================================================
FUNCTION  ftm_wlan_bdf_set_filename

DESCRIPTION
  Set bdf_file path for further bdf file read/write operation

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
static void ftm_wlan_bdf_set_filename(ftm_wlan_req_pkt_type *wlan_ftm_set_fname_pkt, ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{
    ftm_wlan_rsp_pkt_type *ftm_set_fname_resp = NULL;
    uint16_t rsp_pkt_len;
    uint16_t size;
    unsigned char err_code;

    rsp_pkt_len = sizeof(ftm_set_fname_resp->common_header) + sizeof(ftm_set_fname_resp->cmd.set_fname);
    size =  wlan_ftm_set_fname_pkt->cmd_data_len - rsp_pkt_len;
    rsp_pkt_len += 1;   //for 1 byte of reserved data

    ftm_set_fname_resp->common_header.cmd_id = FTM_WLAN_BDF_SET_FNAMEPATH;

    if (size == 0 || size >= MAX_FILE_PATH_SIZE) {
        DPRINTF(FTM_DBG_ERROR, "ftm_daemon: set_filename failed: fname_length %d\n", size);
        bdf_file[0] = '\0';
        gReadWriteBdf = BDF_IN_NONE;
        err_code = WLAN_BDF_PATH_SET_FAILED;
    } else {
        memcpy(bdf_file,  wlan_ftm_set_fname_pkt->cmd.set_fname.data, size);
        bdf_file[size] = '\0';
        if (strcasecmp(bdf_file, "\\DPP\\QCOM\\WLAN_CLPC.PROVISION") == 0)
        {
            DPRINTF(FTM_DBG_INFO, "ftm_daemon: set dpp bdf path:%s\n", bdf_file);
            gReadWriteBdf = BDF_IN_DPP;
            err_code = WLAN_BDF_PATH_SET_SUCCESS;
        }
        else if (strncasecmp(bdf_file, "\\windows\\system32\\", 18) == 0)
        {
            DPRINTF(FTM_DBG_INFO, "ftm_daemon: set bdf path:%s\n", bdf_file);
            gReadWriteBdf = BDF_IN_SYSTEM;
            err_code = WLAN_BDF_PATH_SET_SUCCESS;
        }
        else
        {   
            DPRINTF(FTM_DBG_ERROR, "ftm_daemon: unsupported bdf path:%s\n", bdf_file);
            DPRINTF(FTM_DBG_ERROR, "ftm_daemon: support dpp path:%s\n", "\\DPP\\QCOM\\WLAN_CLPC.PROVISION");
            DPRINTF(FTM_DBG_ERROR, "ftm_daemon: support path:%s\n", "\\windows\\system32\\xxx.bin");
            DPRINTF(FTM_DBG_ERROR, "ftm_daemon: support path:%s\n", "\\windows\\system32\\drivers\\xxx.bin");
            gReadWriteBdf = BDF_IN_NONE;
            err_code = WLAN_BDF_PATH_SET_FAILED;
        }
    }

    ftm_set_fname_resp->common_header.cmd_rsp_pkt_size = rsp_pkt_len;
    ftm_set_fname_resp->cmd.set_fname.result = err_code;
    memset(ftm_set_fname_resp->cmd.set_fname.rsvd, 0, sizeof(ftm_set_fname_resp->cmd.set_fname.rsvd));
    memset(ftm_set_fname_resp->cmd.set_fname.data, 0, 1);
    *nrespdata= rsp_pkt_len;
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: set_filename resp msg dump:\n");
    DispHexString2((uint8_t *)ftm_set_fname_resp, (int)rsp_pkt_len);

    return;
}

/*===========================================================================
FUNCTION   ftm_wlan_bdf_get_max_transfer_size

DESCRIPTION
  Get maximum transfer size(in bytes) for further bdf file read/write operation

DEPENDENCIES
  NIL

RETURN VALUE
  NONE

SIDE EFFECTS
  NONE

===========================================================================*/
static void ftm_wlan_bdf_get_max_transfer_size(ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{
    ftm_wlan_rsp_pkt_type *ftm_get_max_size_resp = respdata;
    uint16_t rsp_pkt_len;

    rsp_pkt_len = sizeof(ftm_get_max_size_resp->common_header) + sizeof(ftm_get_max_size_resp->cmd.get_max_transfer_size);

    ftm_get_max_size_resp->common_header.cmd_id = FTM_WLAN_BDF_GET_MAX_TRANSFER_SIZE;
    ftm_get_max_size_resp->common_header.cmd_rsp_pkt_size = rsp_pkt_len;
    ftm_get_max_size_resp->cmd.get_max_transfer_size.max_size = MAX_FTM_BDF_TX_SIZE;
    ftm_get_max_size_resp->cmd.get_max_transfer_size.result = 0;
    memset(ftm_get_max_size_resp->cmd.get_max_transfer_size.rsvd, 0,
           sizeof(ftm_get_max_size_resp->cmd.get_max_transfer_size.rsvd));
    *nrespdata = rsp_pkt_len;
    DPRINTF(FTM_DBG_TRACE, "ftm_daemon: get_max_transfer_size resp msg dump:\n");
    DispHexString2((uint8_t *)ftm_get_max_size_resp, (int)rsp_pkt_len);

    return;
}

/*===========================================================================
FUNCTION   ftm_wlan_dispatch

DESCRIPTION
  WLAN FTM dispatch routine. Main entry point routine for WLAN FTM

DEPENDENCIES
  NIL

RETURN VALUE
  Returns back buffer that is meant to be passed to the diag callback

SIDE EFFECTS
  NONE

===========================================================================*/
void ftm_wlan_dispatch(ftm_wlan_req_pkt_type *wlan_ftm_pkt, unsigned int pkt_len, ftm_wlan_rsp_pkt_type *respdata, unsigned int *nrespdata)
{

    if (!wlan_ftm_pkt || !pkt_len || !respdata || !nrespdata) {
        DPRINTF(FTM_DBG_ERROR, "Invalid ftm wlan Requst Packet\n");
        assert(0);
        return;
    }

    respdata->common_header.cmd_code        = wlan_ftm_pkt->cmd_code;
    respdata->common_header.subsys_id       = wlan_ftm_pkt->subsys_id;    
    respdata->common_header.subsys_cmd_code = wlan_ftm_pkt->subsys_cmd_code;
    respdata->common_header.cmd_id          = wlan_ftm_pkt->cmd_id;
    respdata->common_header.cmd_data_len    = 0;

    if (wlan_ftm_pkt->cmd_id >= FTM_WLAN_CMD_CODE_MAX)
    {
        DPRINTF(FTM_DBG_ERROR, " Unknown Command\n");
        respdata->common_header.cmd_rsp_pkt_size = (uint16_t)pkt_len;
        *nrespdata= pkt_len;
        return;
    }
    DPRINTF(FTM_DBG_TRACE, "\nRequest Packet Dump:\n");
    DispHexString2((uint8_t *)wlan_ftm_pkt, pkt_len);

    switch (wlan_ftm_pkt->cmd_id) {
    case FTM_WLAN_COMMON_OP:
        ftm_wlan_common_op(wlan_ftm_pkt, pkt_len, respdata, nrespdata);
        break;
    case FTM_WLAN_BDF_GET_MAX_TRANSFER_SIZE:
        ftm_wlan_bdf_get_max_transfer_size(respdata, nrespdata);
        break;
    case FTM_WLAN_BDF_READ:
        ftm_wlan_bdf_read(wlan_ftm_pkt, respdata, nrespdata);
        break;
    case FTM_WLAN_BDF_WRITE:
        ftm_wlan_bdf_write(wlan_ftm_pkt, respdata, nrespdata);
        break;
    case FTM_WLAN_BDF_GET_FNAMEPATH:
        ftm_wlan_bdf_get_filename(respdata, nrespdata);
        break;
    case FTM_WLAN_BDF_SET_FNAMEPATH:
        ftm_wlan_bdf_set_filename(wlan_ftm_pkt, respdata, nrespdata);
        break;
    default:
        {
            DPRINTF(FTM_DBG_ERROR, " Unknown Command\n");
            respdata->common_header.cmd_rsp_pkt_size = (uint16_t)pkt_len;
            *nrespdata= pkt_len;
        }
        break;
    }

    return;
}


