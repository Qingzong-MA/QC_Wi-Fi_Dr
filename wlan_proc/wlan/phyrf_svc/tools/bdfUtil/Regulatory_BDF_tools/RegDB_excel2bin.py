'''
 * 	Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
 *  All Rights Reserved.
 *  Confidential and Proprietary - Qualcomm Technologies, Inc.
'''

import sys
from sys import argv
from openpyxl import load_workbook as lw
import shlex
import subprocess
import RegDB_txt2bin
import RegDB_bin2txt
import os


'''
Instructions:
>python regulatory_excel_BDF.py <regulatory Input excel sheet> <BDF txt file>
'''

# Python 3: argv[0] is the script name, argv[1] is the first argument
# Use index 1 for the first command-line argument after the script name.
script = argv[0]
regInput = argv[1]

print("\nRegulatory Excel to BDF converter v2.0")  

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
else:
    # Running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

txt2bin_path = os.path.join(bundle_dir, "RegDB_txt2bin.py")
bin2txt_path = os.path.join(bundle_dir, "RegDB_bin2txt.py")


txtFile = "regdb"
#### SOME DEFS BASED ON CURRENT REGDB SIZES. MAY NEED PER CHIP CONFIG SIZES VARY PER CHIP #####
#STRUCT SIZES
CC_SIZE = 14
DMN_PAIR_SIZE = 3
SUBDMN_MAP_SIZE = 2
REG_RULES_SIZE = 8
REG_DMNS_SIZE = 16
SUPER_DMN_SUBSET_SIZE = 12
REG_DMNS_6G_SIZE = 16
REG_RULES_6G_SIZE = 8
#STRUCT LENGTHS
CC_LEN = 1000
DMN_PAIR_LEN = 1000
SUBDMN_MAP_LEN = 1000
REG_RULE_2G_LEN = 1000
REG_RULE_5G_LEN = 1000
REG_DMN_2G_LEN = 1000
REG_DMN_5G_LEN = 1000
SUPER_DMN_SUBSET_LEN = 1000
REG_DMN_6G_LEN = 1000
REG_RULE_6G_LEN = 1000

print("\n") 
#print("Max countries supported: " + str(CC_LEN)) 
#print("Max reg domain pairs supported: " + str(DMN_PAIR_LEN)) 
#print("Max 2g reg domains supported: " + str(REG_DMN_2G_LEN)) 
#print("Max 5g reg domains supported: " + str(REG_DMN_5G_LEN)) 
#print("Max 2g rules supported: " + str(REG_RULE_2G_LEN)) 
#print("Max 5g rules supported: " + str(REG_RULE_5G_LEN)) 
#print("\n")  


def is_number(s):
    try:
        float(s) # for int, long and float
    except ValueError:
        try:
            complex(s) # for complex
        except ValueError:
            return False
    return True

def clear_contents_of_column_in_sheet(ws,col):
    for row_idx in range(2, ws.max_row + 1):
        cell = ws[col + str(row_idx)]
        cell.value = None

def put_zeroes_column_in_sheet(ws,col):
    for row_idx in range(2, ws.max_row + 1):
        cell = ws[col + str(row_idx)]
        cell.value = 0

def combine_sheets(wi,wo,wbo,find_str):
    wi = wbo[wi]
    wo = wbo[wo]
    for i in range(1,wo.max_row+1):
        if (str(wo.cell(row=i,column=1).value).find(find_str) != -1):
            break
    for j in range(1,wi.max_row):
        wo.cell(row=i+(j-1),column=2).value = wi.cell(row=j+1,column=2).value

#wbi = lw("Regulatory_BDF_Data.xlsx")
wbi = lw(filename = regInput, data_only=True) #to read only values/ not formulae
print("Mapping lookups ...") 

#REGULATORY DATABASE VERSION
ver = wbi['REGDB_VERSION_HISTORY']
versionRegDb = ver.cell(row=1,column=3).value
subversion = ver.cell(row=2,column=3).value
if subversion is None:
    subversion = 0;
customver = ver.cell(row=3,column=3).value
if customver is None:
    customver = 0;

#REGULATORY DOMAINS 2G LOOKUP
ws = wbi['REG_DOMAINS_2G_LOOKUP']  
REG_DOMAINS_2G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_DOMAINS_2G_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#REGULATORY DOMAINS 5G LOOKUP
ws = wbi['REG_DOMAINS_5G_LOOKUP']  
REG_DOMAINS_5G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_DOMAINS_5G_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#REGULATORY DOMAINS 6G LOOKUP
ws = wbi['REG_DOMAINS_6G_LOOKUP']  
REG_DOMAINS_6G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_DOMAINS_6G_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#REGULATORY RULES 2G LOOKUP
ws = wbi['REG_RULES_2G_LOOKUP']  
REG_RULES_2G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_RULES_2G_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#REGULATORY RULES 5G LOOKUP
ws = wbi['REG_RULES_5G_LOOKUP']  
REG_RULES_5G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_RULES_5G_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#REGULATORY RULES 6G LOOKUP
ws = wbi['REG_RULES_6G_LOOKUP']  
REG_RULES_6G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_RULES_6G_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#IMPORTANT MACROS LOOKUP
ws = wbi['IMPORTANT_MACROS_LOOKUP']  
IMPORTANT_MACROS_LOOKUP = {}
for i in range(2,ws.max_row+1):
    IMPORTANT_MACROS_LOOKUP[ws["A"+str(i)].value] = ws["C"+str(i)].value

#DFS LOOKUP
ws = wbi['DFS_LOOKUP']  
DFS_LOOKUP = {}
for i in range(2,ws.max_row+1):
    DFS_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#CTL LOOKUP
ws = wbi['CTL_LOOKUP']  
CTL_LOOKUP = {}
for i in range(2,ws.max_row+1):
    CTL_LOOKUP[ws["A"+str(i)].value] = ws["C"+str(i)].value

#COUNTRY CODE LOOKUP
ws = wbi['COUNTRY_LOOKUP']  
COUNTRY_LOOKUP = {}
for i in range(2,ws.max_row+1):
    COUNTRY_LOOKUP[ws["A"+str(i)].value] = ws["B"+str(i)].value

#REGULATORY DOMAIN PAIR LOOKUP
ws = wbi['REG_DMN_PAIR_LOOKUP']  
REG_DMN_PAIR_LOOKUP = {}
for i in range(2,ws.max_row+1):
    REG_DMN_PAIR_LOOKUP[ws["A"+str(i)].value] = ws["C"+str(i)].value

#REGULATORY DOMAIN PAIR LOOKUP
ws = wbi['SUPER_DMN_6G_LOOKUP']  
SUPER_DMN_6G_LOOKUP = {}
for i in range(2,ws.max_row+1):
    SUPER_DMN_6G_LOOKUP[ws["A"+str(i)].value] = ws["C"+str(i)].value

#REGULATORY DOMAIN PAIR LOOKUP
ws = wbi['SUBDOMAINS_6G_INPUT']  
SUBDOMAINS_6G_INPUT = {}
for i in range(2,ws.max_row+1):
    SUBDOMAINS_6G_INPUT[ws["A"+str(i)].value] = ws["B"+str(i)].value


print("Creating BDF format for given RegDB input ...")  

# GLOBAL COUNTRIES DATABASE CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['ALL_COUNTRIES_INPUT']  
all_cc_out = ['0']*(CC_SIZE*CC_LEN)
alpha_len = 4 #additional alpha len added to flattened rows. only for country lookup
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
    #print "loop "+str(i) # Python 2 print statement
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(0)]=str(COUNTRY_LOOKUP[wi['A'+str(i+1)].value])
    #print Lookup1[wi['A'+str(i)].value] # Python 2 print statement
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(1)]=str(REG_DMN_PAIR_LOOKUP[wi['B'+str(i+1)].value])
    all_cc_out[((i - 1) * (wi.max_column + alpha_len)) + (2)] = str(SUPER_DMN_6G_LOOKUP[wi['C'+str(i+1)].value])
    #print Lookup2[wi['B'+str(i)].value] # Python 2 print statement
    charVal = wi['D'+str(i+1)].value
    finVal = ""
    if len(str(charVal)) == 3:
        for k in range(0,3):
            finVal = str('{:x}'.format(ord(charVal[k])))
            finVal = int("0x"+finVal,16)
            all_cc_out[((i-1)*(wi.max_column+alpha_len))+(3+k)]=str(finVal)
    else:
        for k in range(0,2):
            finVal = str('{:x}'.format(ord(charVal[k])))
            finVal = int("0x"+finVal,16)
            all_cc_out[((i-1)*(wi.max_column+alpha_len))+(3+k)]=str(finVal)
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(5)]=str(0)
    #print finVal # Python 2 print statement
    charVal = wi['E'+str(i+1)].value
    finVal = ""
    if len(str(charVal)) == 3:
        for k in range(0,3):
            finVal = str('{:x}'.format(ord(charVal[k])))
            finVal = int("0x"+finVal,16)
            all_cc_out[((i-1)*(wi.max_column))+(6+k)]=str(finVal)
    else:
        for k in range(0,2):
            finVal = str('{:x}'.format(ord(charVal[k])))
            finVal = int("0x"+finVal,16)
            all_cc_out[((i-1)*(wi.max_column+alpha_len))+(6+k)]=str(finVal)
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(8)]=str(0)
    #print finVal # Python 2 print statement
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(9)]=str(wi['F'+str(i+1)].value)
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(10)]=str(wi['G'+str(i+1)].value)
    all_cc_out[((i - 1) * (wi.max_column + alpha_len)) + (11)] = str(wi['H' + str(i + 1)].value)
    if is_number(str(wi['I'+str(i+1)].value)):
        all_cc_out[((i-1)*(wi.max_column+alpha_len))+(12)]=str(wi['I'+str(i+1)].value)
    else:
        all_cc_out[((i-1)*(wi.max_column+alpha_len))+(12)]=str(IMPORTANT_MACROS_LOOKUP[wi['I'+str(i+1)].value])
    all_cc_out[((i-1)*(wi.max_column+alpha_len))+(13)]=str(wi['J'+str(i+1)].value)

# REGULATORY DOMAIN PAIRS CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_DOMAIN_PAIRS_INPUT']  
reg_dmn_pairs_out = ['0']*(DMN_PAIR_SIZE*DMN_PAIR_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
#    print "loop "+str(i) # Python 2 print statement
    reg_dmn_pairs_out[((i-1)*(wi.max_column))+(0)]=str(REG_DMN_PAIR_LOOKUP[wi['A'+str(i+1)].value])
    reg_dmn_pairs_out[((i-1)*(wi.max_column))+(1)]=str(REG_DOMAINS_5G_LOOKUP[wi['B'+str(i+1)].value])
    reg_dmn_pairs_out[((i-1)*(wi.max_column))+(2)]=str(REG_DOMAINS_2G_LOOKUP[wi['C'+str(i+1)].value])

# REGULATORY RULES 2G CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_RULES_2G_INPUT']  
reg_2g_rules_out = ['0']*(REG_RULES_SIZE*REG_RULE_2G_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
    for j in range(1,8):
        reg_2g_rules_out[((i-1)*(wi.max_column))+(j-1)]=str(wi.cell(row=int(str(i+1)), column=j).value)
    if is_number(str(wi['D'+str(i+1)].value)):
        reg_2g_rules_out[((i-1)*(wi.max_column))+(3)]=str(wi['D'+str(i+1)].value)
    else:
        reg_2g_rules_out[((i-1)*(wi.max_column))+(3)]=str(IMPORTANT_MACROS_LOOKUP[wi['D'+str(i+1)].value])

# REGULATORY RULES 5G CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_RULES_5G_INPUT']  
reg_5g_rules_out = ['0']*(REG_RULES_SIZE*REG_RULE_5G_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
#print(wi.max_row)
for i in range(1,wi.max_row):
#print(i)
    for j in range(1,8):
        reg_5g_rules_out[((i-1)*(wi.max_column))+(j-1)]=str(wi.cell(row=int(str(i+1)), column=j).value)
    if is_number(str(wi['D'+str(i+1)].value)):
        reg_5g_rules_out[((i-1)*(wi.max_column))+(3)]=str(wi['D'+str(i+1)].value)
    else:
        reg_5g_rules_out[((i-1)*(wi.max_column))+(3)]=str(IMPORTANT_MACROS_LOOKUP[wi['D'+str(i+1)].value])
    if is_number(str(wi['F'+str(i+1)].value)):
        reg_5g_rules_out[((i-1)*(wi.max_column))+(5)]=str(wi['F'+str(i+1)].value)
    else:
        reg_5g_rules_out[((i-1)*(wi.max_column))+(5)]=str(CTL_LOOKUP[wi['F'+str(i+1)].value])

# REGULATORY DOMAINS 2G CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_DOMAINS_2G_INPUT']  
reg_2g_dmns_out = ['0']*(REG_DMNS_SIZE*REG_DMN_2G_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
#    print "loop "+str(i) # Python 2 print statement
    if is_number(str(wi['A'+str(i+1)].value)):
        reg_2g_dmns_out[((i-1)*(wi.max_column))+(0)]=str(wi['A'+str(i+1)].value)
    else:
        reg_2g_dmns_out[((i-1)*(wi.max_column))+(0)]=str(CTL_LOOKUP[wi['A'+str(i+1)].value])
    if is_number(str(wi['B'+str(i+1)].value)):
        reg_2g_dmns_out[((i-1)*(wi.max_column))+(1)]=str(wi['B'+str(i+1)].value)
    else:
        reg_2g_dmns_out[((i-1)*(wi.max_column))+(1)]=str(DFS_LOOKUP[wi['B'+str(i+1)].value])
    for j in range(3,7):
        reg_2g_dmns_out[((i-1)*(wi.max_column))+(j-1)]=str(wi.cell(row=int(str(i+1)), column=j).value)
    for j in range(7,18):
        if wi.cell(row=int(str(i+1)), column=j).value == None:
            break
        else:
            if is_number(str(wi.cell(row=int(str(i+1)), column=j).value)):
                reg_2g_dmns_out[((i-1)*(wi.max_column))+(j-1)]=str(wi.cell(row=int(str(i+1)), column=j).value)
            else:
                reg_2g_dmns_out[((i-1)*(wi.max_column))+(j-1)]=str(REG_RULES_2G_LOOKUP[wi.cell(row=int(str(i+1)), column=j).value])

# REGULATORY DOMAINS 5G CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_DOMAINS_5G_INPUT']  
reg_5g_dmns_out = ['0']*(REG_DMNS_SIZE*REG_DMN_5G_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
#    print "loop "+str(i) # Python 2 print statement
    if is_number(str(wi['A'+str(i+1)].value)):
        reg_5g_dmns_out[((i-1)*(wi.max_column))+(0)]=str(wi['A'+str(i+1)].value)
    else:
        reg_5g_dmns_out[((i-1)*(wi.max_column))+(0)]=str(CTL_LOOKUP[wi['A'+str(i+1)].value])
    if is_number(str(wi['B'+str(i+1)].value)):
        reg_5g_dmns_out[((i-1)*(wi.max_column))+(1)]=str(wi['B'+str(i+1)].value)
    else:
        reg_5g_dmns_out[((i-1)*(wi.max_column))+(1)]=str(DFS_LOOKUP[wi['B'+str(i+1)].value])
    for j in range(3,7):
        reg_5g_dmns_out[((i-1)*(wi.max_column))+(j-1)]=str(wi.cell(row=int(str(i+1)), column=j).value)
    for j in range(7,18):
        if wi.cell(row=int(str(i+1)), column=j).value == None:
            break
        else:
            if is_number(str(wi.cell(row=int(str(i+1)), column=j).value)):
                reg_5g_dmns_out[((i-1)*(wi.max_column))+(j-1)]=str(wi.cell(row=int(str(i+1)), column=j).value)
            else:
                reg_5g_dmns_out[((i-1)*(wi.max_column))+(j-1)]=str(REG_RULES_5G_LOOKUP[wi.cell(row=int(str(i+1)), column=j).value])

wi = wbi['SUPER_DOMAIN_INPUT']  
super_dmn_out = ['0']*(SUPER_DMN_SUBSET_SIZE*SUPER_DMN_SUBSET_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
#    print "loop "+str(i) # Python 2 print statement
    super_dmn_out[((i-1)*(wi.max_column))+(0)]=str(SUPER_DMN_6G_LOOKUP[wi['A'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(1)]=str(REG_DOMAINS_6G_LOOKUP[wi['B'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(2)]=str(REG_DOMAINS_6G_LOOKUP[wi['C'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(3)]=str(REG_DOMAINS_6G_LOOKUP[wi['D'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(4)]=str(REG_DOMAINS_6G_LOOKUP[wi['E'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(5)]=str(REG_DOMAINS_6G_LOOKUP[wi['F'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(6)]=str(REG_DOMAINS_6G_LOOKUP[wi['G'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(7)]=str(REG_DOMAINS_6G_LOOKUP[wi['H'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(8)]=str(REG_DOMAINS_6G_LOOKUP[wi['I'+str(i+1)].value])
    super_dmn_out[((i-1)*(wi.max_column))+(9)]=str(REG_DOMAINS_6G_LOOKUP[wi['J'+str(i+1)].value])
    super_dmn_out[((i - 1) * (wi.max_column)) + (10)] = str(REG_DOMAINS_6G_LOOKUP[wi['K'+str(i+1)].value])
    super_dmn_out[((i - 1) * (wi.max_column)) + (11)] = str(REG_DOMAINS_6G_LOOKUP[wi['L'+str(i+1)].value])

# REGULATORY RULES 6G CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_RULES_6G_INPUT']  
reg_6g_rules_out = ['0'] * (REG_RULES_6G_SIZE * REG_RULE_6G_LEN)
# put_zeroes_column_in_sheet(wo, 'B')
for i in range(1, wi.max_row):
    for j in range(1, 8):
        reg_6g_rules_out[((i - 1) * (wi.max_column)) + (j - 1)] = str(wi.cell(row=int(str(i + 1)), column=j).value)
    if is_number(str(wi['G' + str(i + 1)].value)):
        reg_6g_rules_out[((i - 1) * (wi.max_column)) + (3)] = str(wi['D' + str(i + 1)].value)
    else:
        reg_6g_rules_out[((i - 1) * (wi.max_column)) + (3)] = str(IMPORTANT_MACROS_LOOKUP[wi['D' + str(i + 1)].value])

# REGULATORY DOMAINS 6G CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['REG_DOMAINS_6G_INPUT']  
reg_6g_dmns_out = ['0'] * (REG_DMNS_6G_SIZE * REG_DMN_6G_LEN)
# put_zeroes_column_in_sheet(wo, 'B')
for i in range(1, wi.max_row):
#    print "loop "+str(i) # Python 2 print statement
    if is_number(str(wi['A' + str(i + 1)].value)):
        reg_6g_dmns_out[((i - 1) * (wi.max_column)) + (0)] = str(wi['A' + str(i + 1)].value)
    else:
        reg_6g_dmns_out[((i - 1) * (wi.max_column)) + (0)] = str(CTL_LOOKUP[wi['A' + str(i + 1)].value])
    for j in range(2, 5):
        reg_6g_dmns_out[((i - 1) * (wi.max_column)) + (j - 1)] = str(wi.cell(row=int(str(i + 1)), column=j).value)
    for j in range(5, 16):
        if wi.cell(row=int(str(i + 1)), column=j).value == None:
            break
        else:
            if is_number(str(wi.cell(row=int(str(i + 1)), column=j).value)):
                reg_6g_dmns_out[((i - 1) * (wi.max_column)) + (j - 1)] = str(
                    wi.cell(row=int(str(i + 1)), column=j).value)
            else:
                reg_6g_dmns_out[((i - 1) * (wi.max_column)) + (j - 1)] = str(
                    REG_RULES_6G_LOOKUP[wi.cell(row=int(str(i + 1)), column=j).value])

# REGULATORY DOMAIN PAIRS CONVERSION TO BDF FLATTENED FORMAT
wi = wbi['SUBDOMAINS_6G_MAP']  
sub_dmn_6g_map_out = ['0']*(SUBDMN_MAP_SIZE*SUBDMN_MAP_LEN)
#put_zeroes_column_in_sheet(wo, 'B')
for i in range(1,wi.max_row):
    sub_dmn_6g_map_out[((i-1)*(wi.max_column))+(0)]=str(REG_DOMAINS_6G_LOOKUP[wi['A'+str(i+1)].value])
    sub_dmn_6g_map_out[((i-1)*(wi.max_column))+(1)]=str(SUBDOMAINS_6G_INPUT[wi['B'+str(i+1)].value])


print("Created BDF format of regDB input ...")  

txtLines = list()
with open("regdb.txt", "r") as txt:
    txtLines = txt.readlines()

ind = 0
for i in txtLines:
    if "REGULATORY_DB_SECTION" in i:
        break
    ind += 1

print("Fetching RegDB indices in BDF ...")  
#cc indices start - end
ccstr = "regDbAllCountries"
cc_start =ind+1 
cc_end = cc_start
curr = txtLines[cc_start]
while ccstr in curr:
    cc_end += 1
    curr = txtLines[cc_end]
cc_end -= 1

#dmn pairs indices start - end
dmnstr = "regDbRegDmnPairs"
dmn_start = cc_end + 1
dmn_end = dmn_start
curr = txtLines[dmn_start]
while dmnstr in curr:
    dmn_end += 1
    curr = txtLines[dmn_end]
dmn_end -= 1
#2g rules indices start - end
reg2grulesStr = "regDbRegRule2g"
reg2grule_start = dmn_end + 1
reg2grule_end = reg2grule_start
curr = txtLines[reg2grule_start]
while reg2grulesStr in curr:
    reg2grule_end += 1
    curr = txtLines[reg2grule_end]
reg2grule_end -= 1
#5g rules indices start - end
reg5grulesStr = "regDbRegRule5g"
reg5grule_start = reg2grule_end + 1
reg5grule_end = reg5grule_start
curr = txtLines[reg5grule_start]
while reg5grulesStr in curr:
    reg5grule_end += 1
    curr = txtLines[reg5grule_end]
reg5grule_end -= 1
#6g rules indices start - end
reg6grulesStr = "regDbRegRule6g"
reg6grule_start = reg5grule_end + 1
reg6grule_end = reg6grule_start
curr = txtLines[reg6grule_start]
while reg6grulesStr in curr:
    reg6grule_end += 1
    curr = txtLines[reg6grule_end]
reg6grule_end -= 1
#2g dmns indices start - end
reg2gdmnsStr = "regDbRegDomains2g"
reg2gdmn_start = reg6grule_end + 1
reg2gdmn_end = reg2gdmn_start
curr = txtLines[reg2gdmn_start]
while reg2gdmnsStr in curr:
    reg2gdmn_end += 1
    curr = txtLines[reg2gdmn_end]
reg2gdmn_end -= 1
#5g dmns indices start - end
reg5gdmnsStr = "regDbRegDomains5g"
reg5gdmn_start = reg2gdmn_end + 1
reg5gdmn_end = reg5gdmn_start
curr = txtLines[reg5gdmn_start]
while reg5gdmnsStr in curr:
    reg5gdmn_end += 1
    curr = txtLines[reg5gdmn_end]
reg5gdmn_end -= 1
#6g dmns indices start - end
reg6gdmnsStr = "regDbRegDomains6g"
reg6gdmn_start = reg5gdmn_end + 1
reg6gdmn_end = reg6gdmn_start
curr = txtLines[reg6gdmn_start]
while reg6gdmnsStr in curr:
    reg6gdmn_end += 1
    curr = txtLines[reg6gdmn_end]
reg6gdmn_end -= 1
#super dmn pairs indices start - end
dmnstr_6g = "regDbSuperDmnSubsets"
dmn_start_6g = reg6gdmn_end + 1
dmn_end_6g = dmn_start_6g
curr = txtLines[dmn_start_6g]
while dmnstr_6g in curr:
    dmn_end_6g += 1
    curr = txtLines[dmn_end_6g]
dmn_end_6g -= 1

print("Fetched regDB indices ...")  
subdmnstr = "regDbSubDomain6gMap"
subdmnstart = dmn_end_6g + 1
subdmnend = subdmnstart

curr = txtLines[subdmnstart]
while subdmnstr in curr:
    subdmnend += 1
    curr = txtLines[subdmnend]
subdmnend -= 1

def valCpy(ind_start,ind_end,valDict,txtLines):
    t = 0

    for i in range(ind_start,ind_end+1):
        curr = txtLines[i].strip().split("\t")
        curr[2] = " "+valDict[t]+" "
        curr = "\t".join(curr)
        curr = curr+"\n"
        txtLines[i] = curr
        t += 1
    return txtLines

# copy cc values
txtLines = valCpy(cc_start,cc_end,all_cc_out,txtLines)
# copy regdmn pair values
txtLines = valCpy(dmn_start,dmn_end,reg_dmn_pairs_out,txtLines)
# copy regrules 2g
txtLines = valCpy(reg2grule_start,reg2grule_end,reg_2g_rules_out,txtLines)
#copy regrules 5g
txtLines = valCpy(reg5grule_start,reg5grule_end,reg_5g_rules_out,txtLines)
#copy reg dmns 2g
txtLines = valCpy(reg2gdmn_start,reg2gdmn_end,reg_2g_dmns_out,txtLines)
#copy reg dmns 5g
#print(reg2gdmn_end)
#print(reg5gdmn_start)
txtLines = valCpy(reg5gdmn_start,reg5gdmn_end,reg_5g_dmns_out,txtLines)
# copy 6g super domain values
txtLines = valCpy(dmn_start_6g,dmn_end_6g,super_dmn_out,txtLines)
#copy regrules 6g
txtLines = valCpy(reg6grule_start,reg6grule_end,reg_6g_rules_out,txtLines)
#copy reg dmns 6g
txtLines = valCpy(reg6gdmn_start,reg6gdmn_end,reg_6g_dmns_out,txtLines)
#copy reg dmns 6g
txtLines = valCpy(subdmnstart,subdmnend,sub_dmn_6g_map_out,txtLines)

print("Copied regulatory values to respective BDF indices ...")  

for i in range(subdmnend,subdmnend+10+1):
    if "regDbEnable" in txtLines[i]:
        curr = txtLines[i].strip().split("\t")

        curr[2] = " "+"1"+" "
        curr = "\t".join(curr)
        curr = curr+"\n"
        txtLines[i] = curr
    if "regDbVersion" in txtLines[i]:
        curr = txtLines[i].strip().split("\t")
        print("RegDB version: "+str(versionRegDb))  
        curr[2] = " "+str(versionRegDb)+" "
        curr = "\t".join(curr)
        curr = curr+"\n"
        txtLines[i] = curr
    if "regDbSubVer" in txtLines[i]:
        curr = txtLines[i].strip().split("\t")
        ##print(t)
        print ("RegDB sub version: "+str(subversion))
        curr[2] = " "+str(subversion)+" "
        curr = "\t".join(curr)
        curr = curr+"\n"
        txtLines[i] = curr
    if "regDbCustomVer" in txtLines[i]:
        curr = txtLines[i].strip().split("\t")
        ##print(t)
        print ("RegDB custom version: "+str(customver))
        curr[2] = " "+str(customver)+" "
        curr = "\t".join(curr)
        curr = curr+"\n"
        txtLines[i] = curr

#COPY TO NEW BDF TXT FILE
print(f"Calling {txt2bin_path}...")
with open(txtFile+"_new.txt","w") as txt:
    txt.truncate() 
    for k in txtLines:
        txt.writelines(k)
print("Successfully created new BDF file with updated regulatory values!")  
wbi.close()

try:
    result = subprocess.run(
        shlex.split("python RegDB_txt2bin.py regdb_new.txt regdb.bin"),
        capture_output=True, # Captures stdout and stderr
        text=True,           # Decodes stdout/stderr as strings (assuming UTF-8 by default)
        check=True           # Raises CalledProcessError on non-zero exit code
    )

    if result.stdout:
        print("RegDB_txt2bin.py output:")
        print(result.stdout)
    if result.stderr:
        print("RegDB_txt2bin.py errors:")
        print(result.stderr)

except subprocess.CalledProcessError as e:
    # This block executes if RegDB_txt2bin.py returns a non-zero exit code
    print(f"Error: RegDB_txt2bin.py failed with exit code {e.returncode}")
    print(f"Stdout:\n{e.stdout}")
    print(f"Stderr:\n{e.stderr}")
except FileNotFoundError:
    # This block executes if 'python' or 'RegDB_txt2bin.py' is not found
    print("Error: Command or script not found. Make sure 'python' is in your PATH and RegDB_txt2bin.py exists.")
except Exception as e:
    # Catch any other unexpected errors
    print(f"An unexpected error occurred: {e}")


try:
    result = subprocess.run(
        shlex.split("python RegDB_bin2txt.py regdb.bin regdb.txt"),
        capture_output=True, # Captures stdout and stderr
        text=True,           # Decodes stdout/stderr as strings (assuming UTF-8 by default)
        check=True           # Raises CalledProcessError on non-zero exit code
    )
    
    if result.stdout:
        print("RegDB_bin2txt.py output:")
        print(result.stdout)
    if result.stderr:
        print("RegDB_bin2txt.py errors:")
        print(result.stderr)

except subprocess.CalledProcessError as e:
    # This block executes if RegDB_bin2txt.py returns a non-zero exit code
    print(f"Error: RegDB_bin2txt.py failed with exit code {e.returncode}")
    print(f"Stdout:\n{e.stdout}")
    print(f"Stderr:\n{e.stderr}")
except FileNotFoundError:
    # This block executes if 'python' executable or 'RegDB_bin2txt.py' script is not found
    print("Error: Command or script not found. Make sure 'python' is in your PATH and RegDB_bin2txt.py exists.")
except Exception as e:
    # Catch any other unexpected errors
    print(f"An unexpected error occurred: {e}")
        
sys.exit()()
