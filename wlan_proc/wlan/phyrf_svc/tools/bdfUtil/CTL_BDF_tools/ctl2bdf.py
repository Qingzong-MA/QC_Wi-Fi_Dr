#import pandas as pd
from telnetlib import NOP
from pandas import read_excel, read_csv, ExcelWriter
from openpyxl import load_workbook
from functools import reduce
from itertools import takewhile
import warnings
# from pandas import ExcelFile
import sys, os, io
import argparse
#from datetime import date
import glob
import numpy

#import chip specific headers
import eHeavyClip as enhanced_heavy_clip
import config_wcn7850
import config_qcc2072
import config_wcn7750
import config_wcn7880
import config_qcn9224
import config_ipq5332_qcn6432

config_file = ""
regRules_file = ""
exceptions_file = ""
custom_exp_file_name = ""

bdf_file_name = ''
g_file_var = []

#CTL Config Global Variables
g_product_category = 0
g_ctl_regions_supported = 0
g_ant_gain = []
g_array_gain_cap = []
g_margin = []
g_max_penalty = [0, 0, 0]
g_hc_offset = []
g_exception_adjust = []
g_he_offset_5g = []
g_he_offset_2g = []
g_enable_exception = 0
g_ctl_flags = 0
g_6g_supported = 0
g_agCapExt2_ctl_Region_Map = []
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
arrayGainCapExt2Index1 = numpy.zeros(9)
arrayGainCapExt2Index2 = numpy.zeros(9)

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

def get_data_frame_from_excel(filename:str, sheet:str):
    try:
        warnings.simplefilter(action="ignore", category=UserWarning)
        wb = load_workbook(filename = filename, data_only = True)
        df = read_excel(wb, engine="openpyxl", sheet_name=sheet, skiprows=0, na_filter=False)
        # df.head()
        wb.close()
        warnings.resetwarnings()
        return df
    except PermissionError:
        print("{} is open. Please close it and try again".format(filename))
        sys.exit()
        
# Read the CTL Config from Excel file
def read_config():
    global g_product_category, g_ctl_regions_supported, g_enable_exception, g_ant_gain, g_array_gain_cap
    global g_6g_supported, g_margin, g_max_penalty, g_ctl_flags, g_exception_adjust#, g_hc_offset
    global  g_array_gain_cap_ext2_FCC, g_array_gain_cap_ext2_ETSI, g_EnableAGCapExt2
    fcc_array_gain = []
    etsi_array_gain = []

    ctl_Region_Map = []
    g_array_gain_cap_ext2_FCC = [[],[],[],[],[],[],[],[],[]]
    g_array_gain_cap_ext2_ETSI = [[],[],[],[],[],[],[],[],[]]
    g_EnableAGCapExt2 = 0
    df = get_data_frame_from_excel(config_file, sheet="CTL ENGINE CONFIG")
    print("Reading the Config Excel File \"{}\"".format(config_file))
    
    for i in df.index:
        if df['Field Name'][i] == 'Client or AP':
            if df['Value'][i].strip() == 'Client':
                g_product_category = 0
            elif df['Value'][i].strip() == 'AP':
                g_product_category = 1
        elif 'UL OFDMA' in df['Field Name'][i].upper():
            if 'NOT SUPPORTED' in df['Value'][i].upper():
                g_ctl_flags = 0
            else:
                g_ctl_flags = 1
        elif 'DL OFDMA' in df['Field Name'][i].upper():
            if 'SAME BW' in df['Value'][i].upper():
                g_ctl_flags |= 1 << 1
        elif '6G CATEGORIES SUPPORTED' in df['Field Name'][i].upper():
            power_type = df['Value'][i].upper()
            for types in power_type.split('|'):
                if types == 'LPI':
                    g_6g_supported += 1
                elif types == 'SP':
                    g_6g_supported += 2
                elif types == 'VLP':
                    g_6g_supported += 4
        elif df['Field Name'][i] == 'Supported CTL_Regions':
            temp = df['Value'][i]
            for string in temp.upper().split('|'):
                if string == 'FCC':
                    g_ctl_regions_supported += 1
                else:
                    value = 1 << DictCtlRegion[string] # ctlRegionsSupported is stored as a bit map in BDF
                    g_ctl_regions_supported += value
        elif df['Field Name'][i] == 'Enable Exception Table':
            if 'ENABLE' in df['Value'][i].upper():
                g_enable_exception = 1
            elif 'DISABLE' in df['Value'][i].upper():
                g_enable_exception = 0
        elif 'ADDED MARGIN' in df['Field Name'][i].upper():
            if ((df['Value'][i] != '') and (((df['Value'][i] * MULTIPLIER_4 ) >= -12) and ((df['Value'][i] * MULTIPLIER_4) <= 12))):
                g_margin.append(int(df['Value'][i] * MULTIPLIER_4))
            elif((df['Value'][i] != '') and ((int(df['Value'][i]) < -3) or (int(df['Value'][i]) > 3))):
                print( "Error: Margin not within limits. So defaulting to 0. Pls Check and update limit for "+df['Field Name'][i])
                g_margin.append(0)
            else:
                g_margin.append(0)
        elif 'MAX PENALTY' in df['Field Name'][i].upper():
            if df['Value'][i] != '':
                g_max_penalty.append(int(df['Value'][i] * MULTIPLIER_4))
            else:
                g_max_penalty.append(0)
        elif 'Ant_Gain' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -60) and ((df['Value'][i] * MULTIPLIER_4) <= 96)):
                g_ant_gain.append(int(df['Value'][i] * MULTIPLIER_4))
            elif((df['Value'][i] != '') and ((df['Value'][i]* MULTIPLIER_4) < -60)):
                print( "Error: Antenna Gain is less than min value. So defaulting to -60. Pls Check and update limit for "+df['Field Name'][i])
                g_ant_gain.append(-60)
            elif((df['Value'][i] != '') and (((df['Value'][i] * MULTIPLIER_4) > 96))):
                print( "Error: Antenna Gain is greater than max value. So defaulting to 96. Pls Check and update limit for "+df['Field Name'][i])
                g_ant_gain.append(96)
            else:
                g_ant_gain.append(0)
        elif 'FCC ARRAY GAIN CAP' in df['Field Name'][i].upper():
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= 10) and ((df['Value'][i] * MULTIPLIER_4) <= 52)):
                fcc_array_gain.append(int(df['Value'][i] * MULTIPLIER_4))
            if ((df['Value'][i] != '') and (((df['Value'][i] * MULTIPLIER_4) < 10) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap not within limits. So defaulting to 255. Pls Check and update limit for "+df['Field Name'][i])
                fcc_array_gain.append(255)
            else:
                # append 255 if Array Gain Cap is empty on the Excel Sheet
                fcc_array_gain.append(255)
        elif 'ETSI ARRAY GAIN CAP' in df['Field Name'][i].upper():
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= 10) and ((df['Value'][i] * MULTIPLIER_4) <= 52)):
                etsi_array_gain.append(int(df['Value'][i] * MULTIPLIER_4))
            if ((df['Value'][i] != '') and (((df['Value'][i] * MULTIPLIER_4) < 10) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap not within limits. So defaulting to 255. Pls Check and update limit for "+df['Field Name'][i])
                etsi_array_gain.append(255)
            else:
                # append 255 if Array Gain Cap is empty on the Excel Sheet
                etsi_array_gain.append(255)
        elif 'Ext_AG_Cap to CTL Region Mapping' in df['Field Name'][i]:
            if df['Value'][i] != '':
                temp = df['Value'][i]
                ctlRegionMap = 0
                for string in temp.upper().split('|'):
                    if string == 'FCC':
                        ctlRegionMap += 1
                    else:
                        value = 1 << DictCtlRegion[string] # ctlRegionsSupported is stored as a bit map in BDF
                        ctlRegionMap += value
                g_agCapExt2_ctl_Region_Map.append(ctlRegionMap)
            else:
                if 'Ext_AG_Cap to CTL Region Mapping - FCC Group' in df['Field Name'][i]:
                    print( "Defaulting Ext_AG_Cap to CTL Region Mapping - FCC Group to FCC")
                    g_agCapExt2_ctl_Region_Map.append(1)
                else:
                    print( "Defaulting Ext_AG_Cap to CTL Region Mapping - ETSI Group to ETSI")
                    g_agCapExt2_ctl_Region_Map.append(2)
        elif 'Enable_Extended_AG_Cap_Feature' in df['Field Name'][i]:
             if 'ENABLE' in df['Value'][i].upper():
                g_EnableAGCapExt2 = 1
             elif 'DISABLE' in df['Value'][i].upper():
                g_EnableAGCapExt2 = 0  
        elif 'FCC Extended AGain Cap Band 2_4' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[0].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[0].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[0].append(127)
        elif 'ETSI Extended AGain Cap Band 2_4' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[0].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[0].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[0].append(127)
        elif 'FCC Extended AGain Cap Band 5_2' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[1].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[1].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[1].append(127)
        elif 'ETSI Extended AGain Cap Band 5_2' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[1].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[1].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[1].append(127)
        elif 'FCC Extended AGain Cap Band 5_3' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[2].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[2].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[2].append(127)
        elif 'ETSI Extended AGain Cap Band 5_3' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[2].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[2].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[2].append(127)
        elif 'FCC Extended AGain Cap Band 5_6' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[3].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[3].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[3].append(127)
        elif 'ETSI Extended AGain Cap Band 5_6' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[3].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[3].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[3].append(127)
        elif 'FCC Extended AGain Cap Band 5_8' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[4].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[4].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[4].append(127)
        elif 'ETSI Extended AGain Cap Band 5_8' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[4].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[4].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[4].append(127)
        elif 'FCC Extended AGain Cap Band 6_2' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[5].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[5].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[5].append(127)
        elif 'ETSI Extended AGain Cap Band 6_2' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[5].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[5].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[5].append(127)
        elif 'FCC Extended AGain Cap Band 6_5' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[6].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[6].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[6].append(127)
        elif 'ETSI Extended AGain Cap Band 6_5' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[6].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[6].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[6].append(127)
        elif 'FCC Extended AGain Cap Band 6_7' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[7].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[7].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[7].append(127)
        elif 'ETSI Extended AGain Cap Band 6_7' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[7].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[7].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[7].append(127)
        elif 'FCC Extended AGain Cap Band 7_0' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_FCC[8].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_FCC[8].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_FCC[8].append(127)
        elif 'ETSI Extended AGain Cap Band 7_0' in df['Field Name'][i]:
            if ((df['Value'][i] != '') and ((df['Value'][i] * MULTIPLIER_4) >= -48 ) and (df['Value'][i] * MULTIPLIER_4) <= 52):
               g_array_gain_cap_ext2_ETSI[8].append(int(df['Value'][i] * MULTIPLIER_4))
            elif(df['Value'][i] != '' and (((df['Value'][i] * MULTIPLIER_4) < -48) or ((df['Value'][i] * MULTIPLIER_4) > 52))):
                print( "Error: Array Gain Cap Ext2 not within limits. So defaulting to 127. Pls Check and update limit for "+df['Field Name'][i])
                g_array_gain_cap_ext2_ETSI[8].append(127)
            else:
                # append 127 if Array Gain Cap is empty on the Excel Sheet
                g_array_gain_cap_ext2_ETSI[8].append(127)
    # append both FCC and ETSI to one array gain cap variable
    g_array_gain_cap.append(fcc_array_gain)
    g_array_gain_cap.append(etsi_array_gain)

    df_hc = get_data_frame_from_excel(config_file, "HC_Offset and Excpt_Adjust")

    for i in df_hc.index:
        if 'HC_OFFSET' in df_hc['Variable'][i].upper():
            if df_hc['Value'][i] != '':
                g_hc_offset.append(int(df_hc['Value'][i] * MULTIPLIER_4))
            else:
                g_hc_offset.append(0)
        elif 'PERCENT' in df_hc['Variable'][i].upper():
            if df_hc['Value'][i] != '':
                g_exception_adjust.append(int(df_hc['Value'][i] * MULTIPLIER_4))
            else:
                g_exception_adjust.append(0)
        elif 'HE_OFFSET_5G' in df_hc['Variable'][i].upper():
            if df_hc['Value'][i] != '':
                g_he_offset_5g.append(int(df_hc['Value'][i] * MULTIPLIER_4))
            else:
                g_he_offset_5g.append(0)
        elif 'HE_OFFSET_2G' in df_hc['Variable'][i].upper():
            if df_hc['Value'][i] != '':
                g_he_offset_2g.append(int(df_hc['Value'][i] * MULTIPLIER_4))
            else:
                g_he_offset_2g.append(0)


# update the CTL Config in BDF
def update_bdf_config(line):
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
    global arrayGainCapExtIndex
    global agCapExt2_ctlRegionMapIndex
    global arrayGainCapExt2Index1
    global arrayGainCapExt2Index2
    
    if "ctlConfig" not in line:
        return

    index = g_file_var.index(line)
    if "ctlRegionsSupported" in line:
        temp = " " + str(g_ctl_regions_supported) + " \n"
        line = line.replace(line.split('\t')[2], temp)
    if "ctlConfig.ctlFlags" in line:
        temp = " " + str(g_ctl_flags) + " \n"
        line = line.replace(line.split('\t')[2], temp)
    if "productCategory" in line:
        temp = " " + str(g_product_category) + " \n"
        line = line.replace(line.split('\t')[2], temp)
    if "ctlConfig.support6GCases" in line:
        temp = " " + str(g_6g_supported) + " \n"
        line = line.replace(line.split('\t')[2], temp)
    if "isExceptionEnabled" in line:
        temp = " " + str(g_enable_exception) + " \n"
        line = line.replace(line.split('\t')[2], temp)
    if "ctlConfig.antennaGain" in line:
        if antennaGainIndex < len(g_ant_gain):
            temp = " " + str(g_ant_gain[antennaGainIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        antennaGainIndex += 1
    if "ctlConfig.arrayGainCaps[0]" in line:
        if arrayGainCapIndex < len(g_array_gain_cap[0]):
            temp = " " + str(g_array_gain_cap[0][arrayGainCapIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapIndex += 1
    if "ctlConfig.arrayGainCaps[1]" in line:
        if arrayGainCapIndex1 < len(g_array_gain_cap[1]):
            temp = " " + str(g_array_gain_cap[1][arrayGainCapIndex1]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapIndex1 += 1
    if "ctlConfig.margin" in line:
        temp = " " + str(g_margin[marginIndex]) + " \n"
        line = line.replace(line.split('\t')[2], temp)
        marginIndex += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_enable" in line:
        temp = " " + str(g_EnableAGCapExt2) + " \n"
        line = line.replace(line.split('\t')[2], temp)
    if "ctlConfig_ext2.ctl_region_map" in line:
        if agCapExt2_ctlRegionMapIndex < len(g_agCapExt2_ctl_Region_Map):
            temp = " " + str(g_agCapExt2_ctl_Region_Map[agCapExt2_ctlRegionMapIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        agCapExt2_ctlRegionMapIndex += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][0]" in line:
        if arrayGainCapExt2Index1[0] < len(g_array_gain_cap_ext2_FCC[0]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[0][int(arrayGainCapExt2Index1[0])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][0]" in line:
        if arrayGainCapExt2Index1[0] < len(g_array_gain_cap_ext2_FCC[0]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[0][int(arrayGainCapExt2Index1[0])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][0]" in line:
        if arrayGainCapExt2Index1[0] < len(g_array_gain_cap_ext2_FCC[0]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[0][int(arrayGainCapExt2Index1[0])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][0]" in line:
        if arrayGainCapExt2Index2[0] < len(g_array_gain_cap_ext2_ETSI[0]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[0][int(arrayGainCapExt2Index2[0])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][0]" in line:
        if arrayGainCapExt2Index2[0] < len(g_array_gain_cap_ext2_ETSI[0]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[0][int(arrayGainCapExt2Index2[0])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][0]" in line:
        if arrayGainCapExt2Index2[0] < len(g_array_gain_cap_ext2_ETSI[0]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[0][int(arrayGainCapExt2Index2[0])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[0] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][1]" in line:
        if arrayGainCapExt2Index1[1] < len(g_array_gain_cap_ext2_FCC[1]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[1][int(arrayGainCapExt2Index1[1])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][1]" in line:
        if arrayGainCapExt2Index1[1] < len(g_array_gain_cap_ext2_FCC[1]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[1][int(arrayGainCapExt2Index1[1])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][1]" in line:
        if arrayGainCapExt2Index1[1] < len(g_array_gain_cap_ext2_FCC[1]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[1][int(arrayGainCapExt2Index1[1])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][1]" in line:
        if arrayGainCapExt2Index2[1] < len(g_array_gain_cap_ext2_ETSI[1]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[1][int(arrayGainCapExt2Index2[1])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][1]" in line:
        if arrayGainCapExt2Index2[1] < len(g_array_gain_cap_ext2_ETSI[1]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[1][int(arrayGainCapExt2Index2[1])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][1]" in line:
        if arrayGainCapExt2Index2[1] < len(g_array_gain_cap_ext2_ETSI[1]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[1][int(arrayGainCapExt2Index2[1])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[1] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][2]" in line:
        if arrayGainCapExt2Index1[2] < len(g_array_gain_cap_ext2_FCC[2]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[2][int(arrayGainCapExt2Index1[2])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][2]" in line:
        if arrayGainCapExt2Index1[2] < len(g_array_gain_cap_ext2_FCC[2]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[2][int(arrayGainCapExt2Index1[2])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][2]" in line:
        if arrayGainCapExt2Index1[2] < len(g_array_gain_cap_ext2_FCC[2]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[2][int(arrayGainCapExt2Index1[2])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][2]" in line:
        if arrayGainCapExt2Index2[2] < len(g_array_gain_cap_ext2_ETSI[2]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[2][int(arrayGainCapExt2Index2[2])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][2]" in line:
        if arrayGainCapExt2Index2[2] < len(g_array_gain_cap_ext2_ETSI[2]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[2][int(arrayGainCapExt2Index2[2])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][2]" in line:
        if arrayGainCapExt2Index2[2] < len(g_array_gain_cap_ext2_ETSI[2]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[2][int(arrayGainCapExt2Index2[2])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[2] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][3]" in line:
        if arrayGainCapExt2Index1[3] < len(g_array_gain_cap_ext2_FCC[3]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[3][int(arrayGainCapExt2Index1[3])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][3]" in line:
        if arrayGainCapExt2Index1[3] < len(g_array_gain_cap_ext2_FCC[3]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[3][int(arrayGainCapExt2Index1[3])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][3]" in line:
        if arrayGainCapExt2Index1[3] < len(g_array_gain_cap_ext2_FCC[3]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[3][int(arrayGainCapExt2Index1[3])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][3]" in line:
        if arrayGainCapExt2Index2[3] < len(g_array_gain_cap_ext2_ETSI[3]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[3][int(arrayGainCapExt2Index2[3])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][3]" in line:
        if arrayGainCapExt2Index2[3] < len(g_array_gain_cap_ext2_ETSI[3]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[3][int(arrayGainCapExt2Index2[3])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][3]" in line:
        if arrayGainCapExt2Index2[3] < len(g_array_gain_cap_ext2_ETSI[3]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[3][int(arrayGainCapExt2Index2[3])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[3] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][4]" in line:
        if arrayGainCapExt2Index1[4] < len(g_array_gain_cap_ext2_FCC[4]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[4][int(arrayGainCapExt2Index1[4])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][4]" in line:
        if arrayGainCapExt2Index1[4] < len(g_array_gain_cap_ext2_FCC[4]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[4][int(arrayGainCapExt2Index1[4])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][4]" in line:
        if arrayGainCapExt2Index1[4] < len(g_array_gain_cap_ext2_FCC[4]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[4][int(arrayGainCapExt2Index1[4])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][4]" in line:
        if arrayGainCapExt2Index2[4] < len(g_array_gain_cap_ext2_ETSI[4]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[4][int(arrayGainCapExt2Index2[4])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][4]" in line:
        if arrayGainCapExt2Index2[4] < len(g_array_gain_cap_ext2_ETSI[4]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[4][int(arrayGainCapExt2Index2[4])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][4]" in line:
        if arrayGainCapExt2Index2[4] < len(g_array_gain_cap_ext2_ETSI[4]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[4][int(arrayGainCapExt2Index2[4])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[4] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][5]" in line:
        if arrayGainCapExt2Index1[5] < len(g_array_gain_cap_ext2_FCC[5]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[5][int(arrayGainCapExt2Index1[5])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][5]" in line:
        if arrayGainCapExt2Index1[5] < len(g_array_gain_cap_ext2_FCC[5]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[5][int(arrayGainCapExt2Index1[5])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][5]" in line:
        if arrayGainCapExt2Index1[5] < len(g_array_gain_cap_ext2_FCC[5]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[5][int(arrayGainCapExt2Index1[5])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][5]" in line:
        if arrayGainCapExt2Index2[5] < len(g_array_gain_cap_ext2_ETSI[5]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[5][int(arrayGainCapExt2Index2[5])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][5]" in line:
        if arrayGainCapExt2Index2[5] < len(g_array_gain_cap_ext2_ETSI[5]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[5][int(arrayGainCapExt2Index2[5])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][5]" in line:
        if arrayGainCapExt2Index2[5] < len(g_array_gain_cap_ext2_ETSI[5]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[5][int(arrayGainCapExt2Index2[5])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[5] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][6]" in line:
        if arrayGainCapExt2Index1[6] < len(g_array_gain_cap_ext2_FCC[6]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[6][int(arrayGainCapExt2Index1[6])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][6]" in line:
        if arrayGainCapExt2Index1[6] < len(g_array_gain_cap_ext2_FCC[6]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[6][int(arrayGainCapExt2Index1[6])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][6]" in line:
        if arrayGainCapExt2Index1[6] < len(g_array_gain_cap_ext2_FCC[6]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[6][int(arrayGainCapExt2Index1[6])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][6]" in line:
        if arrayGainCapExt2Index2[6] < len(g_array_gain_cap_ext2_ETSI[6]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[6][int(arrayGainCapExt2Index2[6])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][6]" in line:
        if arrayGainCapExt2Index2[6] < len(g_array_gain_cap_ext2_ETSI[6]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[6][int(arrayGainCapExt2Index2[6])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][6]" in line:
        if arrayGainCapExt2Index2[6] < len(g_array_gain_cap_ext2_ETSI[6]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[6][int(arrayGainCapExt2Index2[6])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[6] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][7]" in line:
        if arrayGainCapExt2Index1[7] < len(g_array_gain_cap_ext2_FCC[7]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[7][int(arrayGainCapExt2Index1[7])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][7]" in line:
        if arrayGainCapExt2Index1[7] < len(g_array_gain_cap_ext2_FCC[7]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[7][int(arrayGainCapExt2Index1[7])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][7]" in line:
        if arrayGainCapExt2Index1[7] < len(g_array_gain_cap_ext2_FCC[7]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[7][int(arrayGainCapExt2Index1[7])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][7]" in line:
        if arrayGainCapExt2Index2[7] < len(g_array_gain_cap_ext2_ETSI[7]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[7][int(arrayGainCapExt2Index2[7])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][7]" in line:
        if arrayGainCapExt2Index2[7] < len(g_array_gain_cap_ext2_ETSI[7]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[7][int(arrayGainCapExt2Index2[7])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][7]" in line:
        if arrayGainCapExt2Index2[7] < len(g_array_gain_cap_ext2_ETSI[7]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[7][int(arrayGainCapExt2Index2[7])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[7] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[0][8]" in line:
        if arrayGainCapExt2Index1[8] < len(g_array_gain_cap_ext2_FCC[8]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[8][int(arrayGainCapExt2Index1[8])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[0][8]" in line:
        if arrayGainCapExt2Index1[8] < len(g_array_gain_cap_ext2_FCC[8]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[8][int(arrayGainCapExt2Index1[8])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[0][8]" in line:
        if arrayGainCapExt2Index1[8] < len(g_array_gain_cap_ext2_FCC[8]):
            temp = " " + str(g_array_gain_cap_ext2_FCC[8][int(arrayGainCapExt2Index1[8])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index1[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx4[1][8]" in line:
        if arrayGainCapExt2Index2[8] < len(g_array_gain_cap_ext2_ETSI[8]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[8][int(arrayGainCapExt2Index2[8])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx3[1][8]" in line:
        if arrayGainCapExt2Index2[8] < len(g_array_gain_cap_ext2_ETSI[8]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[8][int(arrayGainCapExt2Index2[8])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[8] += 1
    if "ctlConfig_ext2.arrayGainCaps_ext2_Ntx2[1][8]" in line:
        if arrayGainCapExt2Index2[8] < len(g_array_gain_cap_ext2_ETSI[8]):
            temp = " " + str(g_array_gain_cap_ext2_ETSI[8][int(arrayGainCapExt2Index2[8])]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainCapExt2Index2[8] += 1
    if "ctlConfig.maxPenalty" in line:
        temp = " " + str(g_max_penalty[maxPenaltyIndex]) + " \n"
        line = line.replace(line.split('\t')[2], temp)
        maxPenaltyIndex += 1
    if "ctlConfig.heavyClipOffsetMCS" in line:
        if hcOffsetIndex < len(g_hc_offset):
            temp = " " + str(g_hc_offset[hcOffsetIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        else: #MCS 8 - 13 uses the same HC offset value
            temp = " " + str(g_hc_offset[len(g_hc_offset) - 1]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        hcOffsetIndex += 1
    if "ctlConfig.exceptionAdjust" in line:
        if excpAdjustIndex < len(g_exception_adjust):
            temp = " " + str(g_exception_adjust[excpAdjustIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        excpAdjustIndex += 1
    if "ctlConfig.ctlData5G_HeOffset" in line:
        if heOffset5GIndex < len(g_he_offset_5g):
            temp = " " + str(g_he_offset_5g[heOffset5GIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        heOffset5GIndex += 1
    if "ctlConfig.ctlData2G_HeOffset" in line:
        if heOffset2GIndex < len(g_he_offset_2g):
            temp = " " + str(g_he_offset_2g[heOffset2GIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        heOffset2GIndex += 1
    
    g_file_var[index] = line


# Read the CTL RegRules from Excel file
def read_RegRules():
    df = get_data_frame_from_excel(regRules_file, "REGRULES")
    print("Reading the RegRules Excel File \"{}\"".format(regRules_file))
    
    for i in df.index:
        # populate the device category from RegRules
        index = df['Device Category For Rule (dev_category)'][i]
        g_device_category.append(DictDevCategory[index])

        # populate the CTL Region from RegRules
        index = df['CTL Region (ctl_region)'][i].upper()
        g_ctl_region.append(DictCtlRegion[index])

        # populate the Frequency Band from RegRules
        index = df['Freq Band (freq_band)'][i].strip()
        g_freq_band.append(DictFreqBand[index])

        # populate the Power Rules Index from RegRules
        index = df['Power Rules Index'][i].strip()
        g_power_rules.append(DictPowerRules[index])

        # populate the Array Gain Rules Index from RegRules
        index = df['Array Gain Index'][i].strip()
        g_array_gain_rules.append(DictArrayGainRules[index])


# update the CTL RegRules in BDF
def update_bdf_RegRules(line):
    global g_file_var

    global devCategoryIndex
    global subBandIndex
    global ctlRegionIndex
    global powerRulesIndex
    global arrayGainIndex

    if 'regRulesEntries' not in line:
        return

    index = g_file_var.index(line)
    if ".devCategory" in line:
        if devCategoryIndex < len(g_device_category): 
            temp = " " + str(g_device_category[devCategoryIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        devCategoryIndex += 1
    if "subBand" in line:
        if subBandIndex < len(g_freq_band): 
            temp = " " + str(g_freq_band[subBandIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        subBandIndex += 1
    if "regRulesEntries" in line and "ctlRegion" in line:
        if ctlRegionIndex < len(g_ctl_region): 
            temp = " " + str(g_ctl_region[ctlRegionIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        ctlRegionIndex += 1
    if "powerRulesIndex" in line:
        if powerRulesIndex < len(g_power_rules): 
            temp = " " + str(g_power_rules[powerRulesIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        powerRulesIndex += 1
    if "arrayGainIndex" in line:
        if arrayGainIndex < len(g_array_gain_rules): 
            temp = " " + str(g_array_gain_rules[arrayGainIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainIndex += 1
    
    g_file_var[index] = line


def read_PowerRules():
    df = get_data_frame_from_excel(regRules_file, "Power Rules")
    print("Reading Power Rules from RegRules Excel File \"{}\"".format(regRules_file))
    
    for i in df.index:
        g_pwr_rules_index.append(df['Index'][i])

        if df['array_gain_allow'][i] != '':
            g_array_gain_allow.append(df['array_gain_allow'][i])
        if df['total_eirp'][i] != '':
            g_total_eirp.append(df['total_eirp'][i])
        else:
            g_total_eirp.append(255)     
        if df['total_limit'][i] != '':
            g_total_limit.append(df['total_limit'][i])
        else:
            g_total_limit.append(255)
        if df['psd_limit'][i] != '':
            g_psd_limit.append(df['psd_limit'][i])
        else:
            g_psd_limit.append(-127)
        if df['psd_rbw'][i] == 1000:
            g_psd_rbw.append(1)
        elif df['psd_rbw'][i] == 500:
            g_psd_rbw.append(2)
        elif df['psd_rbw'][i] == 3:
            g_psd_rbw.append(df['psd_rbw'][i])
        else:
            g_psd_rbw.append(0)
        if df['is_psd'][i] == '':
            g_is_psd.append(2)
        else:
            g_is_psd.append(df['is_psd'][i])
        if df['psd_eirp_less_20Mhz'][i] != '':
            g_psd_less_20.append(df['psd_eirp_less_20Mhz'][i])
        else:
            g_psd_less_20.append(-127)
        if df['psd_eirp_20Mhz'][i] != '':
            g_psd_20.append(df['psd_eirp_20Mhz'][i])
        else:
            g_psd_20.append(-127)
        if df['psd_eirp_40Mhz'][i] != '':
            g_psd_40.append(df['psd_eirp_40Mhz'][i])
        else:
            g_psd_40.append(-127)
        if df['psd_eirp_80Mhz'][i] != '':
            g_psd_80.append(df['psd_eirp_80Mhz'][i])
        else:
            g_psd_80.append(-127)
        if df['psd_eirp_160Mhz'][i] != '':
            g_psd_160.append(df['psd_eirp_160Mhz'][i])
        else:
            g_psd_160.append(-127)
        if df['psd_eirp_320Mhz'][i] != '':
            g_psd_320.append(df['psd_eirp_320Mhz'][i])
        else:
            g_psd_320.append(-127)


# update the CTL PowerRules in BDF
def update_bdf_PowerRules(line):
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

    index = g_file_var.index(line)
    if ".isPSD" in line:
        if isPsdIndex < len(g_is_psd): 
            temp = " " + str(g_is_psd[isPsdIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        isPsdIndex += 1
    if ".arrayGainAllow" in line:
        if arrayGainAllowIndex < len(g_array_gain_allow): 
            temp = " " + str(g_array_gain_allow[arrayGainAllowIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        arrayGainAllowIndex += 1
    if ".totalEIRP" in line:
        if totalEirpIndex < len(g_total_eirp): 
            temp = " " + str(g_total_eirp[totalEirpIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        totalEirpIndex += 1
    if ".totalLimit" in line:
        if totalLimitIndex < len(g_total_limit): 
            temp = " " + str(g_total_limit[totalLimitIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        totalLimitIndex += 1
    if ".psdLimit" in line:
        if psdLimitIndex < len(g_psd_limit): 
            temp = " " + str(g_psd_limit[psdLimitIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psdLimitIndex += 1
    if ".psdRBW" in line:
        if psdRbwIndex < len(g_psd_rbw): 
            temp = " " + str(g_psd_rbw[psdRbwIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psdRbwIndex += 1
    if ".psdEIRPLess20Mhz" in line:
        if psdLess20Index < len(g_psd_less_20):
            temp = " " + str(g_psd_less_20[psdLess20Index]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psdLess20Index += 1
    if ".psdEIRP20Mhz" in line:
        if psd20Index < len(g_psd_20):
            temp = " " + str(g_psd_20[psd20Index]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psd20Index += 1
    if ".psdEIRP40Mhz" in line:
        if psd40Index < len(g_psd_40):
            temp = " " + str(g_psd_40[psd40Index]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psd40Index += 1
    if ".psdEIRP80Mhz" in line:
        if psd80Index < len(g_psd_80):
            temp = " " + str(g_psd_80[psd80Index]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psd80Index += 1
    if ".psdEIRP160Mhz" in line:
        if psd160Index < len(g_psd_160):
            temp = " " + str(g_psd_160[psd160Index]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psd160Index += 1
    if ".psdEIRP320Mhz" in line:
        if psd320Index < len(g_psd_320):
            temp = " " + str(g_psd_320[psd320Index]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psd320Index += 1

    g_file_var[index] = line


def read_ArrayGainRules():
    df = get_data_frame_from_excel(regRules_file, "Array_Gain_Rules")
    print("Reading Array Gain Rules from RegRules Excel File \"{}\"".format(regRules_file))
    
    for i in df.index:
        if df['Index'][i] != '':
            g_array_rules_index.append(df['Index'][i])

        if df['eirp_array_gain_for_beamform'][i] == 'E':
            g_eirp_array_gain_bf.append(1)
        elif df['eirp_array_gain_for_beamform'][i] == 'F':
            g_eirp_array_gain_bf.append(2)
        elif df['eirp_array_gain_for_beamform'][i] == 'N':
            g_eirp_array_gain_bf.append(0)
        
        if df['eirp_array_gain_for_non_bf'][i] == 'E':
            g_eirp_array_gain_nbf.append(1)
        elif df['eirp_array_gain_for_non_bf'][i] == 'F':
            g_eirp_array_gain_nbf.append(2)
        elif df['eirp_array_gain_for_non_bf'][i] == 'N':
            g_eirp_array_gain_nbf.append(0)
        
        if df['total_array_gain_for_beamform'][i] == 'E':
            g_total_array_gain_bf.append(1)
        elif df['total_array_gain_for_beamform'][i] == 'F':
            g_total_array_gain_bf.append(2)
        elif df['total_array_gain_for_beamform'][i] == 'N':
            g_total_array_gain_bf.append(0)
        
        if df['total_array_gain_for_non_bf'][i] == 'E':
            g_total_array_gain_nbf.append(1)
        elif df['total_array_gain_for_non_bf'][i] == 'F':
            g_total_array_gain_nbf.append(2)
        elif df['total_array_gain_for_non_bf'][i] == 'N':
            g_total_array_gain_nbf.append(0)
        
        if df['PSD_array_gain_for_beamform'][i] == 'E':
            g_psd_array_gain_bf.append(1)
        elif df['PSD_array_gain_for_beamform'][i] == 'F':
            g_psd_array_gain_bf.append(2)
        elif df['PSD_array_gain_for_beamform'][i] == 'N':
            g_psd_array_gain_bf.append(0)
        
        if df['PSD_array_gain_for_non_bf'][i] == 'E':
            g_psd_array_gain_nbf.append(1)
        elif df['PSD_array_gain_for_non_bf'][i] == 'F':
            g_psd_array_gain_nbf.append(2)
        elif df['PSD_array_gain_for_non_bf'][i] == 'N':
            g_psd_array_gain_nbf.append(0)


# update the CTL Array Gain Rules in BDF
def update_bdf_ArrayGainRules(line):
    global g_file_var

    global eirpGainBFIndex
    global eirpGainNBFIndex
    global totalGainBFIndex
    global totalGainNBFIndex
    global psdGainBFIndex
    global psdGainNBFIndex

    if "arrayGainRulesEntries" not in line:
        return

    index = g_file_var.index(line)
    if ".eirpArrayGainBF" in line:
        if eirpGainBFIndex < len(g_eirp_array_gain_bf): 
            temp = " " + str(g_eirp_array_gain_bf[eirpGainBFIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        eirpGainBFIndex += 1
    if ".eirpArrayGainNonBF" in line:
        if eirpGainNBFIndex < len(g_eirp_array_gain_nbf): 
            temp = " " + str(g_eirp_array_gain_nbf[eirpGainNBFIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        eirpGainNBFIndex += 1
    if ".totalArrayGainBF" in line:
        if totalGainBFIndex < len(g_total_array_gain_bf): 
            temp = " " + str(g_total_array_gain_bf[totalGainBFIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        totalGainBFIndex += 1
    if ".totalArrayGainNonBF" in line:
        if totalGainNBFIndex < len(g_total_array_gain_nbf): 
            temp = " " + str(g_total_array_gain_nbf[totalGainNBFIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        totalGainNBFIndex += 1
    if ".psdArrayGainBF" in line:
        if psdGainBFIndex < len(g_psd_array_gain_bf): 
            temp = " " + str(g_psd_array_gain_bf[psdGainBFIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psdGainBFIndex += 1
    if ".psdArrayGainNonBF" in line:
        if psdGainNBFIndex < len(g_psd_array_gain_nbf): 
            temp = " " + str(g_psd_array_gain_nbf[psdGainNBFIndex]) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        psdGainNBFIndex += 1

    g_file_var[index] = line



# Read the exception excel file and populate the variables
def read_Exception():
    global g_dictExcpTable
    global g_excp_mgmt_2g_startIdx, g_excp_mgmt_2g_endIdx
    global g_excp_mgmt_5g_startIdx, g_excp_mgmt_5g_endIdx
    global g_excp_mgmt_6g_startIdx, g_excp_mgmt_6g_endIdx

    ## FIXME
    '''
    pandas\core\dtypes\cast.py:1429: DeprecationWarning: np.find_common_type is deprecated.  Please use `np.result_type` or `np.promote_types`.
    See https://numpy.org/devdocs/release/1.25.0-notes.html and the docs for more information.  (Deprecated NumPy 1.25)
    '''
    warnings.simplefilter(action="ignore", category=DeprecationWarning)
    if custom_exp_file_name != "":
        try:
            print("Import exceptions list from \"{}\" and overwriting exceptions list in \"{}\"".format(custom_exp_file_name, exceptions_file))

            # CSV exported from QRCT has some additional meta data, which is stripped by the below snippet
            csv_string=""
            with open(custom_exp_file_name) as excp_file:
                lines = excp_file.readlines()
                start_idx = 1 if lines[0].startswith("---") else 0  # Skip first line if it is section separator ---
                excep_lines = takewhile(lambda line: not line.startswith("---"), lines[start_idx:]) # Read lines till it contains section separator ---
                csv_string = reduce(lambda l1,l2 : l1+l2, excep_lines)

            df = read_csv(io.StringIO(csv_string), na_filter=False)

            # Mapping between the column names of the imported CSV and the Excel file.
            column_mapping = {
                "6G Category":"Must Choose LPI, VLP or SP (for 6G Only)", 
                "Exception Power": "Value (-3 to +16dB)         [Zero Not allowed]   [.25 dB Increments]"
            }
            # To better align with the name in the Excel and works better with bdf2ctl.py
            df.rename(columns=column_mapping, inplace=True)
        except PermissionError:
            print("{} is open. Please close the Excel file and try again".format(custom_exp_file_name))
            exit()
    else:
        df = get_data_frame_from_excel(exceptions_file, "EXCEPTION TABLE")
    warnings.resetwarnings()

    print("Reading Exception Excel File \"{}\"".format(exceptions_file))
    
    for i in df.index:
        ctl_group = 0

        region = df['CTL Region'][i].upper()
        if (region != ''):
            g_excp_ctl_region.append(DictCtlRegion[region])
        else:
            break

        index = df['Must Choose LPI, VLP or SP (for 6G Only)'][i].strip()


        if (index != '') and (index != '2/5G'):
            if ("6G" in index):
                pos = index.find('_')
                index = index[(pos+1):]
            ctl_group += DictPowerType6G[index] << 5

        try:
            index = df['CTL Group'][i].strip()
            if "2G" in index:
                ctl_group += DictCtlGroup2G[index]
            elif "5G" in index or "6G" in index:
                ctl_group += DictCtlGroup5G6G[index]
                ctl_group += 1 << 7     # Set MSB as 1 for 5G/6G 
        except KeyError:
            if "5G" in index or "6G" in index:
                temp_index = index.split("_")
                rates_strings = temp_index[len(temp_index) - 1].split('/')
                ratesInString = False
                for itr in DictCtlGroup5G6G.keys():
                    temp_itr = itr.split("_")
                    if temp_index[1] != temp_itr[1]:
                        continue
                    for j in range(len(rates_strings)+1):
                        if (j >= len(rates_strings)) or (rates_strings[j] not in itr):
                            break
                    if (j >= len(rates_strings)):
                        ratesInString = True
                        break
                if ratesInString == False:
                    print("Couldn't map the CTL group " + index + ". Please review the name again in the reference Exceptions CTL file.")
                    exit(-1)
                ctl_group += DictCtlGroup5G6G[itr]
                ctl_group += 1 << 7     # Set MSB as 1 for 5G/6G
            else:
                print("Couldn't map the CTL group " + index + ". Please review the name again in the reference Exceptions CTL file.")
                exit(-1)


        # append to the ctl_group list
        g_excp_ctl_group.append(ctl_group)
        
        index = df['Fc or Subband'][i]
        try:
            index = index.strip()
        except AttributeError:
            index = index
        if index != '':
            try:
                g_excp_fc_or_subband.append(int(DictSubBandExcp[str(index).split(' ')[0]]))  # subband Exception
            except KeyError:
                g_excp_fc_or_subband.append(int(index))  # Frequency Exception


        value = df['Value (-3 to +16dB)         [Zero Not allowed]   [.25 dB Increments]'][i]
        
        if index != '':
            g_excp_value.append(int(float(value) * MULTIPLIER_4))
    
    if custom_exp_file_name != "":
        warnings.simplefilter(action="ignore", category=UserWarning)
        excelbook = load_workbook(exceptions_file)
        del excelbook["EXCEPTION TABLE"]
        excelbook.save(exceptions_file)
        warnings.resetwarnings()

        with ExcelWriter(exceptions_file, mode='a') as writer:
            df.to_excel(writer, sheet_name="EXCEPTION TABLE", index=False)
        print("Update exception excel file \"{}\"".format(exceptions_file))

    dictTest = {}    # dictionary to store and sort the exception table
    for i in range(len(g_excp_ctl_region)):
        dictTest[i] = {'ctl_region' : g_excp_ctl_region[i], 
                       'ctl_group' : g_excp_ctl_group[i], 
                       'fc_or_subband' : g_excp_fc_or_subband[i],
                       'value' : g_excp_value[i] }

    #sort the dictionary
    dictTest = dict(sorted(dictTest.items(), key = lambda x: (x[1]['ctl_region'], x[1]['ctl_group'], x[1]['fc_or_subband'])))

    # To make the index(Key) in order (0,1,2...N) for easy access
    index = 0
    for k,v in dictTest.items():
        g_dictExcpTable[index] = v
        index += 1
        #print(v, v['ctl_group'] & 0x1F)

    # Validations
    ## Duplicate Exception Entry Detection
    if len(g_dictExcpTable) > 0:
        duplicateItem = False
        item = g_dictExcpTable[0]
        for i in range(1,len(g_dictExcpTable)):
            item2 = g_dictExcpTable[i]
            if item['ctl_region'] == item2['ctl_region'] and item['ctl_group'] == item2['ctl_group'] and item['fc_or_subband'] == item2['fc_or_subband']:
                duplicateItem = True
                break
            item = item2

        ## Check for Zero Values
        zeroExcep = next(filter(lambda x: x['value']==0,g_dictExcpTable.values()),False)
        
        ## Check for valid exception entry range
        MIN_RANGE = -12
        MAX_RANGE = 64
        rangeExcep = next(filter(lambda x: x['value'] < MIN_RANGE or  x['value'] > MAX_RANGE,g_dictExcpTable.values()),False)

        ## Check for Subband Entries > 80MHz
        MIN_FREQ = 256
        CTL_GRP_160_START = 13
        subbandAbove80 = next(filter(lambda x: x['fc_or_subband'] < MIN_FREQ and x['ctl_group']&0x1F >= CTL_GRP_160_START,g_dictExcpTable.values()),False)

        if zeroExcep != False:
            print("ERROR: Zero Value for Exception is invalid.")
        if rangeExcep != False:
            print("ERROR: Out of range Exception entries.")
        if duplicateItem:
            print("ERROR: Duplicate Exception Entry found.")
        if subbandAbove80 != False:
            print("ERROR: Subband Exception Entries above 80MHz are not allowed.")

        ## Return in case of any error
        if (zeroExcep != False) or (rangeExcep != False) or duplicateItem or (subbandAbove80 != False):
            print("Exiting...")
            sys.exit(1)


    #Populate the 2G, 5G and 6G Excp management variables
    for k,v in g_dictExcpTable.items():
        if v['ctl_group'] < 0x1F:  #2G
            if g_excp_mgmt_2g_startIdx[v['ctl_region']][v['ctl_group']] == -1:
                g_excp_mgmt_2g_startIdx[v['ctl_region']][v['ctl_group']] = k
                g_excp_mgmt_2g_endIdx[v['ctl_region']][v['ctl_group']] = k
            else:
                g_excp_mgmt_2g_endIdx[v['ctl_region']][v['ctl_group']] = k
        # 0x60 translates to 6th and 7th bit on. If the below condition is zero
        # then its 5G
        elif v['ctl_group'] & 0x60 == 0 and v['ctl_group'] & 0x1F != 19:   #5G
            # bits 0-4 are used for packet types
            ctl_group = v['ctl_group'] & 0x1F
            if g_excp_mgmt_5g_startIdx[v['ctl_region']][ctl_group] == -1:
                g_excp_mgmt_5g_startIdx[v['ctl_region']][ctl_group] = k
                g_excp_mgmt_5g_endIdx[v['ctl_region']][ctl_group] = k
            else:
                g_excp_mgmt_5g_endIdx[v['ctl_region']][ctl_group] = k
        else:   #6G
            # bits 0-4 are used for packet types
            ctl_group = v['ctl_group'] & 0x1F
            if g_excp_mgmt_6g_startIdx[v['ctl_region']][ctl_group] == -1:
                g_excp_mgmt_6g_startIdx[v['ctl_region']][ctl_group] = k
                g_excp_mgmt_6g_endIdx[v['ctl_region']][ctl_group] = k
            else:
                g_excp_mgmt_6g_endIdx[v['ctl_region']][ctl_group] = k


# update the CTL Exception Table in BDF
def update_bdf_ExceptionTable(line):
    global g_file_var

    global excpCtlRegionIndex
    global excpCtlGroupIndex
    global excpFreqSubbandIndex
    global excpValueIndex

    if "ctlExceptionEntries" not in line:
        return

    index = g_file_var.index(line)
    if ".ctlRegion" in line:
        if excpCtlRegionIndex < len(g_dictExcpTable):
            temp = " " + str(g_dictExcpTable[excpCtlRegionIndex]['ctl_region']) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        excpCtlRegionIndex += 1
    if ".ctlGroup" in line:
        if excpCtlGroupIndex < len(g_dictExcpTable):
            temp = " " + str(g_dictExcpTable[excpCtlGroupIndex]['ctl_group']) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        excpCtlGroupIndex += 1
    if ".freqSubBand" in line:
        if excpFreqSubbandIndex < len(g_dictExcpTable):
            temp = " " + str(g_dictExcpTable[excpFreqSubbandIndex]['fc_or_subband']) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        excpFreqSubbandIndex += 1
    if ".value" in line:
        if excpValueIndex < len(g_dictExcpTable):
            temp = " " + str(g_dictExcpTable[excpValueIndex]['value']) + " \n"
            line = line.replace(line.split('\t')[2], temp)
        excpValueIndex += 1
    
    g_file_var[index] = line


# update the CTL Exception Table in BDF
def update_bdf_ExceptionMgmt(line):
    global g_file_var

    if "ctlExcp" not in line:
        return

    index = g_file_var.index(line)

    if "ctlExcp2G" in line:
        for (key1 , value1) in DictCtlRegion.items():
            for  (key2, value2) in DictCtlGroup2G.items():
                region = DictCtlRegion[key1]
                ctl_group_2g = DictCtlGroup2G[key2]
                # Populate the freqIdxStart
                if "ctlExcp2G[{}].exceptionMgmt[{}].freqIdxStart".format(region, ctl_group_2g) in line:
                    if g_excp_mgmt_2g_startIdx[region][ctl_group_2g] != -1:
                        temp = " " + str(g_excp_mgmt_2g_startIdx[region][ctl_group_2g]) + " \n"
                        line = line.replace(line.split('\t')[2], temp)
                # Populate the freqIdxEnd
                elif "ctlExcp2G[{}].exceptionMgmt[{}].freqIdxEnd".format(region, ctl_group_2g) in line:
                    if g_excp_mgmt_2g_endIdx[region][ctl_group_2g] != -1:
                        temp = " " + str(g_excp_mgmt_2g_endIdx[region][ctl_group_2g]) + " \n"
                        line = line.replace(line.split('\t')[2], temp)
    elif "ctlExcp5G" in line:
        for (key1 , value1) in DictCtlRegion.items():
            for  (key2, value2) in DictCtlGroup5G6G.items():
                region = DictCtlRegion[key1]
                ctl_group_5g = DictCtlGroup5G6G[key2]
                # Populate the freqIdxStart
                if "ctlExcp5G[{}].exceptionMgmt[{}].freqIdxStart".format(region, ctl_group_5g) in line:
                    if g_excp_mgmt_5g_startIdx[region][ctl_group_5g] != -1:
                        temp = " " + str(g_excp_mgmt_5g_startIdx[region][ctl_group_5g]) + " \n"
                        line = line.replace(line.split('\t')[2], temp)
                # Populate the freqIdxEnd
                elif "ctlExcp5G[{}].exceptionMgmt[{}].freqIdxEnd".format(region, ctl_group_5g) in line:
                    if g_excp_mgmt_5g_endIdx[region][ctl_group_5g] != -1:
                        temp = " " + str(g_excp_mgmt_5g_endIdx[region][ctl_group_5g]) + " \n"
                        line = line.replace(line.split('\t')[2], temp)
    elif "ctlExcp6G" in line:
        for (key1 , value1) in DictCtlRegion.items():
            for  (key2, value2) in DictCtlGroup5G6G.items():
                region = DictCtlRegion[key1]
                ctl_group_6g = DictCtlGroup5G6G[key2]
                # Populate the freqIdxStart
                if "ctlExcp6G[{}].exceptionMgmt[{}].freqIdxStart".format(region, ctl_group_6g) in line:
                    if g_excp_mgmt_6g_startIdx[region][ctl_group_6g] != -1:
                        temp = " " + str(g_excp_mgmt_6g_startIdx[region][ctl_group_6g]) + " \n"
                        line = line.replace(line.split('\t')[2], temp)
                # Populate the freqIdxEnd
                elif "ctlExcp6G[{}].exceptionMgmt[{}].freqIdxEnd".format(region, ctl_group_6g) in line:
                    if g_excp_mgmt_6g_endIdx[region][ctl_group_6g] != -1:
                        temp = " " + str(g_excp_mgmt_6g_endIdx[region][ctl_group_6g]) + " \n"
                        line = line.replace(line.split('\t')[2], temp)

    g_file_var[index] = line



def create_bdf_file(file_name):
    # Create the new bdf file with the values populated
    file_write = open(file_name, "w+")
    for line in g_file_var:
        file_write.writelines(line)
    file_write.close()


#clear the CTL_ENGINE fields before updating the fields
def clear_bdf_file(file_name):
    fp = open(bdf_file_name, 'r')
    bdf_file = fp.readlines()
    fp.close()

    for line in bdf_file:
        index = g_file_var.index(line)
        if "CTL_ENGINE" in line:
            temp = " " + "0" + " \n"
            line = line.replace(line.split('\t')[2], temp)
            if "CTL_ENGINE.nvCtl.nvId" not in line and "CTL_ENGINE.nvCtl.nvLen" not in line and "ctlConfig_ext.additional_arrayGainCaps_forMaxNtxNss" not in line:
                g_file_var[index] = line


if __name__ == '__main__':
    cmdParser = argparse.ArgumentParser(description="Populate CTL ENGINE fields in the BDF")
    cmdParser.add_argument('-f', '--file', action="store", default="bdwlan.txt", help="BDF File to be populated")
    cmdParser.add_argument('-c', '--chip', action="store", default="wcn7850", help="[wcn7850/qcn9224/ipq5332/qcn6432]")
    cmdParser.add_argument('-e', '--expfile', action="store", default="", help="name of custom exceptions .csv file")
    cmdParser.add_argument("-ho", "--heavyclipOffset", dest="sheet_HC", help="expanded heavy clip excel file")
    args = cmdParser.parse_args()

    bdf_file_name = args.file
    custom_exp_file_name = args.expfile
    print("Executing ctl2bdf script for chip - {}".format(args.chip))

    ## FIXME
    ## This can be optimized with parent import for entire CTL engine and inherited import based on chip for heavy clip
    ## Fixme can be done iff CTL engine remains common across wifi7 chipsets
    if args.chip == 'qcc2072':
        DictCtlRegion = config_qcc2072.CTL_REGION
        DictDevCategory = config_qcc2072.DEVICE_CATEGORY
        DictFreqBand = config_qcc2072.FREQ_BAND
        DictPowerRules = config_qcc2072.POWER_RULES
        DictArrayGainRules = config_qcc2072.ARRAY_GAIN_RULES
        DictSubBandExcp = config_qcc2072.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_qcc2072.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_qcc2072.CTL_GROUPS_2G
        DictPowerType6G = config_qcc2072.POWER_TYPE_6G
        enhanced_heavy_clip_import = None
    if args.chip == 'wcn7750':
        DictCtlRegion = config_wcn7750.CTL_REGION
        DictDevCategory = config_wcn7750.DEVICE_CATEGORY
        DictFreqBand = config_wcn7750.FREQ_BAND
        DictPowerRules = config_wcn7750.POWER_RULES
        DictArrayGainRules = config_wcn7750.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn7750.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn7750.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn7750.CTL_GROUPS_2G
        DictPowerType6G = config_wcn7750.POWER_TYPE_6G
        enhanced_heavy_clip_import = None
    if args.chip == 'wcn7880':
        DictCtlRegion = config_wcn7880.CTL_REGION
        DictDevCategory = config_wcn7880.DEVICE_CATEGORY
        DictFreqBand = config_wcn7880.FREQ_BAND
        DictPowerRules = config_wcn7880.POWER_RULES
        DictArrayGainRules = config_wcn7880.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn7880.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn7880.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn7880.CTL_GROUPS_2G
        DictPowerType6G = config_wcn7880.POWER_TYPE_6G
        enhanced_heavy_clip_import = None
    if args.chip == 'wcn7850':
        DictCtlRegion = config_wcn7850.CTL_REGION
        DictDevCategory = config_wcn7850.DEVICE_CATEGORY
        DictFreqBand = config_wcn7850.FREQ_BAND
        DictPowerRules = config_wcn7850.POWER_RULES
        DictArrayGainRules = config_wcn7850.ARRAY_GAIN_RULES
        DictSubBandExcp = config_wcn7850.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_wcn7850.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_wcn7850.CTL_GROUPS_2G
        DictPowerType6G = config_wcn7850.POWER_TYPE_6G
        enhanced_heavy_clip_import = None
        # enhanced_heavy_clip_import = config_wcn7850.ENHANCED_HEAVY_CLIP

    elif args.chip == "qcn9224":
        DictCtlRegion = config_qcn9224.CTL_REGION
        DictDevCategory = config_qcn9224.DEVICE_CATEGORY
        DictFreqBand = config_qcn9224.FREQ_BAND
        #DictPowerRules = config_qcn9224.POWER_RULES
        DictArrayGainRules = config_qcn9224.ARRAY_GAIN_RULES
        DictSubBandExcp = config_qcn9224.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_qcn9224.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_qcn9224.CTL_GROUPS_2G
        DictPowerType6G = config_qcn9224.POWER_TYPE_6G
        enhanced_heavy_clip_import = config_qcn9224.ENHANCED_HEAVY_CLIP

    elif args.chip == "ipq5332" or args.chip == "qcn6432":
        DictCtlRegion = config_ipq5332_qcn6432.CTL_REGION
        DictDevCategory = config_ipq5332_qcn6432.DEVICE_CATEGORY
        DictFreqBand = config_ipq5332_qcn6432.FREQ_BAND
        #DictPowerRules = config_ipq5332_qcn6432.POWER_RULES
        DictArrayGainRules = config_ipq5332_qcn6432.ARRAY_GAIN_RULES
        DictSubBandExcp = config_ipq5332_qcn6432.SUBBAND_EXCEPTIONS
        DictCtlGroup5G6G = config_ipq5332_qcn6432.CTL_GROUPS_5G_6G
        DictCtlGroup2G = config_ipq5332_qcn6432.CTL_GROUPS_2G
        DictPowerType6G = config_ipq5332_qcn6432.POWER_TYPE_6G
        enhanced_heavy_clip_import = config_ipq5332_qcn6432.ENHANCED_HEAVY_CLIP


    ## Updating only 
    if args.sheet_HC and enhanced_heavy_clip_import:
        enhanced_heavy_clip_import["FILE_NAME"] = args.sheet_HC
        enhanced_heavy_clip_import["BDF_NAME"] = bdf_file_name
        # Heavy clip MCS offset
        print("BDF \"{}\" used to update heavy clip MCS offset".format(bdf_file_name))
        enhanced_heavy_clip.main(enhanced_heavy_clip_import)
    else:
        #populate the excel file name variable
        excel_file_list = glob.glob("*.xlsx")
        for file_name in excel_file_list:
            if "CONFIG" in file_name:
                config_file = file_name
            elif "REGRULES" in file_name:
                regRules_file = file_name
            elif "EXCEPTIONS" in file_name:
                exceptions_file = file_name
        
        # populate the g_file_var global variable
        fp = open(bdf_file_name, 'r')
        g_file_var = fp.readlines()
        fp.close()
        if args.chip == "qcn9224" or args.chip == "ipq5332" or args.chip == "qcn6432":
            df1 = read_excel(regRules_file, sheet_name='Power Rules', skiprows=0, na_filter=False)
            DictPowerRules=dict(zip(df1["Description"], df1["Index"]))
        #clear the CTL_ENGINE fields before writing to the file
        clear_bdf_file(bdf_file_name)

        print("\nBDF File selected: {}\n".format(bdf_file_name))
        bdf_file_new = bdf_file_name.replace(".txt", "_new.txt")

        # read the Config Excel File
        read_config()
        # read the RegRules Excel File
        read_RegRules()
        # read the RegRules Excel File
        read_PowerRules()
        # read the RegRules Excel File 
        read_ArrayGainRules()
        #read the Exception Excel File
        read_Exception()

        print("Creating new BDF File: {}\n".format(bdf_file_new))

        # Update the global variable: g_file_var (Used for updating the BDF with CTL Engine Fields)
        for string in g_file_var:
            if "CTL_ENGINE" in string:
                update_bdf_config(string)
                update_bdf_RegRules(string)
                update_bdf_PowerRules(string)
                update_bdf_ArrayGainRules(string)
                update_bdf_ExceptionTable(string)
                update_bdf_ExceptionMgmt(string)

        # Create the new BDF File
        create_bdf_file(bdf_file_new)

        if enhanced_heavy_clip_import and os.path.exists(enhanced_heavy_clip_import["FILE_NAME"]):
            enhanced_heavy_clip_import["BDF_NAME"] = bdf_file_new
            # Heavy clip MCS offset
            print("BDF \"{}\" used to update heavy clip MCS offset".format(bdf_file_new))
            enhanced_heavy_clip.main(enhanced_heavy_clip_import)
