#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <string.h>
#include <assert.h>
#include <getopt.h>
#include <stdint.h>
#include <net/if.h>
#include <assert.h>
#include <signal.h>
#include <unistd.h>
#include <bsd/string.h>

#include "shared/Socket.h"
#include "ftm_wlan.h"
#include "ftm_dbg.h"

static char *progname = NULL;
int running;
unsigned int g_dbg_level = FTM_DBG_TRACE | FTM_DBG_INFO | FTM_DBG_ERROR;

#define MBUFFER 1024*4
#define DIAG_MAX_RSP_SIZ  3*1024

#define MCLIENT 3

static struct _Socket *_ListenSocket;   // this is the socket on which we listen for client connections

static struct _Socket *_ClientSocket[MCLIENT];  // these are the client sockets

#define MCOMMAND 50

static int _CommandNext=0;      // index of next command to perform
static int _CommandRead=0;      // index of slot for next command read from socket

static char *_Command[MCOMMAND];
//static char _CommandClient[MCOMMAND];

#define DIAG_TERM_CHAR 0x7E
#define DIAG_TAIL_LEN     3

#define AHDLC_FLAG    0x7E   // Flag byte in Async HDLC
#define AHDLC_ESCAPE  0x7D   // Escape byte in Async HDLC
#define AHDLC_ESC_M   0x20   // Escape mask in Async HDLC

#define MAX_HS_WIDTH    16/2

enum CmdCode
{
    version = 0x0,
    esn = 0x1,
    status = 0xC,
    nvItemRead = 0x26,
    phoneState = 0x3F,
    subSystemDispatch = 0x4B,
    featureQuery = 0x51,
    embeddedFileOperation = 0x59,
    diagProtLoopback = 0x7B,
    extendedBuildID = 0x7C
};

enum SubsystemID
{
    DIAG_SUBSYS_FTM  = 11, /* Factory Test Mode */
};

// List of responses
unsigned char verResponseMsg[] = {
    version,                        //CMD_CODE (0)
    0x4F, 0x63, 0x74, 0x20, 0x30, 0x38,
    0x20, 0x32, 0x30, 0x31, 0x31,       //COMP_DATE (Compilation date)
    0x31, 0x30, 0x3A, 0x30, 0x37, 0x3A,
    0x30, 0x30,                      //COMP_TIME
    0x4F, 0x63, 0x74, 0x20, 0x30, 0x38,
    0x20, 0x32, 0x30, 0x31, 0x31,       //REL_DATE (Compilation date)
    0x31, 0x30, 0x3A, 0x30, 0x37, 0x3A,
    0x30, 0x30,                      //REL_TIME
    0x41, 0x41, 0x41, 0x31, 0x30,
    0x30, 0x30, 0x30,                 //VER_DIR
    0,                              //SCM
    1,                              //MOB_CAL_REV
    255,                            //MOB_MODEL
    1, 0,                            //MOB_FIRM_REV
    0,                              //SLOT_CYCLE_INDEX
    1, 0                            //MSM_VER
};
unsigned char esnResponseMsg[] = {
    esn,                            //CMD_CODE (1)
    0xEF, 0xBE, 0xAD, 0xDE             //ESN
};
unsigned char statusResponseMsg[] = {
    status,                 //CMD_CODE (12) 1
    0, 0, 0,                //RESERVED 3
    0xce, 0xfa, 0xbe, 0xba, //ESN 4
    6, 0,                   //RF_MODE 2
    0, 0, 0, 0,             //MIN1 (Analog) 4
    0, 0, 0, 0,             //MIN1 (CDMA) 4
    0, 0,                   //MIN2 (Analog) 2
    0, 0,                   //MIN2 (CDMA) 2
    0,                      //RESERVED 1
    0, 0,                   //CDMA_RX_STATE 2
    0xff,                   //CDMA_GOOD_FRAMES 1
    0, 0,                   //ANALOG_CORRECTED_FRAMES 2
    0, 0,                   //ANALOG_BAD_FRAMES 2
    0, 0,                   //ANALOG_WORD_SYNCS 2 
    0, 0,                   //ENTRY_REASON 2
    0, 0,                   //CURRENT_CHAN 2
    0,                      //CDMA_CODE_CHAN 1
    0, 0,                   //PILOT_BASE 2
    0, 0,                   //SID 2
    0, 0,                   //NID 2
    0, 0,                   //LOCAID 2
    0, 0,                   //RSSI 2
    0                       //POWER  1                                     

};
unsigned char nvItemReadResponseMsg[] = {
    nvItemRead,             // CMD_CODE (0x26)
    71, 0,                  //NV_ITEM
    0x4E, 0x41, 0x52, 0x54,    // ITEM_DATA
    0x5F, 0x41, 0x50, 0x2F,
    0x4D, 0x6F, 0x62, 0x0,
    0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0                     // STATUS
};
unsigned char phoneStateResponseMsg[] = {
    phoneState,                     //CMD_CODE (0x3F)
    0x1,                            //PHONE_STATE
    0x0, 0x0                         //EVENT_COUNT
};
unsigned char featureQueryRespMsg[] = {
    featureQuery,
    0, 0,
    0
};
unsigned char extendedBuildIDRespMsg[] = {
    extendedBuildID,        // CMD_CODE (0x7C)
    2,                      // Version
    0, 0,                    // Reserved
    0xE8, 0x3, 0, 0,           // MSM Revision (assigned to 1000)
    1, 0x40, 0, 0,             // Manufacturer model number (assigned to 4001)
    0x31, 0,                 // Softwareversion (ascii value of 1)
    0x4E, 0x41, 0x52, 0x54, 0x5F,
    0x41, 0x50, 0x2F, 0x4D, 0x6F,
    0x62, 0x0                // Model string (NART_AP/Mob)
};

int ClientAccept()
{
    int it;
    int noblock;
    struct _Socket *TryClientSocket;
    static int OldestClient = 0;

    if(_ListenSocket!=0)
    {
        //
        // If we have no clients, we will block waiting for a client.
        // Otherwise, just check and go on.
        //
        noblock=0;
        for(it=0; it<MCLIENT; it++)
        {
            if(_ClientSocket[it]!=0)
            {
                noblock=1;
                break;
            }
        }
        if(noblock==0)
        {
            printf("\nReady for Client(QDart) Connection!\n" );
        }
        //
        // Look for new client
        //
        for(it=0; it<MCLIENT; it++)
        {
            if(_ClientSocket[it]==0)
            {
                _ClientSocket[it]=SocketAccept(_ListenSocket,noblock);// don't block
                if(_ClientSocket[it]!=0)
                {
                    printf("Client connection is established at [%d]!\n",it);
                    return it;
                }
            }
        }
        // In case all clients have been used up, but there is another client want to connect, give away the oldest one
        if (it == MCLIENT)
        {
            TryClientSocket = SocketAccept(_ListenSocket,noblock);
            if (TryClientSocket)
            {
                SocketClose(_ClientSocket[OldestClient]);
                _ClientSocket[OldestClient] = TryClientSocket;

                return it;
            }
        }
    }
    return -1;
}

static unsigned short Calc_CRC_16_l(unsigned char* pBufPtr, int bufLen)
{
    /* 
        The CRC table size is based on how many bits at a time we are going
        to process through the table.  Given that we are processing the data
        8 bits at a time, this gives us 2^8 (256) entries.
    */
    //const int c_iCRC_TAB_SIZE = 256;	// 2^CRC_TAB_BITS


    /* CRC table for 16 bit CRC, with generator polynomial 0x8408,
    ** calculated 8 bits at a time, LSB first.
    */
    unsigned short _aCRC_16_L_Table[] = 
    {
        0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
        0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
        0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
        0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
        0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
        0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
        0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
        0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
        0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
        0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
        0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
        0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
        0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
        0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
        0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
        0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
        0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
        0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
        0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
        0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
        0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
        0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
        0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
        0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
        0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
        0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
        0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
        0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
        0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
        0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
        0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
        0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78
    };

    /* - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */

    /* Mask for CRC-16 polynomial:
    **
    **      x^16 + x^12 + x^5 + 1
    **
    ** This is more commonly referred to as CCITT-16.
    ** Note:  the x^16 tap is left off, it's implicit.
    */
    const unsigned short c_iCRC_16_L_POLYNOMIAL = 0x8408;

    /* Seed value for CRC register.  The all ones seed is part of CCITT-16, as
    ** well as allows detection of an entire data stream of zeroes.
    */
    const unsigned short c_iCRC_16_L_SEED = 0xFFFF;


    unsigned short data, crc_16;

    /* 
        Generate a CRC-16 by looking up the transformation in a table and
        XOR-ing it into the CRC, one byte at a time.
    */
    int i = 0;
    int iLen = bufLen * 8;

    for (crc_16 = c_iCRC_16_L_SEED; iLen >= 8; iLen -= 8, i++)
    {
//        temp1 = (crc_16 ^ pBufPtr[i]);
//        temp1 = temp1 & 0x00ff;
//        temp2 = (crc_16 >> 8) & 0xff;
//        crc_16 = (short)(_aCRC_16_L_Table[temp1] ^ temp2);
        crc_16 = (unsigned short)(_aCRC_16_L_Table[(crc_16 ^ pBufPtr[i]) & 0x00ff] ^ (crc_16 >> 8));
    }

    /* 
        Finish calculating the CRC over the trailing data bits
  
        XOR the MS bit of data with the MS bit of the CRC.
        Shift the CRC and data left 1 bit.
        If the XOR result is 1, XOR the generating polynomial in with the CRC.
    */
    if (iLen != 0)
    {

        data = (unsigned short)(((unsigned short)(pBufPtr[i])) << (16 - 8));  // Align data MSB with CRC MSB

        while (iLen-- != 0)
        {
            if (((crc_16 ^ data) & 0x01) != 0)
            {                                       // Is LSB of XOR a 1

                crc_16 >>= 1;                       // Right shift CRC
                crc_16 ^= c_iCRC_16_L_POLYNOMIAL;   // XOR polynomial into CRC

            }
            else
            {

                crc_16 >>= 1;                        // Right shift CRC

            }  // if ( ((crc_16 ^ data) & 0x01) != 0 )

            data >>= 1;                             // Right shift data

        }   // while (iLen-- != 0)

    }// if (iLen != 0) {

    return ((unsigned short)~crc_16);            // return the 1's complement of the CRC

}

static unsigned int TrimDiagPacket(unsigned char *inputMsg, int cmdLen)
{
    int i = 0,j = 0;
    int startPktContent = DIAGPKT_COMMON_OP_CONTENT_START;
    int ESCAPEcnt=0;
    unsigned char tempBuf[MBUFFER] = {0};


    if (cmdLen > MBUFFER) {
        assert(0);
        return 0;
    }
    //copy common header and RSVD data (12+4)
    for (i = 0; i < startPktContent; i++) {
        tempBuf[i] = inputMsg[i];
    }

    //strip out any esc characters as go
    for (i = startPktContent, j=startPktContent; j < cmdLen; i++, j++) {
            //look to see if there are any esc characters we need to remove
            if(inputMsg[j] == AHDLC_ESCAPE) {
                //skip this character
                j++;
                //next character needs xor
                tempBuf[i] = inputMsg[j] ^ AHDLC_ESC_M;
                ESCAPEcnt++;
            }
            else {
                tempBuf[i] = inputMsg[j];
            }
    }
    memcpy(inputMsg ,  tempBuf, cmdLen);
    inputMsg[i - DIAG_TAIL_LEN] = 0;
    return ESCAPEcnt;
}

static unsigned int PaddingDiagPacket(unsigned char *outputMsg, int cmdLen)
{
    int i = 0,j = 0;
    int ESCAPEcnt=0;
    unsigned char tempBuf[DIAG_MAX_RSP_SIZ] = {0};


    if (cmdLen > DIAG_MAX_RSP_SIZ) {
        assert(0);
        return 0;
    }

    memcpy(tempBuf , outputMsg, cmdLen);

    for ( i = 0,j = 0; i < cmdLen; i++,j++ )
    {
        if( ( tempBuf[i] == AHDLC_ESCAPE ) || ( tempBuf[i] == AHDLC_FLAG ) )
        {
            // add esc character in front of this char and increase pktLen by 1
            outputMsg[j++] = AHDLC_ESCAPE;
            outputMsg[j] = tempBuf[i] ^ AHDLC_ESC_M;
            ESCAPEcnt++;
        }
        else
        {
            outputMsg[j] = tempBuf[i];
        }
    }
    return ESCAPEcnt;
}

#define INITIAL_BUF_SIZE      512
#define MIN_THRESHOLD         8
#define PRINTABLE(x)          ((x) > 31 && (x) < 128)
int bufferAdjustCheck(int *pRemain, int *pBufsz, char **pBuf)
{
  int remain, bufsz;
  char *buf;

  remain = *pRemain;
  buf = *pBuf;
  if (remain < MIN_THRESHOLD) {
    bufsz = *pBufsz + INITIAL_BUF_SIZE;
    buf = realloc(buf, bufsz);
    if (!buf)
          return -1;

    remain += INITIAL_BUF_SIZE;
    *pRemain = remain;
    *pBuf = buf;
    *pBufsz = bufsz;
  }

  return 0;
}

void DispHexString2(unsigned char *pkt_buffer, int recvsize)
{
  char *buf;
  int i, j, k;
  int pos, bufsz, remain;

  bufsz = INITIAL_BUF_SIZE;
  remain = bufsz;
  pos = 0;

  buf = (char *)calloc(INITIAL_BUF_SIZE, sizeof(char));
  if (!buf) {
    perror("fail to calloc");
    return;
  }
  //printf("recvsize %d\n", recvsize);
  for (i = 0; i < recvsize; i += MAX_HS_WIDTH) {
    pos += snprintf(buf + pos, remain, "\n[%4.4d] ", i);
    remain = bufsz - pos;
    if (bufferAdjustCheck(&remain, &bufsz, &buf))
        return;
    for (j = i, k = 0; (k < MAX_HS_WIDTH) && ((j+k) < recvsize); k++) { 
      pos += snprintf(buf + pos, remain, "0x%2.2X ", (pkt_buffer[j+k])&0xFF);
      remain = bufsz - pos;
      if (bufferAdjustCheck(&remain, &bufsz, &buf))
        return;
      }
    for (; (k < MAX_HS_WIDTH); k++) {
      pos += snprintf(buf + pos, remain, "%s", "     ");
      remain = bufsz - pos;
      if (bufferAdjustCheck(&remain, &bufsz, &buf))
        return;
    }
    pos += snprintf(buf + pos, remain, "%s", " ");
    remain = bufsz - pos;
    if (bufferAdjustCheck(&remain, &bufsz, &buf))
      return;
    for (j = i, k = 0; (k < MAX_HS_WIDTH) && ((j + k) < recvsize); k++) {
      pos += snprintf(buf + pos, remain, "%c", PRINTABLE(pkt_buffer[j + k]) ? pkt_buffer[j + k] : '.');
      remain = bufsz - pos;
      if (bufferAdjustCheck(&remain, &bufsz, &buf))
        return;
    }
  }

  printf("%s\n", buf);
  free(buf);
  return;
}

void DispHexString(unsigned char *pkt_buffer, int recvsize)
{
  int i, j, k;

  printf("\n");
  for (i=0; i<recvsize; i+=MAX_HS_WIDTH) {
    printf("[%4.4d] ",i);
    for (j=i, k=0; (k<MAX_HS_WIDTH) && ((j+k)<recvsize); k++)
      printf("0x%2.2X ",(pkt_buffer[j+k])&0xFF);
    for (; (k<MAX_HS_WIDTH ); k++)
      printf("     ");
    printf(" ");
    for (j=i, k=0; (k<MAX_HS_WIDTH) && ((j+k)<recvsize); k++)
      printf("%c",(pkt_buffer[j+k]>32)?pkt_buffer[j+k]:'.');
    printf("\n");
  }
}

static void ClientClose(int client)
{
    if(client>=0 && client<MCLIENT && _ClientSocket[client]!=0)
    {
        SocketClose(_ClientSocket[client]);
        _ClientSocket[client]=0;
    }
}

int SocketSend(int client, unsigned char *buffer, int length)
{
    int nwrite;

    if(_ListenSocket==0|| (client>=0 && client<MCLIENT && _ClientSocket[client]!=0))
    {
        if ( _ListenSocket == 0 )
        {
            //DbgPrintf("%s",response);
        }
        else
        {
            nwrite=SocketWrite(_ClientSocket[client],buffer,length);

            if(nwrite<0)
            {
                DPRINTF(FTM_DBG_ERROR, "Error - Call to SocketWrite() failed.\n" );
                ClientClose(client);
                return -1;
            }
        }
        return 0;
    }
    else
    {
        return -1;
    }

}

static void RspAssemble(unsigned char *inputMsg, unsigned int length, unsigned char *respdata, unsigned int *nrespdata) 
{
    unsigned int i;

    for (i = 0; i < length; i++)
    {
        respdata[i] = inputMsg[i];
    }

    *nrespdata = length;
}

static int processWlanDiagPacket(unsigned char *inputMsg, unsigned int length, unsigned char *respdata, unsigned int *nrespdata)
{
    ftm_wlan_req_pkt_type *ftm_wlan_diag_req  = (ftm_wlan_req_pkt_type *)inputMsg;

    if (!inputMsg)
    {
        DPRINTF(FTM_DBG_ERROR, "inputMsg is NULL\n");
        return 0;
    }

    switch (ftm_wlan_diag_req->cmd_code)
    {
        case version:
            DPRINTF(FTM_DBG_INFO, "echo for version \n");
            RspAssemble(verResponseMsg, sizeof(verResponseMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        case esn:
            DPRINTF(FTM_DBG_INFO, "echo for esn\n");
            RspAssemble(esnResponseMsg, sizeof(esnResponseMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        case status:
            DPRINTF(FTM_DBG_INFO, "echo for status\n");
            RspAssemble(statusResponseMsg, sizeof(statusResponseMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        case phoneState:
            DPRINTF(FTM_DBG_INFO, "echo for phoneState\n");
            RspAssemble(phoneStateResponseMsg, sizeof(phoneStateResponseMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        case nvItemRead:
            DPRINTF(FTM_DBG_INFO, "echo for nvItemRead\n");
            RspAssemble(nvItemReadResponseMsg, sizeof(nvItemReadResponseMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        case subSystemDispatch:
            if ((DIAG_SUBSYS_FTM != ftm_wlan_diag_req->subsys_id)||
                (FTM_WLAN_CMD_CODE != ftm_wlan_diag_req->subsys_cmd_code))
            {
                DPRINTF(FTM_DBG_ERROR, "Can't support FTMSubsystem subsys_id %d subsys_cmd_code %d !\n",
                ftm_wlan_diag_req->subsys_id, ftm_wlan_diag_req->subsys_cmd_code);
                DPRINTF(FTM_DBG_ERROR, "FTMSubsystem message not processed. Just echo back the message\n");
                RspAssemble(inputMsg, length, respdata, nrespdata);
                break;
            }
            
            ftm_wlan_dispatch(ftm_wlan_diag_req, length, (ftm_wlan_rsp_pkt_type *)respdata, nrespdata);
        
            break;
        case featureQuery:
            DPRINTF(FTM_DBG_INFO, "echo for featureQuery\n");
            RspAssemble(featureQueryRespMsg, sizeof(featureQueryRespMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        case embeddedFileOperation:
            DPRINTF(FTM_DBG_INFO, "echo for embeddedFileOperation\n");
            RspAssemble(inputMsg, length, respdata, nrespdata);
            break;
        case diagProtLoopback:
            DPRINTF(FTM_DBG_INFO, "echo for diagProtLoopback\n");
            RspAssemble(inputMsg, length, respdata, nrespdata);
            break;
        case extendedBuildID:
            DPRINTF(FTM_DBG_INFO, "echo for extendedBuildID\n");
            RspAssemble(extendedBuildIDRespMsg, sizeof(extendedBuildIDRespMsg) / sizeof(unsigned char), respdata, nrespdata);
            break;
        default:
            DPRINTF(FTM_DBG_ERROR, "echo for UNKNOWN ID %d!\n", ftm_wlan_diag_req->cmd_code);
            RspAssemble(inputMsg, length, respdata, nrespdata);
            break;
    }

    return 1;
}

int SocketSendRsp(int client, unsigned char *RspBuffer, int RespLen)
{
    unsigned int ESCAPEcnt=0;
    unsigned short crc = 0;

    DPRINTF(FTM_DBG_INFO, "Raw DiagPacket resp len %d \n", RespLen);
    crc = Calc_CRC_16_l(RspBuffer, RespLen);
    RspBuffer[RespLen + 0] = (char)(crc & 0xff);
    RspBuffer[RespLen + 1] = (char)(crc >> 8);
    ESCAPEcnt = PaddingDiagPacket(RspBuffer, (RespLen+2));
    DPRINTF(FTM_DBG_INFO, "ESCAPEcnt %d \n", ESCAPEcnt);
    if((RespLen+ESCAPEcnt+2) > DIAG_MAX_RSP_SIZ)
        DPRINTF(FTM_DBG_ERROR, " Padding Resp message too large %d !\n", (RespLen+ESCAPEcnt+2));
        
    RspBuffer[RespLen+ESCAPEcnt+2] = DIAG_TERM_CHAR;

    return SocketSend(client, RspBuffer, RespLen+ESCAPEcnt+DIAG_TAIL_LEN);
}

void CommandRead()
{
    unsigned char buffer[MBUFFER];
    unsigned char RspBuffer[DIAG_MAX_RSP_SIZ];
    int nread;
    //int ntotal;
    int it;
    int diagPacketReceived = 0;
    unsigned int cmdLen = 0;
    unsigned int RespLen = DIAG_MAX_RSP_SIZ - DIAG_TAIL_LEN;
    unsigned int ESCAPEcnt=0;
    

    //
    // look for new clients
    //
    ClientAccept();
    //
    // try to read everything on the client socket
    //
    //ntotal=0;
    while(_CommandNext!=_CommandRead || _Command[_CommandRead]==0)
    {
        if(_ListenSocket==0)
        {
        }
        else
        {
            //
            // read commands from each client in turn
            //
            for(it=0; it<MCLIENT; it++)
            {
                if(_ClientSocket[it]!=0)
                {
                    nread = (int)SocketRead(_ClientSocket[it],buffer,MBUFFER-1);
                    if(nread>0)
                    {
                        DPRINTF(FTM_DBG_TRACE, "SocketRead() return %d bytes\n", nread);
                        DispHexString2(buffer,nread);

                        diagPacketReceived = 0;
                        cmdLen = 0;
                        if ((nread>1) && (buffer[nread-1]==DIAG_TERM_CHAR))
                        {
                            diagPacketReceived = 1;
                            buffer[nread-1]=0;
                            cmdLen = nread-0;
                        }
                        //Needed for linux path
                        if ((nread>2) && (buffer[nread-2]==DIAG_TERM_CHAR))
                        {
                            diagPacketReceived = 1;
                            buffer[nread-2]=0;
                            cmdLen = nread - 1;
                        }
                        //
                        // check to see if we received a diag packet
                        //
                        if ((diagPacketReceived) && (cmdLen > 0)) {
                            ESCAPEcnt = TrimDiagPacket(buffer, cmdLen);
                            if(processWlanDiagPacket((unsigned char *)buffer, cmdLen-ESCAPEcnt-DIAG_TAIL_LEN, RspBuffer, &RespLen)) {
                                DPRINTF(FTM_DBG_INFO, "--processDiagPacket-succeed------ Wait For Next Diag Packet ----------------\n\n");
                            }
                            else
                            {
                                DPRINTF(FTM_DBG_INFO, "--processDiagPacket-failed------- Wait For Next Diag Packet ----------------\n\n");
                            }
                            if (RespLen > (DIAG_MAX_RSP_SIZ - DIAG_TAIL_LEN)) {
                                DPRINTF(FTM_DBG_ERROR, " Resp message too large needs to be less than %d [%d]!\n", DIAG_MAX_RSP_SIZ - DIAG_TAIL_LEN, RespLen);
                                continue;
                            }

                            SocketSendRsp(it, RspBuffer, RespLen);
                        }
                    }
                    else if(nread<0)
                    {
                        printf("Closing connection <-- Remote connection closed.\n");
                        ClientClose(it);
                        exit(1);
                    }
                }
            }
        }
    }
    return ; //ntotal;
}

void ftm_wlan_run(int port)
{
    if(port <= 0){
        printf("wrong port!\n");
        exit(-1);
    }

    _ListenSocket = SocketListen(port);

    if(!_ListenSocket){
        printf( "Can't open control process listen port %d.", port );
        exit(-1);
    }

    memset(_ClientSocket, 0, sizeof(_ClientSocket));

    ClientAccept();
    running = 1;
    while(running) {
        printf("run %d\n", running);
        CommandRead();
        sleep(1);
    }

}



void usage()
{
    fprintf(stderr, "\nusage: %s [options] \n"

            "   -i <wlan interface>\n"
            "       --interface=<wlan interface>\n"
            "                       wlan adapter name (wlan, eth, etc.) default wlan\n"

            "   -p <port number>\n "
            "       --port=<port number>\n"

            "       --help          display this help and exit\n"
            , progname);

    exit(EXIT_FAILURE);
}

void sig_handler(int signum)
{
    int i;

    printf("Caught!\n");
    for(i = 0; i < MCLIENT; i++)
      ClientClose(i);
    printf("before exit\n");
    running = 0;
}

int main(int argc, char *argv[])
{
    int c;
    int port = 0;
    progname = argv[0];
    
    static struct option options[] =
    {
        {"help", no_argument, NULL, 'h'},
        {"interface", required_argument, NULL, 'i'},
        {"port", required_argument, NULL, 'p'},
        {0, 0, 0, 0},
    };

    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = sig_handler;
    //sigaction(SIGTERM|SIGINT, &action, NULL);
    sigaction(SIGINT, &action, NULL);

    while(1){
        c = getopt_long(argc, argv, "hi:p:", options, NULL);
        if(c < 0)
            break;

        switch(c)
        {
            case 'i':
                strlcpy(g_ifname, optarg, IFNAMSIZ);
                break;
            case 'p':
                port = atoi(optarg);
                break;
            case 'h':
            default:
                usage();
                break;
        }
    }

    ftm_wlan_run(port);
    return 0;
}
