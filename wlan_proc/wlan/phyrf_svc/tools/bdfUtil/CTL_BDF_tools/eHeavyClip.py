import os
import argparse
from openpyxl import load_workbook
import re
import utillity as utils

class heavy_clip_data:
    def __init__(self):
        self.channel_index = {
            "2G" : {
                "START_BW20" : 255, "STOP_BW20" : 255,
                "START_BW40" : 255, "STOP_BW40" : 255,
                },
            "5G" : {
                "START_BW20" : 255, "STOP_BW20" : 255,
                "START_BW40" : 255, "STOP_BW40" : 255,
                "START_BW80" : 255, "STOP_BW80" : 255,
                "START_BW160" : 255, "STOP_BW160" : 255,
                "START_BW320" : 255, "STOP_BW320" : 255,
            },
            "6G" : {
                "START_BW20" : 255, "STOP_BW20" : 255,
                "START_BW40" : 255, "STOP_BW40" : 255,
                "START_BW80" : 255, "STOP_BW80" : 255,
                "START_BW160" : 255, "STOP_BW160" : 255,
                "START_BW320" : 255, "STOP_BW320" : 255,
            },
        }
        self.channel_mcs_offset = {
            "PHYA0" : { "FCC_2G" : [], "ROW_2G" : [], "FCC_5G" : [], "ROW_5G" : [], "FCC_6G" : [], "ROW_6G" : [] },
            "PHYA1" : { "FCC_5G" : [], "ROW_5G" : [], "FCC_6G" : [], "ROW_6G" : []},
            "PHYB"  : { "FCC_2G" : [], "ROW_2G" : [], "FCC_5G" : [], "ROW_5G" : []},
        }
        self.channel_info = {"2G" : [], "5G" : [], "6G" : []}
        self.mcs_group_info = { "PHYA0" : [], "PHYA1" : [], "PHYB" : [] }
        self.ndp_info = { "PHYA0" : None, "PHYA1" : None, "PHYB" : None }
        self.nonht_dup_info = { "PHYA0" : None, "PHYA1" : None, "PHYB" : None }
        self.ctl_domain = []
        self.expanded_hc_enable = None

class BDF_utils:
    def __init__(self, dictHC, hc_data_obj):
        self.fields_to_parse = dictHC["BDF_FIELDS"]
        self.bdf_name = dictHC["BDF_NAME"]
        self.band_phy_rel = dictHC["BAND_PHY_REL"]
        self.support_ctl_engine = dictHC["SUPPORT_CTL_ENGINE"]
        self.hc_data_obj = hc_data_obj        

    def update_ctl_domain(self, data_list):
        value = 0        
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*\\[(\\d+)\\]", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            value = self.hc_data_obj.ctl_domain[int(match.groups()[0])]

        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"

    def update_mcs_group(self, data_list):
        value = 0        
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*_(\\w+)\\[(\\d+)\\]", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            mcs_group = self.hc_data_obj.mcs_group_info[match.groups()[0]]
            value = mcs_group[int(match.groups()[1])]
        
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"
    
    def update_ndp(self, data_list):
        value = 0
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*_(\\w+)", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            value = self.hc_data_obj.ndp_info[match.groups()[0]]
        
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"
    
    def update_chan_start_stop(self, data_list):
        value = 0
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*_(\\w+)\\[(\\d+)\\]", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            band_chan_index = self.hc_data_obj.channel_index[match.groups()[0]]
            band_width = ""
            if match.groups()[1] == "0":
                band_width = "BW20"
            elif match.groups()[1] == "1":
                band_width = "BW40"
            elif match.groups()[1] == "2":
                band_width = "BW80"
            elif match.groups()[1] == "3":
                band_width = "BW160"
            elif match.groups()[1] == "4":
                band_width = "BW320"

            if "HC_Freq_Start_Index" in field_need:
                band_width = "START_" + band_width
            elif "HC_Freq_End_Index" in field_need:
                band_width = "STOP_" + band_width

            value = band_chan_index[band_width]
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"
    
    def update_chan(self, data_list):
        value = 0        
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*_(\\w+)\\[(\\d+)\\]", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            band_channel_info = self.hc_data_obj.channel_info[match.groups()[0]]
            value = band_channel_info[int(match.groups()[1])]
        
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"

    def update_chan_mcs_offset(self, data_list):
        value = 0        
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*offset_([a-zA-Z0-9]+)_?([a-zA-Z0-9]+)?\\[(\\d+)\\]\\[(\\d+)\\]", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            band_phy_info = self.band_phy_rel[match.groups()[0]]
            phy_info = match.groups()[1]
            if phy_info is not None and phy_info in band_phy_info:
                phy_key = phy_info
            else:
                phy_key = band_phy_info

            band_channel_info = self.hc_data_obj.channel_mcs_offset[phy_key]
            if match.groups()[2] == "0":
                band_channel_key = "FCC_{}".format(match.groups()[0])
            elif match.groups()[2] == "1":
                band_channel_key = "ROW_{}".format(match.groups()[0])
            value = band_channel_info[band_channel_key][int(match.groups()[3])]
        
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"

    def update_nonht_dup(self, data_list):
        value = 0        
        field_need = data_list[1].split('.')[1]

        # print("field - {}".format(field_need))
        match = re.match(".*_(\\w+)", field_need)
        if match:
            # print("Group - {}, Groups - {}".format(match.group(), match.groups()))
            value = self.hc_data_obj.nonht_dup_info[match.groups()[0]]
        
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"

    def update_expanded_HC(self, data_list):
        value = 0
        if self.hc_data_obj.expanded_hc_enable is not None:
            value = int(self.hc_data_obj.expanded_hc_enable)
        data_list[-1] = str(value)
        data_string = "\t".join(data_list)
        return data_string + "\n"

    def update_expanded_heavy_clip(self):
        file_name, extension = os.path.splitext(self.bdf_name)

        if self.support_ctl_engine:
            pattern_exp_hc_section = "CTL_ENGINE"
            pattern_bdf_flag_section = "BDF_ENABLE_DISABLE_FLAGS"
        else:
            pattern_exp_hc_section = "HEAVYCLIP_CTLMCS_TABLE"

        file_obj_read = open(self.bdf_name, "r")
        file_obj_write = open(file_name + "_new" + extension, "w")
        print("Creating new BDF File: {}_new{}".format(file_name, extension))

        txt_lines = file_obj_read.readlines()
        for line in txt_lines:
            if pattern_exp_hc_section in line:
                line_data_list = line.split('\t')
                for key, pattern_field in self.fields_to_parse.items():
                    field_need = line_data_list[1].split('.')[1]

                    ## Got needed string here, based on key of pattern_field call needed APIs
                    if pattern_field in field_need:
                        if key == "ctl_domain":
                            modified_line = self.update_ctl_domain(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key == "mcs_group":
                            modified_line = self.update_mcs_group(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key == "ndp_mcs":
                            modified_line = self.update_ndp(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key in ["chan_start_idx", "chan_end_idx"]:
                            modified_line = self.update_chan_start_stop(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key == "chan_number":
                            modified_line = self.update_chan(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key == "mcs_offset":
                            modified_line = self.update_chan_mcs_offset(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key == "nonht_dup":
                            modified_line = self.update_nonht_dup(line_data_list)
                            file_obj_write.write(modified_line)
                        elif key == "enable_flag":
                            modified_line = self.update_expanded_HC(line_data_list)
                            file_obj_write.write(modified_line)
                        break
                else:
                    file_obj_write.write(line)

            elif self.support_ctl_engine and pattern_bdf_flag_section in line:
                line_data_list = line.split('\t')
                for key, pattern_field in self.fields_to_parse.items():
                    field_need = line_data_list[1].split('.')[1]

                    ## Got needed string here, based on key of pattern_field call needed APIs
                    if pattern_field in field_need:
                        if key == "enable_flag":
                            modified_line = self.update_expanded_HC(line_data_list)
                            file_obj_write.write(modified_line)
                        break
                else:
                    file_obj_write.write(line)

            else:
                file_obj_write.write(line)

        file_obj_read.close()
        file_obj_write.close()

class enhanced_heavy_clip_parser:
    def __init__(self, dictHC):
        self.file_name = dictHC["FILE_NAME"]
        self.sheet_name = dictHC["SHEET_NAME"]
        self.mcs_group = dictHC["MCS_GROUP"]
        self.support_ctl_engine = dictHC["SUPPORT_CTL_ENGINE"]
        self.max_channel = dictHC["MAX_CHANNEL"]
        self.__MAJOR__ = 1
        self.__MINOR__ = 0

        ## Used for parsing across APIs
        self.phy_mcs_limit = {
                "PHYA0" : { "START" :0, "STOP" : 0},
                "PHYA1" : { "START" :0, "STOP" : 0},
                "PHYB"  : { "START" :0, "STOP" : 0},
            }
        
        if self.support_ctl_engine:
            self.ctl_domain_shift = { "FCC" : 0, "ETSI" : 1, "JPN" : 2, "KOR" : 3, "CHN" : 4, "USR" : 5}
        else:
            self.ctl_domain_shift = { "FCC" : 0, "ETSI" : 2, "JPN" : 3, "KOR" : 4, "CHN" : 5, "USR" : 6}


    def sanity_check(self):
        hcBook = load_workbook(self.file_name)        
        sanity_row_start, sanity_row_stop = 3, 3 
        sanity_col_start, sanity_col_stop = 10, 11

        sheet_name, __ = os.path.splitext(self.file_name)
        tool_version, sheet_version = 0, 0

        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]
            for row in hcSheet.iter_rows(
                min_row = sanity_row_start, max_row = sanity_row_stop,
                min_col = sanity_col_start, max_col = sanity_col_stop):
                for idx, cell in enumerate(row):
                    # print("row - {}, col - {}, value - {}, type - {}".format(cell.row, cell.column, cell.value, type(cell.value)))
                    if cell.value is not None:
                        if idx == 0 and type(cell.value) is int:
                            tool_version = cell.value
                        else:
                            sheet_version = cell.value

        # print("Sheet version {}:{}".format(tool_version, sheet_version))
        if self.__MAJOR__ > tool_version:
            utils.print_warning("EnhancedHeavyClip tool version v{}, whereas input \"{}\" has v{}, updates will happen till v{}".
                                format(self.__MAJOR__, sheet_name, tool_version, tool_version))
        elif self.__MAJOR__ < tool_version:
            utils.print_warning("EnhancedHeavyClip tool version v{}, whereas input \"{}\" has v{}, updates will happen till v{}".
                                format(self.__MAJOR__, sheet_name, tool_version, self.__MAJOR__))
        hcBook.close()


    def update_chan_start_stop(self, hcdata):
        hcBook = load_workbook(self.file_name)
        try:
            if self.sheet_name in hcBook.sheetnames:
                hcSheet = hcBook[self.sheet_name]
                #print(f"row : {hcSheet.max_row}, col : {hcSheet.max_column}")
                
                ## Pre-processing data
                bw_row_start, bw_col_start = 41, 2
                chan_row_start, chan_col_start = bw_row_start + 1, 2
                current_band = None

                ## Assuming max_row = chan_row_start + 6 based on support for 2G/5G/6G
                ## Assuming max_col = bw_col_start + 5 base on support for BW till 320MHz
                for row in hcSheet.iter_rows(
                    min_row = chan_row_start, max_row = chan_row_start + 5,
                    min_col = bw_col_start, max_col = bw_col_start + 5):
                    chan_type = ""
                    for cell in row:
                        # print("row - {}, col - {}, value - {}".format(cell.row, cell.column, cell.value))                
                        if cell.value is not None:
                            if cell.column == chan_col_start:
                                values = cell.value.split()
                                chan_type, band_key = values[0], values[1]
                                if band_key in hcdata.channel_index:
                                    current_band = hcdata.channel_index[band_key]
                            else:
                                bw_value = hcSheet.cell(
                                    row = bw_row_start, 
                                    column = cell.column).value
                                bw_key = "{}_{}".format(chan_type, bw_value)
                                if current_band and bw_key in current_band:
                                    max_channel_value = self.max_channel[band_key]
                                    if cell.value < max_channel_value:
                                        current_band[bw_key] = cell.value
                                    else:
                                        # print("{} max number of channel entries allowed {}".format(band_key, max_channel_value))
                                        raise ValueError("For [Band-{}] [BandWidth-{}] [Channel-{}] expect less than {}".format(band_key, bw_key, cell.value, max_channel_value))
        except Exception as excp:
            hcBook.close()
            raise excp

    def update_chan(self, hcdata):
        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]

            ## Pre-processing data
            row_start_offset, row_stop_offset = 40, 132
            col_start_offset, col_stop_offset = 9, 10

            for row in hcSheet.iter_rows(
                min_row = row_start_offset, max_row = row_stop_offset,
                min_col = col_start_offset, max_col = col_stop_offset):
                    for idx, cell in enumerate(row):
                        # print("row - {}, col - {}, value - {}".format(cell.row, cell.column, cell.value))                
                        band_check_value = hcSheet.cell(row = cell.row, column = col_start_offset).value                        
                        if band_check_value in ["2.4GHz", "5GHz", "6GHz"]:
                            band = band_check_value[0] + "G"
                        elif idx != 0 and cell.value is not None and cell.value != "Reserved":
                            channel_list = hcdata.channel_info[band]
                            channel_list.append(int(cell.value))
                        elif idx != 0 and cell.value == "Reserved":
                            channel_list = hcdata.channel_info[band]
                            channel_list.append(255)
        hcBook.close()

    def update_chan_mcs_offset(self, hcdata): 
        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]
            
            ## FIXME : seprate PHY start and stop out of this API
            ## Pre-processing data
            col_start_offset, col_stop_offset = 9, 34
            row_start_offset, row_stop_offset = 38, 132

            ## PHY start and stop limit parsing
            prev_key = None
            for row in hcSheet.iter_rows(
                min_row = row_start_offset, max_row = row_start_offset,
                min_col = col_start_offset, max_col = col_stop_offset):
                for cell in row:
                    # print("row - {}, col - {}, value - {}".format(cell.row, cell.column, cell.value))
                    if cell.value is not None:
                        for key in self.phy_mcs_limit:
                            if cell.value == key:
                                phy_limit = self.phy_mcs_limit[key]
                                phy_limit["START"] = cell.column

                                if prev_key:
                                    phy_limit = self.phy_mcs_limit[prev_key]
                                    phy_limit["STOP"] = cell.column - 1

                                prev_key = cell.value

            if prev_key:
                phy_limit = self.phy_mcs_limit[prev_key]
                phy_limit["STOP"] = col_stop_offset

            # print(self.phy_mcs_limit)
            
            ## Filling up MCS offset data
            for key, value in self.phy_mcs_limit.items():
                mcs_offset_dict = hcdata.channel_mcs_offset[key]
                band = None
                mcs_value = 0
                for row in hcSheet.iter_rows(
                    min_row = row_start_offset + 2, max_row = row_stop_offset,
                    min_col = value["START"], max_col = value["STOP"]):
                    for idx, cell in enumerate(row):
                        band_check_value = hcSheet.cell(row = cell.row, column = col_start_offset).value
                        if band_check_value in ["2.4GHz", "5GHz", "6GHz"]:
                            band = band_check_value[0] + "G"
                            # print(band)
                        elif cell.value is not None and cell.value != "NOT APPLICABLE":
                            mcs_shift = idx % self.mcs_group
                            ctl_region = hcSheet.cell(row = row_start_offset + 2, column = cell.column).value.split()[0]
                            mcs_offset_key = "{}_{}".format(ctl_region, band)
                            # print(mcs_offset_key)

                            ctl_region_list = mcs_offset_dict[mcs_offset_key]
                            mcs_value += int(cell.value) << (mcs_shift * self.mcs_group)

                            # print(f"group - {mcs_shift} - {mcs_value}")
                            if mcs_shift == (self.mcs_group - 1):
                                ctl_region_list.append(mcs_value)
                                mcs_value = 0
                ## For debug
                # break
        hcBook.close()

    def update_mcs_group(self, hcdata):
        row_start_offset, row_stop_offset = 36, 36
        mcs_bin_pattern = ["BIN1", "BIN2", "BIN3", "BIN4"]

        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]

            for key, value in self.phy_mcs_limit.items():
                mcs_group_list = hcdata.mcs_group_info[key]

                for row in hcSheet.iter_rows(
                min_row = row_start_offset, max_row = row_stop_offset,
                min_col = value["START"], max_col = value["STOP"]):
                    for cell in row:
                        mcs_group_data = hcSheet.cell(row = row_start_offset - 1, column = cell.column).value

                        if mcs_group_data is not None:                            
                            mcs_group_bin = mcs_group_data.split()[3]
                            final_mcs_group_value = 0
                            if mcs_group_bin in mcs_bin_pattern:
                                if cell.value is None:
                                    final_mcs_group_value = 0
                                elif type(cell.value) is int:
                                    mcs = cell.value
                                    final_mcs_group_value |= 1 << int(mcs)
                                else:
                                    mcs_list = cell.value.split(',')
                                    for mcs in mcs_list:
                                        final_mcs_group_value |= 1 << int(mcs)
                                mcs_group_list.append(final_mcs_group_value)

        hcBook.close()

    def update_ndp(self, hcdata):
        row_start_offset, row_stop_offset = 32, 32

        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]

            for key, value in self.phy_mcs_limit.items():
                for row in hcSheet.iter_rows(
                min_row = row_start_offset, max_row = row_stop_offset,
                min_col = value["START"], max_col = value["STOP"]):
                    for cell in row:
                        # print("row - {}, col - {}, value - {}, type - {}".format(cell.row, cell.column, cell.value, type(cell.value)))
                        if cell.value is not None and type(cell.value) is int:
                            hcdata.ndp_info[key] = cell.value

        hcBook.close()

    def update_nonht_dup(self, hcdata):
        nonht_shift = { "nonHT40" : 0, "nonHT80" : 4, "nonHT160" : 8, "nonHT320" : 12 }

        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]

            for key, value in self.phy_mcs_limit.items():
                row_start_offset, row_stop_offset = 30, 30
                nonht_value = 0
                for row in hcSheet.iter_rows(
                min_row = row_start_offset, max_row = row_stop_offset,
                min_col = value["START"], max_col = value["STOP"]):
                    for cell in row:
                        # print("row - {}, col - {}, value - {}, type - {}".format(cell.row, cell.column, cell.value, type(cell.value)))
                        if cell.value is not None:
                            nonht_dup_data = hcSheet.cell(row = row_start_offset - 1, column = cell.column).value
                            nonht_key = nonht_dup_data.split('_')[0]
                            # print("{}, shift - {}, value - {}".format(nonht_key, nonht_shift[nonht_key], cell.value))
                            nonht_value |= cell.value << nonht_shift[nonht_key]

                hcdata.nonht_dup_info[key] = nonht_value

        hcBook.close()

    def update_ctl_domain(self, hcdata):
        row_start_offset, row_stop_offset = 6, 7
        col_start_offset, col_stop_offset = 15, 20

        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]

            for row in hcSheet.iter_rows(
            min_row = row_start_offset, max_row = row_stop_offset,
            min_col = col_start_offset, max_col = col_stop_offset):
                ctl_domain_value = 0
                for cell in row:
                    # print("row - {}, col - {}, value - {}, type - {}".format(cell.row, cell.column, cell.value, type(cell.value)))
                    if cell.value is not None:
                        ctl_key = hcSheet.cell(row = row_start_offset - 1, column = cell.column).value
                        # print("{}, shift - {}, value - {}".format(ctl_key, self.ctl_domain_shift[ctl_key], cell.value))
                        ctl_domain_value |= cell.value << self.ctl_domain_shift[ctl_key]

                hcdata.ctl_domain.append(ctl_domain_value)

        hcBook.close()

    def update_expanded_HC(self, hcdata):
        row_start_offset, row_stop_offset = 16, 16
        col_start_offset, col_stop_offset = 16, 16
        
        hcBook = load_workbook(self.file_name)
        if self.sheet_name in hcBook.sheetnames:
            hcSheet = hcBook[self.sheet_name]

            for row in hcSheet.iter_rows(
            min_row = row_start_offset, max_row = row_stop_offset,
            min_col = col_start_offset, max_col = col_stop_offset):
                for cell in row:
                    # print("row - {}, col - {}, value - {}, type - {}".format(cell.row, cell.column, cell.value, type(cell.value)))
                    if cell.value is not None:
                        if type(cell.value) is int and cell.value == 1:
                            hcdata.expanded_hc_enable = True
                        elif type(cell.value) is int and cell.value == 0:
                            hcdata.expanded_hc_enable = False

        hcBook.close()

def main(enhanced_heavy_clip_import):    
    hcdata = heavy_clip_data()
    hcObj = enhanced_heavy_clip_parser(enhanced_heavy_clip_import)
    bdf_data = BDF_utils(enhanced_heavy_clip_import, hcdata)

    hcObj.sanity_check()

    hcObj.update_chan_start_stop(hcdata)
    # print(hcdata.channel_index)

    hcObj.update_chan(hcdata)
    # print(hcdata.channel_info)

    hcObj.update_chan_mcs_offset(hcdata)
    # print(hcdata.channel_mcs_offset)

    hcObj.update_mcs_group(hcdata)
    # print(hcdata.mcs_group_info)

    hcObj.update_ndp(hcdata)
    # print(hcdata.ndp_info)

    hcObj.update_nonht_dup(hcdata)
    # print(hcdata.nonht_dup_info)

    hcObj.update_ctl_domain(hcdata)
    # print(hcdata.ctl_domain)

    hcObj.update_expanded_HC(hcdata)
    # print(hcdata.expanded_hc_enable)

    bdf_data.update_expanded_heavy_clip()

# USE this for debugging purpose
if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("-ho", "--heavyclipOffset", dest="sheet_HC", help="heavy clip excel file")
    cli_parser.add_argument("-c", "--chip", help="[wcn7850/qcn9224/ipq5332/qcn6432]")
    cli_parser.add_argument('-f', '--file', dest="bdf", action="store", default="bdwlan.txt", help="BDF File to be populated")
    cli_args = cli_parser.parse_args()

    #import chip specific headers
    import config_qcn9224
    import config_ipq5332_qcn6432
    import config_wcn7850

    enhanced_heavy_clip_import = None
    if cli_args.chip == "qcn9224":
        enhanced_heavy_clip_import = config_qcn9224.ENHANCED_HEAVY_CLIP
    if cli_args.chip == "ipq5332" or cli_args.chip =="qcn6432":
        enhanced_heavy_clip_import = config_ipq5332_qcn6432.ENHANCED_HEAVY_CLIP
    elif cli_args.chip == "wcn7850":
        enhanced_heavy_clip_import = config_wcn7850.ENHANCED_HEAVY_CLIP

    if enhanced_heavy_clip_import:
        if cli_args.sheet_HC:
            enhanced_heavy_clip_import["FILE_NAME"] = cli_args.sheet_HC

        if cli_args.bdf:
            enhanced_heavy_clip_import["BDF_NAME"] = cli_args.bdf

    main(enhanced_heavy_clip_import)
