import ins_bids_class as bids
import os
import json
import time
import shutil


class Analysis(dict):
    keylist = ['Name', 'Path', 'Mode', 'Intermediate', 'required_parameters', 'Parameters']
    required_keys = ['Name']
    path_defaults = r'D:\ProjectPython\SoftwarePipeline'
    anywave_path = r'C:\anywave_april\AnyWave.exe'
    #subject_file = r'D:\ProjectPython\SoftwarePipeline\SubjectToAnalyse.json'
    curr_bids = None
    curr_path = os.getcwd()
    error_str = ''

    def __init__(self, name=None, bids_dir=None, keylist=None, required_keys=None):
        if keylist:
            self.keylist = keylist
        else:
            self.keylist = self.__class__.keylist
        if required_keys:
            self.required_keys = required_keys
        if bids_dir and isinstance(bids_dir, bids.BidsDataset):
            self.curr_bids = bids_dir
        #self.keylist = self.keylist + self.required_keys
        for key in self.keylist:
            if key in Arguments.get_list_subclasses_names() + bids.Subject.get_list_subclasses_names():
                self[key] = []
            elif key in self.get_list_subclasses_names():
                self[key] = {}
            elif key == 'Name':
                self[key] = name
            else:
                self[key] = ''
        if name:
            self.read_parameter_file()
            self.analysis_dict = {key: value for key, value in self.items() if key in ['Mode', 'Parameters', 'Docker', 'Matlab', 'AnyWave', 'SubjectToAnalyse']}
            self.analysis_value = dict()
        # self.analysis_dict = {key: value for key, value in self['Parameters'].items() if not key == 'Callname'}
        # self['Parameters'].select_parameter_analysis(self.analysis_dict, self.param_vars, self.param_dict)

    def __setitem__(self, key, value):
        if key in self.keylist:
            # redefinir le setitem de parameters et subjecttoanalyse
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
                            filename = os.path.join(self.path_defaults, value)
                        if not os.path.exists(filename):
                            str_issue = 'file: ' + str(filename) + ' does not exist.'
                            raise FileNotFoundError(str_issue)
                    else:
                        value = self.path_defaults
                    dict.__setitem__(self, key, value)
            else:
                dict.__setitem__(self, key, value)

    def copy_values(self, input_dict):
        for key in input_dict:
            if key in bids.Subject.get_list_subclasses_names():
                for elmt in input_dict[key]:
                    mod_dict = eval(key + '()')
                    mod_dict.copy_values(elmt)
                    self[key].append(mod_dict)
            elif key in Analysis.get_list_subclasses_names():
                self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = input_dict[key]

    def read_parameter_file(self):
        jsonfile = os.path.join(self.path_defaults, self['Name'] + '.json')
        with open(jsonfile, 'r') as file:
            read_json = json.load(file)
            self.copy_values(read_json)
        if self['Path']:
            self.curr_path = self['Path']

    def select_parameter_analysis(self):

        def create_variable_type(key, param, param_vars):
            if isinstance(param, list) and param:
                param_vars['Variable_' + key] = param
                # multiple_selection_param['Variable_'+key] = is_multiple
            elif isinstance(param, str) and param:
                param_vars['StringVar_' + key] = param
            elif isinstance(param, dict) and param:
                param_vars['askopenfile_' + key] = param
            elif isinstance(param, bool):
                param_vars['Bool_' + key] = param

        def parse_parameters_file(analysis_dict, param_vars, param_dict, curr_bids):
            for key in analysis_dict.keys():
                param = None
                if key == 'Mode':
                    param = analysis_dict[key]
                    create_variable_type(key, param, param_vars)
                elif key in Arguments.get_list_subclasses_names():
                    if isinstance(analysis_dict[key], list):
                        for arg in analysis_dict[key]:
                            param, is_multiple = arg.get_arguments_value(curr_bids)
                            create_variable_type(key, param, param_vars)
                elif isinstance(analysis_dict[key], Arguments):
                    param, is_multiple = analysis_dict[key].get_arguments_value(curr_bids)
                    create_variable_type(key, param, param_vars)
                elif isinstance(analysis_dict[key], Parameters):
                    parse_parameters_file(analysis_dict[key], param_vars, param_dict, curr_bids)
                elif isinstance(analysis_dict[key], bool):
                    param_dict[key] = ''
                    param_vars['Bool_' + key] = ''
                if param is not None:
                    param_dict[key] = ''

        param_dict = {}
        param_vars = {}
        parse_parameters_file(self.analysis_dict, param_vars, param_dict, self.curr_bids)

        return param_dict, param_vars

    def get_analysis_value(self, param_vars, sujet_dict):

        def get_subjects_to_analyse(value_dict, sujet_dict):
            for id in sujet_dict['sub']:
                for se in sujet_dict['ses']:
                    for ta in sujet_dict['task']:
                        sujet = SubjectToAnalyse()
                        sujet['sub'] = id
                        sujet['ses'] = se
                        sujet['task'] = ta
                        value_dict.append(sujet)

        if self['Intermediate'] in Parameters.get_list_subclasses_names():
            clef = self['Intermediate']
        else:
            clef = 'Parameters'
        #Ajout d'un required_paramters
        req_list=[]
        if self['required_parameters']:
            req_list = self['Parameters']['required_parameters']
        self.analysis_value[clef] = eval(clef+'([' + ', '.join(req_list) + '])')
        self.analysis_value['SubjectToAnalyse'] = []
        self.analysis_value[clef].path = self.curr_path
        temp_value = {}

        #Get the value gave by the user
        for var in param_vars:
            isntype = var.split('_')
            clef_size = len(isntype[0]) + 1
            key = var[clef_size::]
            if isntype[0] == 'Variable':
                id_var = param_vars[var].current()
                if key in Analysis.keylist:
                    value = self.analysis_dict[key][id_var]
                elif key in Arguments.get_list_subclasses_names():
                    for elt in self.analysis_dict['Parameters'][key]:
                        value = elt.get_selected_value()
                temp_value[key] = value
            elif isntype[0] == 'StringVar' or isntype[0] == 'Bool':
                if param_vars[var].get():
                    temp_value[key] = param_vars[var].get()

        #initiate the value for the command
        #key_list = self.analysis_value[clef].required_keys
        key_list = self['Parameter'].keys()
        for key in key_list:
            if key in self.analysis_value[clef].keys():
                del self.analysis_value[clef][key]
            if key == 'Callname':
                self.analysis_value[clef][key] = self.analysis_dict['Parameters'][key]
            elif key not in Arguments.get_list_subclasses_names():
                if key not in temp_value.keys():
                    self.analysis_value[clef][key] = self.analysis_dict['Parameters'][key]['default']
                else:
                    self.analysis_value[clef][key] = temp_value[key]
            else:
                value = self.analysis_dict['Parameters'][key]
                if isinstance(value, list):
                    if len(value)==1:
                        get_subjects_to_analyse(self.analysis_value['SubjectToAnalyse'], sujet_dict)
                        temp_dict = eval(key + '()')
                        temp_dict.copy_values(value[0])
                        new_key, new_value = temp_dict.get_value(self.curr_bids.dirname, self.analysis_value['SubjectToAnalyse'])
                else:
                    temp_dict = eval(key+'()')
                    temp_dict.copy_values(value)
                    new_key, new_value = temp_dict.get_value(self.curr_bids.dirname, sub_list=self.analysis_value['SubjectToAnalyse'])

                self.analysis_value[clef][new_key] = new_value
                #del self.analysis_value[clef][key]

        for key, value in temp_value.items():
            if key not in self.analysis_value[clef].keys():
                self.analysis_value[clef][key] = value

    def run_analysis(self):
        for key in self.analysis_value.keys():
            if isinstance(self.analysis_value[key], Parameters):
                cmd_line = self.analysis_value[key].create_command_line()
                if isinstance(cmd_line, list):
                    for cmd in cmd_line:
                        os.system(cmd)
                        time.sleep(15)
                else:
                    os.system(cmd_line)
        # for sub in self['SubjectToAnalyse']:
        #     input_list, output_list = sub.create_input_output_list(self['Name'], self['Parameters'], self.curr_bids)
        #     if not len(input_list) == len(output_list):
        #         print('The number of input file is different to the number of output files')
        #         break
        #     idx_out = 0
        #     for elt in input_list:
        #         cmd_line = self['Parameters'].create_command_line(elt, output_list[idx_out], self)
        #         os.system(cmd_line)
        #         time.sleep(10)
        #         idx_out += 1

    # function write by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class SubjectToAnalyse(bids.Subject):
    keylist = ['sub', 'ses', 'task', 'modality', 'fileLoc']

    def __init__(self, mod=None):
        super().__init__()
        if mod:
            self['modality'] = mod

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    #A finir
    def subject_entry(self, entry_type, entry_list):
        if isinstance(entry_type, Input):
            input_type = entry_type['type']
            if input_type in self.keylist:
                entry_list.append(self[input_type])
            else:
                pass
        elif isinstance(entry_type, Output):
            pass
        elif isinstance(entry_type, list):
            for elt in entry_type:
                self.subject_entry(elt, entry_list)

    def input_files(self, bids_dest, val_list):
        dirname = ''
        filename = ''
        ext = ''
        piece_dirname = []
        for key in self.keylist:
            if self[key] and not key == 'modality':
                if isinstance(self[key], str):
                    str2add = self[key]
                else:
                    str2add = str(self[key]).zfill(2)
                filename += key + '-' + str2add + '_'
        piece_dirname += [shrt_name for _, shrt_name in enumerate(filename.split('_')) if
                          shrt_name.startswith('sub-') or shrt_name.startswith('ses-')]
        mod_type = self['modality']
        if mod_type in bids.Electrophy.get_list_subclasses_names():
            ext = '.vhdr'
        elif mod_type in bids.Imagery.get_list_subclasses_names():
            ext = '.nii'
        piece_dirname += [mod_type.lower()]
        dirname = os.path.join(bids_dest, *piece_dirname)
        with os.scandir(dirname) as it:
            for entry in it:
                name, ext_entry = os.path.splitext(entry.name)
                if name.startswith(filename) and ext_entry == ext:
                    val_list.append("'" + entry.path + "'")

    #A refaire avec les nouvelles clefs
    def output_files(self, bids_dest, val_list, out_type=None):
        input_list = []
        self.input_files(bids_dest, input_list)
        # modality_type = []
        # if not isinstance(param_type, Parameters):
        #     raise TypeError('Second arguments should be Parameters type')
        # # if isinstance(param_type['Input'], list):
        # #     for elt in param_type['Input']:
        # #         modality_type.append(elt['modality'])
        # # else:
        # #     self['modality'] = param_type['Input']['modality']
        # if not self['fileLoc']:
        #     for key in self.keylist:
        #         if self[key] and not key == 'modality':
        #             if isinstance(self[key], str):
        #                 str2add = self[key]
        #             else:
        #                 str2add = str(self[key]).zfill(2)
        #             filename += key + '-' + str2add + '_'
        #     piece_dirname += [shrt_name for _, shrt_name in enumerate(filename.split('_')) if
        #                       shrt_name.startswith('sub-') or shrt_name.startswith('ses-')]
        #     mod_type = self['modality']
        #     if mod_type in bids.Electrophy.get_list_subclasses_names():
        #         ext = '.vhdr'
        #     elif mod_type in bids.Imagery.get_list_subclasses_names():
        #         ext = '.nii'
        #     piece_dirname += [mod_type.lower()]
        #     dirname = os.path.join(bids_dest, *piece_dirname)
        #     dirname_derivatives = os.path.join(bids_dest, 'derivatives', name, *piece_dirname)
        #     os.makedirs(dirname_derivatives, exist_ok=True)
        #     with os.scandir(dirname) as it:
        #         for entry in it:
        #             name, ext_entry = os.path.splitext(entry.name)
        #             if name.startswith(filename) and ext_entry == ext:
        #                 input_list.append("'" + entry.path + "'")
        # else:
        #     input_list.append(self['fileLoc'])
        dirname_derivatives = os.path.join(bids_dest, 'derivatives')
        for input in input_list:
            in_name, in_ext = os.path.splitext(input)
            outputpath = in_name.replace(bids_dest, dirname_derivatives)
            # outputpath = outputpath.replace('_' + mod_type.lower(), '_EPA')
            if isinstance(out_type, list):
                for out in out_type:
                    val_list.append(outputpath + '.' + out + "'")
            else:
                val_list.append(outputpath + '.' + out_type + "'")

        return val_list


class Parameters(Analysis):
    keylist = []
    required_keys = ['Callname', 'Input', 'Output']
    path = None

    def __init__(self, keylist=None, required_keys=None):
        if required_keys:
            self.required_keys = required_keys
        if keylist:
            self.keylist = keylist
        #self.path = Parameters.path
        super().__init__(keylist=self.keylist, required_keys=self.required_keys)
        # for key in self.keylist:
        #     if key in Arguments.get_list_subclasses_names():
        #         self[key] = []
        #     else:
        #         self[key] = ''

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def create_command_line(self, Input, Output, analysis_pipeline):
        name_cmd = []
        if not Input or not Output:
            raise TypeError('Subject to analyse is missing')
        elif not isinstance(analysis_pipeline, Analysis):
            raise TypeError('The fourth arguments should be pipeline analysis')
        for key in self:
            if isinstance(self[key], Arguments):
                if not key in Arguments.get_list_subclasses_names():
                    arg_value, argpresent = self[key].get_final_value()
                    if argpresent:
                        name_cmd.append(key + ' ' + arg_value)
                else:
                    pass
            #A modifier
            elif key in Arguments.get_list_subclasses_names():
                name_cmd.append(eval(key))
        if self['Intermediate']:
            if self['Intermediate'] == 'Matlab':
                cmd_line_base = "matlab -nodisplay -nosplash -nodesktop -r \"cd('" + analysis_pipeline.curr_path + "'); " + \
                                self['Callname']
                param_line = '(' + ','.join(name_cmd) + ')' + '; exit"'
            elif self['Intermediate'] == 'Python':
                cmd_line_base = 'python ' + analysis_pipeline.curr_path + self['Callname'] + '.py '
                param_line = ' '.join(name_cmd)
            elif self['Intermediate'] == 'AnyWave':
                cmd_line_base = analysis_pipeline.anywave_path + ' ' + self['Callname']
                param_line = ' -'.join(name_cmd)
        else:
            cmd_line_base = os.path.join(analysis_pipeline.curr_path, self['Callname'] + '.exe')
            param_line = ' -'.join(name_cmd)
        cmd_line = cmd_line_base + param_line
        return cmd_line

    def copy_values(self, input_dict):
        for key in input_dict:
            if key in Arguments.get_list_subclasses_names() and isinstance(input_dict[key], list):
                self[key] = []
                for elt in input_dict[key]:
                    self[key].append(eval(key + '()'))
                    self[key][-1].copy_values(elt)
            elif key in Arguments.get_list_subclasses_names():
                self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            elif key not in self.required_keys:
                self[key] = Arguments(list(input_dict[key].keys()))
                self[key].copy_values(input_dict[key])
            else:
                self[key] = input_dict[key]

    def update(self, input_dict):
        if isinstance(input_dict, dict):
            for key in input_dict:
                if key not in self.keys():
                    del (input_dict[key])
                else:
                    self.__setitem__(key, input_dict[key])


class Docker(Parameters):
    required_keys = ['BidsDirectory', 'Output', 'Callname', 'Input'] # 'participant', 'group',

    def __init__(self, required_keys=None):
        if required_keys:
            self.required_keys = self.required_keys + required_keys
        super().__init__(required_keys=self.required_keys)

    def create_command_line(self):
        name_cmd = []
        cmd_line_base = 'docker run -it --rm '
        dir = []
        for key, value in self.items():
            if key.startswith('/'):
                if len(name_cmd) < 1:
                    name_cmd.append('-v ' + value + ':' + key + ':ro')
                else:
                    name_cmd.append('-v ' + value + ':' + key)
                dir.append(key)
            elif key == 'Callname':
                name_cmd.append(value)
                name_cmd.append(' '.join(dir))
            elif key == 'Mode':
                pass
            else:
                if isinstance(value, list):
                    name_cmd.append(key + ' ' + '['+', '.join(value)+']')
                elif isinstance(value, bool) and value:
                    name_cmd.append(key)
                elif value:
                    name_cmd.append(key + ' ' + value)

        param_line = ' '.join(name_cmd)
        cmd_line = cmd_line_base + param_line
        return cmd_line


class Matlab(Parameters):
    required_keys = ['Callname', 'Input', 'Output']

    def __init__(self, required_keys=None):
        if required_keys:
            self.required_keys = self.required_keys + required_keys
        super().__init__(required_keys=self.required_keys)

    def create_command_line(self):
        cmd_line = []
        cmd_line_base = "matlab -nodisplay -nosplash -nodesktop -r \"cd('" + self.path + "'); "

        i=0
        if 'Input' in self.keys():
            if isinstance(self['Input'], list):
                input_size = len(self['Input'])
        else:
            input_size=1
        while i < input_size:
            name_cmd = []
            for key, value in self.items():
                if key in Arguments.get_list_subclasses_names() and isinstance(value, list):
                    name_cmd.append(value[i])
                else:
                    name_cmd.append(value)
            cmd_line.append(cmd_line_base + ' '.join(name_cmd) + '; exit')
            i=i+1
        return cmd_line


class AnyWave(Parameters):
    pass


class Arguments(Analysis):
    keylist = ['tag', 'modality', 'path', 'type', 'default', 'unit', 'read', 'multipleselection', 'final', 'selected']

    def __init__(self, keylist=None):
        if keylist:
            self.keylist = keylist
        super().__init__(keylist=self.keylist)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def copy_values(self, input_dict):
        for key in input_dict:
            self[key] = input_dict[key]

    def get_arguments_value(self, bids_dataset):
        param = None
        is_multipleselection =False
        if 'default' in self.keylist:
            if isinstance(self['default'], str):
                param = str(id(self)) + '_' + self['default']
            elif isinstance(self['default'], bool):
                param = self['default']
        elif 'read' in self.keylist:
            is_multipleselection = self['multipleselection']
            reading_type = self['read'].strip('*')
            name, ext = os.path.splitext(reading_type)
            bids_cls_list = bids.BidsSidecar.get_list_subclasses_names()
            subcl_list = []
            for cl in bids_cls_list:
                if eval('bids.' + cl +'.extension') == ext:
                    for subcl in eval('bids.' + cl + '.get_list_subclasses_names()'):
                        if eval('bids.' + subcl + '.modality_field') == name:
                            if name == 'events':
                                str_type = 'trial_type'
                            elif name == 'channels':
                                str_type = 'name'
                            subcl_list.append(subcl)
            param = []
            for sub in bids_dataset['Subject']:
                for mod in sub:
                    if mod in bids.ModalityType.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
                        for elt in sub[mod]:
                            for key in elt.keys():
                                if key in subcl_list and elt[key]:
                                    idx = elt[key].header.index(str_type)
                                    for elt_val in elt[key][1::]:
                                        if len(elt_val[idx]) < 22:
                                            param.append(elt_val[idx])
            param = list(set(param))

        return param, is_multipleselection


class Input(Arguments):
    keylist = ['tag', 'modality', 'type']

    def __init__(self, keylist=None):
        if keylist:
            self.keylist = keylist
        super().__init__(keylist)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def get_arguments_value(self, bids_dataset):
        param = None
        is_multipleselection = False
        if self['modality']:
            if isinstance(self['modality'], list):
                param = self['modality']
                is_multipleselection = True
            elif isinstance(self['modality'], str):
                if 'path' in self.keys():
                    param = {self['modality']: 'input_path_'+ self['tag']}
                    is_multipleselection = True

        return param, is_multipleselection

    def get_value(self, bids_dirname, sub_list=None):
        value = []
        if not self['tag']:
            key = 'Input'
        else:
            key = self['tag']
        if self['type']=='file':
            if self['modality']:
                for elt in sub_list:
                    elt['modality'] = self['modality']
                    elt.input_files(bids_dirname, val_list=value)
        elif self['type']=='sub':
            for elt in sub_list:
                value.append(elt['sub'])
        return key, value


class Output(Arguments):
    keylist = ['tag', 'directory', 'type', 'extension']

    def __init__(self, keylist=None):
        if keylist:
            self.keylist = keylist
        super().__init__(keylist)

    def get_arguments_value(self, bids_dataset):
        is_multipleselection = False
        param = self['type']
        return param, is_multipleselection

    def get_value(self, bids_dirname, sub_list=None):
        value = ''
        if not self['tag']:
            key = 'Output'
        else:
            key = self['tag']
        if self['directory']:
            value = os.path.join(bids_dirname, 'derivatives')
        elif self['type'] == 'file':
            value=[]
            for elt in sub_list:
                elt.output_files(bids_dirname, value, out_type=self['extension'])
        return key, value


class BidsDirectory(Arguments):
    keylist = ['tag', 'directory']

    def get_value(self, bids_dirname, sub_list=None):
        value = ''
        key = self['tag']
        if self['directory']:
            value = bids_dirname

        return key, value


class VerifDerivatives(bids.Pipeline):
    dirname = None
    analysis = None

    def __init__(self, bids_dir, analysis_name):
        self.dirname = os.path.join(bids_dir, 'derivatives')
        self.analysis = analysis_name
        self.check_output_results()

    def check_output_results(self):
        def create_directory_from_filename(filename):
            filename, ext = os.path.splitext(filename)
            modality = [mod.allowed_modalities for mod in bids.ModalityType.get_list_subclasses_names()]
            dirname = []
            attributes = filename.split('_')
            for att in attributes:
                if att.startswith('sub') or att.stratswith('ses'):
                    dirname.append(att)
                elif att in modality:
                    dirname.append(att)
            return '/'.join(dirname)

        with os.scandir(self.dirname) as it:
            for entry in it:
                if entry.is_file():
                    if entry.name.startswith('sub'):
                        dirname = create_directory_from_filename(entry.name)
                        new_dirname = os.path.join(self.dirname, self.analysis, dirname)
                        os.makedirs(new_dirname, exist_ok=True)
                        shutil.move(entry, new_dirname)



if __name__ == '__main__':
    bids_dir = r'D:\Data\Test_Ftract_Import\Bids_import_all'
    bids_dataset = bids.BidsDataset(bids_dir)
    Analyse = Analysis('delphos', bids_dataset)
    Analyse.select_parameter_analysis()
    Analyse.run_analysis()