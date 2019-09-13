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

    def get_channels_header(self):
        def compare_values(list2compare, type_err):
            err=''
            if isinstance(list2compare, list):
                for elt in list2compare[1:]:
                    a = set(list2compare[0])
                    b = set(elt)
                    if a.union(b):
                        c = b.difference(a)
                        list2compare[0].extend(list(c))
                    else:
                        err = 'Not the same'
                return err
            elif isinstance(list2compare, dict):
                for key in list2compare:
                    error = compare_values(list2compare[key], type_err)
                    if error:
                        err += 'The {0} inside this subject {1} are not similar.\n'.format(type_err, key)
                    else:
                        list2compare[key] = list(set(list2compare[key][0]))
                        list2compare[key].sort()
                if not err:
                    keylist = list(list2compare.keys())
                    taille = len(keylist)
                    if taille < 2:
                        return err
                    i = 1
                    while i < taille:
                        if not list2compare[keylist[i-1]] == list2compare[keylist[i]]:
                            err = 'The {0} list are not identical throught your analysis.\n'.format(type_err)
                            return err
                        i += 1
            return err

        for dev in self:
            channels_possibility = {sub: [] for sub in self[dev]}
            header_possibility = {sub: [] for sub in self[dev]}
            for sub in self[dev]:
                for file in self[dev][sub]['header']:
                    channels_possibility[sub].append(self[dev][sub]['channels'][file])
                    header_possibility[sub].append(self[dev][sub]['header'][file])
            error_chan = compare_values(channels_possibility, 'channels')
            self.possibility['channels'][dev] = channels_possibility
            error_header = compare_values(header_possibility, 'header')
            if not error_header:
                val = list(header_possibility.keys())
                self.possibility['header'][dev] = header_possibility[val[0]]
            self.error = error_chan + error_header
        #error_chan = compare_values(self.possibility['channels'], 'channels')
        if not error_chan:
            self.possibility['channels']['isimilar'] = True
        else:
            self.error += error_chan
            self.possibility['channels']['isimilar'] = False

    def create_tsv_table(self, selection):
        err = ''
        header = self.required_header
        tsv_dict = {}
        for key in self:
            header_key = selection[key]['header']
            for sub in self[key]:
                if sub not in tsv_dict.keys():
                    nbr_chan = len(self.possibility['channels'][key][sub])
                    tsv_dict[sub] = {hd: ['NaN']*nbr_chan for hd in header_key}
                    tsv_dict[sub]['channels'] = self.possibility['channels'][key][sub]
                    tsv_dict[sub]['patient_id'] = [sub] * nbr_chan
                # if self.possibility['channels']['isimilar'] and not tsv_dict[sub]['channels']:
                #     tsv_dict[sub]['channels'] = self.possibility['channels'][key]
                # elif not self.possibility['channels']['isimilar']:
                #     err = 'The channels are not the same throught your files.\n Bids Manager doesn"t know what to do.\n'
                #     return err
                # if not tsv_dict[sub]['patient_id']:
                #     tsv_dict[sub]['patient_id'] = [sub] * len(tsv_dict[sub]['channels'])
                ##Doit revoir comment récupérer les données car je dois prendre en compte les valeurs de canaux et écrire en fonction
                sel_type = selection[key]['multi']
                for ct, file in enumerate(self[key][sub]['data']):
                    value = self[key][sub]['data'][file]
                    if isinstance(value, dict):
                        keylist = list(value.keys())
                        is_xls = all(elt.isdigit() for elt in keylist)
                        if is_xls:
                            for cnt, key in enumerate(value):
                                for head in header_key:
                                    idx = value[key][0].index(head)
                                    st = ''
                                    tmp_data = [val[idx] for val in value[key][1:]]
                                    if sel_type == 'All':
                                        if cnt >0:
                                            st = '_'+str(cnt+1)
                                        tsv_dict[sub][head+st] = tmp_data
                                    elif sel_type == 'Maximum':
                                        if not head in tsv_dict[sub].keys():
                                            tsv_dict[sub][head] = tmp_data
                                        else:
                                            tsv_dict[sub][head] = max(tsv_dict[sub][head], tmp_data)
                                    elif sel_type == 'Average':
                                        if not head in tsv_dict[sub].keys():
                                            tsv_dict[sub][head] = tmp_data
                                        else:
                                            pass
                                            #ne fonctionne pas car python ne sait pas manipuler des calculs matricielle
                                            #tsv_dict[sub][head] = (tsv_dict[sub][head] + tmp_data)/2
                                    header.append(head + st)
                        else:
                            if sel_type == 'All':
                                st = ''
                                if ct > 0:
                                    st = '_'+str(ct+1)
                                for head in header_key:
                                    val = eval('value["' + head + '"]')
                                    if isinstance(val, ndarray):
                                        val = val.tolist()
                                    tsv_dict[sub][head+st] = val
                                    header.append(head + st)
                            #A finir
                    elif isinstance(self[key][sub]['data'][file], list):
                        for head in header_key:
                            idx = value[0].index(head)
                            st = ''
                            tmp_data = [val[idx] for val in value[1:]]
                            if sel_type == 'All':
                                if ct > 0:
                                    st = '_' + str(ct + 1)
                                tsv_dict[sub][head + st] = tmp_data
                            elif sel_type == 'Maximum':
                                if not head in tsv_dict[sub].keys():
                                    tsv_dict[sub][head] = tmp_data
                                else:
                                    tsv_dict[sub][head] = max(tsv_dict[sub][head], tmp_data)
                            elif sel_type == 'Average':
                                if not head in tsv_dict[sub].keys():
                                    tsv_dict[sub][head] = tmp_data
                                else:
                                    pass
                                    # ne fonctionne pas car python ne sait pas manipuler des calculs matricielle
                                    #tsv_dict[sub][head] = (tsv_dict[sub][head] + tmp_data) / 2
                            header.append(head + st)
        tsv_file = bids.BidsTSV(header=header)
        for sub in tsv_dict:
            for i in range(0, len(tsv_dict[sub]['patient_id']), 1):
                temp_dict = {key: tsv_dict[sub][key][i] for key in tsv_dict[sub]}
                tsv_file.append(temp_dict)
        tsv_file.write_file(tsvfilename=os.path.join(self.derivatives_dir, 'statistics_table.tsv'))
        return err


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


def parse_dir(path, sub=None, ext=None):
    final_dict = {}
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
                    final_dict[sub] = {key: [] for key in ['data', 'channels', 'header']}
                final_dict[sub]['data'] = metrique
                final_dict[sub]['channels'] = channels
                final_dict[sub]['header'] = header
    return final_dict



def parse_mod_dir(path, extd=None):
    if not extd:
        extd =CreateTable.readable_extension
    metric = {}
    chanlabel = {}
    header_val = {}
    with os.scandir(path) as it:
        for entry in it:
            name, ext = os.path.splitext(entry.name)
            if entry.is_file() and ext in extd:
                if ext == '.mat':
                    metrique, channels, header = read_mat_table(entry.path)
                elif ext == '.tsv':
                    metrique, channels, header = read_tsv_table(entry.path)
                elif ext == '.xls' or ext == '.xlsx':
                    metrique, channels, header = read_xls_table(entry.path)
                metric[name] = metrique
                chanlabel[name] = channels
                header_val[name] = header

    return metric, chanlabel, header_val
