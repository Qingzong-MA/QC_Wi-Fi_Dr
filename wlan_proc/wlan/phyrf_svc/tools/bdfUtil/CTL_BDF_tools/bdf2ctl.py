'''
 * 	Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
 *  All rights reserved.
 *  Confidential and Proprietary - Qualcomm Technologies, Inc.
'''

#import pandas as pd
from pickle import FALSE
from pandas import DataFrame, ExcelWriter
# from pandas import ExcelFile
# import sys, os
import argparse
#from datetime import date
#import glob
import numpy
from pyparsing import col

#import chip specific headers
import config_wcn7850
import config_wcn7880
import config_wcn8850
import config_wcn7750
import config_qcc2072

config_file = ""
regRules_file = ""
exceptions_file = ""

bdf_file_name = ''
g_file_var = []

#CTL Config Global Variables
g_product_category = 0
g_ctl_regions_supported = 0
g_ant_gain = []
g_array_gain_cap = [[],[]]
g_margin = []
g_max_penalty = []
g_hc_offset = []
g_he_offset_5g = []
g_he_offset_2g = []
g_exception_adjust = []
g_enable_exception = 0
g_ctl_flags = 0
g_6g_supported = 0
g_array_gain_cap_ext2_FCC = [[],[],[],[],[],[],[],[],[]]
g_array_gain_cap_ext2_ETSI = [[],[],[],[],[],[],[],[],[]]

g_agCapExt2_ctlRegionMap = []
g_arrayGainCaps_ext2_enable = 0
antennaGainIndex = 0
arrayGainCapIndex = 0
arrayGainCapIndex1 = 0
marginIndex = 0
maxPenaltyIndex = 0
hcOffsetIndex = 0
heOffset5GIndex = 0
heOffset2GIndex = 0
excpAdjustIndex = 0
agCapExt2_ctlRegionMapIndex = 0
g_array_gain_cap_ext2_FCC_index = numpy.zeros(9)
g_array_gain_cap_ext2_ETSI_index = numpy.zeros(9)

# Dictionary for storing the enums from Config File
DictCtlRegion = {}
DictDevCategory = {}
DictFreqBand = {}
DictPowerRules = {}
DictArrayGainRules = {}
DictSubBandExcp = {}
DictCtlGroup5G6G = {}
DictCtlGroup2G = {}
DictPowerType6G = {}

#CTL RegRules Global Variable
g_ctl_region = []
g_device_category = []
g_freq_band = []
g_power_rules = []
g_array_gain_rules = []

devCategoryIndex = 0
subBandIndex = 0
ctlRegionIndex = 0
powerRulesIndex = 0
arrayGainIndex = 0

#CTL Power Rules Global Variable
g_pwr_rules_index = []
g_array_gain_allow = []
g_total_eirp = []
g_total_limit = []
g_psd_limit = []
g_psd_rbw = []
g_is_psd = []
g_psd_less_20 = []
g_psd_20 = []
g_psd_40 = []
g_psd_80 = []
g_psd_160 = []
g_psd_320 = []

isPsdIndex = 0
arrayGainAllowIndex = 0
totalEirpIndex = 0
totalLimitIndex = 0
psdLimitIndex = 0
psdRbwIndex = 0
psdLess20Index = 0
psd20Index = 0
psd40Index = 0
psd80Index = 0
psd160Index = 0
psd320Index = 0

#CTL Array Gain Rules Global Variable
g_array_rules_index = []
g_eirp_array_gain_bf = []
g_eirp_array_gain_nbf = []
g_total_array_gain_bf = []
g_total_array_gain_nbf = []
g_psd_array_gain_bf = []
g_psd_array_gain_nbf = []

eirpGainBFIndex = 0
eirpGainNBFIndex = 0
totalGainBFIndex = 0
totalGainNBFIndex = 0
psdGainBFIndex = 0
psdGainNBFIndex = 0


# CTL Exception Table Global Variable
g_excp_ctl_region = []
g_excp_value = []
g_excp_ctl_group = []
g_excp_fc_or_subband = []
g_dictExcpTable = {}

excpCtlRegionIndex = 0
excpCtlGroupIndex = 0
excpFreqSubbandIndex = 0
excpValueIndex = 0

# 10 - CTL regions; 11 - CTL_Groups for 2G
g_excp_mgmt_2g_startIdx = numpy.full((10,11), -1)
g_excp_mgmt_2g_endIdx = numpy.full((10,11), -1)
# 10 - CTL regions; 19 - CTL_Groups for 5G
g_excp_mgmt_5g_startIdx = numpy.full((10, 20), -1)
g_excp_mgmt_5g_endIdx = numpy.full((10, 20), -1)
# 10 - CTL regions; 20 - CTL_Groups for 6G
g_excp_mgmt_6g_startIdx = numpy.full((10, 20), -1)
g_excp_mgmt_6g_endIdx = numpy.full((10, 20), -1)

MULTIPLIER_4 = 4

# Create the data frame for the CTL Config in Excel file
def update_config():
    global g_product_category, g_ctl_regions_supported, g_enable_exception, g_ant_gain, g_array_gain_cap
    global g_6g_supported, g_margin, g_max_penalty, g_ctl_flags, g_exception_adjust#, g_hc_offset
    
    print("Creating the CTL Engine Config sheet in Excel File\n")

    with ExcelWriter('BDF Tool - CONFIG.xlsx') as writer:  

        sheet_list_product_category = {
            0: ["Client", 0, "For Client with or without SAP"], 
            1: ["AP", 1, "for AP"]
        }
        column_list = ["Description", "Enum / Value", "**Comment**"]
        df = DataFrame(list(sheet_list_product_category.values()), columns=column_list)
        df.to_excel(writer, sheet_name="Product Category", index=False)

        sheet_list_6g_cat = {
            1: ["LPI", 1], 
            2: ["VLP", 2], 
            4: ["SP", 4]
        }
        column_list = ["Enum_text", "Bitmap Value"]
        df = DataFrame(list(sheet_list_6g_cat.values()), columns=column_list)
        df["**Comment**"] = "000 is allowed"
        df.to_excel(writer, sheet_name="6G Category", index=False)

        column_list = ["Enum_text", "Bitmap Value"]
        sheet_list_ctl_regions = [[x, 1 << y] for x,y in DictCtlRegion.items()]
        df = DataFrame(sheet_list_ctl_regions, columns=column_list)
        df["**Comment**"] = "00000 is not allowed"
        df.to_excel(writer, sheet_name="Supported CTL Regions", index=False)

        sheet_list_ul_ofdma = {
            1: ["UL OFDMA Supported", 1], 
            0: ["UL OFDMA Not Supported", 0]
        }
        column_list = ["Enum_text", "Enum / Value"]
        df = DataFrame(list(sheet_list_ul_ofdma.values()), columns=column_list)
        df.to_excel(writer, sheet_name="UL_OFDMA_Support", index=False)

        sheet_list_dl_ofdma = {
            1: ["DL_OFDMA Shares Exception Data with HT/VHT/EHT/HE of Same BW", 1], 
            0: ["DL_OFDMA Has Its Own Exception Data for each BW", 0]
        }
        column_list = ["Enum_text", "Enum / Value"]
        df = DataFrame(list(sheet_list_dl_ofdma.values()), columns=column_list)
        df.to_excel(writer, sheet_name="DL_OFDMA_Shares_Exceptions", index=False)

        sheet_list_excpt_table = {
            1: ["Enable Exception Table", 1],
            0: ["Ignore Exception Table", 0]
        }
        column_list = ["Enum_text", "Enum / Value"]
        df = DataFrame(list(sheet_list_excpt_table.values()), columns=column_list)
        df.to_excel(writer, sheet_name="Enable Exception Table", index=False)
        
        sheet_list_Enum_Lookup_table = {
            1: ["Enable", 1],
            0: ["Disable", 0]
        }
        column_list = ["Enum_text", "Enum / Value"]
        df = DataFrame(list(sheet_list_Enum_Lookup_table.values()), columns=column_list)
        df.to_excel(writer, sheet_name="Enum_Lookup", index=False)

        sheet_list_engine_cfg = []

        field = 'Client or AP'
        elem = [field, sheet_list_product_category[g_product_category][0]]
        sheet_list_engine_cfg.append(elem)

        field = 'UL OFDMA Supported?'
        elem = [field, sheet_list_ul_ofdma[g_ctl_flags & 1][0]]
        sheet_list_engine_cfg.append(elem)

        field = "DL OFDMA Share Exceptions?"
        elem = [field, sheet_list_dl_ofdma[((g_ctl_flags & (1 << 1)) >> 1)][0]]
        sheet_list_engine_cfg.append(elem)

        field = "List 6G Categories Supported"
        elem = [field]
        vals = []
        temp = g_6g_supported
        itr = 0
        while temp > 0:
            if (1 & temp):
                vals.append(sheet_list_6g_cat[1 << itr][0])
            temp = temp >> 1
            itr += 1
        elem.append('|'.join(vals))
        sheet_list_engine_cfg.append(elem)

        field = "Supported CTL_Regions"
        elem = [field]
        vals = []
        temp = g_ctl_regions_supported
        itr = 0
        while temp > 0:
            if (1 & temp):
                vals.append(list(DictCtlRegion.keys())[list(DictCtlRegion.values()).index(itr)])
            temp = temp >> 1
            itr += 1
        elem.append('|'.join(vals))
        sheet_list_engine_cfg.append(elem)

        field = 'Enable Exception Table'
        elem = [field, sheet_list_excpt_table[g_enable_exception][0]]
        sheet_list_engine_cfg.append(elem)

        fields = ["Added Margin 2G", "Added Margin 5G", "Added Margin 6G"]
        for i in range(min(marginIndex, len(fields))):
            if((g_margin[i] >= -12) and (g_margin[i] <= 12)):
                sheet_list_engine_cfg.append([fields[i], (g_margin[i] / MULTIPLIER_4)])
            else:
                print("Error: Margin not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])

        fields = ["Max Penalty 2G", "Max Penalty 5G", "Max Penalty 6G"]
        for i in range(min(maxPenaltyIndex, len(fields))):
            sheet_list_engine_cfg.append([fields[i], (g_max_penalty[i] / MULTIPLIER_4)])

        fields = [
            'Ant_Gain  Gain_Band_2_4', 
            'Ant_Gain  Gain_Band_5_2', 
            'Ant_Gain  Gain_Band_5_3', 
            'Ant_Gain  Gain_Band_5_6', 
            'Ant_Gain  Gain_Band_5_8', 
            'Ant_Gain  Gain_Band_6_2', 
            'Ant_Gain  Gain_Band_6_5', 
            'Ant_Gain  Gain_Band_6_7', 
            'Ant_Gain  Gain_Band_7_0'
        ]

        for i in range(min(antennaGainIndex, len(fields))):
            if ((g_ant_gain[i] >= -60) and (g_ant_gain[i] <= 96)):
                sheet_list_engine_cfg.append([fields[i], (g_ant_gain[i] / MULTIPLIER_4)])
            elif((g_ant_gain[i] < -60) or (g_ant_gain[i] > 96)):
                print("Error: Antenna Gain not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])

        fields = [
            'FCC Array Gain Cap Band 2_4', 
            'FCC Array Gain Cap Band 5_2', 
            'FCC Array Gain Cap Band 5_3', 
            'FCC Array Gain Cap Band 5_6', 
            'FCC Array Gain Cap Band 5_8', 
            'FCC Array Gain Cap Band 6_2', 
            'FCC Array Gain Cap Band 6_5', 
            'FCC Array Gain Cap Band 6_7', 
            'FCC Array Gain Cap Band 7_0'
        ]

        for i in range(min(arrayGainCapIndex, len(fields))):
            if ((g_array_gain_cap[0][i] != 255) and (g_array_gain_cap[0][i] >= -10) and (g_array_gain_cap[0][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap[0][i] / MULTIPLIER_4])
            elif((g_array_gain_cap[0][i] != 255) and ((g_array_gain_cap[0][i] < -10) or (g_array_gain_cap[0][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])

        fields = [
            'ETSI Array Gain Cap Band 2_4',
            'ETSI Array Gain Cap Band 5_2',
            'ETSI Array Gain Cap Band 5_3',
            'ETSI Array Gain Cap Band 5_6',
            'ETSI Array Gain Cap Band 5_8',
            'ETSI Array Gain Cap Band 6_2',
            'ETSI Array Gain Cap Band 6_5',
            'ETSI Array Gain Cap Band 6_7',
            'ETSI Array Gain Cap Band 7_0'
        ]

        for i in range(min(arrayGainCapIndex1, len(fields))):
            if ((g_array_gain_cap[1][i] != 255) and (g_array_gain_cap[1][i] >= -10) and (g_array_gain_cap[1][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap[1][i] / MULTIPLIER_4])
            elif((g_array_gain_cap[1][i] != 255) and ((g_array_gain_cap[1][i] < -10) or (g_array_gain_cap[1][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
        field = 'Enable_Extended_AG_Cap_Feature'
        elem = [field, sheet_list_Enum_Lookup_table[g_arrayGainCaps_ext2_enable][0]]
        sheet_list_engine_cfg.append(elem)
                
        fields = [
            'Ext_AG_Cap to CTL Region Mapping - FCC Group',
            'Ext_AG_Cap to CTL Region Mapping - ETSI Group'
         ]

        for i in range(min(agCapExt2_ctlRegionMapIndex, len(fields))):
            if g_agCapExt2_ctlRegionMap[i] != 0:
                elem = [fields[i]]
                vals = []
                temp = g_agCapExt2_ctlRegionMap[i]
                itr = 0
                while temp > 0:
                    if (1 & temp):
                        vals.append(list(DictCtlRegion.keys())[list(DictCtlRegion.values()).index(itr)])
                    temp = temp >> 1
                    itr += 1
                elem.append('|'.join(vals))
                sheet_list_engine_cfg.append(elem)
            else:
                if i == 0:
                    sheet_list_engine_cfg.append([fields[i], list(DictCtlRegion.keys())[list(DictCtlRegion.values()).index(0)]])
                    print("Defaulting "+ fields[i] + " to FCC")
                else:
                    sheet_list_engine_cfg.append([fields[i], list(DictCtlRegion.keys())[list(DictCtlRegion.values()).index(1)]])
                    print("Defaulting "+ fields[i] + " to ETSI")
#Array Gain Cap Ext2 - sub band 0
        fields = [
            'FCC Extended AGain Cap Band 2_4 4_1' ,
            'FCC Extended AGain Cap Band 2_4 4_2' ,
            'FCC Extended AGain Cap Band 2_4 4_3' ,
            'FCC Extended AGain Cap Band 2_4 4_4' ,
            'FCC Extended AGain Cap Band 2_4 3_1' ,
            'FCC Extended AGain Cap Band 2_4 3_2' ,
            'FCC Extended AGain Cap Band 2_4 3_3' ,
            'FCC Extended AGain Cap Band 2_4 2_1' ,
            'FCC Extended AGain Cap Band 2_4 2_2'
        ]


        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[0]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[0][i] != 127) and (g_array_gain_cap_ext2_FCC[0][i] >= -48) and (g_array_gain_cap_ext2_FCC[0][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[0][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[0][i] != 127) and ((g_array_gain_cap_ext2_FCC[0][i] < -48) or (g_array_gain_cap_ext2_FCC[0][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])

        fields = [
            'ETSI Extended AGain Cap Band 2_4 4_1' ,
            'ETSI Extended AGain Cap Band 2_4 4_2' ,
            'ETSI Extended AGain Cap Band 2_4 4_3' ,
            'ETSI Extended AGain Cap Band 2_4 4_4' ,
            'ETSI Extended AGain Cap Band 2_4 3_1' ,
            'ETSI Extended AGain Cap Band 2_4 3_2' ,
            'ETSI Extended AGain Cap Band 2_4 3_3' ,
            'ETSI Extended AGain Cap Band 2_4 2_1' ,
            'ETSI Extended AGain Cap Band 2_4 2_2'
        ]


        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[0]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[0][i] != 127) and (g_array_gain_cap_ext2_ETSI[0][i] >= -48) and (g_array_gain_cap_ext2_ETSI[0][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[0][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[0][i] != 127) and ((g_array_gain_cap_ext2_ETSI[0][i] < -48) or (g_array_gain_cap_ext2_ETSI[0][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])

#Array Gain Cap Ext2 - sub band 1                
        fields = [
            'FCC Extended AGain Cap Band 5_2 4_1',
            'FCC Extended AGain Cap Band 5_2 4_2',
            'FCC Extended AGain Cap Band 5_2 4_3',
            'FCC Extended AGain Cap Band 5_2 4_4',
            'FCC Extended AGain Cap Band 5_2 3_1',
            'FCC Extended AGain Cap Band 5_2 3_2',
            'FCC Extended AGain Cap Band 5_2 3_3',
            'FCC Extended AGain Cap Band 5_2 2_1',
            'FCC Extended AGain Cap Band 5_2 2_2'
        ]
        
        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[1]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[1][i] != 127) and (g_array_gain_cap_ext2_FCC[1][i] >= -48) and (g_array_gain_cap_ext2_FCC[1][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[1][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[1][i] != 127) and ((g_array_gain_cap_ext2_FCC[1][i] < -48) or (g_array_gain_cap_ext2_FCC[1][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])

        fields = [
            'ETSI Extended AGain Cap Band 5_2 4_1' ,
            'ETSI Extended AGain Cap Band 5_2 4_2' ,
            'ETSI Extended AGain Cap Band 5_2 4_3' ,
            'ETSI Extended AGain Cap Band 5_2 4_4' ,
            'ETSI Extended AGain Cap Band 5_2 3_1' ,
            'ETSI Extended AGain Cap Band 5_2 3_2' ,
            'ETSI Extended AGain Cap Band 5_2 3_3' ,
            'ETSI Extended AGain Cap Band 5_2 2_1' ,
            'ETSI Extended AGain Cap Band 5_2 2_2'
        ]


        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[1]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[1][i] != 127) and (g_array_gain_cap_ext2_ETSI[1][i] >= -48) and (g_array_gain_cap_ext2_ETSI[1][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[1][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[1][i] != 127) and ((g_array_gain_cap_ext2_ETSI[1][i] < -48) or (g_array_gain_cap_ext2_ETSI[1][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
             
#Array Gain Cap Ext2 - sub band 2
        fields = [
            'FCC Extended AGain Cap Band 5_3 4_1',
            'FCC Extended AGain Cap Band 5_3 4_2',
            'FCC Extended AGain Cap Band 5_3 4_3',
            'FCC Extended AGain Cap Band 5_3 4_4',
            'FCC Extended AGain Cap Band 5_3 3_1',
            'FCC Extended AGain Cap Band 5_3 3_2',
            'FCC Extended AGain Cap Band 5_3 3_3',
            'FCC Extended AGain Cap Band 5_3 2_1',
            'FCC Extended AGain Cap Band 5_3 2_2'
        ]


        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[2]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[2][i] != 127) and (g_array_gain_cap_ext2_FCC[2][i] >= -48) and (g_array_gain_cap_ext2_FCC[2][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[2][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[2][i] != 127) and ((g_array_gain_cap_ext2_FCC[2][i] < -48) or (g_array_gain_cap_ext2_FCC[2][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])

        fields = [
            'ETSI Extended AGain Cap Band 5_3 4_1' ,
            'ETSI Extended AGain Cap Band 5_3 4_2' ,
            'ETSI Extended AGain Cap Band 5_3 4_3' ,
            'ETSI Extended AGain Cap Band 5_3 4_4' ,
            'ETSI Extended AGain Cap Band 5_3 3_1' ,
            'ETSI Extended AGain Cap Band 5_3 3_2' ,
            'ETSI Extended AGain Cap Band 5_3 3_3' ,
            'ETSI Extended AGain Cap Band 5_3 2_1' ,
            'ETSI Extended AGain Cap Band 5_3 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[2]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[2][i] != 127) and (g_array_gain_cap_ext2_ETSI[2][i] >= -48) and (g_array_gain_cap_ext2_ETSI[2][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[2][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[2][i] != 127) and ((g_array_gain_cap_ext2_ETSI[2][i] < -48) or (g_array_gain_cap_ext2_ETSI[2][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for"+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
#Array Gain Cap Ext2 - sub band 3       
        fields = [
            'FCC Extended AGain Cap Band 5_6 4_1' ,
            'FCC Extended AGain Cap Band 5_6 4_2' ,
            'FCC Extended AGain Cap Band 5_6 4_3' ,
            'FCC Extended AGain Cap Band 5_6 4_4' ,
            'FCC Extended AGain Cap Band 5_6 3_1' ,
            'FCC Extended AGain Cap Band 5_6 3_2' ,
            'FCC Extended AGain Cap Band 5_6 3_3' ,
            'FCC Extended AGain Cap Band 5_6 2_1' ,
            'FCC Extended AGain Cap Band 5_6 2_2'
        ]
        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[3]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[3][i] != 127) and (g_array_gain_cap_ext2_FCC[3][i] >= -48) and (g_array_gain_cap_ext2_FCC[3][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[3][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[3][i] != 127) and ((g_array_gain_cap_ext2_FCC[3][i] < -48) or (g_array_gain_cap_ext2_FCC[3][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
        fields = [
            'ETSI Extended AGain Cap Band 5_6 4_1' ,
            'ETSI Extended AGain Cap Band 5_6 4_2' ,
            'ETSI Extended AGain Cap Band 5_6 4_3' ,
            'ETSI Extended AGain Cap Band 5_6 4_4' ,
            'ETSI Extended AGain Cap Band 5_6 3_1' ,
            'ETSI Extended AGain Cap Band 5_6 3_2' ,
            'ETSI Extended AGain Cap Band 5_6 3_3' ,
            'ETSI Extended AGain Cap Band 5_6 2_1' ,
            'ETSI Extended AGain Cap Band 5_6 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[3]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[3][i] != 127) and (g_array_gain_cap_ext2_ETSI[3][i] >= -48) and (g_array_gain_cap_ext2_ETSI[3][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[3][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[3][i] != 127) and ((g_array_gain_cap_ext2_ETSI[3][i] < -48) or (g_array_gain_cap_ext2_ETSI[3][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
 
#Array Gain Cap Ext2 - sub band 4 
        fields = [
            'FCC Extended AGain Cap Band 5_8 4_1',
            'FCC Extended AGain Cap Band 5_8 4_2',
            'FCC Extended AGain Cap Band 5_8 4_3',
            'FCC Extended AGain Cap Band 5_8 4_4',
            'FCC Extended AGain Cap Band 5_8 3_1',
            'FCC Extended AGain Cap Band 5_8 3_2',
            'FCC Extended AGain Cap Band 5_8 3_3',
            'FCC Extended AGain Cap Band 5_8 2_1',
            'FCC Extended AGain Cap Band 5_8 2_2'
        ]        

        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[4]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[4][i] != 127) and (g_array_gain_cap_ext2_FCC[4][i] >= -48) and (g_array_gain_cap_ext2_FCC[4][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[4][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[4][i] != 127) and ((g_array_gain_cap_ext2_FCC[4][i] < -48) or (g_array_gain_cap_ext2_FCC[4][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
        fields = [
            'ETSI Extended AGain Cap Band 5_8 4_1' ,
            'ETSI Extended AGain Cap Band 5_8 4_2' ,
            'ETSI Extended AGain Cap Band 5_8 4_3' ,
            'ETSI Extended AGain Cap Band 5_8 4_4' ,
            'ETSI Extended AGain Cap Band 5_8 3_1' ,
            'ETSI Extended AGain Cap Band 5_8 3_2' ,
            'ETSI Extended AGain Cap Band 5_8 3_3' ,
            'ETSI Extended AGain Cap Band 5_8 2_1' ,
            'ETSI Extended AGain Cap Band 5_8 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[4]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[4][i] != 127) and (g_array_gain_cap_ext2_ETSI[4][i] >= -48) and (g_array_gain_cap_ext2_ETSI[4][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[4][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[4][i] != 127 ) and ((g_array_gain_cap_ext2_ETSI[4][i] < -48) or (g_array_gain_cap_ext2_ETSI[4][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
              
#Array Gain Cap Ext2 - sub band 5              
        fields = [
            'FCC Extended AGain Cap Band 6_2 4_1',
            'FCC Extended AGain Cap Band 6_2 4_2',
            'FCC Extended AGain Cap Band 6_2 4_3',
            'FCC Extended AGain Cap Band 6_2 4_4',
            'FCC Extended AGain Cap Band 6_2 3_1',
            'FCC Extended AGain Cap Band 6_2 3_2',
            'FCC Extended AGain Cap Band 6_2 3_3',
            'FCC Extended AGain Cap Band 6_2 2_1',
            'FCC Extended AGain Cap Band 6_2 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[5]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[5][i] != 127) and (g_array_gain_cap_ext2_FCC[5][i] >= -48) and (g_array_gain_cap_ext2_FCC[5][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[5][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[5][i] != 127) and ((g_array_gain_cap_ext2_FCC[5][i] < -48) or (g_array_gain_cap_ext2_FCC[5][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                              
        fields = [
            'ETSI Extended AGain Cap Band 6_2 4_1' ,
            'ETSI Extended AGain Cap Band 6_2 4_2' ,
            'ETSI Extended AGain Cap Band 6_2 4_3' ,
            'ETSI Extended AGain Cap Band 6_2 4_4' ,
            'ETSI Extended AGain Cap Band 6_2 3_1' ,
            'ETSI Extended AGain Cap Band 6_2 3_2' ,
            'ETSI Extended AGain Cap Band 6_2 3_3' ,
            'ETSI Extended AGain Cap Band 6_2 2_1' ,
            'ETSI Extended AGain Cap Band 6_2 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[5]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[5][i] != 127) and (g_array_gain_cap_ext2_ETSI[5][i] >= -48) and (g_array_gain_cap_ext2_ETSI[5][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[5][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[5][i] != 127) and ((g_array_gain_cap_ext2_ETSI[5][i] < -48) or (g_array_gain_cap_ext2_ETSI[5][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
#Array Gain Cap Ext2 - sub band 6 
        fields = [
            'FCC Extended AGain Cap Band 6_5 4_1',
            'FCC Extended AGain Cap Band 6_5 4_2',
            'FCC Extended AGain Cap Band 6_5 4_3',
            'FCC Extended AGain Cap Band 6_5 4_4',
            'FCC Extended AGain Cap Band 6_5 3_1',
            'FCC Extended AGain Cap Band 6_5 3_2',
            'FCC Extended AGain Cap Band 6_5 3_3',
            'FCC Extended AGain Cap Band 6_5 2_1',
            'FCC Extended AGain Cap Band 6_5 2_2'
        ]


        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[6]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[6][i] != 127) and (g_array_gain_cap_ext2_FCC[6][i] >= -48) and (g_array_gain_cap_ext2_FCC[6][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[6][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[6][i] != 127) and ((g_array_gain_cap_ext2_FCC[6][i] < -48) or (g_array_gain_cap_ext2_FCC[6][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
        fields = [
            'ETSI Extended AGain Cap Band 6_5 4_1' ,
            'ETSI Extended AGain Cap Band 6_5 4_2' ,
            'ETSI Extended AGain Cap Band 6_5 4_3' ,
            'ETSI Extended AGain Cap Band 6_5 4_4' ,
            'ETSI Extended AGain Cap Band 6_5 3_1' ,
            'ETSI Extended AGain Cap Band 6_5 3_2' ,
            'ETSI Extended AGain Cap Band 6_5 3_3' ,
            'ETSI Extended AGain Cap Band 6_5 2_1' ,
            'ETSI Extended AGain Cap Band 6_5 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[6]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[6][i] != 127) and (g_array_gain_cap_ext2_FCC[6][i] >= -48) and (g_array_gain_cap_ext2_FCC[6][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[6][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[6][i] != 127) and ((g_array_gain_cap_ext2_ETSI[6][i] < -48) or (g_array_gain_cap_ext2_ETSI[6][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
  
#Array Gain Cap Ext2 - sub band 7  
        fields = [
            'FCC Extended AGain Cap Band 6_7 4_1',
            'FCC Extended AGain Cap Band 6_7 4_2',
            'FCC Extended AGain Cap Band 6_7 4_3',
            'FCC Extended AGain Cap Band 6_7 4_4',
            'FCC Extended AGain Cap Band 6_7 3_1',
            'FCC Extended AGain Cap Band 6_7 3_2',
            'FCC Extended AGain Cap Band 6_7 3_3',
            'FCC Extended AGain Cap Band 6_7 2_1',
            'FCC Extended AGain Cap Band 6_7 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[7]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[7][i] != 127) and (g_array_gain_cap_ext2_FCC[7][i] >= -48) and (g_array_gain_cap_ext2_FCC[7][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[7][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[7][i] != 127) and ((g_array_gain_cap_ext2_FCC[7][i] < -48) or (g_array_gain_cap_ext2_FCC[7][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
        fields = [
            'ETSI Extended AGain Cap Band 6_7 4_1' ,
            'ETSI Extended AGain Cap Band 6_7 4_2' ,
            'ETSI Extended AGain Cap Band 6_7 4_3' ,
            'ETSI Extended AGain Cap Band 6_7 4_4' ,
            'ETSI Extended AGain Cap Band 6_7 3_1' ,
            'ETSI Extended AGain Cap Band 6_7 3_2' ,
            'ETSI Extended AGain Cap Band 6_7 3_3' ,
            'ETSI Extended AGain Cap Band 6_7 2_1' ,
            'ETSI Extended AGain Cap Band 6_7 2_2'
        ]
        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[7]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[7][i]!= 127) and (g_array_gain_cap_ext2_ETSI[7][i] >= -48) and (g_array_gain_cap_ext2_ETSI[7][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[7][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[7][i] != 127) and ((g_array_gain_cap_ext2_ETSI[7][i] < -48) or (g_array_gain_cap_ext2_ETSI[7][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
                
#Array Gain Cap Ext2 - sub band 8
        fields = [
            'FCC Extended AGain Cap Band 7_0 4_1',
            'FCC Extended AGain Cap Band 7_0 4_2',
            'FCC Extended AGain Cap Band 7_0 4_3',
            'FCC Extended AGain Cap Band 7_0 4_4',
            'FCC Extended AGain Cap Band 7_0 3_1',
            'FCC Extended AGain Cap Band 7_0 3_2',
            'FCC Extended AGain Cap Band 7_0 3_3',
            'FCC Extended AGain Cap Band 7_0 2_1',
            'FCC Extended AGain Cap Band 7_0 2_2'
        ]

        for i in range(min(int(g_array_gain_cap_ext2_FCC_index[8]), len(fields))):
            if ((g_array_gain_cap_ext2_FCC[8][i]!= 127) and (g_array_gain_cap_ext2_FCC[8][i] >= -48) and (g_array_gain_cap_ext2_FCC[8][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_FCC[8][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_FCC[8][i]!= 127) and ((g_array_gain_cap_ext2_FCC[8][i] < -48) or (g_array_gain_cap_ext2_FCC[8][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
 
        fields = [
            'ETSI Extended AGain Cap Band 7_0 4_1' ,
            'ETSI Extended AGain Cap Band 7_0 4_2' ,
            'ETSI Extended AGain Cap Band 7_0 4_3' ,
            'ETSI Extended AGain Cap Band 7_0 4_4' ,
            'ETSI Extended AGain Cap Band 7_0 3_1' ,
            'ETSI Extended AGain Cap Band 7_0 3_2' ,
            'ETSI Extended AGain Cap Band 7_0 3_3' ,
            'ETSI Extended AGain Cap Band 7_0 2_1' ,
            'ETSI Extended AGain Cap Band 7_0 2_2'
        ]
        for i in range(min(int(g_array_gain_cap_ext2_ETSI_index[8]), len(fields))):
            if ((g_array_gain_cap_ext2_ETSI[8][i]!= 127) and (g_array_gain_cap_ext2_ETSI[8][i] >= -48) and (g_array_gain_cap_ext2_ETSI[8][i] <= 52)):
                sheet_list_engine_cfg.append([fields[i], g_array_gain_cap_ext2_ETSI[8][i] / MULTIPLIER_4])
            elif((g_array_gain_cap_ext2_ETSI[8][i]!= 127) and ((g_array_gain_cap_ext2_ETSI[8][i] < -48) or (g_array_gain_cap_ext2_ETSI[8][i] > 52))):
                print("Error: arrayGain Cap not within limits. So not updating for "+ fields[i])
                sheet_list_engine_cfg.append([fields[i], ''])
            else:
                sheet_list_engine_cfg.append([fields[i], ''])
        column_list = ["Field Name", "Value"]
        df = DataFrame(sheet_list_engine_cfg, columns = column_list)
        df.to_excel(writer, sheet_name="CTL ENGINE CONFIG", index=False)

        sheet_list_hc_off_excpt_adj = []

        column_list = ["Variable", "Value"]
        MAX_MCS = 13
        for i in range(MAX_MCS):
            if i < 8:
                sheet_list_hc_off_excpt_adj.append(["HC_Offset_MCS{}".format(i), (g_hc_offset[i] / MULTIPLIER_4)])
            else:
                # MCS 8 to 13 have the same values
                sheet_list_hc_off_excpt_adj.append(["HC_Offset_MCS8-13", (g_hc_offset[i] / MULTIPLIER_4)])
                break
        
        fields = [
                '2g_BW20_40_Percent_88',
                '2g_BW20_40_Percent_75',
                '2g_BW20_40_Percent_63',
                '2g_BW20_40_Percent_50',
                '5g_6g_BW20_40_Percent_88',
                '5g_6g_BW20_40_Percent_75',
                '5g_6g _BW20_40_Percent_63',
                '5g_6g _BW20_40_Percent_50',
                '5g_6g_BW80_160_Percent_88',
                '5g_6g_BW80_160_Percent_75',
                '5g_6g _BW80_160_Percent_63',
                '5g_6g _BW80_160_Percent_50',
                '5g_6g_BW240_320_Percent_88',
                '5g_6g_BW240_320_Percent_75',
                '5g_6g _BW240_320_Percent_63',
                '5g_6g _BW240_320_Percent_50'
            ]

        for i in range(min(excpAdjustIndex,len(fields))):
            sheet_list_hc_off_excpt_adj.append([fields[i], (g_exception_adjust[i] / MULTIPLIER_4)])

        fields = [
            'HE_offset_5G_FCC_20_UNII1-2a',
            'HE_offset_5G_FCC_20_UNII2c-4',
            'HE_offset_5G_ETSI_20_UNII1-2a',
            'HE_offset_5G_ETSI_20_UNII2c-4',
            'HE_offset_5G_MKK_20_UNII1-2a',
            'HE_offset_5G_MKK_20_UNII2c-4',
            'HE_offset_5G_KOR_20_UNII1-2a',
            'HE_offset_5G_KOR_20_UNII2c-4',
            'HE_offset_5G_CHN_20_UNII1-2a',
            'HE_offset_5G_CHN_20_UNII2c-4',
            'HE_offset_5G_USRDfnd_20_UNII1-2a',
            'HE_offset_5G_USRDfnd_20_UNII2c-4',
            'HE_offset_5G_FCC_40-160_UNII1-2a',
            'HE_offset_5G_FCC_40-160_UNII2c-4',
            'HE_offset_5G_ETSI_40-160_UNII1-2a',
            'HE_offset_5G_ETSI_40-160_UNII2c-4',
            'HE_offset_5G_MKK_40-160_UNII1-2a',
            'HE_offset_5G_MKK_40-160_UNII2c-4',
            'HE_offset_5G_KOR_40-160_UNII1-2a',
            'HE_offset_5G_KOR_40-160_UNII2c-4',
            'HE_offset_5G_CHN_40-160_UNII1-2a',
            'HE_offset_5G_CHN_40-160_UNII2c-4',
            'HE_offset_5G_USRDfnd_40-160_UNII1-2a',
            'HE_offset_5G_USRDfnd_40-160_UNII2c-4'
        ]

        for i in range(min(heOffset5GIndex,len(fields))):
            sheet_list_hc_off_excpt_adj.append([fields[i], (g_he_offset_5g[i] / MULTIPLIER_4)])

        fields = [
            'HE_offset_2G_FCC',
            'HE_offset_2G_ETSI',
            'HE_offset_2G_MKK',
            'HE_offset_2G_KOR',
            'HE_offset_2G_CHN'
        ]

        for i in range(min(heOffset2GIndex,len(fields))):
            sheet_list_hc_off_excpt_adj.append([fields[i], (g_he_offset_2g[i] / MULTIPLIER_4)])
            
        df = DataFrame(sheet_list_hc_off_excpt_adj, columns = column_list)
        df.to_excel(writer, sheet_name="HC_Offset and Excpt_Adjust", index=False)

# read the CTL Config from BDF
def read_bdf_config(line):
    global g_file_var

    global antennaGainIndex
    global arrayGainCapIndex
    global arrayGainCapIndex1
    global marginIndex
    global maxPenaltyIndex
    global hcOffsetIndex
    global heOffset5GIndex
    global heOffset2GIndex
    global excpAdjustIndex
    global agCapExt2_ctlRegionMapIndex

    global g_product_category, g_ctl_regions_supported, g_enable_exception, g_ant_gain, g_array_gain_cap
    global g_6g_supported, g_margin, g_max_penalty, g_ctl_flags, g_exception_adjust#, g_hc_offset
    global g_array_gain_cap_ext2_FCC, g_array_gain_cap_ext2_ETSI, g_array_gain_cap_ext2_Ntx3, g_array_gain_cap_ext2_Ntx2, g_arrayGainCaps_ext2_enable
    global g_array_gain_cap_ext2_FCC_index, g_array_gain_cap_ext2_ETSI_index, g_array_gain_cap_ext2_Ntx3_index, g_array_gain_cap_ext2_Ntx2_index
    
    if "ctlConfig" not in line:
        return

    if "ctlRegionsSupported" in line:
        g_ctl_regions_supported = int(line.split('\t')[2])
    if "ctlConfig.ctlFlags" in line:
        g_ctl_flags = int(line.split('\t')[2])
    if "productCategory" in line:
        g_product_category = int(line.split('\t')[2])
    if "ctlConfig.support6GCases" in line:
        g_6g_supported = int(line.split('\t')[2])
    if "isExceptionEnabled" in line:
        g_enable_exception = int(line.split('\t')[2])
    if "ctlConfig.antennaGain" in line:
        g_ant_gain.append(int(line.split('\t')[2]))
        antennaGainIndex += 1
    if "ctlConfig.arrayGainCaps[0]" in line:
        g_array_gain_cap[0].append(int(line.split('\t')[2]))
        arrayGainCapIndex += 1
    if "ctlConfig.arrayGainCaps[1]" in line:
        g_array_gain_cap[1].append(int(line.split('\t')[2]))
        arrayGainCapIndex1 += 1
    if "ctlConfig.margin" in line:
        g_margin.append(int(line.split('\t')[2]))
        marginIndex += 1
    if "ctlConfig.maxPenalty" in line:
        g_max_penalty.append(int(line.split('\t')[2]))
        maxPenaltyIndex += 1
    if "ctlConfig.heavyClipOffsetMCS" in line:
        #MCS 8 - 13 uses the same HC offset value
        #Maybe restrict the number of entries here.
        g_hc_offset.append(int(line.split('\t')[2]))
        hcOffsetIndex += 1
    if "ctlConfig.exceptionAdjust" in line:
        g_exception_adjust.append(int(line.split('\t')[2]))
        excpAdjustIndex += 1
    if "ctlConfig.ctlData5G_HeOffset" in line:
        g_he_offset_5g.append(int(line.split('\t')[2]))
        heOffset5GIndex += 1
    if "ctlConfig.ctlData2G_HeOffset" in line:
        g_he_offset_2g.append(int(line.split('\t')[2]))
        heOffset2GIndex += 1
    if "ctlConfig_ext2.ctl_region_map" in line:
        g_agCapExt2_ctlRegionMap.append(int(line.split('\t')[2]))
        agCapExt2_ctlRegionMapIndex += 1
    if "arrayGainCaps_ext2_enable" in line:
        g_arrayGainCaps_ext2_enable = int(line.split('\t')[2])
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][0]" in line:
        g_array_gain_cap_ext2_FCC[0].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][0]" in line:
        g_array_gain_cap_ext2_FCC[0].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][0]" in line:
        g_array_gain_cap_ext2_FCC[0].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][1]" in line:
        g_array_gain_cap_ext2_FCC[1].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][1]" in line:
        g_array_gain_cap_ext2_FCC[1].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][1]" in line:
        g_array_gain_cap_ext2_FCC[1].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][2]" in line:
        g_array_gain_cap_ext2_FCC[2].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][2]" in line:
        g_array_gain_cap_ext2_FCC[2].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][2]" in line:
        g_array_gain_cap_ext2_FCC[2].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][3]" in line:
        g_array_gain_cap_ext2_FCC[3].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][3]" in line:
        g_array_gain_cap_ext2_FCC[3].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][3]" in line:
        g_array_gain_cap_ext2_FCC[3].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][4]" in line:
        g_array_gain_cap_ext2_FCC[4].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][4]" in line:
        g_array_gain_cap_ext2_FCC[4].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][4]" in line:
        g_array_gain_cap_ext2_FCC[4].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][5]" in line:
        g_array_gain_cap_ext2_FCC[5].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][5]" in line:
        g_array_gain_cap_ext2_FCC[5].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][5]" in line:
        g_array_gain_cap_ext2_FCC[5].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][6]" in line:
        g_array_gain_cap_ext2_FCC[6].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][6]" in line:
        g_array_gain_cap_ext2_FCC[6].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][6]" in line:
        g_array_gain_cap_ext2_FCC[6].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][7]" in line:
        g_array_gain_cap_ext2_FCC[7].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][7]" in line:
        g_array_gain_cap_ext2_FCC[7].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][7]" in line:
        g_array_gain_cap_ext2_FCC[7].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][8]" in line:
        g_array_gain_cap_ext2_FCC[8].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][8]" in line:
        g_array_gain_cap_ext2_FCC[8].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][8]" in line:
        g_array_gain_cap_ext2_FCC[8].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_FCC_index[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][0]" in line:
        g_array_gain_cap_ext2_ETSI[0].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][0]" in line:
        g_array_gain_cap_ext2_ETSI[0].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][0]" in line:
        g_array_gain_cap_ext2_ETSI[0].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][1]" in line:
        g_array_gain_cap_ext2_ETSI[1].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][1]" in line:
        g_array_gain_cap_ext2_ETSI[1].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][1]" in line:
        g_array_gain_cap_ext2_ETSI[1].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][2]" in line:
        g_array_gain_cap_ext2_ETSI[2].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][2]" in line:
        g_array_gain_cap_ext2_ETSI[2].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][2]" in line:
        g_array_gain_cap_ext2_ETSI[2].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][3]" in line:
        g_array_gain_cap_ext2_ETSI[3].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][3]" in line:
        g_array_gain_cap_ext2_ETSI[3].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][3]" in line:
        g_array_gain_cap_ext2_ETSI[3].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][4]" in line:
        g_array_gain_cap_ext2_ETSI[4].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][4]" in line:
        g_array_gain_cap_ext2_ETSI[4].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][4]" in line:
        g_array_gain_cap_ext2_ETSI[4].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][5]" in line:
        g_array_gain_cap_ext2_ETSI[5].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][5]" in line:
        g_array_gain_cap_ext2_ETSI[5].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][5]" in line:
        g_array_gain_cap_ext2_ETSI[5].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][6]" in line:
        g_array_gain_cap_ext2_ETSI[6].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][6]" in line:
        g_array_gain_cap_ext2_ETSI[6].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][6]" in line:
        g_array_gain_cap_ext2_ETSI[6].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][7]" in line:
        g_array_gain_cap_ext2_ETSI[7].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][7]" in line:
        g_array_gain_cap_ext2_ETSI[7].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][7]" in line:
        g_array_gain_cap_ext2_ETSI[7].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][8]" in line:
        g_array_gain_cap_ext2_ETSI[8].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][8]" in line:
        g_array_gain_cap_ext2_ETSI[8].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][8]" in line:
        g_array_gain_cap_ext2_ETSI[8].append(int(line.split('\t')[2]))  
        g_array_gain_cap_ext2_ETSI_index[8] += 1
# Update the CTL RegRules in the Excel file
def update_RegRules():

    global devCategoryIndex
    global subBandIndex
    global ctlRegionIndex
    global powerRulesIndex
    global arrayGainIndex

    print("Update RegRules in Excel file\n")

    with ExcelWriter('BDF Tool - REGRULES.xlsx') as writer:
        column_list = ["Description", "Enum/Value"]
        df = DataFrame(list(DictDevCategory.items()), columns=column_list)
        df.to_excel(writer, sheet_name="Device Category", index=False)

        column_list = ["Enum_text", "Enum/Value"]
        df = DataFrame(list(DictCtlRegion.items()), columns=column_list)
        df.to_excel(writer, sheet_name="CTL Region", index=False)

        column_list = ["Freq Band", "Value"]
        df = DataFrame(list(DictFreqBand.items()), columns=column_list)
        df.to_excel(writer, sheet_name="Freq Bands for RegRules", index=False)

        update_PowerRules(writer)

        update_ArrayGainRules(writer)

        column_list = ["kHz/Name", "Enum/Value"]
        sheet_list_psd_rbw = [
            ['Null', 0],
            ['1000', 1],
            ['500', 2],
            ['3', 3]
        ]
        df = DataFrame(sheet_list_psd_rbw, columns=column_list)
        df.to_excel(writer, sheet_name="psd_rbw", index=False)

        sheet_list_reg_rules = []

        column_list = ['Table Entry', 'Device Category For Rule (dev_category)', 'CTL Region (ctl_region)', 'Freq Band (freq_band)', 'Power Rules Index', 'Array Gain Index']
        for i in range(devCategoryIndex):
            elem = []
            elem.append(i)
            elem.append(list(DictDevCategory.keys())[list(DictDevCategory.values()).index(g_device_category[i])])
            elem.append(list(DictCtlRegion.keys())[list(DictCtlRegion.values()).index(g_ctl_region[i])])
            elem.append(list(DictFreqBand.keys())[list(DictFreqBand.values()).index(g_freq_band[i])])
            elem.append(list(DictPowerRules.keys())[list(DictPowerRules.values()).index(g_power_rules[i])])
            elem.append(list(DictArrayGainRules.keys())[list(DictArrayGainRules.values()).index(g_array_gain_rules[i])])
            sheet_list_reg_rules.append(elem)
        df = DataFrame(sheet_list_reg_rules, columns=column_list)
        df.to_excel(writer, sheet_name="REGRULES", index=False)

# read the CTL RegRules from BDF
def read_bdf_RegRules(line):
    global g_file_var

    global devCategoryIndex
    global subBandIndex
    global ctlRegionIndex
    global powerRulesIndex
    global arrayGainIndex

    if 'regRulesEntries' not in line:
        return

    if ".devCategory" in line:
        temp = int(line.split('\t')[2])
        if temp in DictDevCategory.values():
            g_device_category.append(temp)
            devCategoryIndex += 1
    if "subBand" in line:
        temp = int(line.split('\t')[2])
        if temp in DictFreqBand.values():
            g_freq_band.append(temp)
            subBandIndex += 1
    if "regRulesEntries" in line and "ctlRegion" in line:
        temp = int(line.split('\t')[2])
        if temp in DictCtlRegion.values():
            g_ctl_region.append(temp)
            ctlRegionIndex += 1
    if "powerRulesIndex" in line:
        temp = int(line.split('\t')[2])
        if temp in DictPowerRules.values():
            g_power_rules.append(temp)
            powerRulesIndex += 1
    if "arrayGainIndex" in line:
        temp = int(line.split('\t')[2])
        if temp in DictArrayGainRules.values():
            g_array_gain_rules.append(temp)
            arrayGainIndex += 1

def update_PowerRules(writer):
    global isPsdIndex
    global arrayGainAllowIndex
    global totalEirpIndex
    global totalLimitIndex
    global psdLimitIndex
    global psdRbwIndex
    global psdLess20Index
    global psd20Index
    global psd40Index
    global psd80Index
    global psd160Index
    global psd320Index

    print("Updating Power Rules in RegRules Excel File\n")

    column_list = ['Description', 'Index', 'array_gain_allow', 'total_eirp', 'total_limit', 'psd_limit', 'psd_rbw', 'is_psd', 'psd_eirp_less_20Mhz', 'psd_eirp_20Mhz', 'psd_eirp_40Mhz', 'psd_eirp_80Mhz', 'psd_eirp_160Mhz', 'psd_eirp_320Mhz']
    sheet_list_power_rules = [list(x) for x in DictPowerRules.items()]

    for i in range(len(sheet_list_power_rules)):
        temp_idx = sheet_list_power_rules[i][1]
        if temp_idx >= len(g_array_gain_allow):
            sheet_list_power_rules[i].append(0)
        else:
            sheet_list_power_rules[i].append(g_array_gain_allow[temp_idx])
        if g_total_eirp[temp_idx] == 255:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_total_eirp[temp_idx])
        if g_total_limit[temp_idx] == 255:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_total_limit[temp_idx])
        if g_psd_limit[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_limit[temp_idx])
        if g_psd_rbw[temp_idx] == 1:
            sheet_list_power_rules[i].append(1000)
        elif g_psd_rbw[temp_idx] == 2:
            sheet_list_power_rules[i].append(500)
        elif g_psd_rbw[temp_idx] == 3:
            sheet_list_power_rules[i].append(3)
        else:
            sheet_list_power_rules[i].append('')
        if g_is_psd[temp_idx] == 2:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_is_psd[temp_idx])
        if g_psd_less_20[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_less_20[temp_idx])
        if g_psd_20[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_20[temp_idx])
        if g_psd_40[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_40[temp_idx])
        if g_psd_80[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_80[temp_idx])
        if g_psd_160[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_160[temp_idx])
        if g_psd_320[temp_idx] == -127:
            sheet_list_power_rules[i].append('')
        else:
            sheet_list_power_rules[i].append(g_psd_320[temp_idx])
        
    df = DataFrame(sheet_list_power_rules, columns=column_list)
    df.to_excel(writer, sheet_name="Power Rules", index=False)

# read the CTL PowerRules from BDF
def read_bdf_PowerRules(line):
    global g_file_var

    global isPsdIndex
    global arrayGainAllowIndex
    global totalEirpIndex
    global totalLimitIndex
    global psdLimitIndex
    global psdRbwIndex
    global psdLess20Index
    global psd20Index
    global psd40Index
    global psd80Index
    global psd160Index
    global psd320Index

    if "powerRulesEntries" not in line:
        return

    if ".isPSD" in line:
        g_is_psd.append(int(line.split('\t')[2]))
        isPsdIndex += 1
    if ".arrayGainAllow" in line:
        g_array_gain_allow.append(int(line.split('\t')[2]))
        arrayGainAllowIndex += 1
    if ".totalEIRP" in line:
        g_total_eirp.append(int(line.split('\t')[2]))
        totalEirpIndex += 1
    if ".totalLimit" in line:
        g_total_limit.append(int(line.split('\t')[2]))
        totalLimitIndex += 1
    if ".psdLimit" in line:
        g_psd_limit.append(int(line.split('\t')[2]))
        psdLimitIndex += 1
    if ".psdRBW" in line:
        g_psd_rbw.append(int(line.split('\t')[2]))
        psdRbwIndex += 1
    if ".psdEIRPLess20Mhz" in line:
        g_psd_less_20.append(int(line.split('\t')[2]))
        psdLess20Index += 1
    if ".psdEIRP20Mhz" in line:
        g_psd_20.append(int(line.split('\t')[2]))
        psd20Index += 1
    if ".psdEIRP40Mhz" in line:
        g_psd_40.append(int(line.split('\t')[2]))
        psd40Index += 1
    if ".psdEIRP80Mhz" in line:
        g_psd_80.append(int(line.split('\t')[2]))
        psd80Index += 1
    if ".psdEIRP160Mhz" in line:
        g_psd_160.append(int(line.split('\t')[2]))
        psd160Index += 1
    if ".psdEIRP320Mhz" in line:
        g_psd_320.append(int(line.split('\t')[2]))
        psd320Index += 1

def update_ArrayGainRules(writer):
    global eirpGainBFIndex
    global eirpGainNBFIndex
    global totalGainBFIndex
    global totalGainNBFIndex
    global psdGainBFIndex
    global psdGainNBFIndex

    print("Updating Array Gain Rules in RegRules Excel File\n")

    column_list = ['Description', 'Index', 'eirp_array_gain_for_beamform', 'eirp_array_gain_for_non_bf', 'total_array_gain_for_beamform', 'total_array_gain_for_non_bf', 'PSD_array_gain_for_beamform', 'PSD_array_gain_for_non_bf']
    sheet_list_array_gain_rules = [list(x) for x in DictArrayGainRules.items()]

    for i in range(len(sheet_list_array_gain_rules)):
        temp_idx = sheet_list_array_gain_rules[i][1]
        if g_eirp_array_gain_bf[temp_idx] == 1:
            sheet_list_array_gain_rules[i].append('E')
        elif g_eirp_array_gain_bf[temp_idx] == 2:
            sheet_list_array_gain_rules[i].append('F')
        elif g_eirp_array_gain_bf[temp_idx] == 0:
            sheet_list_array_gain_rules[i].append('N')

        if g_eirp_array_gain_nbf[temp_idx] == 1:
            sheet_list_array_gain_rules[i].append('E')
        elif g_eirp_array_gain_nbf[temp_idx] == 2:
            sheet_list_array_gain_rules[i].append('F')
        elif g_eirp_array_gain_nbf[temp_idx] == 0:
            sheet_list_array_gain_rules[i].append('N')

        if g_total_array_gain_bf[temp_idx] == 1:
            sheet_list_array_gain_rules[i].append('E')
        elif g_total_array_gain_bf[temp_idx] == 2:
            sheet_list_array_gain_rules[i].append('F')
        elif g_total_array_gain_bf[temp_idx] == 0:
            sheet_list_array_gain_rules[i].append('N')

        if g_total_array_gain_nbf[temp_idx] == 1:
            sheet_list_array_gain_rules[i].append('E')
        elif g_total_array_gain_nbf[temp_idx] == 2:
            sheet_list_array_gain_rules[i].append('F')
        elif g_total_array_gain_nbf[temp_idx] == 0:
            sheet_list_array_gain_rules[i].append('N')

        if g_psd_array_gain_bf[temp_idx] == 1:
            sheet_list_array_gain_rules[i].append('E')
        elif g_psd_array_gain_bf[temp_idx] == 2:
            sheet_list_array_gain_rules[i].append('F')
        elif g_psd_array_gain_bf[temp_idx] == 0:
            sheet_list_array_gain_rules[i].append('N')

        if g_psd_array_gain_nbf[temp_idx] == 1:
            sheet_list_array_gain_rules[i].append('E')
        elif g_psd_array_gain_nbf[temp_idx] == 2:
            sheet_list_array_gain_rules[i].append('F')
        elif g_psd_array_gain_nbf[temp_idx] == 0:
            sheet_list_array_gain_rules[i].append('N')
        
    df = DataFrame(sheet_list_array_gain_rules, columns=column_list)
    df.to_excel(writer, sheet_name="Array_Gain_Rules", index=False)

# read the CTL Array Gain Rules from BDF
def read_bdf_ArrayGainRules(line):
    global g_file_var

    global eirpGainBFIndex
    global eirpGainNBFIndex
    global totalGainBFIndex
    global totalGainNBFIndex
    global psdGainBFIndex
    global psdGainNBFIndex

    if "arrayGainRulesEntries" not in line:
        return

    if ".eirpArrayGainBF" in line:
        g_eirp_array_gain_bf.append(int(line.split('\t')[2]))
        eirpGainBFIndex += 1
    if ".eirpArrayGainNonBF" in line:
        g_eirp_array_gain_nbf.append(int(line.split('\t')[2]))
        eirpGainNBFIndex += 1
    if ".totalArrayGainBF" in line:
        g_total_array_gain_bf.append(int(line.split('\t')[2]))
        totalGainBFIndex += 1
    if ".totalArrayGainNonBF" in line:
        g_total_array_gain_nbf.append(int(line.split('\t')[2]))
        totalGainNBFIndex += 1
    if ".psdArrayGainBF" in line:
        g_psd_array_gain_bf.append(int(line.split('\t')[2]))
        psdGainBFIndex += 1
    if ".psdArrayGainNonBF" in line:
        g_psd_array_gain_nbf.append(int(line.split('\t')[2]))
        psdGainNBFIndex += 1

# Update the exception excel file with the parsed values
def update_Exception():
    global g_dictExcpTable
    global g_excp_mgmt_2g_startIdx, g_excp_mgmt_2g_endIdx
    global g_excp_mgmt_5g_startIdx, g_excp_mgmt_5g_endIdx
    global g_excp_mgmt_6g_startIdx, g_excp_mgmt_6g_endIdx
    global excpCtlRegionIndex
    global excpCtlGroupIndex
    global excpFreqSubbandIndex
    global excpValueIndex

    print("Updating Exception Excel File\n")

    with ExcelWriter('BDF Tool - EXCEPTIONS.xlsx') as writer:
        column_list = ["Enum_text", "Enum/Value"]
        df = DataFrame(list(DictCtlRegion.items()), columns=column_list)
        df.to_excel(writer, sheet_name="CTL Region", index=False)

        column_list = ["Enum_text", "Value"]
        sheet_list_ctl_groups = list(DictCtlGroup5G6G.items())
        sheet_list_ctl_groups.extend(list(DictCtlGroup2G.items()))
        df = DataFrame(sheet_list_ctl_groups, columns=column_list)
        df.to_excel(writer, sheet_name="CTL Groups", index=False)

        column_list = ['Enum / Value', 'Description', 'Freq Range']
        myDictSubFreq = {
            'SUB_BAND_2G': '2400-2483', 
            'SUB_BAND_UNII_1': '5150-5250', 
            'SUB_BAND_UNII_2a': '5250-5350', 
            'SUB_BAND_UNII_2c': '5470-5725', 
            'SUB_BAND_UNII_3_4': '5725-5895', 
            'SUB_BAND_UNII_5_LPI': '5925-6425', 
            'SUB_BAND_UNII_6_LPI': '6425-6525', 
            'SUB_BAND_UNII_7_LPI': '6525-6875', 
            'SUB_BAND_UNII_8_LPI': '6875-7125', 
            'SUB_BAND_UNII_5_VLP': '5925-6425', 
            'SUB_BAND_UNII_6_VLP': '6425-6525', 
            'SUB_BAND_UNII_7_VLP': '6525-6875', 
            'SUB_BAND_UNII_8_VLP': '6875-7125', 
            'SUB_BAND_UNII_5_SP': '5925-6425', 
            'SUB_BAND_UNII_6_SP': '6425-6525', 
            'SUB_BAND_UNII_7_SP': '6525-6875', 
            'SUB_BAND_UNII_8_SP': '6875-7125'
        }
        sheet_list_subband_freq = [[y, x, myDictSubFreq[x]] for x,y in DictSubBandExcp.items()]
        df = DataFrame(sheet_list_subband_freq, columns=column_list)
        df.to_excel(writer, sheet_name="Subband for Exceptions", index=False)

        column_list = ["Enum_text", "Bitmap"]
        df = DataFrame(list(DictPowerType6G.items()), columns=column_list)
        df.to_excel(writer, sheet_name="6G Category", index=False)

        column_list = ['Enum_text']
        sheet_list_band = ['5', '6', '2']
        df = DataFrame(sheet_list_band, columns=column_list)
        df.to_excel(writer, sheet_name="Band", index=False)

        column_list = [
            'Index', 
            'CTL Region', 
            'Must Choose LPI, VLP or SP (for 6G Only)', 
            'CTL Group', 
            'Fc or Subband', 
            'Value (-3 to +16dB)         [Zero Not allowed]   [.25 dB Increments]'
        ]
        sheet_list_exception_tbl = []
        for i in range(len(g_dictExcpTable)):
            elem = []
            elem.append(i)

            if g_dictExcpTable[i]['value'] == 0:
                continue
            
            idx = g_dictExcpTable[i]['ctl_region']
            elem.append(list(DictCtlRegion.keys())[list(DictCtlRegion.values()).index(idx)])

            idx = g_dictExcpTable[i]['ctl_group']
            if (idx & (3 << 5)) != 0:
                # 6G category is valid
                category = (idx & (3 << 5)) >> 5
                elem.append(list(DictPowerType6G.keys())[list(DictPowerType6G.values()).index(category)])
            else:
                elem.append('')

            if (idx & (1 << 7)) != 0:
                # This is 5G/6G
                category = (idx & 31)
                elem.append(list(DictCtlGroup5G6G.keys())[list(DictCtlGroup5G6G.values()).index(category)])
            else:
                # This is 2G
                category = (idx & 15)
                elem.append(list(DictCtlGroup2G.keys())[list(DictCtlGroup2G.values()).index(category)])

            idx = g_dictExcpTable[i]['fc_or_subband']
            if idx < len(DictSubBandExcp):
                elem.append(list(DictSubBandExcp.keys())[list(DictSubBandExcp.values()).index(idx)])
            else:
                elem.append(idx)
            
            idx = g_dictExcpTable[i]['value']
            elem.append((idx / MULTIPLIER_4))
            sheet_list_exception_tbl.append(elem)
        df = DataFrame(sheet_list_exception_tbl, columns=column_list)
        df.to_excel(writer, sheet_name="EXCEPTION TABLE", index=False)

# read the CTL Exception Table from BDF
def read_bdf_ExceptionTable(line):
    global g_file_var

    global excpCtlRegionIndex
    global excpCtlGroupIndex
    global excpFreqSubbandIndex
    global excpValueIndex

    if "ctlExceptionEntries" not in line:
        return

    if ".ctlRegion" in line:
        g_excp_ctl_region.append(int(line.split('\t')[2]))
        excpCtlRegionIndex += 1
    if ".ctlGroup" in line:
        g_excp_ctl_group.append(int(line.split('\t')[2]))
        excpCtlGroupIndex += 1
    if ".freqSubBand" in line:
        g_excp_fc_or_subband.append(int(line.split('\t')[2]))
        excpFreqSubbandIndex += 1
    if ".value" in line:
        g_excp_value.append(int(line.split('\t')[2]))
        excpValueIndex += 1

# read the CTL Exception Table from BDF
def read_bdf_ExceptionMgmt(line):
    global g_file_var

    global g_excp_mgmt_2g_startIdx, g_excp_mgmt_2g_endIdx
    global g_excp_mgmt_5g_startIdx, g_excp_mgmt_5g_endIdx
    global g_excp_mgmt_6g_startIdx, g_excp_mgmt_6g_endIdx

    if "ctlExcp" not in line:
        return

    if "ctlExcp2G" in line:
        for (key1 , value1) in DictCtlRegion.items():
            for  (key2, value2) in DictCtlGroup2G.items():
                region = DictCtlRegion[key1]
                ctl_group_2g = DictCtlGroup2G[key2]
                # Populate the freqIdxStart
                if f"ctlExcp2G[{region}].exceptionMgmt[{ctl_group_2g}].freqIdxStart" in line:
                    g_excp_mgmt_2g_startIdx[region][ctl_group_2g] = int(line.split('\t')[2])
                # Populate the freqIdxEnd
                elif f"ctlExcp2G[{region}].exceptionMgmt[{ctl_group_2g}].freqIdxEnd" in line:
                    g_excp_mgmt_2g_endIdx[region][ctl_group_2g] = int(line.split('\t')[2])
    elif "ctlExcp5G" in line:
        for (key1 , value1) in DictCtlRegion.items():
            for  (key2, value2) in DictCtlGroup5G6G.items():
                region = DictCtlRegion[key1]
                ctl_group_5g = DictCtlGroup5G6G[key2]
                # Populate the freqIdxStart
                if f"ctlExcp5G[{region}].exceptionMgmt[{ctl_group_5g}].freqIdxStart" in line:
                    g_excp_mgmt_5g_startIdx[region][ctl_group_5g] = int(line.split('\t')[2])
                # Populate the freqIdxEnd
                elif f"ctlExcp5G[{region}].exceptionMgmt[{ctl_group_5g}].freqIdxEnd" in line:
                    g_excp_mgmt_5g_endIdx[region][ctl_group_5g] = int(line.split('\t')[2])
    elif "ctlExcp6G" in line:
        for (key1 , value1) in DictCtlRegion.items():
            for  (key2, value2) in DictCtlGroup5G6G.items():
                region = DictCtlRegion[key1]
                ctl_group_6g = DictCtlGroup5G6G[key2]
                # Populate the freqIdxStart
                if f"ctlExcp6G[{region}].exceptionMgmt[{ctl_group_6g}].freqIdxStart" in line:
                    g_excp_mgmt_6g_startIdx[region][ctl_group_6g] = int(line.split('\t')[2])
                # Populate the freqIdxEnd
                elif f"ctlExcp6G[{region}].exceptionMgmt[{ctl_group_6g}].freqIdxEnd" in line:
                    g_excp_mgmt_6g_endIdx[region][ctl_group_6g] = int(line.split('\t')[2])


if __name__ == '__main__':
    cmdParser = argparse.ArgumentParser(description="Create Excel sheets from CTL ENGINE fields in the BDF")
    cmdParser.add_argument('-f', '--file', action="store", default="bdwlan.txt", help="BDF File to be populated")
    cmdParser.add_argument('-c', '--chip', action="store", default="hmt", help="chip name")
    args = cmdParser.parse_args()

    bdf_file_name = args.file
    chip = args.chip

    if chip == 'col':
        DictCtlRegion = config_qcc2072.CTL_REGION
        DictDevCategory = config_qcc2072.DEVICE_CATEGORY
        DictFreqBand = config_qcc2072.FREQ_BAND
        DictPowerRules = config_qcc2072.POWER_RULES
        DictArrayGainRules = config_qcc2072.ARRAY_GAIN_RULES
        DictSubBandExcp = config_qcc2072.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_qcc2072.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_qcc2072.CTL_GROUPS_2G
        DictPowerType6G = config_qcc2072.POWER_TYPE_6G
    if chip == 'orn':
        DictCtlRegion = config_wcn7750.CTL_REGION
        DictDevCategory = config_wcn7750.DEVICE_CATEGORY
        DictFreqBand = config_wcn7750.FREQ_BAND
        DictPowerRules = config_wcn7750.POWER_RULES
        DictArrayGainRules = config_wcn7750.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn7750.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn7750.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn7750.CTL_GROUPS_2G
        DictPowerType6G = config_wcn7750.POWER_TYPE_6G
    if chip == 'gng':
        DictCtlRegion = config_wcn7880.CTL_REGION
        DictDevCategory = config_wcn7880.DEVICE_CATEGORY
        DictFreqBand = config_wcn7880.FREQ_BAND
        DictPowerRules = config_wcn7880.POWER_RULES
        DictArrayGainRules = config_wcn7880.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn7880.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn7880.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn7880.CTL_GROUPS_2G
        DictPowerType6G = config_wcn7880.POWER_TYPE_6G
    if chip == 'cng':
        DictCtlRegion = config_wcn8850.CTL_REGION
        DictDevCategory = config_wcn8850.DEVICE_CATEGORY
        DictFreqBand = config_wcn8850.FREQ_BAND
        DictPowerRules = config_wcn8850.POWER_RULES
        DictArrayGainRules = config_wcn8850.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn8850.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn8850.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn8850.CTL_GROUPS_2G
        DictPowerType6G = config_wcn8850.POWER_TYPE_6G
    if chip == 'hmt':
        DictCtlRegion = config_wcn7850.CTL_REGION
        DictDevCategory = config_wcn7850.DEVICE_CATEGORY
        DictFreqBand = config_wcn7850.FREQ_BAND
        DictPowerRules = config_wcn7850.POWER_RULES
        DictArrayGainRules = config_wcn7850.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn7850.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn7850.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn7850.CTL_GROUPS_2G
        DictPowerType6G = config_wcn7850.POWER_TYPE_6G
    # populate the g_file_var global variable
    try:
        with open(bdf_file_name, 'r', encoding='utf-8') as fp: # Added encoding for Python 3
            g_file_var = fp.readlines()
    except FileNotFoundError:
        print(f"Error: BDF file '{bdf_file_name}' not found.")
        exit(1) # Exit if file is not found
    except UnicodeDecodeError:
        print(f"Error: Could not decode '{bdf_file_name}' with UTF-8. Try a different encoding (e.g., 'latin-1' or 'gbk').")
        exit(1)
    except Exception as e:
        print(f"An error occurred while reading '{bdf_file_name}': {e}")
        exit(1)

    print(f"\nBDF File selected: {bdf_file_name}\n") # Use f-string for Python 3.6+

    # Parse the BDF and populate global variable (Reading in the CTL Engine Fields in BDF)
    for string in g_file_var:
        if "CTL_ENGINE" in string:
            read_bdf_config(string)
            read_bdf_RegRules(string)
            read_bdf_PowerRules(string)
            read_bdf_ArrayGainRules(string)
            read_bdf_ExceptionTable(string)
            read_bdf_ExceptionMgmt(string)

    # Populate the global exception table dictionary with the parsed values
    for i in range(len(g_excp_ctl_region)):
        if g_excp_value[i] == 0:
            break
        g_dictExcpTable[i] = {'ctl_region' : g_excp_ctl_region[i], 
                       'ctl_group' : g_excp_ctl_group[i], 
                       'fc_or_subband' : g_excp_fc_or_subband[i],
                       'value' : g_excp_value[i] }

    # update the Config Excel File
    update_config()
    # update the RegRules Excel File
    update_RegRules()
    # update the Exception Excel File
    update_Exception()

    print("\nBDF Tool - CONFIG.xlsx,  BDF Tool - EXCEPTIONS.xlsx and BDF Tool - REGRULES.xlsx are updated from {}".format(bdf_file_name))
