import ins_bids_class as bids
import json
import os
import datetime
import getpass
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
                self.read_directory()

    def read_directory(self, dev_dir):
        with os.scandir(dev_dir) as it:
            for entry in it:
                if entry.is_dir():
                    pip = bids.Pipeline()
                    pip.dirname = entry.path
                    self.parse_pipeline(pip.dirname, entry.name)
                    self.pipelines.append(pip)

    def is_empty(self):
        default = ['log', 'parsing']
        pip_list = [pip['name'] for pip in self.pipelines if pip['name'] not in default]
        if pip_list:
            is_empty = False
        else:
            is_empty = True
        return is_empty, pip_list

    def create_pipeline_directory(self, pip_name):
        def check_pipeline_variant(pip_list, pip_name):
            variant_list = []
            it_exist = False
            for pip in pip_list:
                if pip.startswith(pip_name):
                    variant = pip.split('-')
                    if len(variant) > 1:
                        variant_list.append(variant[1:])
                    it_exist=True
            return it_exist, variant_list

        is_empty, pip_list = self.is_empty()
        if not is_empty:
            it_exist, variant_list = check_pipeline_variant(pip_list, pip_name)
            if it_exist and not variant_list:
                directory_name = pip_name + '-v1'
            elif it_exist and variant_list:
                directory_name = pip_name + '-' + str(len(variant_list)+1)
            elif not it_exist:
                directory_name = pip_name
        else:
            directory_name = pip_name
        directory_path = os.path.join(self.path, directory_name)
        os.makedirs(directory_path, exist_ok=True)
        return directory_path, directory_name

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
                            subinfo[mod_dir + 'Process'][-1].get_sidecar_files()
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
                modality = 'anat'
            dirname.append(modality)
            directory = '/'.join(dirname)
            directory = os.path.join(directory_path, directory)
            os.makedirs(directory, exist_ok=True)
            return directory

        is_present, index_pip = self.pipeline_is_present(pip_name)
        if not is_present:
            pip = bids.Pipeline()
            pip['name'] = pip_name
            pip['DatasetDescJSON'] = bids.DatasetDescJSON()
            pip['DatasetDescJSON'].read_file(jsonfilename=os.path.join(directory_path, 'dataset_description.json'))
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



class DatasetDescPipeline(bids.DatasetDescJSON):
    keylist = ['Name', 'BIDSVersion', 'PipelineDescription', 'SourceDataset', 'Author', 'Date']
    filename = 'dataset_description.json'
    bids_version = '1.0.1'

    def __init__(self, param_vars, subject_list):
        super().__init__()
        self['PipelineDescription'] = {}
        for key in param_vars:
            if key=='Callname':
                self['PipelineDescription']['Name'] = param_vars[key]
            else:
                self['PipelineDescription'][key] = param_vars[key]
        self['SourceDataset'] = {key: subject_list[key] for key in subject_list}
        self['Author'] = getpass.getuser()
        self['Date'] = str(datetime.datetime.now())


class PipelineSetting(dict):
    #A changer pour que l'utilisateurs indique le dossier des softwares json
    keylist = ['Name', 'Path', 'Parameters']
    soft_path = r'D:\ProjectPython\SoftwarePipeline'
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
        if soft_path and os.path.exists(soft_path):
            self.soft_path = soft_path
        self.read_json_parameter_file(soft_name)
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
        #check the validity of the json ??

    def create_parameter_to_inform(self):
        param_vars = {}
        self['Parameters'].create_parameter_to_inform(param_vars)
        for key in param_vars:
            if isinstance(param_vars[key]['value'], bool):
                pass
            elif not param_vars[key]['value']:
                pass
            elif 'str_type' in param_vars[key]['value']:
                param = []
                mark_to_remove = ['?', '***', '*']
                subcl_list = param_vars[key]['value']['subcl_list']
                str_type = param_vars[key]['value']['str_type']
                if subcl_list:
                    for sub in self.curr_bids['Subject']:
                        for mod in sub:
                            if mod in bids.ModalityType.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
                                for elt in sub[mod]:
                                    for clef in elt.keys():
                                        if clef in subcl_list and elt[clef]:
                                            idx = elt[clef].header.index(str_type)
                                            for elt_val in elt[clef][1::]:
                                                if elt_val[idx] not in mark_to_remove:
                                                    param.append(elt_val[idx])
                else:
                    for subject in os.listdir(self.curr_bids.cwdir):
                        if subject.startswith('sub') and os.path.isdir(os.path.join(self.curr_bids.cwdir, subject)):
                            for session in os.listdir(os.path.join(self.curr_bids.cwdir, subject)):
                                if os.path.isdir(os.path.join(self.curr_bids.cwdir, subject, session)):
                                    for mod in os.listdir(os.path.join(self.curr_bids.cwdir, subject, session)):
                                        if os.path.isdir(os.path.join(self.curr_bids.cwdir, subject, session, mod)):
                                            with os.scandir(os.path.join(self.curr_bids.cwdir, subject, session, mod)) as it:
                                                for entry in it:
                                                    if entry.name.endswith(str_type):
                                                        f = open(entry.path, 'r')
                                                        f_cont = f.readlines()
                                                        for line in f_cont:
                                                            trial_type = line.split('\t')
                                                            param.append(trial_type[0])
                                                        f.close()
                                        elif os.path.isfile(os.path.join(self.curr_bids.cwdir, subject, session, mod)) and mod.endswith(str_type):
                                            f = open(os.path.join(self.curr_bids.cwdir, subject, session, mod), 'r')
                                            f_cont = f.readlines()
                                            for line in f_cont[1:]:
                                                trial_type = line.split('\t')
                                                param.append(trial_type[0])
                                            f.close()

                param = list(set(param))
                param.sort()
                param_vars[key]['value'] = param
        return param_vars

    def set_everything_for_analysis(self, param_vars, subject_list):
        #save the param_vars in json file for next analysis
        try:
            dev = DerivativesSetting(self.curr_bids['Derivatives'][0])
            output_directory, output_name = dev.create_pipeline_directory(self['Name'])
            dataset_desc = DatasetDescPipeline(param_vars, subject_list)
            dataset_desc['Name'] = self['Name']
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, 'dataset_description.json'))

            #update the parameters and get the subjects
            self['Parameters'].update_values(param_vars)
            subject_to_analyse = SubjectToAnalyse(subject_list)
            #write the analysis caracteristics

            #Get the value for the command_line
            cmd_arg, cmd_line, input_dict, output_dict = self.create_command_to_run_analysis(output_directory, subject_to_analyse)
        except (EOFError, TypeError, ValueError) as er:
            self.log_error += er
            self.write_error_system()
            return self.log_error

        if not input_dict:
            proc = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            #proc.wait()
            error_proc = proc.communicate()
            self.log_error += cmd_arg.verify_log_for_errors('', error_proc)
            self.write_json_associated(input_dict, output_directory, cmd_arg)
        elif isinstance(input_dict, InputArguments):
            input_list = list(input_dict.values())[0]
            output_list = list(output_dict.values())[0]
            nbr_run = len(input_list)
            idx = 0
            while idx < nbr_run:
                cmd = cmd_line.format(input_list[idx], output_list[idx])
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                proc.wait()
                error_proc = proc.communicate()
                self.log_error += cmd_arg.verify_log_for_errors(input_list[idx], error_proc)
                self.write_json_associated(input_list[idx], output_list[idx], cmd_arg)
                idx = idx + 1
        elif isinstance(input_dict, Input):
            pass
        else:
            self.log_error += str(datetime.datetime.now()) + ': ' + 'ERROR: The analysis {0} could not be run due to an issue with the inputs and the outputs. \n'.format(self['Name'])
            return self.log_error
        self.write_error_system(output_directory)
        dev.parse_pipeline(output_directory, output_name)
        self.curr_bids.save_as_json()

        return self.log_error

    def create_command_to_run_analysis(self, output_directory, subject_to_analyse):
        #Take the mode into account for now, only automatic
        interm = self['Parameters']['Intermediate']
        cmd_line_set = self['Parameters']['command_line_base']
        callname = self['Parameters']['Callname']
        mode = self['Parameters']['Mode']

        if interm:
            cmd_arg = eval(interm + '(bids_directory=self.cwdir, curr_path=self.curr_path, dev_path=output_directory, callname=callname)') #'(bids_directory="'+self.cwdir+'", curr_path="'+self.curr_path+'", dev_path="'+output_directory+'", callname="'+callname+'")')
        else:
            cmd_arg = Parameters(bids_directory=self.cwdir, curr_path=self.curr_path, dev_path=output_directory, callname=callname)

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
        try:
            input_dict = input_p.command_arg(subject_to_analyse, self.curr_bids)
            if isinstance(input_dict, InputArguments):
                input_list = list(input_dict.values())[0]
                in_type = input_p[-1]['type']
            elif isinstance(input_dict, Input):
                pass
            output_dict = output_p.command_arg(output_directory, self['Name'], subject_to_analyse, in_type, input_list) # output_dir, soft_name, subject_list, input_type, input_file_list=None
        except NameError:
            input_dict = None
            output_dict = None

        cmd_line = cmd_arg.command_line_base(cmd_line_set, mode, input_dict, output_dict)

        return cmd_arg, cmd_line, input_dict, output_dict

    def write_json_associated(self, input_file, output_file, analyse):
        def create_json(input_file, output_json, analyse):
            jsonf = bids.BidsJSON()
            jsonf['Description'] = 'Results of ' + self['Name'] + ' analysis.'
            jsonf['RawSources'] = input_file
            jsonf['Parameters'] = analyse
            jsonf['Author'] = getpass.getuser()
            jsonf['Date'] = str(datetime.datetime.now())
            jsonf.write_file(output_json)

        if isinstance(output_file, list):
            output_fin = output_file[0]
        else:
            output_fin = output_file

        if os.path.isfile(output_fin):
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

    def __init__(self, bids_directory=None, curr_path=None, dev_path=None, callname=None):
        if bids_directory:
            self._assign_bids_dir(bids_directory)
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
        for key, value in self.items():
            if key in Parameters.get_list_subclasses_names() + ParametersSide.get_list_subclasses_names():
                value.create_parameter_to_inform(param_vars, key=key)
            elif isinstance(value, Arguments):
                value.create_parameter_to_inform(param_vars, key=key)

    def update_values(self, input_dict):
        keylist = list(self.keys())
        for key in input_dict:
            if key in keylist:
                self[key].update_values(input_dict[key])
            else:
                new_key, *tag = key.split('_')
                if isinstance(tag, list):
                    tag = '_'.join(tag)
                self[new_key].update_values(input_dict[key], tag)

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
                                                  filetypes=[('exe files', '.exe')])
            if not name in filename:
                messagebox.showerror('PathError', 'The selected file is not the good one for this pipeline')
                select_pipeline_path(name)

            return filename

        name = type_of_software(self['Callname'], self['Intermediate'])
        if not name:
            return ''
        if curr_path:
            if not os.path.exists(curr_path):
                curr_path = select_pipeline_path(name)
            else:
                if not name in curr_path:
                    curr_path = select_pipeline_path(name)
        else:
            curr_path = select_pipeline_path(name)
        return curr_path

    def command_arg(self, key, cmd_dict, subject_list):
        if 'value_selected' in self.keys():
            if isinstance(self['value_selected'], list):
                cmd_dict[key] = ', '.join(self['value_selected'])
            else:
                cmd_dict[key] = self['value_selected']
        # elif 'default' in self.keys():
        #     if self['default']:
        #         cmd_dict[key] = self['default']
        elif 'readbids' in self.keys():
            if self['type'] in subject_list.keys():
                type_value = subject_list[self['type']]
            if type_value:
                cmd_dict[key] = type_value

    def command_line_base(self, cmd_line_set, mode, input_p, output_p):
        if not cmd_line_set:
            cmd_base = self.curr_path + ' ' + self.callname
        else:
            cmd_base = self.curr_path + cmd_line_set + ' '

        cmd_line = self.chaine_parameters(input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd

    def chaine_parameters(self, input_dict, output_dict):
        def determine_input_output_type(input_dict, cnt_tot):
            cmd_line = ''
            for key in input_dict:
                if not input_dict.multiplesubject:
                    cmd_line += key + ' {' + str(cnt_tot) + '} '
                    cnt_tot += 1
                else:
                    cmd_line += clef + ' ' + input_dict[clef] + ' '
            return cmd_line

        cmd_line =''
        cnt_tot = 0
        for clef in self:
            if clef == 'Input':
                if isinstance(input_dict, InputArguments):
                    cmd_line += determine_input_output_type(input_dict, cnt_tot)
                elif isinstance(input_dict, Input):
                    is_ready = input_dict.control_length_of_multiple_input()
                    if is_ready:
                        for elt in input_dict:
                            cmd_line += determine_input_output_type(elt, cnt_tot)
                        else:
                            raise TypeError('The two inputs don"t have the same number of entry')
            elif clef == 'Output': #A revoir , aussi l'écriture
                cmd_line += determine_input_output_type(output_dict, cnt_tot)
            elif isinstance(self[clef], bool):
                cmd_line += clef + ' '
            else:
                cmd_line += clef + ' ' + self[clef] + ' '
        return cmd_line

    def verify_log_for_errors(self, input, x):
        log_error = ''
        if isinstance(x, tuple):
            if not x[1]:
                log_error += str(datetime.datetime.now()) + ': ' + input + ': '+ x[0] + '\n'
            elif not x[0] and not x[1]:
                log_error += str(datetime.datetime.now()) + ': ' + input + ' has been analyzed with no error\n'
            else:
                log_error += str(datetime.datetime.now()) + ': ' + input + ': ' + x[1] + '\n'

        return log_error
        #Old version with x
        # if x == 0:
        #     self.log_error += str(datetime.datetime.now()) + ': ' + input + ' has been analyzed with no error\n'
        # elif x == -1:
        #     self.log_error += str(datetime.datetime.now()) + ': ' + input + ' has not been completed\n'

    #Fonction wrote by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names

    @classmethod
    def _assign_bids_dir(cls, bids_dir):
        cls.bids_directory = bids_dir
        PipelineSetting.cwdir = bids_dir


class AnyWave(Parameters):
    anywave_directory = None

    def command_line_base(self, cmd_line_set, mode, input_p, output_p):
        self['plugin'] = self.callname
        cmd_end = ''
        if not cmd_line_set:
            cmd_line_set = ' --run '
        cmd_base = self.curr_path + cmd_line_set + ' '

        cmd_line = self.chaine_parameters(input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd

    def chaine_parameters(self, input, output):
        jsonfilename = os.path.join(self.derivatives_directory, self['plugin'] + '_parameters' + '.json')

        for key, value in self.items():
            if ', ' in value:
                self[key] = value.split(', ')
            elif key in ['Input', 'Output']:
                pass
        del self['Input']
        del self['Output']
        with open(jsonfilename, 'w') as json_file:
            json.dump(self, json_file)
        cmd_line = ' "' + jsonfilename + '" '

        #Handle the input and output
        cnt_tot = 0
        if isinstance(input, InputArguments):
            for key in input:
                cmd_line += key + ' {' + str(cnt_tot) + '} '
                cnt_tot +=1
        elif isinstance(input, Input):
            is_ready = input.control_length_of_multiple_input()
            if is_ready:
                self['Input'] = []
                for elt in input:
                    for key in input:
                        cmd_line += key + ' {' + str(cnt_tot) + '} '
                    cnt_tot +=1
        for key in output:
            cmd_line += key + ' {' + str(cnt_tot) + '} '
            cnt_tot +=1

        return cmd_line

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

    def command_line_base(self, cmd_line_set, mode, input_p, output_p):
        cmd_end = ''
        os.system('docker pull ' + self.callname)
        if not cmd_line_set:
            cmd_line_set = 'docker run -ti --rm'
        #should change outputs in derivatives normally
        cmd_base = cmd_line_set + ' -v ' + self.bids_directory + ':/bids_dataset:ro -v ' + self.derivatives_directory + ':/outputs ' + self.callname + ' /bids_dataset /outputs '

        cmd_line = self.chaine_parameters(input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd

    def chaine_parameters(self, input_dict, output_dict):
        cmd_line =''
        cnt_tot = 0
        for clef in self:
            if clef == 'Input':
                if isinstance(input_dict, InputArguments):
                    for key in input_dict:
                        cmd_line += key + ' {' + str(cnt_tot) + '} '
                        cnt_tot += 1
                elif isinstance(input_dict, Input):
                    is_ready = input_dict.control_length_of_multiple_input()
                    if is_ready:
                        for elt in input_dict:
                            for key in input_dict:
                                cmd_line += key + ' {' + str(cnt_tot) + '} '
                            cnt_tot +=1
                        else:
                            raise TypeError('The two inputs don"t have the same number of entry')
            elif isinstance(self[clef], bool):
                cmd_line += clef + ' '
            elif isinstance(self[clef], list):
                if len(self[clef]) > 1:
                    value = ' '.join(self[clef])
                    cmd_line += clef + ' [' + value + '] '
                else:
                    value = self[clef][0]
                    cmd_line += clef + ' ' + value + ' '
            else:
                cmd_line += clef + ' ' + self[clef] + ' '
        return cmd_line


class Matlab(Parameters):

    def command_line_base(self, cmd_line_set, mode, input_p, output_p):
        cmd_end = ''
        if mode == 'automatic':
            if not cmd_line_set:
                cmd_line_set = "-nodisplay -nosplash -nodesktop -r \"cd('" + self.curr_path + "'); "
            cmd_end = '; exit'
        elif mode == 'manual':
            if not cmd_line_set:
                cmd_line_set = "-nosplash -nodesktop -r \"cd('" + self.curr_path + "'); "
        cmd_base = self.curr_path + cmd_line_set + self.callname + ' '

        cmd_line = self.chaine_parameters(input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd


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
        else:
            param_vars[key]['attribut'] = 'Label'
            param_vars[key]['value'] = self[-1]

    def update_values(self, input_dict):
        for elt in self:
            if not elt == input_dict:
                self.remove(elt)


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

    def update_values(self, input_dict, tag):
        for elt in self:
            if elt['tag'] == tag:
                elt.update_values(input_dict)

    def command_arg(self, subject_list, curr_bids):
        size = len(self)
        if size == 1:
            input_file = self[0].command_arg(subject_list, curr_bids)
            #input_file.copy_values(f_list, flag_process=True)
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


class InputArguments(Parameters):
    keylist = ['tag', 'multiplesubject', 'modality', 'type']
    multiplesubject = False

    def copy_values(self, input_dict, flag_process=False):
        keys = list(input_dict.keys())
        if not keys == self.keylist and not flag_process:
            raise KeyError('Your json is not conform')
        else:
            for key in input_dict:
                self[key] = input_dict[key]

    def create_parameter_to_inform(self, param_vars, key=None):
        if len(self['modality']) > 1:
            param_vars[key]['attribut'] = 'Listbox'
            param_vars[key]['value'] = self['modality']
        elif not self['modality']:
            param_vars[key]['attribut'] = None
            param_vars[key]['value'] = None
        else:
            param_vars[key]['value'] = self['modality'][-1]
            param_vars[key]['attribut'] = 'Label'
        if self['multiplesubject']:
            self.multiplesubject = True
        param_vars[key]['unit'] = self['type']

    def update_values(self, input_dict):
        self['value_selected'] = input_dict

    def command_arg(self, subject_list, curr_bids):
        f_list = []
        if 'value_selected' in self.keys():
            modality = self['value_selected']
        else:
            modality = self['modality']
        if not modality:
            pass
            #return 'ERROR: Don"t know on each modality we should process'
        else:
            subject_list['modality'] = modality

        if self['type'] == 'file':
            f_list = self.get_subject_files(modality, subject_list, curr_bids)
        elif self['type'] == 'sub':
            f_list = subject_list['sub']
        else:
            raise ValueError('The selected type is not conform')
        input_to_return = InputArguments()
        input_to_return[self['tag']] = f_list
        input_to_return.multiplesubject = self.multiplesubject

        return input_to_return #{self['tag']: f_list}

    def get_subject_files(self, modality, subject_list, curr_bids):
        input_files = []
        modality = modality.capitalize()
        #Old version
        for sub in curr_bids['Subject']:
            if sub['sub'] in subject_list['sub']:
                for mod in sub[modality]:
                    is_in = False
                    for key in mod:
                        if key in subject_list.keylist and subject_list[key]:
                            if mod[key] and mod[key] in subject_list[key]:
                                is_in = True
                            else:
                                is_in = False
                    if is_in:
                        input_files.append(os.path.join(curr_bids.cwdir, mod['fileLoc']))

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

    def create_parameter_to_inform(self, param_vars, key=None):
        if self['multiplesubject']:
            self.multiplesubject = True

    def update_values(self, input_dict):
        self['value_selected'] = input_dict

    def command_arg(self, output_dir, soft_name, subject_list, input_type, input_file_list=None):
        def create_output_file(output_dir, filename, extension, soft_name, bids_directory):
            out_file = []
            soft_name = soft_name.lower()
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory)
            file_elt = filename.split('_')
            for ext in extension:
                file_elt[-1] = soft_name + '.' + ext
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
    read_value = ['read', 'multipleselection']
    list_value = ['possible_value', 'multipleselection']
    file_value = ['fileLoc', 'extension'] #To modify
    bool_value = ['default']
    bids_value = ['readbids', 'type']

    def copy_values(self, input_dict):
        for key in input_dict:
            self[key] = input_dict[key]

    def create_parameter_to_inform(self, param_vars, key=None):
        param_vars[key] = {}
        keys = list(self.keys())
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
            param_vars[key]['value'] = ''
        elif keys == self.bool_value:
            param_vars[key]['attribut'] = 'Bool'
            param_vars[key]['value'] = self['default']
        elif keys == self.bids_value:
            param_vars[key]['attribut'] = 'Label'
            param_vars[key]['value'] = self['type']
        elif keys == self.read_value:
            if self['multipleselection']:
                st_type = 'Variable'
            else:
                st_type = 'Listbox'
            param_vars[key]['attribut'] = st_type
            reading_type = self['read'].strip('*')
            name, ext = os.path.splitext(reading_type)
            bids_cls_list = bids.BidsSidecar.get_list_subclasses_names()
            if 'DatasetDescPipeline' in bids_cls_list:
                bids_cls_list.remove('DatasetDescPipeline')
            subcl_list = []
            str_type = ''
            for cl in bids_cls_list:
                if eval('bids.' + cl + '.extension') == ext:
                    for subcl in eval('bids.' + cl + '.get_list_subclasses_names()'):
                        if eval('bids.' + subcl + '.modality_field') == name:
                            if name == 'events':
                                str_type = 'trial_type'
                            elif name == 'channels':
                                str_type = 'name'
                            else:
                                str_type = 'name'
                            subcl_list.append(subcl)

            if not str_type and not subcl_list:
                str_type = reading_type

            param_vars[key]['value'] = {'str_type': str_type, 'subcl_list': subcl_list}

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
    keylist = ['sub', 'ses', 'task', 'acq', 'run']

    def __init__(self, input_dict=None):
        for key in self.keylist:
            self[key] = []
        if input_dict:
            self.copy_values(input_dict)

    def copy_values(self, input_dict):
        for key in input_dict:
            self[key] = input_dict[key]
