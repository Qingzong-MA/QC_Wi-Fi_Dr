/*
 * Copyright (c) 2016 Qualcomm Atheros, Inc.
 * All Rights Reserved.
 * Qualcomm Atheros Confidential and Proprietary.
 */

// This is an auto-generated file from input\cmdBasicRspHandler.s
#ifndef _CMDBASICRSPHANDLER_H_
#define _CMDBASICRSPHANDLER_H_

#if defined(__cplusplus) || defined(__cplusplus__)
extern "C" {
#endif

#if defined(WIN32) || defined(WIN64)
#pragma pack (push, 1)
#endif //WIN32 || WIN64

typedef struct basicrsp_parms {
    A_UINT16	cmdId;
    A_UINT8	phyId;
    A_UINT8	status;
} __ATTRIB_PACK CMD_BASICRSP_PARMS;

typedef struct _EFUSEREADRSP_PARMS_{
	A_UINT32 	status;
	A_UINT32	numBytes;
	A_UINT8		otp_data[8];	
}__ATTRIB_PACK CMD_EFUSEREADRSP_PARMS;

typedef struct _EFUSEWRITERSP_PARMS_{
	A_UINT32 	status;	
}__ATTRIB_PACK CMD_EFUSEWRITERSP_PARMS;

typedef void (*BASICRSP_OP_FUNC)(void *pParms);
typedef void (*OTPREADRSP_OP_FUNC)(void *pParms);
typedef void (*OTPWRITERSP_OP_FUNC)(void *pParms);


// Exposed functions

void* initBASICRSPOpParms(A_UINT8 *pParmsCommon, PARM_OFFSET_TBL *pParmsOffset, PARM_DICT *pParmDict);
A_BOOL BASICRSPOp(void *pParms);

void* initOTPREADRSPOpParms(A_UINT8 *pParmsCommon, PARM_OFFSET_TBL *pParmsOffset, PARM_DICT *pParmDict);
A_BOOL OTPREADRSPOp(void *pParms);

void* initOTPWRITERSPOpParms(A_UINT8 *pParmsCommon, PARM_OFFSET_TBL *pParmsOffset, PARM_DICT *pParmDict);
A_BOOL OTPWRITERSPOp(void *pParms);


#if defined(WIN32) || defined(WIN64)
#pragma pack(pop)
#endif //WIN32 || WIN64


#if defined(__cplusplus) || defined(__cplusplus__)
}
#endif

#endif //_CMDBASICRSPHANDLER_H_
