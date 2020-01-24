import os
from scipy.io import loadmat
from numpy import ndarray
import json
import xlrd

#variables used in all script
__modality_type__ = ['ieeg', 'eeg', 'meg', 'beh'] #'anat', 'pet', 'func', 'fmap', 'dwi',
__channel_name__ = ['channel', 'channels', 'electrode_name', 'electrodes_name', 'electrode_names', 'label', 'labels']


def go_throught_dir_to_convert(dirname):
    if not os.path.exists(dirname):
        raise ('The directroy doesn"t exists')
    with os.scandir(dirname) as it:
        for entry in it:
            if (entry.name.startswith('sub-') or entry.name.startswith('ses-')) and entry.is_dir():
                go_throught_dir_to_convert(entry.path)
            elif entry.name in __modality_type__ and entry.is_dir():
                file_list = os.listdir(entry.path)
                ext_list = [os.path.splitext(os.path.join(entry.path, file))[1] for file in file_list]
                ext_list = list(set(ext_list))
                if '.tsv' in ext_list:
                    return
                elif '.mat' in ext_list and ('.xls' and '.xlsx') not in ext_list:
                    mat_file = [file for file in file_list if '.mat' in file]
                    for file in mat_file:
                        filename = os.path.join(entry.path, file)
                        json_dict, tsv_dict = convert_mat_file(filename)
                        write_file_after_convert(json_dict, tsv_dict)
                    return
                elif ('.xls' and '.xlsx') in ext_list:
                    xls_file = [file for file in file_list if '.xls' in file]
                    for file in xls_file:
                        filename = os.path.join(entry.path, file)
                        json_dict, tsv_dict = convert_xls_file(filename)
                        write_file_after_convert(json_dict, tsv_dict)
                    return


def parse_derivatives_folder(folder, table2write, table_attributes):
    with os.scandir(folder) as it:
        for entry in it:
            if entry.name in __modality_type__ and entry.is_dir():
                go_throught_dir_to_convert(entry.path)
                file_list = os.listdir(entry.path)
                for file in file_list:
                    if os.path.splitext(file)[1] == '.tsv':
                        json_dict, tsv_dict = read_tsv(os.path.join(entry.path, file))
                        key2remove = []
                        for key in tsv_dict:
                            if key.lower() in __channel_name__ and all(isinstance(elt, str) for elt in tsv_dict[key]):
                                channel = tsv_dict[key]
                                key2remove.append(key)
                        create_table(tsv_dict, channel, key2remove, table2write, table_attributes, file)
            elif entry.name not in ['log', 'log_old', 'parsing', 'parsing_old'] and entry.is_dir():
                parse_derivatives_folder(entry.path, table2write, table_attributes)


def write_big_table(derivatives_folder):
    #before write_table
    table2write = [[]]
    table_attributes = [[]]
    table_attributes[0] = ['sub']
    write_big_table(derivatives_folder, table2write, table_attributes)
    if not len(table2write) == len(table_attributes):
        print('ERROR')
    else:
        final_table = [None] * len(table2write)
        for i in range(0, len(table2write), 1):
            final_table.extend(table_attributes[i])
            final_table.extend(table2write[i])
    filename = 'statistical_table.tsv'
    write_table(final_table, filename, derivatives_folder)


def convert_mat_file(filename):
    def turn_array_in_list(elt):
        if isinstance(elt, ndarray):
            value = elt.tolist()
            final_value = turn_array_in_list(value)
        elif isinstance(elt, list):
            value = []
            for val in elt:
                if isinstance(val, list):
                    inter_value = turn_array_in_list(val)
                    value.extend(inter_value)
                elif isinstance(val, ndarray):
                    if val.dtype.fields is None:
                        if val.size == 1:
                            value.append(val.item())
                        elif val.size <= 306:
                            val = val.tolist()
                            inter_value = turn_array_in_list(val)
                            value.extend(inter_value)
                else:
                    value.append(val)
            final_value = value
        return final_value

    data = loadmat(filename)
    json_dict = {}
    tsv_dict = {}
    mat_keys = ['__header__', '__version__', '__globals__']
    keylist = [key for key in data.keys() if key not in mat_keys]
    for key in keylist:
        if data[key].dtype.hasobject and data[key].dtype.fields is not None:
            dt = data[key].dtype
            for stname in dt.names:
                value = turn_array_in_list(data[key][stname])
                if isinstance(value, str):
                    json_dict[stname] = value
                elif isinstance(value, list):
                    if len(value) == 1:
                        json_dict[stname] = value[0]
                    else:
                        tsv_dict[stname] = value
                else:
                    tsv_dict[stname] = value
        else:
            if data[key].size == 1:
                json_dict[key] = data[key].item()
            elif data[key].size > 1:
                shape = data[key].shape
                if len(shape) <= 2:
                    value = turn_array_in_list(data[key])
                    tsv_dict[key] = value
                else:
                    json_dict[key] = 'value is in {} dimension'.format(len(shape))
    json_dict['filename'] = filename
    return json_dict, tsv_dict


def convert_xls_file(filename):
    workbook = xlrd.open_workbook(filename)
    nsheets = workbook.nsheets
    json_dict = {}
    tsv_dict = {}
    for i in range(0, nsheets, 1):
        json_dict[i] = {}
        worksheet = workbook.sheet_by_index(i)
        ncol = worksheet.ncols
        nrow = worksheet.nrows
        if ncol == 0:
            continue
        tmp_dict = {worksheet._cell_values[0].index(key): key for key in worksheet._cell_values[0]}
        tsv_tmp_dict = {key: [] for key in worksheet._cell_values[0]}
        for lines in worksheet._cell_values[1:]:
            if not all(elt == '' for elt in lines):
                for cnt, elt in enumerate(lines):
                    tsv_tmp_dict[tmp_dict[cnt]].append(elt)
            else:
                idx = worksheet._cell_values.index(lines) + 1
                for line in worksheet._cell_values[idx::]:
                    if not all(elt == '' for elt in line):
                        count = sum(1 for e in line if e != '')
                        if count % 2 == 0:
                            for j in range(0, ncol, 2):
                                if line[j]:
                                    json_dict[i][line[j]] = line[j+1]
                break
        tsv_dict[i] = tsv_tmp_dict
    if len(tsv_dict.keys()) == 1:
        tsv_dict = tsv_dict[0]
        json_dict = json_dict[0]
    json_dict['filename'] = filename
    return json_dict, tsv_dict


def convert_txt_file(filename):
    json_dict = {'filename': filename}
    f = open(filename, 'r+')
    f_cont = f.readlines()
    f_cont = [line.replace('\n', '') for line in f_cont]
    if all('\t' in line for line in f_cont):
        pass
    #to complicated to handle I guess
    #Recuperer les lignes avec separateur /n
    #si dans la ligne /t
    #en faire un tableau
    pass


def read_tsv(filename):
    json_dict = {'filename': filename}
    file = open(filename, 'r+')
    data = file.readlines()
    data = [line.replace('\n', '') for line in data]
    header = data[0].split('\t')
    tsv_dict = {key: [] for key in header}
    for lines in data[1::]:
        line = lines.split('\t')
        for key in header:
            idx = header.index(key)
            tsv_dict[key].append(line[idx])

    return json_dict, tsv_dict


def create_table(tsv_dict, channel, key2remove, table2write, table_attributes=None, file=None):
    header = table2write[0]
    name = {}
    if 'Channel' not in header:
        header.insert(0, 'Channel')
    for key in tsv_dict:
        if key not in key2remove and key not in header and len(tsv_dict[key]) == len(channel):
            header.append(key)
    for i in range(0, len(channel), 1):
        lines = ['n/a'] * len(header)
        chan = channel[i]
        for key in header:
            idx = header.index(key)
            if key in tsv_dict.keys():
                lines[idx] = str(tsv_dict[key][i])
            elif key in name.keys():
                lines[idx] = str(name[key])
            elif key == 'Channel':
                lines[idx] = chan
        table2write.append(lines)
    # create_attributes_table
    if table_attributes:
        name_list = os.path.basename(file).split('_')
        name = {elt.split('-')[0]: elt.split('-')[1] for elt in name_list if '-' in elt}
        headatt = table_attributes[0]
        for key in name:
            if key not in headatt:
                headatt.append(key)
        for i in range(0, len(channel), 1):
            lines = ['n/a'] * len(headatt)
            for key in headatt:
                ida = headatt.index(key)
                if key in name:
                    lines[ida] = name[key]
            table_attributes.append(lines)


def write_table(table2write, filename, path, json_dict=None):
    if json_dict:
        if 'filename' in json_dict:
            file, ext = os.path.splitext(json_dict['filename'])
            jsonfilename = file + '.json'
        else:
            jsonfilename = os.path.splitext(filename)[0] + '.json'
        with open(jsonfilename, 'a+') as f:
            json_str = json.dumps(json_dict, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)
    #write tsv file
    if path not in filename:
        tsvfilename = os.path.join(path, filename)
    else:
        tsvfilename = filename
    with open(tsvfilename, 'w') as file:
        for lines in table2write:
            file.write('\t'.join(lines) + '\n')


def write_file_after_convert(json_dict, tsv_dict):
    filename = os.path.splitext(json_dict['filename'])[0] + '.tsv'
    path = os.path.dirname(filename)
    flag_multifile = all(isinstance(key, int) for key in tsv_dict.keys())
    key2remove = []
    if flag_multifile:
        for i in tsv_dict:
            for key in tsv_dict[i]:
                if key.lower() in __channel_name__ and all(isinstance(elt, str) for elt in tsv_dict[i][key]):
                    channel = tsv_dict[i][key]
                    key2remove.append(key)
            if not key2remove:
                continue
            table2write = [[]]
            create_table(tsv_dict[i], channel, key2remove, table2write)
            if 'filename' in json_dict[i]:
                filename = os.path.splitext(json_dict[i]['filename'])[0] + '.tsv'
            else:
                filename = os.path.splitext(filename)[0] + '_run-' + str(i) + '.tsv'
            if table2write[0] != ['Channel']:
                write_table(table2write, filename, path, json_dict=json_dict[i])

    else:
        table2write = [[]]
        for key in tsv_dict:
            if key.lower() in __channel_name__ and all(isinstance(elt, str) for elt in tsv_dict[key]):
                channel = tsv_dict[key]
                key2remove.append(key)
        create_table(tsv_dict, channel, key2remove, table2write)
        if table2write[0] != ['Channel']:
            write_table(table2write, filename, path, json_dict)
