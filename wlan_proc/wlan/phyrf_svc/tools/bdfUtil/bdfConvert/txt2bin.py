'''
 * 	Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
 *  All rights reserved.
 *  Confidential and Proprietary - Qualcomm Technologies, Inc.
'''
from sys import argv
#import binascii
import struct
import math

import sys

# script, txtFile, binFile = argv

byteCount = 0
checkSum = 0
wordVal = 0
wordCheck = 0

def checksumCal(typeVal, checksumVal, byteSize, num):
    global byteCount
    global checkSum
    global wordVal
    global wordCheck
    lenVal = (typeVal[(len(typeVal)-2):])
    res = 0
    if(lenVal == "t8"):
        res = ((1 << 8) + num) if((num < 0) and (typeVal[0] == 'i')) else num
    elif(lenVal == "16"): # Changed to elif for efficiency
        res = ((1 << 16) + num) if((num < 0) and (typeVal[0] == 'i')) else num
    elif(lenVal == "32"): # Changed to elif
        res = ((1 << 32) + num) if((num < 0) and (typeVal[0] == 'i')) else num
    elif(lenVal == "64"): # Changed to elif
        res = ((1 << 64) + num) if((num < 0) and (typeVal[0] == 'i')) else num
    if(checksumVal == "checksum"):
        byteCount = byteCount + 2
        workCheck = byteCount % 2
        checkSum = (checkSum + 0) & 65535
    else:
        while (byteSize != 0):
            byteCount += 1
            wordCheck = byteCount % 2
            wordVal = res % 256 if(wordCheck == 1) else (wordVal | ((res % 256)*256))
            if(wordCheck == 0):
                checkSum = checkSum ^ wordVal
            res = res // 256 # Changed to integer division
            byteSize -= 1
            
def num_bytes(typeVal):
    lenVal = (typeVal[(len(typeVal)-2):])
    if(lenVal == "t8" or lenVal[0] == '_'):
        return 1
    if(lenVal == "16"):
        return 2
    if(lenVal == "32"):
        return 4
    if(lenVal == "64"):
        return 8
    return 1

def data_type(typeVal):
    lenVal = (typeVal[(len(typeVal)-2):])
    res = 'n'
    if(lenVal == "t8"):
        res = 'b' if(typeVal[0] == 'i') else 'B'
    elif(lenVal == "16"): # Changed to elif
        res = 'h' if(typeVal[0] == 'i') else 'H'
    elif(lenVal == "32"): # Changed to elif
        res = 'l' if(typeVal[0] == 'i') else 'L'
    elif(lenVal == "64"): # Changed to elif
        res = 'q' if(typeVal[0] == 'i') else 'Q'
    if(res == 'n'):
        res = 'b'
    return res

def bit_pack(a, txtLines):
    s = 1
    byt = 0
    num = 0
    while s:
        txtLines[a] = txtLines[a].strip()
        lineSet = txtLines[a].split('\t')
        if lineSet[2][0] == ' ':
            val = lineSet[2].split(' ')[1] # Accessing [1] directly
        else:
            val = lineSet[2]
        if val.find("0x") != -1:
            val = str(int(val, 0))
        else:
            val = val
        byteOffset = lineSet[0][(len(lineSet[0])-3):]
        num = num | ((int(val)*(int(math.pow(2, int(byteOffset[0]))))))
        byt += int(byteOffset[2])
        if byt == 8:
            s = 0
        else:
            a += 1
    return a, num

def main(argv):
    splArgsList = ["-v"]
    script, splArg, txtFile, binFile = ["","","",""]
    ### List of variables for splArgs ###
    vercpy = False

    if len(argv)==3:
        script, txtFile, binFile = argv
    elif len(argv)==4:
        script, splArg, txtFile, binFile = argv
        if splArg not in splArgsList:
            exit()
        if splArg == "-v":
            vercpy = True
        ### Reserved for future ###

    ### Template version variables ###
    tplVer1=0
    tplVer2=0
    tplVer3=0

    #print "Generating "+binFile+" from "+txtFile+"."
    txt = open(txtFile, "r")
    txtLines = txt.readlines()
    f = open(binFile, "wb")
    f.truncate
    seekVal = 0
    a = 0
    if "#######" in txtLines[0]:
        a=1

    if vercpy==True:
        version = txtLines[0].split(" ")[4]
        print ("Copying txt tpl version "+str(version)+" to binary.")
        #exit()
        tplVer1=version.split(".")[0]
        tplVer2=version.split(".")[1]
        tplVer3=version.split(".")[2]
    #print tplVer1,tplVer2,tplVer3
    #exit()
    global checkSum
    checkSum = 0 
    if(sys.byteorder == "little"):
        order = '<'
    else:
        order = '>'

    while (a < len(txtLines)):
        #print a
        txtLines[a] = txtLines[a].strip()
        lineSet = txtLines[a].split('\t')
        if lineSet[2][0] == ' ':
            num = lineSet[2].split(' ')
            num = num[1]
        else:
            num = lineSet[2]
        if num.find("0x") != -1:
            num =  int(num, 0)
        else:
            num = int(num)
        #print lineSet[1]
        if "bdfTemplateVer" in lineSet[1]:
            #raw_input()
            if vercpy == True:
                if "bdfTemplateVer1" in lineSet[1]:
                    num=int(tplVer1)
                if "bdfTemplateVer2" in lineSet[1]:
                    num=int(tplVer2)
                if "bdfTemplateVer3" in lineSet[1]:
                    num=int(tplVer3)
					#print("Copied BDF txt template version to binary.")                
        f.seek(seekVal)
        seekVal += num_bytes(lineSet[0])
        if lineSet[0][(len(lineSet[0])-2):][0] == '_':
            a, num = bit_pack(a, txtLines)
            f.write(struct.pack(order + 'B', int(num)))
            checksumCal("uint8", "WrongVal", 1, int(num))
        else:
            # b/B for signed/unsigned char (integer in Python)
            f.write(struct.pack(order + data_type(lineSet[0]), int(num)))
            checksumCal(lineSet[0], lineSet[1][(len(lineSet[1])-8):], num_bytes(lineSet[0]), int(num))
        a += 1
    checkSum = 65535 ^ checkSum
    #print checkSum
    seekVal = 0
    a = 0
    if "#######" in txtLines[0]:
        a=1
    while (a < len(txtLines)):
        txtLines[a] = txtLines[a].strip()
        lineSet = txtLines[a].split('\t')
        f.seek(seekVal)
        seekVal += num_bytes(lineSet[0])
        if lineSet[1][(len(lineSet[1])-8):] == "checksum":
            f.write(struct.pack(order + 'H', int(checkSum)))
            break
        a += 1
        #print a
    f.close
    txt.close
    print("\nGenerated {} from {} ".format(binFile, txtFile))

if __name__== "__main__":
    main(sys.argv)
