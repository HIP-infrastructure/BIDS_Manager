import os
from scipy.io import loadmat
from numpy import ndarray
import ins_bids_class as bids
import xlrd


class CreateTable(dict):
    readable_extension = ['.mat', '.tsv', '.xls', '.xlsx']
    readable_modality = ['ieeg', 'eeg', 'meg']
    required_header = ['patient_id', 'channels']

    def __init__(self, bids_dev, selected_deriv):
        self.error = ''
        self.derivatives_dir = bids_dev
        self.possibility = {key: {} for key in ['channels', 'header']}
        self.keylist = selected_deriv
        for key in selected_deriv:
            path = os.path.join(self.derivatives_dir, key)
            self[key] = parse_dir(path, ext=selected_deriv[key])
        self.get_channels_header()
        # if self.error:
        #     raise ValueError(self.error)
##Revoir toute la façon de comparer les channels car je dois comparer entre les process aussi
##Je devrais proposer à l'utilisateur le choix entre les différent file dans le deriv
##Revoir aussi comment faire pour mettre dans l'ordre des channels pour tsv si pas dans le mm ordre, comment récupérer la valeur

    def get_channels_header(self):
        for dev in self:
            for sub in self[dev]:
                self[dev][sub]['channels'].compare_values()
                self[dev][sub]['header'].compare_values()
                self[dev][sub].simplify_dict()
            self.error += self[dev].compare_files_between_subject()


    def create_tsv_table(self, selection):
        err = ''
        header = self.required_header
        tsv_dict = {}
        for key in self:
            for file in self[key].files_header:
                if file == 'header':
                    st = ''
                else:
                    st = '_'+file
                multi_type = selection[key][file]['multi']
                head_main = selection[key][file]['header']
                for sub in self[key]:
                    if multi_type == 'All':
                        header_key = [hd + '_' + str(cnt) + st for hd in head_main for cnt in range(0, len(self[key][sub][file]))]
                    else:
                        header_key = [hd + st for hd in head_main]
                    idx_channels = self[key][sub].specific_file[file]
                    nbr_chan = len(self[key][sub].electrodes_label[idx_channels])
                    if sub not in tsv_dict.keys():
                        tsv_dict[sub] = {}
                        tsv_dict[sub]['channels'] = self[key][sub].electrodes_label[idx_channels]
                        tsv_dict[sub]['patient_id'] = [sub] * nbr_chan
                    for hd in header_key:
                        tsv_dict[sub][hd] = ['NaN'] * nbr_chan
                    self[key][sub].create_tsv_table(tsv_dict[sub], multi_type, head_main, file_type=file)
                header.extend(header_key)

        tsv_file = bids.BidsTSV(header=header)
        for sub in tsv_dict:
            for i in range(0, len(tsv_dict[sub]['patient_id']), 1):
                temp_dict = {key: tsv_dict[sub][key][i] for key in tsv_dict[sub]}
                tsv_file.append(temp_dict)
        tsv_file.write_file(tsvfilename=os.path.join(self.derivatives_dir, 'statistics_table_max.tsv'))
        return err


class Derivatives(dict):

    def __init__(self):
        self.files_header = {}

    def compare_files_between_subject(self):
        error = ''
        for sub in self:
            for elt in self[sub].specific_file:
                idx = self[sub].specific_file[elt]
                if elt not in self.files_header:
                    self.files_header[elt] = self[sub].header_label[idx]
                elif elt in self.files_header:
                    if not self.files_header[elt] == self[sub].header_label[idx]:
                        error += 'Files throught subjects don"t have the same header for same analysis.\n'
                elif elt == 'files':
                    self.files_header[elt] = self[sub].header_label
        return error


class SubjectData(Derivatives):
    participant_id = ''
    specific_file = None

    def __init__(self, name):
        self.participant_id = name
        self.electrodes_label = None
        self.header_label = None
        for key in ['data', 'channels', 'header']:
            self[key] = {}

    def simplify_dict(self):
        if self['channels'].is_specific_file:
            self.specific_file = {key: cnt for cnt, key in enumerate(self['channels'])}
        else:
            self.specific_file = {'files': 0}
        self.electrodes_label = [val for val in self['channels'].values_label]
        self.header_label = [val for val in self['header'].values_label]
        for elt in self['data']:
            self[elt] = self['data'][elt]
        del self['channels']
        del self['header']
        del self['data']

    def create_tsv_table(self, tsv_dict, multi_type, header_key, file_type):
        def read_tsv_data(list2read, elt2get, channelslist):
            res_dict = {}
            idx_elt = list2read[0].index(elt2get)
            for elt in list2read[1:]:
                idx_chan = [channelslist.index(val) for val in elt if val in channelslist][0]
                res_dict[idx_chan] = elt[idx_elt]
            return res_dict

        clef = file_type
        if file_type:
            st ='_'+file_type
        elif file_type == 'files':
            st = ''
        chan_list = tsv_dict['channels']
        for hd in header_key:
            hd_label = hd+st
            for cnt, elt in enumerate(self[clef]):
                hd_dict = read_tsv_data(self[clef][elt], hd, chan_list)
                if multi_type == 'All':
                    hd_label = hd + '_' + str(cnt) + st
                    for key in hd_dict:
                        tsv_dict[hd_label][key] = hd_dict[key]
                elif multi_type == 'Maximum':
                    for key in hd_dict:
                        if tsv_dict[hd_label][key] == 'NaN':
                            tsv_dict[hd_label][key] = hd_dict[key]
                        elif hd_dict[key] != 'NaN' and tsv_dict[hd_label][key] != 'NaN':
                            tsv_dict[hd_label][key] = max(tsv_dict[hd_label][key], hd_dict[key])
                elif multi_type == 'Average':
                    for key in hd_dict:
                        tsv_dict[hd_label][key] = 0
                        if hd_dict[key] != 'NaN':
                            tsv_dict[hd_label][key] += float(hd_dict[key])
                        else:
                            tsv_dict[hd_label][key] += 0
            if multi_type == 'Average':
                size = len(self[clef])
                tsv_dict[hd_label] = [str(val/size) for val in tsv_dict[hd_label]]


class ManipulateData(SubjectData):
    is_specific_file = False
    error = ''

    def __init__(self, multiple_file=None):
        if multiple_file:
            for elt in multiple_file:
                self[elt] = SpecificFile()
            self.is_specific_file = True
        else:
            self['files'] = {}

    def compare_values(self):
        def create_list_all_values(final_list, list2compare):
            error = ''
            if isinstance(list2compare, list):
                a = set(final_list)
                b = set(list2compare)
                if not final_list:
                    final_list.extend(list2compare)
                elif a.union(b):
                    c = b.difference(a)
                    final_list.extend(list(c))
                else:
                    error = 'Values are different throught files in same subject.\n'
            elif isinstance(list2compare, dict):
                for elt in list2compare:
                    err = create_list_all_values(final_list, list2compare[elt])
                    error += err
            return error

        for elt in self:
            if self.is_specific_file:
                new_list = []
                self.error += create_list_all_values(new_list, self[elt])
                self.values_label.append(new_list)
            else:
                self.error += create_list_all_values(self.values_label, self[elt])

class SpecificFile(ManipulateData):
    def __init__(self):
        self = {}

class Header(ManipulateData):

    def __init__(self, multiple_file=None):
        self.values_label = []
        super().__init__(multiple_file=multiple_file)

class Data(ManipulateData):
    pass

class Channels(ManipulateData):

    def __init__(self, multiple_file=None):
        self.values_label = []
        super().__init__(multiple_file=multiple_file)



def read_tsv_table(file):
    file = open(file, 'r+')
    data = file.readlines()
    data = [line.replace('\n', '') for line in data]
    header = data[0].split('\t')
    data = [line.split('\t') for line in data]
    for elt in header:
        if elt in ['Channels', 'channels', 'label', 'electrode_names']:
            idx = header.index(elt)
    channels = [line[idx] for line in data[1:]]
    file.close()
    return data, channels, header


def read_mat_table(file):
    data = loadmat(file)
    header = list(data.keys())
    channels = []
    for key in data:
        if key in ['electrode_names', 'label']:
            if isinstance(data[key], ndarray):
                channels = data[key].tolist()
                channels = [elt[0] for elt in channels[0]]
            else:
                channels = data[key]
    return data, channels, header


def read_xls_table(file):
    workbook = xlrd.open_workbook(file)
    nsheets = workbook.nsheets
    data = {}
    header = []
    channels = []
    for i in range(0, nsheets, 1):
        worksheet = workbook.sheet_by_index(i)
        nrow = worksheet.nrows
        if nrow:
            head = worksheet.row(0)
            tmp_header = [elt.value for elt in head]
            if not header:
                header = tmp_header
            elif not header == tmp_header:
                raise ValueError('The different sheets don"t have the same header.\n')
            data[str(i)] = [worksheet.row_values(ro) for ro in range(0, nrow, 1)]
            for key in header:
                if key in ['electrode_names', 'label', 'Channels', 'Channel']:
                    idx = header.index(key)
                    tmp_channels = [elt[idx] for elt in data[str(i)][1:]]
                    if not channels:
                        channels = tmp_channels
                    elif not channels == tmp_channels:
                        raise ValueError('The different sheets don"t have the same channels.\n')

    return data, channels, header


def get_nbr_file(path, extd):
    listfile = [fil for fil in os.listdir(path) if os.path.splitext(fil)[1] in extd]
    common_pre = os.path.commonprefix(listfile[0:2])
    possible_file = []
    final_val = None
    i = 2
    while i < (len(listfile)-1):
        tmp_common = os.path.commonprefix(listfile[i-1:i+1])
        if not tmp_common == common_pre:
            for fil in listfile[i-2:i]:
                possible_file.append(fil.split(common_pre)[1])
            common_pre = tmp_common
        i += 1
    if possible_file:
        possible_file.sort()
        final_val = [possible_file[i] for i in range(0, len(possible_file) - 1) if possible_file[i] == possible_file[i + 1]]
        final_val = list(set(final_val))

    metric = Data(multiple_file=final_val)
    chanlabel = Channels(multiple_file=final_val)
    header_val = Header(multiple_file=final_val)

    return listfile, final_val, metric, chanlabel, header_val


def parse_dir(path, sub=None, ext=None):
    final_dict = Derivatives()
    with os.scandir(path) as it:
        for entry in it:
            if entry.name.startswith('sub') and entry.is_dir():
                sub = entry.name.split('-')[1]
                sub_dict = parse_dir(entry.path, sub=sub, ext=ext)
                for key in sub_dict:
                    final_dict[key] = sub_dict[key]
            elif entry.name.startswith('ses-') and entry.is_dir():
                ses_dict = parse_dir(entry.path, sub=sub, ext=ext)
                for key in ses_dict:
                    final_dict[key] = ses_dict[key]
            elif entry.name in CreateTable.readable_modality:
                metrique, channels, header = parse_mod_dir(entry.path, extd=ext)
                if not sub in final_dict.keys():
                    final_dict[sub] = SubjectData(sub)
                final_dict[sub]['data'] = metrique
                final_dict[sub]['channels'] = channels
                final_dict[sub]['header'] = header
    return final_dict


def parse_mod_dir(path, extd=None):
    if not extd:
        extd = CreateTable.readable_extension
    listfile, possible_elt, metric, chanlabel, header_val = get_nbr_file(path, extd)
    for fil in listfile:
        filename = os.path.join(path, fil)
        name, ext = os.path.splitext(fil)
        ext = ext.split('.')[1]
        metrique, channels, header = eval('read_'+ext+'_table(filename)')
        if possible_elt:
            for elt in possible_elt:
                if elt in fil:
                    metric[elt][name] = metrique
                    chanlabel[elt][name] = channels
                    header_val[elt][name] = header
        else:
            metric['files'][name] = metrique
            chanlabel['files'][name] = channels
            header_val['files'][name] = header

    return metric, chanlabel, header_val
    #
    # with os.scandir(path) as it:
    #     for entry in it:
    #         name, ext = os.path.splitext(entry.name)
    #         if entry.is_file() and ext in extd:
    #             if ext == '.mat':
    #                 metrique, channels, header = read_mat_table(entry.path)
    #             elif ext == '.tsv':
    #                 metrique, channels, header = read_tsv_table(entry.path)
    #             elif ext == '.xls' or ext == '.xlsx':
    #                 metrique, channels, header = read_xls_table(entry.path)
    #             metric[name] = metrique
    #             chanlabel[name] = channels
    #             header_val[name] = header
