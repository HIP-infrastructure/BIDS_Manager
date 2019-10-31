import ins_bids_class as bids
import json
import os
import datetime
import getpass
import getopt
import sys
import subprocess
import shutil
from tkinter import messagebox, filedialog


class DerivativesSetting(object):
    path = None
    pipelines = []

    def __init__(self, bids_dev):
        if isinstance(bids_dev, bids.Derivatives):
            self.pipelines = bids_dev['Pipeline']
            self.path = os.path.join(bids_dev.cwdir, 'derivatives')
        elif isinstance(bids_dev, str):
            if os.path.exists(bids_dev) and bids_dev.endswith('derivatives'):
                self.path = bids_dev
                self.read_directory(bids_dev)

    def read_directory(self, dev_dir):
        with os.scandir(dev_dir) as it:
            for entry in it:
                if entry.is_dir():
                    pip = bids.Pipeline()
                    pip.dirname = entry.path
                    empty_dir = self.empty_dirs(entry.name, recursive=True)
                    if not empty_dir:
                        self.parse_pipeline(pip.dirname, entry.name)
                    else:
                        shutil.rmtree(entry.path, ignore_errors=True)
                    #self.pipelines.append(pip)

    def is_empty(self):
        default = ['log', 'parsing']
        pip_list = [pip['name'] for pip in self.pipelines if pip['name'] not in default]
        if pip_list:
            is_empty = False
        else:
            is_empty = True
        return is_empty, pip_list

    def create_pipeline_directory(self, pip_name, param_var, subject_list):
        def check_pipeline_variant(pip_list, pip_name):
            variant_list = []
            it_exist = False
            for pip in pip_list:
                if pip.startswith(pip_name):
                    # variant = pip.split('-')
                    # if len(variant) > 1:
                    #     variant_list.append(variant[1:])
                    variant_list.append(pip)
                    it_exist=True
            return it_exist, variant_list
        directory_name = None
        is_empty, pip_list = self.is_empty()
        mode = (param_var['Mode'] == 'manual')
        if not is_empty:
            it_exist, variant_list = check_pipeline_variant(pip_list, pip_name)
            if it_exist:
                for elt in variant_list:
                    dataset_file = os.path.join(self.path, elt, DatasetDescPipeline.filename)
                    if not os.path.exists(dataset_file):
                        dataset_file = None
                    desc_data = DatasetDescPipeline(filename=dataset_file)
                    same_param, sub_inside = desc_data.compare_parameters(param_var, subject_list)
                    if (same_param and not sub_inside) or mode:
                        directory_name = elt
                        if not mode:
                            #desc_data['SourceDataset']['sub'].append(subject_list['sub'])
                            desc_data.update(subject_list)
                        break
                if not directory_name:
                    directory_name = pip_name + '-v' + str(len(variant_list) + 1)
                    desc_data = DatasetDescPipeline(param_vars=param_var, subject_list=subject_list)
                    desc_data['Name'] = directory_name
            # if it_exist and not variant_list:
            #     directory_name = pip_name + '-v1'
            # elif it_exist and variant_list:
            #     directory_name = pip_name + '-v' + str(len(variant_list)+1)
            else:
                directory_name = pip_name
                desc_data = DatasetDescPipeline(param_vars=param_var, subject_list=subject_list)
                desc_data['Name'] = directory_name
        else:
            directory_name = pip_name
            desc_data = DatasetDescPipeline(param_var, subject_list)
            desc_data['Name'] = directory_name
        directory_path = os.path.join(self.path, directory_name)
        os.makedirs(directory_path, exist_ok=True)
        return directory_path, directory_name, desc_data

    def pipeline_is_present(self, pip_name):
        is_present = False
        idx= None
        for pip in self.pipelines:
            if pip['name'] == pip_name:
                is_present = True
                idx = self.pipelines.index(pip)

        return is_present, idx

    def parse_pipeline(self, directory_path, pip_name):
        #Function wrote by Nicolas and adapted by Aude
        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses)
                    elif not mod_dir and file.name.capitalize() in bids.ModalityType.get_list_subclasses_names() and \
                            file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.capitalize())
                    elif not mod_dir and file.name.endswith('_scans.tsv') and file.is_file():
                        tmp_scantsv = bids.ScansTSV()
                        tmp_scantsv.read_file(file)
                        for scan in subinfo['Scans']:
                            scan.compare_scanstsv(tmp_scantsv)
                    elif mod_dir and file.is_file():
                        filename, ext = os.path.splitext(file)
                        if ext.lower() == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext.lower() in bids.Process.allowed_file_formats:
                            subinfo[mod_dir + 'Process'] = eval('bids.' + mod_dir + 'Process()')
                            subinfo[mod_dir + 'Process'][-1]['fileLoc'] = file.path
                            subinfo[mod_dir + 'Process'][-1].get_attributes_from_filename()
                            subinfo[mod_dir + 'Process'][-1]['modality'] = mod_dir
                            #subinfo[mod_dir + 'Process'][-1].get_sidecar_files()
                        # elif mod_dir + 'GlobalSidecars' in bids.BidsBrick.get_list_subclasses_names() and ext.lower() \
                        #         in eval(mod_dir + 'GlobalSidecars.allowed_file_formats') and filename.split('_')[-1]\
                        #         in [eval(value + '.modality_field') for _, value in
                        #             enumerate(bids.IeegGlobalSidecars.complementary_keylist)]:
                        #     subinfo[mod_dir + 'GlobalSidecars'] = eval(mod_dir + 'GlobalSidecars(filename+ext)')
                        #     subinfo[mod_dir + 'GlobalSidecars'][-1]['fileLoc'] = file.path
                        #     subinfo[mod_dir + 'GlobalSidecars'][-1].get_attributes_from_filename()
                        #     subinfo[mod_dir + 'GlobalSidecars'][-1].get_sidecar_files()
                    elif mod_dir and file.is_dir():
                        str2add = 'Process'
                        subinfo[mod_dir + str2add] = eval('bids.' + mod_dir + str2add + '()')
                        subinfo[mod_dir + str2add][-1]['fileLoc'] = file.path

        def get_attribute_filename(filename):
            dir_list = ['sub', 'ses']
            dirname = []
            filename, ext = os.path.splitext(filename)
            if ext == '.gz':
                filename, ext = os.path.splitext(filename)
            fname_pieces = filename.split('_')
            for word in fname_pieces:
                w = word.split('-')
                if len(w) == 2 and w[0] in dir_list:
                    dirname.append(w[0]+'-'+w[1])
            modality = fname_pieces[-1]
            if not modality.capitalize() in bids.ModalityType.get_list_subclasses_names():
                modality = ''
            dirname.append(modality)
            directory = '/'.join(dirname)
            directory = os.path.join(directory_path, directory)
            os.makedirs(directory, exist_ok=True)
            return directory

        is_present, index_pip = self.pipeline_is_present(pip_name)
        if not is_present:
            pip = bids.Pipeline(name=pip_name, dirname=self.path)
            self.pipelines.append(pip)
        else:
            pip = self.pipelines[index_pip]
        name = pip_name.split('-')
        name = name[0]
        with os.scandir(directory_path) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.is_file():
                    directory = get_attribute_filename(entry.name)
                    shutil.move(entry, os.path.join(directory, entry.name))
                elif entry.name.startswith(name) and entry.is_dir():
                    for file in os.listdir(entry):
                        shutil.move(os.path.join(entry, file), directory_path)
                elif entry.name.startswith('sub-') and entry.is_dir():
                    sub, subname = entry.name.split('-')
                    pip['SubjectProcess'].append(bids.SubjectProcess())
                    pip['SubjectProcess'][-1]['sub'] = subname
                    parse_sub_bids_dir(entry.path, pip['SubjectProcess'][-1])

    def empty_dirs(self, pip_name, recursive=False):
        def is_empty(files, default_files):
            return (len(files) == 0 or all(file in default_files for file in files))

        empty_dirs = False
        emp_dirs = []
        pip_directory = os.path.join(self.path, pip_name)
        analyse_name = pip_name.split('-')[0].lower()
        default_files = [DatasetDescPipeline.filename, bids.ParticipantsTSV.filename, Parameters.filename, 'log_error_analyse.log', analyse_name + '_parameters.json']
        for root, dirs, files in os.walk(pip_directory, topdown=False):
            # print root, dirs, files
            if recursive:
                all_subs_empty = True  # until proven otherwise
                for sub in dirs:
                    full_sub = os.path.join(root, sub)
                    if full_sub not in emp_dirs:
                        # print full_sub, "not empty"
                        all_subs_empty = False
                        break
            else:
                all_subs_empty = (len(dirs) == 0)
            if all_subs_empty and is_empty(files, default_files):
                empty_dirs = True
                emp_dirs.append(root)
                # yield root
        return empty_dirs


class DatasetDescPipeline(bids.DatasetDescJSON):
    keylist = ['Name', 'BIDSVersion', 'PipelineDescription', 'SourceDataset', 'Author', 'Date']
    filename = 'dataset_description.json'
    bids_version = '1.3.0'

    def __init__(self, filename=None, param_vars=None, subject_list=None):
        super().__init__()
        if filename:
            self.read_file(filename)
        else:
            self['PipelineDescription'] = {}
            self['Author'] = getpass.getuser()
            self['Date'] = str(datetime.datetime.now())
            if param_vars and subject_list:
                for key in param_vars:
                    if key == 'Callname':
                        self['PipelineDescription']['Name'] = param_vars[key]
                    else:
                        self['PipelineDescription'][key] = param_vars[key]
                self['SourceDataset'] = {key: subject_list[key] for key in subject_list}

    def read_file(self, jsonfilename):
        if os.path.splitext(jsonfilename)[1] == '.json':
            if not os.path.exists(jsonfilename):
                print('datasetdescription.json does not exists.')
                return
            with open(jsonfilename, 'r') as file:
                read_json = json.load(file)
                for key in read_json:
                    if key == 'Authors' and isinstance(self[key], list) and self[key] == ['n/a']:
                        self[key] = read_json[key]
                    elif (key in self.keylist and self[key] == 'n/a') or key not in self.keylist:
                        self[key] = read_json[key]
        else:
            raise TypeError('File is not ".json".')

    def compare_parameters(self, param_vars, subject_list):
        keylist = [key for key in param_vars if not key == 'Callname']
        is_same = []
        if isinstance(self['PipelineDescription'], str):
            is_same = False
            no_subject = False
            return is_same, no_subject
        for key in keylist:
            if self['PipelineDescription'][key] == param_vars[key]:
                is_same.append(True)
            else:
                is_same.append(False)
        is_same = all(is_same)
        sub_in = []
        elt_in = []
        for key in subject_list:
            if key in self['SourceDataset'].keys():
                if isinstance(subject_list[key], dict):
                    for elt in subject_list[key]:
                        elt_in.append(any(el in self['SourceDataset'][key][elt] for el in subject_list[key][elt]))
                else:
                    sub_in.append(any(elt in self['SourceDataset'][key] for elt in subject_list[key]))
            else:
                elt_in.append(True)
        #subject_inside = all(sub in self['SourceDataset']['sub'] for sub in subject_list['sub'])
        subject_inside = all(sub_in and elt_in)

        return is_same, subject_inside

    def update(self, subject2add):
        for elt in subject2add:
            if isinstance(subject2add[elt], list):
                self['SourceDataset'][elt].extend(subject2add[elt])
                self['SourceDataset'][elt] = list(set(self['SourceDataset'][elt]))
            elif isinstance(subject2add[elt], dict):
                for clef in subject2add[elt]:
                    self['SourceDataset'][elt][clef].extend(subject2add[elt][clef])
                    self['SourceDataset'][elt][clef] = list(set(self['SourceDataset'][elt][clef]))


class PipelineSetting(dict):
    keylist = ['Name', 'Path', 'Parameters']
    soft_path = os.path.join(os.getcwd(), 'SoftwarePipeline')
    log_error = ''
    curr_dev = None
    curr_bids = None
    curr_path = None
    cwdir=None

    def __init__(self, bids_dir, soft_name, soft_path=None):
        if isinstance(bids_dir, str):
            if os.path.exists(bids_dir):
                try:
                    self.curr_bids = bids.BidsDataset(bids_dir)
                    self.cwdir = self.curr_bids.cwdir
                except:
                    self.log_error += 'ERROR: The bids data selected is not conform'
                    raise EOFError(self.log_error)
            else:
                self.log_error += 'ERROR: The bids data selected doesn"t exist'
                raise EOFError(self.log_error)
        elif isinstance(bids_dir, bids.BidsDataset):
            self.curr_bids = bids_dir
            self.cwdir = self.curr_bids.cwdir
        Parameters._assign_bids_dir(self.cwdir, self.curr_bids)
        if soft_path and os.path.exists(soft_path):
            self.soft_path = soft_path
        if soft_name + '.json' in os.listdir(self.soft_path):
            err_str = self.read_json_parameter_file(soft_name)
            if err_str:
                raise EOFError(err_str)
        else:
            self.log_error += 'ERROR: The software doesn"t exist'
            raise EOFError(self.log_error)
        if self.curr_path is not self['Path']:
            self['Path'] = self.curr_path
            self.write_file(os.path.join(self.soft_path, soft_name + '.json'))

    def __setitem__(self, key, value):
        if key in self.keylist:
            if isinstance(key, str):
                dict.__setitem__(self, key, value)
            elif isinstance(key, eval(key)):
                super().__setitem__(key, value)
            elif key == 'Path':
                if value.__class__.__name__ in ['str', 'unicode']:  # makes it python 2 and python 3 compatible
                    if value:
                        if os.path.isabs(value):
                            filename = value
                        else:
                            filename = os.path.join(self.soft_path, value)
                        if not os.path.exists(filename):
                            str_issue = 'file: ' + str(filename) + ' does not exist.'
                            raise FileNotFoundError(str_issue)
                    else:
                        value = self.soft_path
                    dict.__setitem__(self, key, value)
            else:
                dict.__setitem__(self, key, value)

    def copy_values(self, input_dict):
        for key in input_dict:
            if key in self.keylist:
                if key == 'Parameters':
                    self[key] = Parameters(self.curr_bids.cwdir)
                    self[key].copy_values(input_dict[key])
                else:
                    self[key] = input_dict[key]
            elif key in Parameters.get_list_subclasses_names():
                self[key] = eval(key+'()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = input_dict[key]

    def read_json_parameter_file(self, soft_name):
        jsonfile = os.path.join(self.soft_path, soft_name + '.json')
        with open(jsonfile, 'r') as file:
            read_json = json.load(file)
            self.copy_values(read_json)
        self.curr_path = self['Parameters'].check_presence_of_software(self['Path'])
        if self.curr_path.startswith('ERROR'):
            raise EOFError(self.curr_path)
        #check the validity of the json ??
        if not all(key in self.keys() for key in self.keylist):
            raise EOFError("JSON is not conform.")

    def create_parameter_to_inform(self):
        def read_file(file, elements):
            param = []
            name, ext = os.path.splitext(file)
            if ext == '.csv':
                split_value = ', '
            else:
                split_value = '\t'
            f = open(file, 'r')
            f_cont = f.readlines()
            if elements == 'header':
                header = f_cont[0].split(split_value)
                for val in header:
                    param.append(val)
                f.close()
                return param
            elif elements.isnumeric():
                idx = int(elements)
            elif elements:
                line = f_cont[0].split('\n')[0]
                header = line.split(split_value)
                idx = header.index(elements)
            else:
                idx = 0
            for line in f_cont[1::]:
                line = line.split('\n')[0]
                trial_type = line.split(split_value)
                param.append(trial_type[idx])
            f.close()
            return param

        def compare_listes(liste_final, liste_file):
            is_same = True
            sX = set(liste_final)
            sY = set(liste_file)
            set_common = sX - sY
            if not set_common == sX:
                is_same = False
            for elt in liste_file:
                if elt not in liste_final:
                    liste_final.append(elt)
            return is_same

#Should I give only the value presents in all subjects or indicate that there is not all value for all subjects ???
        param_vars = {}
        input_vars = {}
        keys_2_remove = []
        error_log = ''
        self['Parameters'].create_parameter_to_inform(param_vars)
        for key in param_vars:
            if key.startswith('Input'):
                if param_vars[key]:
                    input_vars[key] = param_vars[key]
                keys_2_remove.append(key)
            elif isinstance(param_vars[key]['value'], bool):
                pass
            elif not param_vars[key]['value']:
                pass
            elif 'file' in param_vars[key]['value']:
                reading_file = param_vars[key]['value']['file']
                elements = param_vars[key]['value']['elements']
                mark_to_remove = ['?', '***', '*']
                param = []
                is_same = True
                for subject in os.listdir(self.curr_bids.cwdir):
                    if subject.endswith(reading_file) and os.path.isfile(os.path.join(self.curr_bids.cwdir, subject)):
                        file_param = read_file(os.path.join(self.curr_bids.cwdir, subject), elements)
                        if not param:
                            param = [elt for elt in file_param]
                        else:
                            is_same = compare_listes(param, file_param)
                        break
                    elif subject.startswith('sub') and os.path.isdir(os.path.join(self.curr_bids.cwdir, subject)):
                        for session in os.listdir(os.path.join(self.curr_bids.cwdir, subject)):
                            if os.path.isdir(os.path.join(self.curr_bids.cwdir, subject, session)):
                                for mod in os.listdir(os.path.join(self.curr_bids.cwdir, subject, session)):
                                    if os.path.isdir(os.path.join(self.curr_bids.cwdir, subject, session, mod)):
                                        with os.scandir(os.path.join(self.curr_bids.cwdir, subject, session, mod)) as it:
                                            for entry in it:
                                                if entry.name.endswith(reading_file):
                                                    file_param = read_file(entry.path, elements)
                                                    if not param:
                                                        param = [elt for elt in file_param]
                                                    else:
                                                        is_same = compare_listes(param, file_param)
                                    elif os.path.isfile(os.path.join(self.curr_bids.cwdir, subject, session, mod)) and mod.endswith(reading_file):
                                        file_param = read_file(os.path.join(self.curr_bids.cwdir, subject, session, mod), elements)
                                        if not param:
                                            param = [elt for elt in file_param]
                                        else:
                                            is_same = compare_listes(param, file_param)
                param = list(set(param))
                param.sort()
                if not param:
                    raise EOFError("All the dataset is not ready for this analysis.\n There is no file format {0} in your Bids database.".format(reading_file))
                elif not is_same:
                    error_log += 'WARNING: Not all files have the same elements.'

                param_vars[key]['value'] = [par for par in param if not par in mark_to_remove]
        for key in keys_2_remove:
            del param_vars[key]

        if self['Parameters'].arg_readbids:
            input_vars['arg_readbids'] = self['Parameters'].arg_readbids

        return param_vars, input_vars, error_log

    def set_everything_for_analysis(self, results):

        def list_for_str_format(order, idx):
            use_list = []
            for elt in order:
                if isinstance(elt, list):
                    if isinstance(elt[idx], list):
                        use_list.append('"'+', '.join(elt[idx])+'"')
                    else:
                        use_list.append(elt[idx])
                else:
                    use_list.append(elt)
            return use_list
        # subject_list = results['subject_selected']
        #input_param = results['input_param']
        # for inp, value in input_param.items():
        #     subject_to_analyse.copy_values(value)
        #Check if the param are dict or file
        param_vars = results['analysis_param']
        if isinstance(param_vars, str):
            file, ext = os.path.splitext(param_vars)
            if not ext == '.json':
                self.log_error += str(datetime.datetime.now()) + ': ' + 'ERROR: The parameters file format is not correct. Format should be json. \n'
                return self.log_error
            else:
                with open(param_vars, 'r') as file:
                    param_vars = json.load(file)

        #save the param_vars in json file for next analysis
        try:
            # update the parameters and get the subjects
            self['Parameters'].update_values(param_vars, results['input_param'])
            #Verify the validity of the input value
            warn, err = verify_subject_has_parameters(self.curr_bids,
                                                      results['subject_selected']['sub'],
                                                      results['input_param'],
                                                      self['Parameters']['Input'])
            if warn:
                self.log_error += 'Warning: ' + warn
            if err:
                raise ValueError(err)
            subject_to_analyse = SubjectToAnalyse(results['subject_selected']['sub'], input_dict=results['input_param'])
            dev = DerivativesSetting(self.curr_bids['Derivatives'][0])
            output_directory, output_name, dataset_desc = dev.create_pipeline_directory(self['Name'], param_vars, subject_to_analyse)
            participants = bids.ParticipantsProcessTSV()


            # Check if the subjects have all the required values
            self['Parameters'].write_file(output_directory)
            # subject_to_analyse = SubjectToAnalyse(subject_list)
            # for inp, value in input_param.items():
            #     subject_to_analyse.copy_values(value)

            dataset_desc['PipelineDescription']['fileLoc'] = os.path.join(output_directory, Parameters.filename)
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, 'dataset_description.json'))

            #Get the value for the command_line
            cmd_arg, cmd_line, order, input_dict, output_dict = self.create_command_to_run_analysis(output_directory, subject_to_analyse) #input_dict, output_dict
        except (EOFError, TypeError, ValueError, SystemError) as er:
            self.log_error += str(er)
            self.write_error_system()
            return self.log_error

        if not order:
            proc = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            error_proc = proc.communicate()
            self.log_error += cmd_arg.verify_log_for_errors('', error_proc)
            self.write_json_associated(order, output_directory, cmd_arg)
            for sub in subject_to_analyse['sub']:
                participants.append({'participant_id': sub})
        elif order:
            taille, idx_in, in_out = input_dict.get_input_values(subject_to_analyse, order)
            if output_dict:
                output_dict.get_output_values(in_out, taille, order, output_directory, idx_in)  # sub
            for sub in in_out:
                idx = 0
                log_error = []
                while idx < taille[sub]:
                    use_list = list_for_str_format(in_out[sub], idx)
                    cmd = cmd_line.format(*use_list)
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            universal_newlines=True)
                    error_proc = proc.communicate()
                    self.log_error += cmd_arg.verify_log_for_errors(use_list, error_proc)
                    if not error_proc[1]:
                        self.write_json_associated(use_list, output_directory, cmd_arg)
                    else:
                        log_error.append(error_proc[1])
                    idx = idx + 1
                if len(log_error) != taille[sub]:
                    participants.append({'participant_id': sub})
        else:
            self.log_error += str(datetime.datetime.now()) + ': ' + 'ERROR: The analysis {0} could not be run due to an issue with the inputs and the outputs.\n'.format(self['Name'])
            return self.log_error
        empty_dir = dev.empty_dirs(output_name, recursive=True)
        if not empty_dir:
            participants.write_file(tsv_full_filename=os.path.join(output_directory, bids.ParticipantsTSV.filename))
            dataset_desc.update(subject_to_analyse)
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, DatasetDescPipeline.filename))
            self.write_error_system(output_directory)
            dev.parse_pipeline(output_directory, output_name)
            self.curr_bids.save_as_json()
        else:
            self.log_error += str(datetime.datetime.now()) + ': ' + 'Warning: The folder {0} has no results so your analysis may not succeed. The folder {0} will be erased.\n'.format(output_name)
            shutil.rmtree(output_directory)

        return self.log_error

    def create_command_to_run_analysis(self, output_directory, subject_to_analyse):
        #Take the mode into account for now, only automatic
        interm = None
        cmd_line_set = None
        callname = self['Parameters']['Callname']
        mode = self['Parameters']['Mode'][-1]
        input_p = None
        output_p = None
        if 'command_line_base' in self['Parameters'].keys():
            cmd_line_set = self['Parameters']['command_line_base']
        if 'Intermediate' in self['Parameters'].keys():
            interm = self['Parameters']['Intermediate']

        if interm:
            cmd_arg = eval(interm + '(curr_path=self.curr_path, dev_path=output_directory, callname=callname)') #'(bids_directory="'+self.cwdir+'", curr_path="'+self.curr_path+'", dev_path="'+output_directory+'", callname="'+callname+'")')
        else:
            cmd_arg = Parameters(curr_path=self.curr_path, dev_path=output_directory, callname=callname)

        for key in self['Parameters']:
            if isinstance(self['Parameters'][key], Arguments):
                self['Parameters'][key].command_arg(key, cmd_arg, subject_to_analyse)
            elif key == 'Input':
                input_p = self['Parameters'][key]
                cmd_arg['Input'] = ''
            elif key == 'Output':
                output_p = self['Parameters'][key]
                output_p.bids_directory = self.cwdir
                cmd_arg['Output'] = ''

        cmd_line, order = cmd_arg.command_line_base(cmd_line_set, mode, output_directory, input_p, output_p)#, input_dict, output_dict)
        #order.multiplesubject = input_p[0]['multiplesubject']
        return cmd_arg, cmd_line, order, input_p, output_p

    def write_json_associated(self, inout_file, output_directory, analyse):
        def create_json(input_file, output_json, analyse):
            jsonf = bids.BidsJSON()
            jsonf['Description'] = 'Results of ' + self['Name'] + ' analysis.'
            jsonf['RawSources'] = input_file
            jsonf['Parameters'] = analyse
            jsonf['Author'] = getpass.getuser()
            jsonf['Date'] = str(datetime.datetime.now())
            jsonf.write_file(output_json)

        output_fin = None
        input_file = None
        for elt in inout_file:
            if output_directory in elt:
                output_fin = elt
            else:
                input_file = elt

        if not output_fin:
            pass
        elif os.path.isfile(output_fin):
            filename, ext = os.path.splitext(output_fin)
            output_json = output_fin.replace(ext, bids.BidsJSON.extension)
            if os.path.exists(output_json):
                pass
            else:
                create_json(input_file, output_json, analyse)
        elif os.path.isdir(output_fin):
            if input_file:
                filename = os.path.basename(input_file)
                filename, ext = os.path.splitext(filename)
                modality = os.path.basename(output_fin)
                filename = filename.replace(modality, '')
                potential_file = [entry for entry in os.listdir(output_fin) if entry.startswith(filename)]
                is_json = False
                for it in potential_file:
                    if it.endswith(bids.BidsJSON.extension):
                        is_json = True
                if not is_json and potential_file:
                    filename, ext = os.path.splitext(potential_file[-1])
                    output_file = potential_file[-1].replace(ext, bids.BidsJSON.extension)
                    output_json = os.path.join(output_fin, output_file)
                    create_json(input_file, output_json, analyse)
            else:
                for entry in os.listdir(output_fin):
                    if os.path.isfile(os.path.join(output_fin, entry)):
                        filename, ext = os.path.splitext(entry)
                        if not (filename.startswith('dataset_description') or filename.startswith(
                                'log_error_analyse') or filename.startswith('participants')):
                            potential_file = [entry for entry in os.listdir(output_fin) if entry.startswith(filename)]
                            is_json = False
                            for it in potential_file:
                                if it.endswith(bids.BidsJSON.extension):
                                    is_json = True
                            if not is_json:
                                filename, ext = os.path.splitext(potential_file[-1])
                                output_file = potential_file[-1].replace(ext, bids.BidsJSON.extension)
                                output_json = os.path.join(output_fin, output_file)
                                create_json('', output_json, analyse)

    def write_error_system(self, output_directory=None):
        if not output_directory:
            output_directory = os.path.join(self.cwdir, 'derivatives', 'log')

        log_file = os.path.join(output_directory, 'log_error_analyse.log')
        #os.makedirs(log_file, exist_ok=True)
        with open(log_file, 'w+') as f:
            f.write(self.log_error)

    def write_file(self, filename):
        with open(filename, 'w+') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)


class Parameters(dict):
    keylist = ['command_line_base', 'Intermediate', 'Callname']
    analyse_type = []
    analyse_type = None
    derivatives_directory = None
    bids_directory = None
    callname = None
    curr_path = None
    curr_bids = None
    arg_readbids = []
    filename = 'parameters_file.json'

    def __init__(self, curr_path=None, dev_path=None, callname=None):
        if dev_path:
            self.derivatives_directory = dev_path
        if callname:
            self.callname = callname
        if curr_path:
            self.curr_path = curr_path

    def copy_values(self, input_dict):
        for key in input_dict:
            if key in self.keylist:
                self[key] = input_dict[key]
            elif key in ParametersSide.get_list_subclasses_names() + Parameters.get_list_subclasses_names():
                self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = Arguments()
                self[key].copy_values(input_dict[key])

    def create_parameter_to_inform(self, param_vars, key=None):
        bool_list = []
        for key, value in self.items():
            if key in Parameters.get_list_subclasses_names() + ParametersSide.get_list_subclasses_names():
                value.create_parameter_to_inform(param_vars, key=key)
            elif isinstance(value, Arguments):
                readbids = value.create_parameter_to_inform(param_vars, key=key)
                if readbids is not None:
                    self.arg_readbids.append(readbids)


    def update_values(self, input_dict, input_param=None):
        keylist = list(self.keys())
        for key in input_dict:
            if key in keylist:
                self[key].update_values(input_dict[key])
            else:
                new_key, *tag = key.split('_')
                if isinstance(tag, list):
                    tag = '_'.join(tag)
                self[new_key].update_values(input_dict[key], tag)
        if input_param:
            input_tag = [elt['tag'] for elt in self['Input']]
            for inp in input_param:
                if inp in input_tag:
                    idx = input_tag.index(inp)
                    self['Input'][idx].update_values(input_param[inp])

    def check_presence_of_software(self, curr_path):
        def type_of_software(name, intermediaire):
            if not intermediaire:
                return name
            elif intermediaire == 'Docker':
                return ''
            else:
                return intermediaire

        def select_pipeline_path(name):
            messagebox.showerror('PathError', 'The current pipeline path is not valid')
            filename = filedialog.askopenfilename(title='Please select ' + name + ' file',
                                                  filetypes=[('exe files', '.exe'), ('m files', '.m'), ('py files', '.py')])
            if not name in filename:
                messagebox.showerror('PathError', 'The selected file is not the good one for this pipeline')
                return 'ERROR: The path is not valid'

            return filename

        interm = None
        if 'Intermediate' in self.keys():
            interm = self['Intermediate']
        name = type_of_software(self['Callname'], interm)
        if not name:
            return ''
        if curr_path:
            if not os.path.exists(curr_path):
                curr_path = select_pipeline_path(name)
            elif not name in curr_path:
                curr_path = select_pipeline_path(name)
        else:
            curr_path = select_pipeline_path(name)
        return curr_path

    def command_arg(self, key, cmd_dict, subject_list):
        if 'value_selected' in self.keys():
            # if isinstance(self['value_selected'], list):
            #     cmd_dict[key] = ', '.join(self['value_selected'])
            # else:
            cmd_dict[key] = self['value_selected']
        # elif 'default' in self.keys():
        #     if self['default']:
        #         cmd_dict[key] = self['default']
        elif 'readbids' in self.keys():
            type_value = None
            for clef in subject_list.keys():
                if clef == self['type']:
                    type_value = subject_list[self['type']]
                elif isinstance(subject_list[clef], dict):
                    type_value = []
                    for elt in subject_list[clef]:
                        if elt == self['type']:
                            type_value.extend(subject_list[clef][self['type']])
                if type_value:
                    cmd_dict[key] = type_value

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        if not cmd_line_set:
            cmd_base = self.curr_path
        else:
            cmd_base = self.curr_path + cmd_line_set

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    def chaine_parameters(self, output_directory, input_dict, output_dict):
        cmd_line =''
        cnt_tot = 0
        order = {}
        for clef in self:
            if clef == 'Input':
                for elt in input_dict:
                    if elt['multiplesubject'] and elt['type'] == 'dir':
                        if not elt.deriv_input:
                            cmd_line += ' ' + elt['tag'] + ' ' + self.bids_directory
                        elif elt.deriv_input and (elt['deriv-folder'] and elt['deriv-folder'] != ''):
                            cmd_line += ' ' + elt['tag'] +  ' ' + os.path.join(self.bids_directory, 'derivatives', elt['deriv-folder'])
                    else:
                        if elt.deriv_input:
                            if elt['deriv-folder'] == '' and not elt['optional']:
                                raise ValueError('The derivative folder for this paramater {} should be mentionned.\n'.format(elt['tag']))
                            elif elt['deriv-folder'] != '':
                                order[elt['tag']] = cnt_tot
                                cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                                cnt_tot += 1
                        else:
                            order[elt['tag']] = cnt_tot
                            cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                            cnt_tot += 1
            elif clef == 'Output':
                if output_dict['multiplesubject'] and output_dict['directory']:
                    cmd_line += ' ' + output_dict['tag'] + ' ' + output_directory
                else:
                    order[output_dict['tag']] = cnt_tot
                    cmd_line += ' ' + output_dict['tag'] + ' {' + str(cnt_tot) + '}'
                    cnt_tot += 1
                #cmd_line += determine_input_output_type(output_dict, cnt_tot, order)
                #order.append(output_dict)
            elif isinstance(self[clef], bool):
                cmd_line += ' ' + clef
            elif isinstance(self[clef], list):
                if len(self[clef]) == 1:
                    cmd_line += ' ' + clef + ' ' + self[clef][0]
                else:
                    cmd_line += ' ' + clef + ' "' + ', '.join(self[clef]) + '"'
            else:
                cmd_line += ' ' + clef + ' ' + self[clef]
        return cmd_line, order

    def verify_log_for_errors(self, input, x):
        log_error = ''
        if isinstance(x, tuple):
            if not x[0] and not x[1]:
                log_error += str(datetime.datetime.now()) + ': ' + ' '.join(input) + ' has been analyzed with no error\n'
            elif not x[1]:
                log_error += str(datetime.datetime.now()) + ': ' + ' '.join(input) + ': '+ x[0] + '\n'
            else:
                log_error += str(datetime.datetime.now()) + ': ERROR: ' + ' '.join(input)+ ': ' + x[1] + '\n'

        return log_error

    def write_file(self, output_directory):
        filename = os.path.join(output_directory, self.filename)
        with open(filename, 'w+') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)

    #Fonction wrote by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names

    @classmethod
    def _assign_bids_dir(cls, bids_dir, curr_bids):
        cls.bids_directory = bids_dir
        cls.curr_bids = curr_bids
        PipelineSetting.cwdir = bids_dir


class AnyWave(Parameters):
    anywave_directory = None

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        self['plugin'] = self.callname
        cmd_end = ''
        if not cmd_line_set:
            cmd_line_set = ' --run'
        cmd_base = self.curr_path + cmd_line_set

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    def chaine_parameters(self, output_directory, input, output):
        jsonfilename = os.path.join(self.derivatives_directory, self['plugin'] + '_parameters' + '.json')

        del self['Input']
        del self['Output']
        with open(jsonfilename, 'w') as json_file:
            json.dump(self, json_file)
        cmd_line = ' "' + jsonfilename + '"'

        order = {}
        #Handle the input and output
        cnt_tot = 0
        for cn, elt in enumerate(input):
            if elt['multiplesubject'] and elt['type'] == 'dir':
                cmd_line += ' ' + elt['tag'] + ' ' + self.bids_directory
            else:
                if not elt['tag']:
                    order['in' + str(cn)] = cnt_tot
                else:
                    order[elt['tag']] = cnt_tot
                cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                cnt_tot += 1

        if output['multiplesubject'] and output['directory']:
            cmd_line += ' ' + output['tag'] + ' ' + output_directory
        else:
            if not output['tag']:
                order['out'] = cnt_tot
            else:
                order[output['tag']] = cnt_tot
            cmd_line += ' ' + output['tag'] + ' {' + str(cnt_tot) + '}'
            cnt_tot += 1

        return cmd_line, order

    def verify_log_for_errors(self, input, x=None):
        log_error = ''
        # read log in Documents
        home = os.path.expanduser('~')
        if getpass.getuser() == 'jegou':
            self.anywave_directory = r'Z:\Mes documents\AnyWave\Log'
        else:
            self.anywave_directory = os.path.join(home, 'Documents', 'AnyWave', 'Log')
        temp_time = 0
        filename =''
        with os.scandir(self.anywave_directory) as it:
            for entry in it:
                time_file = os.path.getctime(entry)
                if time_file > temp_time:
                    temp_time = time_file
                    filename = entry.path
        f = open(filename, 'r')
        f_cont = f.readlines()
        for elt in f_cont:
            log_error += elt
        f.close()

        return log_error


class Docker(Parameters):
    keylist = ['command_line_base', 'Intermediate', 'Callname']

    def __init__(self, curr_path=None, dev_path=None, callname=None):
        super().__init__(curr_path=curr_path, dev_path=dev_path, callname=callname)
        out_docker = subprocess.check_output("docker -v", shell=True)
        out_docker = out_docker.decode("utf-8")
        if not out_docker.startswith('Docker version'):
            raise SystemError('Docker is not installed on your computer.\n Please install docker before to continue.\n')

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        os.system('docker pull ' + self.callname)
        if not cmd_line_set:
            cmd_line_set = 'docker run -ti --rm'
        #should change outputs in derivatives normally
        cmd_base = cmd_line_set + ' -v ' + self.bids_directory + ':/bids_dataset:ro -v ' + self.derivatives_directory + ':/outputs ' + self.callname + ' /bids_dataset /outputs'

        cmd_line, order = self.chaine_parameters(input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    def chaine_parameters(self, input_dict, output_dict):
        cmd_line =''
        cnt_tot = 0
        order = {}
        for clef in self:
            # if clef == 'Input':
            #     for elt in input_dict:
            #         if elt['multiplesubject'] and elt['type'] == 'dir':
            #             cmd_line += elt['tag'] + ' ' + self.bids_directory
            #         else:
            #             order[elt['tag']] = cnt_tot
            #             cmd_line += elt['tag'] + ' {' + str(cnt_tot) + '} '
            #             cnt_tot += 1
            # el
            if isinstance(self[clef], bool):
                cmd_line += ' ' + clef
            elif isinstance(self[clef], list):
                if len(self[clef]) > 1:
                    value = ' '.join(self[clef])
                    cmd_line += ' ' + clef + ' [' + value + ']'
                else:
                    value = self[clef][0]
                    cmd_line += ' ' + clef + ' ' + value
            else:
                cmd_line += ' ' + clef + ' ' + self[clef]
        return cmd_line, order


class Matlab(Parameters):

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        cmd_end = ''
        if mode == 'automatic':
            if not cmd_line_set:
                cmd_line_set = "matlab -wait -nosplash -nodesktop -r \"cd('" + os.path.dirname(self.curr_path) + "'); "
            cmd_end = '; exit\"'
        elif mode == 'manual':
            if not cmd_line_set:
                cmd_line_set = "matlab -wait -nosplash -nodesktop -r \"cd('" + os.path.dirname(self.curr_path) + "'); "
        cmd_base = cmd_line_set + self.callname

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line + cmd_end
        return cmd, order

    def chaine_parameters(self, output_directory, input_dict, output_dict):
        cmd_line = []
        cnt_tot = 0
        order = {}
        for clef in self:
            if clef == 'Input':
                for cn, elt in enumerate(input_dict):
                    if elt['multiplesubject'] and elt['type'] == 'dir':
                        if elt['tag']:
                            cmd_line.append("'" + elt['tag'] + "'")
                        cmd_line.append("'" + self.bids_directory + "' ")
                    else:
                        if not elt['tag']:
                            order['in'+str(cn)] = cnt_tot
                        else:
                            order[elt['tag']] = cnt_tot
                        cmd_line.append("'{" + str(cnt_tot) + "}'")
                        cnt_tot += 1
            elif clef == 'Output':
                if output_dict['multiplesubject'] and output_dict['directory']:
                    if output_dict['tag']:
                        cmd_line.append("'"+output_dict['tag']+"'")
                    cmd_line.append("'" + output_directory + "'")
                else:
                    if not output_dict['tag']:
                        order['out'] = cnt_tot
                    else:
                        order[output_dict['tag']] = cnt_tot
                    cmd_line.append("'{" + str(cnt_tot) + "}'")
                    cnt_tot += 1
            elif isinstance(self[clef], list):
                cmd_line.append(" '"+clef+"' ")
                value = '", '.join(self[clef])
                cmd_line.append("'" + value +"'")
            elif self[clef].isnumeric():
                cmd_line.append(" '"+clef+"' ")
                cmd_line.append(self[clef])
            else:
                cmd_line.append(" '" + clef + "' ")
                cmd_line.append("'"+self[clef]+"'")
        cmd_line = '(' + ', '.join(cmd_line) + ')'

        return cmd_line, order


class ParametersSide(list):

    def copy_values(self, input_dict):
        for elt in input_dict:
            self.append(elt)

    #Fonction wrote by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class Mode(ParametersSide):

    def create_parameter_to_inform(self, param_vars, key=None):
        param_vars[key] = {}
        if len(self) > 1:
            param_vars[key]['attribut'] = 'Listbox'
            param_vars[key]['value'] = self
        elif len(self) == 1:
            param_vars[key]['attribut'] = 'Label'
            param_vars[key]['value'] = self[-1]

    def update_values(self, input_dict):
        key2remove = []
        for elt in self:
            if not elt == input_dict:
                key2remove.append(elt)
                #self.remove(elt)
        for key in key2remove:
            self.remove(key)


class Input(ParametersSide):

    def copy_values(self, input_dict):
        for elt in input_dict:
            mod_dict = InputArguments()
            mod_dict.copy_values(elt)
            self.append(mod_dict)

    def create_parameter_to_inform(self, param_vars, key=None):
        for input in self:
            key = 'Input_' + input['tag']
            param_vars[key] = {}
            input.create_parameter_to_inform(param_vars, key=key)

    def update_values(self, input_dict, tag, input_param=None):
        for elt in self:
            if elt['tag'] == tag:
                elt.update_values(input_dict)

    def command_arg(self, subject_list, curr_bids):
        size = len(self)
        if size == 1:
            input_file = self[0].command_arg(subject_list, curr_bids)
        else:
            input_file = Input()
            for elt in self:
                f_list = elt.command_arg(subject_list, curr_bids)
                input_file.append(f_list)
        return input_file

    def control_length_of_multiple_input(self):
        taille = [len(list(elt.values())[0]) for elt in self]
        result = all(elem == taille[0] for elem in taille)
        if result:
            return True
        else:
            return False

    def get_input_values(self, subject_to_analyse, order):
        def compare_length_multi_input(in_out, idx_in):
            err = ''
            for i in range(0, len(idx_in)-1):
                if len(in_out[i]) != len(in_out[i+1]):
                    'ERROR: The elements in the list don"t have the same size'
            return err

        in_out = {clef: ['']*len(order) for clef in subject_to_analyse['sub']}
        temp = {clef: 0 for clef in subject_to_analyse['sub']}
        order_tag = [tag for tag in order]
        idx_in = []
        for cn, elt in enumerate(self):
            not_inside = False
            if not elt['tag']:
                idx = order['in'+str(cn)]
            elif elt['tag'] not in order_tag:
                not_inside = True
            else:
                idx = order[elt['tag']]
            if not not_inside:
                elt.get_input_values(subject_to_analyse, in_out, idx)
                # if temp:
                #     if temp != len(in_out[idx]):
                #         raise ValueError('The elements in the list don"t have the same size')
                # else:
                #     temp = len(in_out[idx])
                idx_in.append(idx)
        for sub in in_out:
            if len(idx_in) > 1:
                error = compare_length_multi_input(in_out[sub], idx_in)
                if error:
                    raise ValueError(error)
            temp[sub] = len(in_out[sub][idx_in[0]])

        return temp, idx_in, in_out


class InputArguments(Parameters):
    keylist = ['tag', 'multiplesubject', 'modality', 'type']
    keylist_deriv = keylist + ['deriv-folder', 'filetype', 'optional']
    path_key = ['sub', 'ses', 'modality']
    multiplesubject = False
    deriv_input = False

    def copy_values(self, input_dict): #, flag_process=False):
        keys = list(input_dict.keys())
        if not keys == self.keylist and not keys == self.keylist_deriv: #and not flag_process:
            raise KeyError('Your json is not conform.\n')
        else:
            for key in input_dict:
                if key == 'modality' and isinstance(input_dict[key], str):
                    self[key] = []
                    self[key].append(input_dict[key])
                elif key == 'deriv-folder':
                    self[key] = input_dict[key]
                    self.deriv_input = True
                else:
                    self[key] = input_dict[key]
        if self['multiplesubject'] and self['type'] == 'file':
            raise ValueError('Your json is not conform.\n It is not possible to have files as input and process multiple subject.\n')

    def create_parameter_to_inform(self, param_vars, key=None):
        if self.deriv_input: #self.read_deriv_fold is not None:
            param_vars[key]['deriv-folder'] = dict()
            param_vars[key]['deriv-folder']['attribut'] = 'Listbox'
            deriv_list = [elt['name'] for elt in self.curr_bids['Derivatives'][-1]['Pipeline'] if elt['name'] not in ['log', 'parsing', 'parsing_old']]
            param_vars[key]['deriv-folder']['value'] = deriv_list
        if self['modality']:
            param_vars[key]['modality'] = dict()
            if len(self['modality']) > 1:
                param_vars[key]['modality']['attribut'] = 'Listbox'
                param_vars[key]['modality']['value'] = self['modality']
            else:
                param_vars[key]['modality']['value'] = self['modality'][-1]
                param_vars[key]['modality']['attribut'] = 'Label'
        else:
            return

    def update_values(self, input_dict):
        for key in input_dict:
            if key in self.keys() and key == 'deriv-folder':
                self[key] = input_dict[key]
        #self['value_selected'] = input_dict

    def get_input_values(self, subject_to_analyse, in_out, idx):#sub, input_param=None):
        if self.deriv_input: #'deriv-folder' in self.keys():
            if self['deriv-folder'] and self['deriv-folder'] != '':
                self.curr_bids.is_pipeline_present(self['deriv-folder'])
                if not self.curr_bids.curr_pipeline['isPresent']:
                    raise ValueError(
                        'The derivatives folder {} selected doesn"t exists in the Bids Dataset.\n'.format(
                            self['deriv-folder']))
                #self.read_deriv_fold = subject_to_analyse[self['tag']]['deriv-folder']
            elif self['deriv-folder'] == '' and self['optional']:
                return
            else:
                raise ValueError('You have to select a derivatives folder for the input {}'.format(self['tag']))
        if self['type'] == 'file':
            for sub in subject_to_analyse['sub']:
                in_out[sub][idx] = self.get_subject_files(subject_to_analyse[self['tag']], sub)
        elif self['type'] == 'dir':
            path_key = {key: '' for key in self.path_key}
            for key, val in subject_to_analyse[self['tag']].items():
                if key in self.path_key:
                    if isinstance(val, list) and len(val) == 1:
                        path_key[key] = val[0]
                    elif isinstance(val, str):
                        path_key[key] = val.lower()
            for sub in subject_to_analyse['sub']:
                path_key['sub'] = sub
                chemin = []
                if self.deriv_input:
                    chemin.append('derivatives\\' + self['deriv-folder'])
                    path_key['modality'] = path_key['modality'] + 'Process'
                for key, val in path_key.items():
                    if val and key != 'modality':
                        chemin.append(key+'-'+val)
                    elif val and key == 'modality':
                        if val not in bids.ModalityType.get_list_subclasses_names():
                            for mod in bids.ModalityType.get_list_subclasses_names():
                                if val.split('Process')[0] in eval('bids.'+mod+'.allowed_modalities'):
                                    val = mod
                        chemin.append(val.lower())
                in_out[sub][idx] = [os.path.join(self.bids_directory, '\\'.join(chemin))]

    # def command_arg(self, subject_list, curr_bids):
    #     f_list = []
    #     if 'value_selected' in self.keys():
    #         modality = self['value_selected']
    #     else:
    #         modality = self['modality']
    #     if not modality:
    #         pass
    #         #return 'ERROR: Don"t know on each modality we should process'
    #     else:
    #         subject_list['modality'] = modality
    #
    #     if self['type'] == 'file':
    #         f_list = self.get_subject_files(modality, subject_list, curr_bids)
    #     elif self['type'] == 'sub':
    #         f_list = subject_list['sub']
    #     elif self['type'] == 'dir':
    #         f_list = curr_bids.cwdir
    #     else:
    #         raise ValueError('The selected type is not conform')
    #     input_to_return = InputArguments()
    #     input_to_return[self['tag']] = f_list
    #     input_to_return.multiplesubject = self.multiplesubject
    #
    #     return input_to_return #{self['tag']: f_list}

    def get_subject_files(self, subject, sub_id, deriv_reader=None):#, modality, subject_list, curr_bids):
        input_files = []
        if 'modality' not in subject.keys():
            subject['modality'] = self['modality']
        modality = [elt for elt in bids.ModalityType.get_list_subclasses_names() if elt in subject['modality']]
        if not modality:
            modality = [elt for elt in bids.ModalityType.get_list_subclasses_names() if any(elmt in subject['modality'] for elmt in eval('bids.' + elt + '.allowed_modalities'))]
        if self.deriv_input:
            self.curr_bids.is_pipeline_present(self['deriv-folder'])
            for sub in self.curr_bids.curr_pipeline['Pipeline']['SubjectProcess']:
                if sub['sub'] == sub_id:
                    for mod in sub:
                        if mod in modality:
                            for elt in sub[mod]:
                                is_equal = []
                                for key in elt:
                                    if key in subject.keys() and subject[key]:
                                        if elt[key] in subject[key]:
                                            is_equal.append(True)
                                        elif key == 'modality':
                                            pass
                                        else:
                                            is_equal.append(False)
                                    elif key == 'fileLoc':
                                        if elt[key].endswith(self['filetype']):
                                            is_equal.append(True)
                                        else:
                                            is_equal.append(False)
                                is_equal = list(set(is_equal))
                                if not is_equal:
                                    pass
                                elif len(is_equal) == 1 and is_equal[0]:
                                    input_files.append(os.path.join(self.bids_directory, elt['fileLoc']))
        else:
            for sub in self.curr_bids['Subject']:
                if sub['sub'] == sub_id:
                    for mod in sub:
                        if mod in modality:
                            for elt in sub[mod]:
                                is_equal = []
                                for key in elt:
                                    if key in subject.keys() and subject[key]:
                                        if elt[key] in subject[key]:
                                            is_equal.append(True)
                                        elif key == 'modality':
                                            if elt[key] in subject[key]:
                                                is_equal.append(True)
                                            elif elt[key].capitalize() in subject[key]:
                                                is_equal.append(True)
                                            else:
                                                is_equal.append(False)
                                        else:
                                            is_equal.append(False)
                                is_equal = list(set(is_equal))
                                if not is_equal:
                                    pass
                                elif len(is_equal) == 1 and is_equal[0]:
                                    input_files.append(os.path.join(self.bids_directory, elt['fileLoc']))

        return input_files


class Output(Parameters):
    keylist = ['tag', 'multiplesubject', 'directory', 'type', 'extension']
    multiplesubject = False

    def copy_values(self, input_dict, flag_process=False):
        keys = list(input_dict.keys())
        if not keys == self.keylist and not flag_process:
            raise KeyError('Your json is not conform')
        else:
            for key in input_dict:
                self[key] = input_dict[key]
        if self['multiplesubject'] and self['type'] == 'file':
            raise ValueError('Your json is not conform.\n It is not possible to have files as input and process multiple subject.\n')

    def create_parameter_to_inform(self, param_vars, key=None):
        if self['multiplesubject']:
            self.multiplesubject = True

    def update_values(self, input_dict):
        self['value_selected'] = input_dict

    def get_output_values(self, in_out, taille, order, output_directory, idx_in): #sub,
        def create_output_file(output_dir, filename, extension, bids_directory):
            out_file = []
            soft_name = os.path.basename(output_dir).lower()
            soft_name = soft_name.split('-v')[0]
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory + '\\')
            file_elt = filename.split('_')
            if isinstance(extension, list):
                for ext in extension:
                    file_elt[-1] = soft_name + ext
                    filename = '_'.join(file_elt)
                    output = os.path.join(output_dir, dirname, filename)
                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    out_file.append(output)
            else:
                file_elt[-1] = soft_name + extension
                filename = '_'.join(file_elt)
                output = os.path.join(output_dir, dirname, filename)
                os.makedirs(os.path.dirname(output), exist_ok=True)
                out_file.append(output)
            return out_file

        def create_output_sub_dir(output_dir, filename, bids_directory):
            if os.path.isfile(filename):
                dirname, filename = os.path.split(filename)
                trash, dirname = dirname.split(bids_directory + '\\')
            else:
                trash, dirname = filename.split(bids_directory+'\\')
            out_dir = [os.path.join(output_dir, dirname)]
            os.makedirs(out_dir[0], exist_ok=True)
            return out_dir

        if not self['tag']:
            idx = order['out']
        else:
            idx = order[self['tag']]
        if not self['directory']:
            if self['type'] == 'file':
                if not taille:
                    raise EOFError('No input list to create the output')
                else:
                    for sub in in_out:
                        output_files = []
                        for filename in in_out[sub][idx_in[0]]:
                            out_file = create_output_file(output_directory, filename, self['extension'], self.bids_directory)
                            output_files.append(out_file)
                        in_out[sub][idx] = output_files
            # elif self['type'] == 'sub':
            #     if not self['multiplesubject']:
            #         output_files = sub
        else:
            #A revoir avec subject_list
            if self['multiplesubject']:
                for sub in in_out:
                    in_out[sub][idx] = output_directory #[output_directory] * taille[sub]
            else:
                for sub in in_out:
                    output_files = []
                    for filename in in_out[sub][idx_in[0]]:
                        output_dir = create_output_sub_dir(output_directory, filename, self.bids_directory)
                        output_files.append(output_dir)
                    in_out[sub][idx] = output_files

    def command_arg(self, output_dir, soft_name, subject_list, input_type, input_file_list=None):
        def create_output_file(output_dir, filename, extension, soft_name, bids_directory):
            out_file = []
            soft_name = soft_name.lower()
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory + '\\')
            file_elt = filename.split('_')
            if isinstance(extension, list):
                for ext in extension:
                    file_elt[-1] = soft_name + '.' + ext
                    filename = '_'.join(file_elt)
                    output = os.path.join(output_dir, dirname, filename)
                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    out_file.append(output)
            else:
                file_elt[-1] = soft_name + '.' + extension
                filename = '_'.join(file_elt)
                output = os.path.join(output_dir, dirname, filename)
                os.makedirs(os.path.dirname(output), exist_ok=True)
                out_file.append(output)
            return out_file

        def create_output_folder(output_dir, bids_directory, input_name=None, subject_to_analyse=None):
            out_file = []
            if input_name:
                for filename in input_file_list:
                    path = os.path.dirname(filename)
                    trash, path = path.split(bids_directory)
                    output = output_dir + path
                    os.makedirs(output, exist_ok=True)
                    out_file.append(output)
            elif subject_to_analyse:
                for sub in subject_to_analyse['sub']:
                    output = os.path.join(output_dir, sub)
                    os.makedirs(output, exist_ok=True)
                    out_file.append(output)
            return out_file

        output_file_list = []
        out_to_return = Output()
        if not self['directory']:
            if self['type'] == 'file':
                if not input_file_list:
                    raise EOFError('No input list to create the output')
                for filename in input_file_list:
                    out_file = create_output_file(output_dir, filename, self['extension'], soft_name, self.bids_directory)
                    output_file_list.append(out_file)
            elif self['type'] == 'sub':
                #A revoir
                if not self.multiplesubject:
                    output_file_list = subject_list['sub']

        else:
            #A revoir avec subject_list
            if self.multiplesubject:
                output_file_list.append(output_dir)
            elif input_type == 'file':
                output_file_list = create_output_folder(output_dir, self.bids_directory, input_name=input_file_list)
            elif input_type == 'sub':
                output_file_list = create_output_folder(output_dir, self.bids_directory, subject_to_analyse=subject_list)

        out_to_return[self['tag']] = output_file_list
        out_to_return.multiplesubject = self.multiplesubject

        return out_to_return


class Arguments(Parameters):
    unit_value = ['default', 'unit']
    read_value = ['read', 'elementstoread', 'multipleselection']
    list_value = ['possible_value', 'multipleselection']
    file_value = ['fileLoc', 'extension']
    bool_value = ['default']
    bids_value = ['readbids', 'type']

    def copy_values(self, input_dict):
        keylist = list(input_dict.keys())
        if keylist != self.unit_value and keylist != self.read_value and keylist != self.list_value and keylist != self.file_value and keylist != self.bool_value and keylist != self.bids_value:
            raise EOFError(
                'The keys in Parameters of your JSON file are not conform.\n Please modify it according to the given template.\n')
        for key in input_dict:
            self[key] = input_dict[key]

    def create_parameter_to_inform(self, param_vars, key=None):
        param_vars[key] = {}
        keys = list(self.keys())
        readbids = None
        if keys == self.unit_value:
            param_vars[key]['attribut'] = 'StringVar'
            param_vars[key]['value'] = str(self['default']+self['unit'])
            param_vars[key]['unit'] = self['unit']
        elif keys == self.list_value:
            if self['multipleselection']:
                st_type = 'Variable'
            else:
                st_type = 'Listbox'
            param_vars[key]['attribut'] = st_type
            param_vars[key]['value'] = self['possible_value']
        elif keys == self.file_value: #A revoir
            param_vars[key]['attribut'] = 'File'
            param_vars[key]['value'] = [self['extension']]
        elif keys == self.bool_value:
            param_vars[key]['attribut'] = 'Bool'
            param_vars[key]['value'] = self['default']
        elif keys == self.bids_value:
            # param_vars[key]['attribut'] = 'Label'
            # param_vars[key]['value'] = self['type']
            readbids = self['type']
            del param_vars[key]
        elif keys == self.read_value:
            if self['multipleselection']:
                st_type = 'Variable'
            else:
                st_type = 'Listbox'
            param_vars[key]['attribut'] = st_type
            reading_type = self['read'].strip('*')
            param_vars[key]['value'] = {'file': reading_type, 'elements': self['elementstoread']}
        else:
            raise EOFError('The keys in Parameters of your JSON file are not conform.\n Please modify it according to the template given.\n')

        return readbids

    def update_values(self, input_dict):
        if not input_dict:
            pass
        elif isinstance(input_dict, list):
            self['value_selected'] = input_dict
        elif isinstance(input_dict, str):
            if input_dict:
                if 'unit' in self.keys():
                    unit = self['unit']
                    if input_dict == unit:
                        pass
                    elif unit and unit in input_dict:
                        self['value_selected'] = input_dict.split(unit)[0]
                    else:
                        self['value_selected'] = input_dict
                elif 'type' in self.keys():
                    unit = self['type']
                    if not input_dict == unit:
                        self['value_selected'] = input_dict
                else:
                    self['value_selected'] = input_dict
        elif isinstance(input_dict, bool):
            self['value_selected'] = input_dict


class SubjectToAnalyse(Parameters):
    #required_keys = 'sub'
    keylist = ['ses', 'task', 'acq', 'proc', 'run', 'modality']

    def __init__(self, sub_list, input_dict=None):
        if isinstance(sub_list, list):
            self['sub'] = sub_list
        else:
            self['sub'] = [sub_list]
        if input_dict:
            for key, val in input_dict.items():
                self[key] = {}
                for clef in val.keys():
                    if isinstance(val[clef], list):
                        self[key][clef] = val[clef]
                    else:
                        self[key][clef] = [val[clef]]
        else:
            for key in self.keylist:
                self[key] = []

    # def check_subjects_param(self):
    #     input_keys = [key for key in self.keys()if key != 'sub']
    #     flag_list = any(key == 'modality' for key in input_keys)
    #     for sub in self['sub']:
    #         self.curr_bids.is_subject_present(sub)
    #         if not flag_list:
    #             for elt in input_keys:
    #                 mod_type = input_keys[elt]['modality'][0]
    #                 if mod_type


    def copy_values(self, input_dict):
        for key in input_dict:
            if key not in self.keys():
                self[key] = []
            if isinstance(input_dict[key], str):
                self[key].append(input_dict[key])
            else:
                self[key].extend(input_dict[key])

    def write_file(self, output_directory):
        filename = os.path.join(output_directory, 'subjects_selected_file.json')
        with open(filename, 'w+') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)


def verify_subject_has_parameters(curr_bids, sub_id, input_vars, param=None):
    warn_txt = ''
    err_txt = ''
    sub2remove = []
    deriv_folder = None
    for key in input_vars:
        keylist = []
        if input_vars[key] is None:
            continue
        if 'modality' not in input_vars[key].keys() and param is None:
            warn_txt += 'No modality has been mentionned for the input {}. Bids pipeline will select the one by default.\n'.format(key)
            input_vars[key]['modality'] = bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names()
        elif 'modality' not in input_vars[key].keys() and param[key]:
            input_vars[key]['modality'] = param[key]['modality']
        if 'deriv-folder' in input_vars[key].keys():
            deriv_folder = input_vars[key]['deriv-folder']
            if deriv_folder == '':
                continue
        if any(elmt not in bids.ModalityType.get_list_subclasses_names() for elmt in input_vars[key]['modality']):
            mod = []
            for elmt in input_vars[key]['modality']:
                if elmt in bids.ModalityType.get_list_subclasses_names():
                    mod.append(elmt)
                else:
                    val = [elt for elt in bids.ModalityType.get_list_subclasses_names() if elmt in eval('bids.' + elt + '.allowed_modalities')]
                    if deriv_folder:
                        val = [va for va in val if va in bids.Process.get_list_subclasses_names()]
                    else:
                        val = [va for va in val if va not in bids.Process.get_list_subclasses_names()]
                    mod.extend(val)
            mod = list(set(mod))
        else:
            mod = input_vars[key]['modality']
        if len(mod) > 1:
            err_txt += 'There is too many modalities selected in the input {}\n.'.format(key)
            return warn_txt, err_txt
        keylist = [clef for clef in input_vars[key] if (clef != 'modality' and clef != 'deriv-folder')]
        for clef in keylist:
            for sid in sub_id:
                if deriv_folder:
                    curr_bids.is_pipeline_present(deriv_folder)
                    curr_bids.curr_pipeline['Pipeline'].is_subject_present(sid, True)
                    if curr_bids.curr_pipeline['Pipeline'].curr_subject['isPresent']:
                        if not mod[-1].endswith('Process'):
                            mod[-1] = mod[-1]+'Process'
                        elmt = [val[clef] for val in curr_bids.curr_pipeline['Pipeline'].curr_subject['SubjectProcess'][mod[-1]]]
                    else:
                        elmt=[]
                else:
                    curr_bids.is_subject_present(sid)
                    elmt = [val[clef] for val in curr_bids.curr_subject['Subject'][mod[-1]]]
                if not any(elt in elmt for elt in input_vars[key][clef]):
                    warn_txt += 'This subject {} doesn"t have the required parameters for the analysis.\n The {} is missing.\n'.format(sid, clef)
                    sub2remove.append(sid)
        if sub2remove:
            for sub in sub2remove:
                warn_txt += 'This subject {} will be removed from the subject selection.'.format(sub)
                sub_id.remove(sub)
        if not sub_id:
            err_txt += 'There is no more subject in the selection.\n Please modify your parameters'

    return warn_txt, err_txt


def main(argv):
    bidsdirectory = None
    analysisname = ''
    parameters = {}
    subjectlist = {}

    try:
        opts, args = getopt.getopt(argv, "hb:a:p:s:", ["bidsdirectory=", "analysisname=", "parameters=", "subjectlist="])
    except getopt.GetoptError:
        print('pipeline_class.py -b <bidsdirectory> -a <analysisname> -p <parameters> -s <subjectlist>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('pipeline_class.py -b <bidsdirectory> -a <analysisname> -p <parameters> -s <subjectlist>')
            sys.exit()
        elif opt in ('-b', '--bidsdirectory'):
            bidsdirectory = arg
        elif opt in ('-a', '--analysisname'):
            analysisname = arg
        elif opt in ('-p', '--parameters'):
            if os.path.exists(arg):
                parameters = arg
            else:
                parameters = eval(arg)
                if not isinstance(parameters, dict):
                    print('ERROR: Parameters should be a dictionnary or filename.\n')
                    sys.exit(-1)
        elif opt in ('-s', '--subjectlist'):
            subjectlist = eval(arg)
            if not isinstance(subjectlist, dict):
                print('ERROR: Subject should be a dictionnary with at least sub as key.\n')
                sys.exit(-1)

    if not bidsdirectory or not analysisname or not parameters or not subjectlist:
        print('ERROR: All arguments are required.\n')
        sys.exit(-1)

    return bidsdirectory, analysisname, parameters, subjectlist


if __name__ == '__main__':
    bidsdirectory, analysisname, parameters, subjectlist = main(sys.argv[1:])
    soft_analyse = PipelineSetting(bidsdirectory, analysisname)
    log_analyse = soft_analyse.set_everything_for_analysis(parameters, subjectlist)
    print(log_analyse)
