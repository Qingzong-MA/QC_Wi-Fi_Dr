'''
 * 	Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
 *  All rights reserved.
 *  Confidential and Proprietary - Qualcomm Technologies, Inc.
'''

from sys import argv
import struct
import math

import sys


def numerical_val(val,nBits,signVal):
    a = nBits // 8  # Use integer division
    numVal = 0
    for b in range(a):
        numVal = numVal << 8
        if sys.byteorder == "little":
            numVal = numVal + val[a - 1 - b]
        else:
            numVal = numVal + val[b]
    if (signVal == 'i') and (numVal > (1 << nBits) / 2):
        return ((1 << nBits) - numVal) * (-1)
    else:
        return numVal

def num_bytes(typeVal):
    lenVal = (typeVal[(len(typeVal)-2):])
    if(lenVal == "t8"):
        return 1
    if(lenVal == "16"):
        return 2
    if(lenVal == "32"):
        return 4
    if(lenVal == "64"):
        return 8
    return 1



def main(argv):

    splArgsList = ["-h", "-b"]
    script, splArg, txtFile, binFile = ["","","",""]
    ### List of variables for splArgs ###
    hexDisp = False
    binDisp = False

    if len(argv)==3:
        script, binFile, txtFile = argv
    elif len(argv)==4:
        script, splArg, binFile, txtFile = argv
        print ("Currently not supported.")
        if splArg not in splArgsList:
            exit()
        if splArg == "-h":
            hexDisp = True
        if splArg == "-b":
            binDisp = True
        ### Reserved for future ###

    #script, binFile, txtFile = argv
    txtFile = txtFile[:(len(txtFile)-4)]
    # Reading Binary values from .bin file as integer numbers
    #print txtFile
    txt = open(txtFile+".txt","r")
    txtLines = txt.readlines()
    f = open(binFile,"rb")
    data = f.read()
    seekVal = 0
    i=0
    if "#######" in txtLines[0]:
        txtLines[i] = txtLines[i].strip()
        i=1
    while (i < len(txtLines)):
        txtLines[i] = txtLines[i].strip()
        lineSet = txtLines[i].split() 
        if lineSet[0][(len(lineSet[0])-2):][0] == '_':
            f.seek(seekVal)
            seekVal += 1
            s = 1
            byt = 0
            num = 0
            val = f.read(1)
            val = numerical_val(val,8,'u')
            while s:
                txtLines[i] = txtLines[i].strip()
                lineSet = txtLines[i].split() # Use str.split()
                byteOffset = lineSet[0][(len(lineSet[0])-3):]
                num = (int(val) & (int(math.pow(2, (int(byteOffset[0]) + int(byteOffset[2])))) - 1)) // (int(math.pow(2, int(byteOffset[0])))) 
                if num >= 0:
                    lineSet[2] = ' ' + str(num)
                else:
                    lineSet[2] = str(num)
                txtLines[i] = '\t'. join(lineSet)
                byt += int(byteOffset[2])
                if byt == 8:
                    s = 0
                else:
                    i += 1  
        else:
            f.seek(seekVal)
            r = num_bytes(lineSet[0])
            seekVal = seekVal + r
            val = f.read(r)
            fin = numerical_val(val,r*8,lineSet[0][0])
            if fin >= 0:
                lineSet[2] = ' ' + str(fin)
            else:
                lineSet[2] = str(fin)
            txtLines[i] = '\t'. join(lineSet)
        i += 1
    txt.close() # Add parentheses to call close method


    txt = open(txtFile+"_new.txt","w")
    # .truncate() is a method of the file object, not a standalone function
    for line in txtLines:
        #writelines expects a list of strings; writing one line at a time
        txt.write(line + " \n") 
    f.close()
    txt.close()

    print("\nGenerated {}_new.txt from {} ".format(txtFile, binFile))

if __name__== "__main__":
    main(sys.argv)
