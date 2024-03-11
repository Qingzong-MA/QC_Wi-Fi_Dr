/*
 * Copyright (c) 2016 Qualcomm Atheros, Inc.
 * All Rights Reserved.
 * Qualcomm Atheros Confidential and Proprietary.
 */

// This is an auto-generated file from input\cmdBasicRspHandler.s
#include "tlv2Inc.h"
#include "cmdBasicRspHandler.h"

void* initBASICRSPOpParms(A_UINT8 *pParmsCommon, PARM_OFFSET_TBL *pParmsOffset, PARM_DICT *pParmDict)
{
    int i;  //for initializing array parameter
    CMD_BASICRSP_PARMS  *pBASICRSPParms = (CMD_BASICRSP_PARMS *)pParmsCommon;

    if (pParmsCommon == NULL) return (NULL);

    i = 0;  //assign a number to avoid warning in case i is not used

    // Populate the parm structure with initial values
    pBASICRSPParms->cmdId = pParmDict[PARM_CMDID].v.valU16;
    pBASICRSPParms->phyId = pParmDict[PARM_PHYID].v.valU8;
    pBASICRSPParms->status = pParmDict[PARM_STATUS].v.valU8;

    // Make up ParmOffsetTbl
    resetParmOffsetFields();
    fillParmOffsetTbl((A_UINT32)PARM_CMDID, (A_UINT32)(((A_UINT8 *)&(pBASICRSPParms->cmdId)) - (A_UINT8 *)pBASICRSPParms), pParmsOffset);
    fillParmOffsetTbl((A_UINT32)PARM_PHYID, (A_UINT32)(((A_UINT8 *)&(pBASICRSPParms->phyId)) - (A_UINT8 *)pBASICRSPParms), pParmsOffset);
    fillParmOffsetTbl((A_UINT32)PARM_STATUS, (A_UINT32)(((A_UINT8 *)&(pBASICRSPParms->status)) - (A_UINT8 *)pBASICRSPParms), pParmsOffset);
    return((void*) pBASICRSPParms);
}

static BASICRSP_OP_FUNC BASICRSPOpFunc = NULL;

TLV2_API void registerBASICRSPHandler(BASICRSP_OP_FUNC fp)
{
    BASICRSPOpFunc = fp;
}

A_BOOL BASICRSPOp(void *pParms)
{
    CMD_BASICRSP_PARMS *pBASICRSPParms = (CMD_BASICRSP_PARMS *)pParms;

#if 0 //for debugging, comment out this line, and uncomment the line below
//#ifdef _DEBUG
    int i;  //for initializing array parameter
    i = 0;  //assign a number to avoid warning in case i is not used

    A_PRINTF("BASICRSPOp: cmdId %u\n", pBASICRSPParms->cmdId);
    A_PRINTF("BASICRSPOp: phyId %u\n", pBASICRSPParms->phyId);
    A_PRINTF("BASICRSPOp: status %u\n", pBASICRSPParms->status);
#endif //_DEBUG

    if (NULL != BASICRSPOpFunc) {
        (*BASICRSPOpFunc)(pBASICRSPParms);
    }
    return(TRUE);
}

static OTPREADRSP_OP_FUNC OTPREADRSPOpFunc = NULL;

TLV2_API void registerOTPREADRSPHandler(OTPREADRSP_OP_FUNC fp)
{
    OTPREADRSPOpFunc = fp;
}

void* initOTPREADRSPOpParms(A_UINT8 *pParmsCommon, PARM_OFFSET_TBL *pParmsOffset, PARM_DICT *pParmDict)
{
    int i;  //for initializing array parameter
    CMD_EFUSEREADRSP_PARMS  *pOTPReadRSPParms = (CMD_EFUSEREADRSP_PARMS *)pParmsCommon;

    if (pParmsCommon == NULL) return (NULL);

    i = 0;  //assign a number to avoid warning in case i is not used

    // Populate the parm structure with initial values
    pOTPReadRSPParms->status = pParmDict[PARM_STATUS].v.valU8;
    pOTPReadRSPParms->numBytes = pParmDict[PARM_NUMBYTES].v.valU8;
	memset(pOTPReadRSPParms->otp_data, 0, sizeof(pOTPReadRSPParms->otp_data));

    // Make up ParmOffsetTbl
    resetParmOffsetFields();
    fillParmOffsetTbl((A_UINT32)PARM_STATUS, (A_UINT32)(((A_UINT8 *)&(pOTPReadRSPParms->status)) - (A_UINT8 *)pOTPReadRSPParms), pParmsOffset);
    fillParmOffsetTbl((A_UINT32)PARM_NUMBYTES, (A_UINT32)(((A_UINT8 *)&(pOTPReadRSPParms->numBytes)) - (A_UINT8 *)pOTPReadRSPParms), pParmsOffset);
    fillParmOffsetTbl((A_UINT32)PARM_EFUSEDATA, (A_UINT32)(((A_UINT8 *)&(pOTPReadRSPParms->otp_data)) - (A_UINT8 *)pOTPReadRSPParms), pParmsOffset);
    return((void*) pOTPReadRSPParms);

}

A_BOOL OTPREADRSPOp(void *pParms)
{
	CMD_EFUSEREADRSP_PARMS *pOTPReadRSPParms = (CMD_EFUSEREADRSP_PARMS *)pParms;

	printf("OTPREADRSPOp\n");
    if (NULL != OTPREADRSPOpFunc) {
        (*OTPREADRSPOpFunc)(pOTPReadRSPParms);
    }
    return(TRUE);

}

static OTPREADRSP_OP_FUNC OTPWRITERSPOpFunc = NULL;

TLV2_API void registerOTPWRITERSPHandler(OTPWRITERSP_OP_FUNC fp)
{
    OTPWRITERSPOpFunc = fp;
}

void* initOTPWRITERSPOpParms(A_UINT8 *pParmsCommon, PARM_OFFSET_TBL *pParmsOffset, PARM_DICT *pParmDict)
{
    int i;  //for initializing array parameter
    CMD_EFUSEWRITERSP_PARMS  *pOTPWriteRSPParms = (CMD_EFUSEWRITERSP_PARMS *)pParmsCommon;

    if (pParmsCommon == NULL) return (NULL);

    i = 0;  //assign a number to avoid warning in case i is not used

    // Populate the parm structure with initial values
    pOTPWriteRSPParms->status = pParmDict[PARM_STATUS].v.valU8;

    // Make up ParmOffsetTbl
    resetParmOffsetFields();
    fillParmOffsetTbl((A_UINT32)PARM_STATUS, (A_UINT32)(((A_UINT8 *)&(pOTPWriteRSPParms->status)) - (A_UINT8 *)pOTPWriteRSPParms), pParmsOffset);
    return((void*) pOTPWriteRSPParms);

}

A_BOOL OTPWRITERSPOp(void *pParms)
{
	CMD_EFUSEWRITERSP_PARMS *pOTPWriteRSPParms = (CMD_EFUSEWRITERSP_PARMS *)pParms;

	printf("OTPWRITERSPOp\n");
    if (NULL != OTPWRITERSPOpFunc) {
        (*OTPWRITERSPOpFunc)(pOTPWriteRSPParms);
    }
    return(TRUE);

}

