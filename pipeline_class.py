import ins_bids_class as bids
import json
import os
import datetime
import getpass
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
                    pip.parse_bids()
                    self.pipelines.append(pip)

    def is_empty(self):
        default = ['log', 'parsing']
        pip_list = [pip['name'] for pip in self.pipelines if pip['name'] not in default]
        if pip_list:
            is_empty = True
        else:
            is_empty = False
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
        return directory_path


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
        self['Date'] = datetime.datetime.now()


class PipelineSetting(dict):
    #A changer pour que l'utilisateurs indique le dossier des softwares json
    keylist = ['Name', 'Path', 'Parameters']
    soft_path = r'D:\ProjectPython\SoftwarePipeline'
    log_error = ''
    curr_dev = None
    curr_bids = None
    curr_path = None

    def __init__(self, bids_dir, soft_name, soft_path=None):
        if isinstance(bids_dir, str):
            if os.path.exists(bids_dir):
                try:
                    self.curr_bids = bids.BidsDataset(bids_dir)
                except:
                    return 'ERROR: The bids data selected is not conform'
            else:
                return 'ERROR: The bids data selected doesn"t exist'
        elif isinstance(bids_dir, bids.BidsDataset):
            self.curr_bids = bids_dir
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
                    self[key] = Parameters()
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
            if 'str_type' in param_vars[key]['value']:
                param=[]
                mark_to_remove = ['?', '***', '*']
                subcl_list = param_vars[key]['value']['subcl_list']
                str_type = param_vars[key]['value']['str_type']
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

                param = list(set(param))
                param.sort()
                param_vars[key]['value'] = param
        return param_vars

    def set_everything_for_analysis(self, param_vars, subject_list):
        #save the param_vars in json file for next analysis
        dev = DerivativesSetting(self.curr_bids['Derivatives'][0])
        output_directory = dev.create_pipeline_directory(self['Name'])
        dataset_desc = DatasetDescPipeline(param_vars, subject_list)
        dataset_desc['Name'] = self['Name']

        #update the parameters
        self['Parameters'].update_values(param_vars)
        #write the analysis caracteristics

        #Get the value for the command_line
        cmd_base, cmd_args, input, output = self.create_command_to_run_analysis(output_directory)
        input_dict, size = input.command_arg(subject_list, self.curr_bids)
        if size < 2:
            output_dict = output.command_arg(output_directory, self['Name'], subject_list, list(input_dict[-1].values())[0])
            nbr_run = len(list(input_dict[-1].values())[0])
            if len(list(output_dict.values())[0]) == nbr_run:
                idx = 0
                cmd_line = ''
                while idx < nbr_run:
                    for key in input_dict[-1]:
                        cmd_line += key + ' ' + input_dict[-1][key][idx] + ' '
                    for clef in cmd_args:
                        cmd_line += clef + ' ' + cmd_args[clef] + ' '
                    for cles in output_dict:
                        if isinstance(output_dict[cles][idx], list):
                            value = ', '.join(output_dict[cles][idx])
                        else:
                            value = output_dict[cles][idx]
                        cmd_line += cles + ' ' + value + ' '
                    x = os.system(cmd_base + cmd_line)
                    #x = 0
                    if x == 0:
                        self.log_error += str(datetime.datetime.now()) + ': ' + input_dict[-1][key][idx] + ' has been analyzed with no error\n'
                    elif x == -1:
                        self.log_error += str(datetime.datetime.now()) + ': ' + input_dict[-1][key][idx] + ' has not been completed\n'
                    idx = idx +1
                    self.write_json_associated(input_dict[-1][key][idx], output_dict[cles][idx], cmd_args)
            else:
                return 'ERROR: Not the same number of input and output'
        else:
            #A finir pour si deux entrées
            pass
        self.write_error_system(output_directory)

    def create_command_to_run_analysis(self, output_directory):
        #Take the mode into account for now, only automatic
        interm = self['Parameters']['Intermediate']
        cmd_line_set = self['Parameters']['command_line_base']
        callname = self['Parameters']['Callname']
        mode = self['Parameters']['Mode']
        cmd_base = ''
        if interm:
            if interm == 'Docker':
                os.system('docker pull '+callname)
                if not cmd_line_set:
                    cmd_line_set = 'docker run -ti --rm'
                cmd_base = cmd_line_set + ' -v ' + self.curr_bids.cwdir + '/bids_dataset:ro -v ' + output_directory + ':/outputs ' + callname + ' '
            elif interm == 'AnyWave':
                if not cmd_line_set:
                    cmd_line_set = ' --run '
                cmd_base = self.curr_path + cmd_line_set + callname +' '
            elif interm == 'Matlab':
                if mode == 'automatic':
                    if not cmd_line_set:
                        cmd_line_set = "-nodisplay -nosplash -nodesktop -r \"cd('" + self.path + "'); "
                elif mode == 'manual':
                    if not cmd_line_set:
                        cmd_line_set = "-nosplash -nodesktop -r \"cd('" + self.path + "'); "
                cmd_base = self.curr_path + cmd_line_set + callname + ' '
        else:
            if not cmd_line_set:
                cmd_base = self.curr_path + ' '
            else:
                cmd_base = self.curr_path + cmd_line_set + ' '

        cmd_arg = {}
        for key in self['Parameters']:
            if isinstance(self['Parameters'][key], Arguments):
                self['Parameters'][key].command_arg(key, cmd_arg)
            elif key == 'Input':
                input = self['Parameters'][key]
            elif key == 'Output':
                output = self['Parameters'][key]
        return cmd_base, cmd_arg, input, output

    def write_json_associated(self, input_file, output_file, analyse):
        if isinstance(output_file, list):
            output_fin = output_file[0]
        else:
            output_fin = output_file
        jsonf = bids.BidsJSON()
        if os.path.isfile(output_fin):
            filename, ext = os.path.splitext(output_fin)
            output_json = output_fin.replace(ext, jsonf.extension)
            if os.path.exists(output_json):
                pass
            else:
                jsonf['Description'] = 'Results of ' + self['Name'] + ' analysis.'
                jsonf['RawSources'] = input_file
                jsonf['Parameters'] = analyse
                jsonf['Author'] = getpass.getuser()
                jsonf['Date'] = datetime.datetime.now()
                jsonf.write_file(output_json)
        elif os.path.isdir(output_fin):
            filename = os.path.basename(input_file)
            filename, ext = os.path.splitext(filename)
            potential_file = [entry for entry in os.listdir(output_fin) if entry.basename.startswith(filename)]
            is_json = False
            for it in potential_file:
                if it.endswith('jsonf.extension'):
                    is_json= True
            if not is_json:
                filename, ext = os.path.splitext(potential_file[-1])
                output_json = potential_file[-1].replace(ext, jsonf.extension)
                jsonf['Description'] = 'Results of ' + self['Name'] + ' analysis.'
                jsonf['RawSources'] = input_file
                jsonf['Parameters'] = analyse
                jsonf['Author'] = getpass.getuser()
                jsonf['Date'] = datetime.datetime.now()
                jsonf.write_file(output_json)

    def write_error_system(self, output_directory):
        log_file = os.path.join(output_directory, 'log_error_analyse.log')
        os.makedirs(log_file, exist_ok=True)
        with open(log_file, 'w') as f:
            f.write(self.log_error)

    def write_file(self, filename):
        with open(filename, 'w') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)


class Parameters(dict):
    keylist = ['command_line_base', 'Intermediate', 'Callname']
    analyse_type = []
    analyse_type = None

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
                new_key, tag = key.split('_')
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

    def command_arg(self, key, cmd_dict):
        if 'value_selected' in self.keys():
            if isinstance(self['value_selected'], list):
                cmd_dict[key] = ', '.join(self['value_selected'])
            else:
                cmd_dict[key] = self['value_selected']
        elif 'default' in self.keys():
            if self['default']:
                cmd_dict[key] = self['default']

    #Fonction wrote by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


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
        input_file = []
        size = len(self)
        for elt in self:
            f_list = elt.command_arg(subject_list, curr_bids)
            input_file.append(f_list)
        return input_file, size


class InputArguments(Parameters):
    keylist = ['tag', 'modality', 'type']

    def copy_values(self, input_dict):
        keys = list(input_dict.keys())
        if not keys == self.keylist:
            return 'ERROR: Your json is not conform'
        else:
            for key in input_dict:
                self[key] = input_dict[key]

    def create_parameter_to_inform(self, param_vars, key=None):
        if len(self['modality']) > 1:
            param_vars[key]['attribut'] = 'Listbox'
            param_vars[key]['value'] = self['modality']
        else:
            param_vars[key]['value'] = self['modality'][-1]
            param_vars[key]['attribut'] = 'Label'
        param_vars[key]['unit'] = self['type']

    def update_values(self, input_dict):
        self['value_selected'] = input_dict

    def command_arg(self, subject_list, curr_bids):
        f_list = []
        if 'value_selected' in self.keys():
            modality = self['value_selected']
        else:
            modality = self['modality']
        subject_list['modality'] = [modality]
        if self['type'] == 'file':
            f_list = self.get_subject_files(modality, subject_list, curr_bids)
        elif self['type'] == 'sub':
            f_list = subject_list['sub']
        else:
            return 'ERROR: The type is not correct'
        return {self['tag']: f_list}

    def get_subject_files(self, modality, subject_list, curr_bids):
        input_files =[]
        modality = modality.capitalize()
        for sub in curr_bids['Subject']:
            if sub['sub'] in subject_list['sub']:
                for mod in sub[modality]:
                    if mod['ses'] in subject_list['ses'] and mod['task'] in subject_list['task']:
                        input_files.append(mod['fileLoc'])

        return input_files


class Output(Parameters):
    keylist = ['tag', 'directory', 'type', 'extension']

    def copy_values(self, input_dict):
        keys = list(input_dict.keys())
        if not keys == self.keylist:
            return 'ERROR: Your json is not conform'
        else:
            for key in input_dict:
                self[key] = input_dict[key]

    def create_parameter_to_inform(self, param_vars, key=None):
        pass

    def update_values(self, input_dict):
        self['value_selected'] = input_dict

    def command_arg(self, output_dir, soft_name, subject_list, input_file_list):
        def create_output_file(output_dir, filename, extension, soft_name):
            out_file = []
            soft_name = soft_name.lower()
            dirname, filename = os.path.split(filename)
            file_elt = filename.split('_')
            for ext in extension:
                file_elt[-1] = soft_name + '.' + ext
                filename = '_'.join(file_elt)
                out_file.append(os.path.join(output_dir, dirname, filename))
            return out_file

        def create_output_folder(output_directory, output_dir, input_name):
            out_file = []
            path, filename = os.path.dirname(input_name)
            for elt in output_directory:
                if elt in path:
                    out_file.append(os.path.join(output_dir, elt))
            return out_file

        output_file_list = []
        output_directory = []
        for sub in subject_list['sub']:
            for ses in subject_list['ses']:
                for mod in subject_list['modality']:
                    folder = os.path.join('sub-'+sub, 'ses-'+ses, mod.lower())
                    output_directory.append(folder)
                    os.makedirs(os.path.join(output_dir, folder), exist_ok=True)
        if not self['directory']:
            if self['type'] == 'file':
                for input in input_file_list:
                    out_file = create_output_file(output_dir, input, self['extension'], soft_name)
                    output_file_list.append(out_file)
            elif self['type'] == 'sub':
                output_file_list = subject_list['sub']
            return {self['tag']: output_file_list}
        else:
            #to simplify the command line, duplicate the folders depending of the number of input
            for input in input_file_list:
                out_file = create_output_folder(output_directory, output_dir, input)
                output_file_list.append(out_file)
            return {self['tag']: output_directory}


class Arguments(Parameters):
    unit_value = ['default', 'unit']
    read_value = ['read', 'multipleselection']
    list_value = ['possible_value', 'multipleselection']
    file_value = ['fileLoc', 'extension'] #To modify
    bool_value = ['defaul']

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
        #A revoir
        elif keys == self.read_value:
            if self['multipleselection']:
                st_type = 'Variable'
            else:
                st_type = 'Listbox'
            param_vars[key]['attribut'] = st_type
            reading_type = self['read'].strip('*')
            name, ext = os.path.splitext(reading_type)
            bids_cls_list = bids.BidsSidecar.get_list_subclasses_names()
            subcl_list = []
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
            param_vars[key]['value'] = {'str_type': str_type, 'subcl_list': subcl_list}

    def update_values(self, input_dict):
        if isinstance(input_dict, list):
            self['value_selected'] = input_dict
        elif isinstance(input_dict, str):
            if 'unit' in self.keys():
                unit = self['unit']
                if unit in input_dict:
                    self['value_selected'] = input_dict.split(unit)[0]
                else:
                    self['value_selected'] = input_dict
            else:
                self['value_selected'] = input_dict
        elif isinstance(input_dict, bool):
            self['value_selected'] = input_dict

