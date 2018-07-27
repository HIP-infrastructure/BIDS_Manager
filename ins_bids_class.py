#!/usr/bin/python3

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import open
from builtins import int
from builtins import range
from builtins import str
from future import standard_library
import os
import json
from datetime import datetime
import pprint
import gzip
import shutil
import random as rnd
import getpass
standard_library.install_aliases()

''' Three main bricks: BidsBrick: to handles the modality and high level directories, BidsJSON: to handles the JSON 
sidecars, BidsTSV: to handle the tsv sidecars. '''


class BidsBrick(dict):

    keylist = ['sub']
    required_keys = ['sub']
    access_time = datetime.now()
    cwdir = os.getcwd()
    allowed_modalities = []
    state_list = ['valid', 'invalid', 'forced']
    curr_state = None
    curr_user = getpass.getuser()

    def __init__(self, keylist=None, required_keys=None):
        """initiate a  dict var for modality info"""
        if keylist:
            self.keylist = keylist
        else:
            self.keylist = self.__class__.keylist
        if required_keys:
            self.required_keys = required_keys
        else:
            self.required_keys = self.__class__.required_keys
        self.curr_state = BidsBrick.curr_state

        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsJSON.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

    def __setitem__(self, key, value):

        if key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names():
                # if value and eval('type(value) == ' + key):
                if value and isinstance(value, eval(key)):
                    # check whether the value is from the correct class when not empty
                    self[key].append(value)
                else:
                    dict.__setitem__(self, key, [])
            elif key in BidsJSON.get_list_subclasses_names():
                if value and isinstance(value, eval(key)):
                    # check whether the value is from the correct class when not empty
                    super().__setitem__(key, value)
                else:
                    dict.__setitem__(self, key, {})
            elif key in BidsTSV.get_list_subclasses_names():
                # if value and eval('type(value) == ' + key):
                if value and isinstance(value, eval(key)):
                    # check whether the value is from the correct class when not empty
                    super().__setitem__(key, value)
                else:
                    dict.__setitem__(self, key, [])
            elif key == 'fileLoc':
                if value.__class__.__name__ in ['str', 'unicode']:  # makes it python 2 and python 3 compatible
                    if value:
                        filename = value
                        if os.path.isabs(value) and BidsBrick.cwdir in value:
                            value = os.path.relpath(value, BidsBrick.cwdir)
                            filename = os.path.join(BidsBrick.cwdir, value)
                        if not os.path.exists(filename):
                            str_issue = 'file: ' + str(filename) + ' does not exist.'
                            self.write_log(str_issue)
                            raise TypeError(str_issue)
                    elif not value == '':
                        str_issue = 'fileLoc value ' + str(value) + ' should be a path.'
                        self.write_log(str_issue)
                        raise TypeError(str_issue)
                    dict.__setitem__(self, key, value)
                else:
                    str_issue = 'fileLoc value ' + str(value) + ' should be a string.'
                    self.write_log(str_issue)
                    raise TypeError(str_issue)
            elif key == 'modality':
                if value:
                    if not self.allowed_modalities or value in self.allowed_modalities:
                        dict.__setitem__(self, key, value)
                    else:
                        str_issue = 'modality value ' + str(value) + ' is not allowed. Check ' + \
                                    self.get_modality_type() + '.allowed_modalities().'
                        self.write_log(str_issue)
                        raise TypeError(str_issue)
                else:
                    dict.__setitem__(self, key, value)

            elif value.__class__.__name__ in ['str', 'unicode', 'int'] or \
                    key in BidsFreeFile.get_list_subclasses_names():
                dict.__setitem__(self, key, value)
            else:
                str_issue = '/!\ key: ' + str(key) + ' should either be a string or an integer /!\ '
                self.write_log(str_issue)
                raise TypeError(str_issue)
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.get_modality_type() +\
                        ' class keyList /!\ '
            self.write_log(str_issue)
            raise TypeError(str_issue)

    def __delitem__(self, key):
        if key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.__class__.__name__ + \
                        ' class keyList /!\ '
            print(str_issue)

    def update(self, input_dict, f=None):
        if isinstance(input_dict, dict):
            for key in input_dict:
                if key not in self.keylist:
                    del (input_dict[key])
                else:
                    self.__setitem__(key, input_dict[key])
            # super().update(input_dict)

    def pop(self, key, val=None):
        if key in self.keylist:
            value = self[key]
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
            return value
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.__class__.__name__ + \
                        ' class keyList /!\ '
            print(str_issue)

    def popitem(self):
        value = []
        for key in self.keylist:
            value.append(self[key])
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        return value

    def clear(self):
        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        if isinstance(self, BidsDataset):
            BidsDataset.curr_log = ''

    def has_all_req_attributes(self, missing_elements=None):  # check if the required attributes are not empty to create
        # the filename (/!\ Json or coordsystem checked elsewhere)
        if not missing_elements:
            missing_elements = ''

        for key in self.keylist:
            if key in BidsDataset.keylist[1:] and key in BidsBrick.get_list_subclasses_names():
                ''' source data, derivatives, code do not have requirements yet'''
                continue
            if self.required_keys:
                if key in self.required_keys and not self[key]:
                    missing_elements += 'In ' + type(self).__name__ + ', key ' + str(key) + ' is missing.\n'
            if self[key] and isinstance(self[key], list):  # check if self has modality brick, if not empty than
                # recursively check whether it has also all req attributes
                for item in self[key]:
                    if issubclass(type(item), BidsBrick):
                        missing_elements = item.has_all_req_attributes(missing_elements)[1]
        return [not bool(missing_elements), missing_elements]

    def get_attributes_from_filename(self, fname=None):
        # get the attribute from the filename, used when parsing pre-existing
        #  bids dataset

        def parse_filename(mod_dict, file):
            fname_pieces = file.split('_')
            for word in fname_pieces:
                w = word.split('-')
                if len(w) == 2 and w[0] in mod_dict.keys():
                    mod_dict[w[0]] = w[1]
            if 'modality' in mod_dict and not mod_dict['modality']:
                mod_dict['modality'] = fname_pieces[-1]

        if isinstance(self, ModalityType) or isinstance(self, GlobalSidecars):
            if 'fileLoc' in self.keys() and self['fileLoc']:
                filename = self['fileLoc']
            else:
                return
            filename, ext = os.path.splitext(os.path.basename(filename))
            if ext.lower() == '.gz':
                filename, ext = os.path.splitext(filename)
            if ext.lower() in self.allowed_file_formats:
                parse_filename(self, filename)

    def create_filename_from_attributes(self):
        filename = ''
        dirname = ''
        if isinstance(self, ModalityType) or isinstance(self, GlobalSidecars):
            for key in self.get_attributes(['fileLoc', 'modality']):
                if self[key]:
                    filename += key + '-' + self[key] + '_'
            filename += self['modality']
            piece_dirname = []
            piece_dirname += [shrt_name for _, shrt_name in enumerate(filename.split('_')) if
                              shrt_name.startswith('sub-') or shrt_name.startswith('ses-')]
            mod_type = self.get_modality_type()
            if isinstance(self, GlobalSidecars):
                mod_type = mod_type.lower().replace(GlobalSidecars.__name__.lower(), '')
            else:
                mod_type = mod_type.lower()
            piece_dirname += [mod_type]
            dirname = '/'.join(piece_dirname)
        return filename, dirname

    def get_sidecar_files(self, in_bids_dir=True, input_dirname=None, input_filename=None):
        # find corresponding JSON file and read its attributes and save fileloc
        def find_sidecar_file(sidecar_dict, fname, drname, direct_search):
            piece_fname = fname.split('_')
            if sidecar_dict.inheritance and not direct_search:
                while os.path.dirname(drname) != BidsDataset.bids_dir:
                    drname = os.path.dirname(drname)
                    has_broken = False
                    with os.scandir(drname) as it:
                        for entry in it:
                            entry_fname, entry_ext = os.path.splitext(entry.name)
                            if entry_ext.lower() == '.gz':
                                entry_fname, entry_ext = os.path.splitext(entry.name)
                            if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                    sidecar_dict.modality_field:
                                for idx in range(1, len(piece_fname)):
                                    # a bit greedy because some case are not possible but should work
                                    j_name = '_'.join(piece_fname[0:-idx] + [sidecar_dict.modality_field]) + \
                                             sidecar_dict.extension
                                    if entry.name == j_name:
                                        # jsondict['fileLoc'] = entry.path
                                        sidecar_dict.read_file(entry.path)
                                        has_broken = True
                                        break
                            if has_broken:
                                break
                if os.path.dirname(drname) == BidsDataset.bids_dir:
                    drname = os.path.dirname(drname)
                    piece_fname = [value for _, value in enumerate(piece_fname) if not (value.startswith('sub-') or
                                                                                        value.startswith('ses-'))]
                    has_broken = False
                    with os.scandir(drname) as it:
                        for entry in it:
                            entry_fname, entry_ext = os.path.splitext(entry.name)
                            if entry_ext.lower() == '.gz':
                                entry_fname, entry_ext = os.path.splitext(entry.name)
                            if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                    sidecar_dict.modality_field:
                                for idx in range(1, len(piece_fname)):
                                    j_name = '_'.join(piece_fname[0:-idx] + [sidecar_dict.modality_field]) + \
                                             sidecar_dict.extension
                                    if entry.name == j_name:
                                        sidecar_dict.read_file(entry.path)
                                        has_broken = True
                                        break
                            if has_broken:
                                break
            else:
                drname = os.path.dirname(drname)
                has_broken = False
                with os.scandir(drname) as it:
                    for entry in it:
                        entry_fname, entry_ext = os.path.splitext(entry.name)
                        if entry_ext.lower() == '.gz':
                            entry_fname, entry_ext = os.path.splitext(entry.name)
                        if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                sidecar_dict.modality_field:
                            for idx in range(1, len(piece_fname)):
                                # a bit greedy because some case are not possible but should work
                                j_name = '_'.join(piece_fname[0:-idx] + [sidecar_dict.modality_field]) + \
                                         sidecar_dict.extension
                                if entry.name == j_name:
                                    # jsondict['fileLoc'] = entry.path
                                    sidecar_dict.read_file(entry.path)
                                    has_broken = True
                                    break
                        if has_broken:
                            break
            sidecar_dict.has_all_req_attributes()

        #  firstly, check whether the subclass needs a JSON or a TSV files
        sidecar_flag = [value for _, value in enumerate(self.keylist) if value in
                        BidsSidecar.get_list_subclasses_names()]

        if isinstance(self, BidsBrick) and sidecar_flag:
            if in_bids_dir:
                if 'fileLoc' in self.keys() and self['fileLoc']:
                    rootdir, filename = os.path.split(self['fileLoc'])
                    if 'sourcedata' in rootdir:
                        # only look for sidecar if in raw folder
                        return
                    main_dirname = BidsDataset.bids_dir
                else:
                    self.write_log('Need file location first to find sidecars ( file attribute: ' +
                                   str(self.get_attributes()) + ')')
            else:
                filename = input_filename
                rootdir = ''
                main_dirname = input_dirname

            filename, ext = os.path.splitext(filename)
            if ext.lower() == '.gz':
                filename, ext = os.path.splitext(filename)
            for sidecar_tag in sidecar_flag:
                if 'modality' in self and not eval(sidecar_tag + '.modality_field'):
                    self[sidecar_tag] = eval(sidecar_tag + '(modality_field=self["modality"])')
                else:
                    self[sidecar_tag] = eval(sidecar_tag + '()')
                find_sidecar_file(self[sidecar_tag], filename, os.path.join(main_dirname, rootdir, filename),
                                  direct_search=not in_bids_dir)
                self[sidecar_tag].simplify_sidecar(required_only=False)

    def save_as_json(self, savedir, file_start=None, write_date=True, compress=True):
        if os.path.isdir(savedir):
            if not file_start:
                file_start = ''
            else:
                if file_start.__class__.__name__ in ['str', 'unicode']:  # makes it pyton2 and python3 compatible
                    if not file_start.endswith('_'):
                        file_start += '_'
                else:
                    str_issue = 'Input file beginning is not a string; json saved with default name.'
                    self.write_log(str_issue)
            if write_date:
                date_string = '_' + BidsBrick.access_time.strftime("%Y-%m-%dT%H-%M-%S")
            else:
                date_string = ''

            json_filename = file_start + type(self).__name__.lower() + date_string + '.json'

            output_fname = os.path.join(savedir, json_filename)
            with open(output_fname, 'w') as f:
                # json.dump(self, f, indent=1, separators=(',', ': '), ensure_ascii=False)
                json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
                f.write(json_str)

            if compress:
                with open(output_fname, 'rb') as f_in, \
                        gzip.open(output_fname + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(output_fname)
        else:
            raise TypeError('savedir should be a directory.')

    def __str__(self):
        return pprint.pformat(self)

    def get_modality_type(self):
        return self.__class__.__name__

    def get_attributes(self, keys2remove=None):
        attr_dict = {key: self[key] for _, key in enumerate(self.keys()) if key not in
                     BidsBrick.get_list_subclasses_names() and key not in BidsSidecar.get_list_subclasses_names()}
        if keys2remove:
            if not isinstance(keys2remove, list):
                keys2remove = [keys2remove]
            for key in keys2remove:
                if key in attr_dict.keys():
                    del(attr_dict[key])
        return attr_dict

    def copy_values(self, input_dict):
        # attr_dict = {key: self[key] for _, key in enumerate(self.keys()) if key not in
        #              BidsBrick.get_list_subclasses_names() and key not in BidsSidecar.get_list_subclasses_names()}
        # self.update(attr_dict)
        for key in input_dict:
            if key in BidsBrick.get_list_subclasses_names():
                if key in GlobalSidecars.get_list_subclasses_names():
                    flag_globalsidecar = True
                else:
                    flag_globalsidecar = False
                for elmt in input_dict[key]:
                    if flag_globalsidecar:
                        self[key] = eval(key + '(elmt["fileLoc"])')
                    else:
                        self[key] = eval(key + '()')
                    self[key][-1].copy_values(elmt)
            elif key in BidsSidecar.get_list_subclasses_names():
                if 'modality' in self and not eval(key + '.modality_field'):
                    self[key] = eval(key + '(modality_field=self["modality"])')
                else:
                    self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = input_dict[key]

    def get_modality_sidecars(self):
        sidecar_dict = {key: self[key] for _, key in enumerate(self.keys()) if key in
                        BidsSidecar.get_list_subclasses_names()}
        return sidecar_dict

    def extract_sidecares_from_sourcedata(self):
        filename, dirname = self.create_filename_from_attributes()

        if not Data2Import.data2import_dir or not Data2Import.data2import_dir:
            str_issue = 'Need import and bids directory to be set.'
            self.write_log(str_issue)
            raise NotADirectoryError(str_issue)
        if isinstance(self, Imagery):
            converter_path = 'D:/roehri/python/PycharmProjects/readFromUploader/dcm2niix.exe'
            conv_ext = ['.nii']
            cmd_line_base = converter_path + " -b y -ba y -m y -z n -f "
            cmd_line = cmd_line_base + filename + ' -o ' + Data2Import.data2import_dir + ' ' + \
                       os.path.join(Data2Import.data2import_dir, self['fileLoc'])
        elif isinstance(self, Electrophy):
            converter_path = 'D:/roehri/AnyWave/AnyWave.exe'
            attr_dict = self.get_attributes(['fileLoc', 'modality'])
            name_cmd = ' '.join(['--bids_' + key + ' ' + attr_dict[key] for key in attr_dict if attr_dict[key]])

            cmd_line = converter_path + ' --seegBIDS "' + os.path.join(Data2Import.data2import_dir, self['fileLoc']) + \
                       '" ' + name_cmd + ' --bids_dir "' + Data2Import.data2import_dir + '" --bids_output sidecars'
            conv_ext = ['.vhdr', '.vmrk', '.dat']
        else:
            str_issue = 'Sidecars from ' + os.path.basename(self['fileLoc']) + ' cannot be extracted!!'
            self.write_log(str_issue)
            return

        os.system(cmd_line)
        # list_filename = [filename + ext for ext in conv_ext]
        dict_copy = eval(self.get_modality_type() + '()')
        set_cwd = BidsBrick.cwdir
        if not BidsBrick.cwdir == Data2Import.data2import_dir:
            BidsBrick.cwdir = Data2Import.data2import_dir

        dict_copy.copy_values(self)
        dict_copy.get_sidecar_files(in_bids_dir=False, input_dirname=Data2Import.data2import_dir,
                                    input_filename=filename)
        BidsBrick.cwdir = set_cwd

        return dict_copy.get_modality_sidecars()

    def get_requirements(self, reqfiloc=None):

        if isinstance(self, BidsDataset) and BidsDataset.bids_dir and \
                os.path.exists(os.path.join(BidsDataset.bids_dir, 'code', 'requirements.json')):
            full_filename = os.path.join(BidsDataset.bids_dir, 'code', 'requirements.json')
        elif os.path.exists(reqfiloc):
            full_filename = reqfiloc
        else:
            full_filename = None

        if isinstance(self, BidsDataset):
            self.requirements = Requirements(full_filename)

            if 'Requirements' not in self.requirements.keys() or not self.requirements['Requirements']:
                self.write_log('/!\\ WARNING /!\\ No requirements set! Default requirements from BIDS 1.0.1 applied')

            if self.requirements['Requirements'] and 'Subject' in self.requirements['Requirements'].keys():

                for key in self.requirements['Requirements']['Subject']:

                    if key == 'keys':
                        ParticipantsTSV.header += [elmt for elmt in self.requirements['Requirements']['Subject']['keys']
                                                   if elmt not in ParticipantsTSV.header]
                        ParticipantsTSV.required_fields += [elmt for elmt in
                                                            self.requirements['Requirements']['Subject']['keys'] if
                                                            elmt not in ParticipantsTSV.required_fields]
                        Subject.keylist += [elmt for elmt in self.requirements['Requirements']['Subject']['keys']
                                            if elmt not in Subject.keylist]
                    elif key in BidsBrick.get_list_subclasses_names() and key + self.requirements.keywords[0] \
                            not in ParticipantsTSV.header:
                        ParticipantsTSV.header.append(key + self.requirements.keywords[0])
                        ParticipantsTSV.required_fields.append(key + self.requirements.keywords[0])

                        if key in Electrophy.get_list_subclasses_names() and key + self.requirements.keywords[1] \
                                not in ParticipantsTSV.header:
                            ParticipantsTSV.header.append(key + self.requirements.keywords[1])
                            ParticipantsTSV.required_fields.append(key + self.requirements.keywords[1])

                if 'Subject' + self.requirements.keywords[0] not in ParticipantsTSV.header:
                    ParticipantsTSV.header.append('Subject' + self.requirements.keywords[0])
                    ParticipantsTSV.required_fields.append('Subject' + self.requirements.keywords[0])
        else:
            requirements = Requirements(full_filename)
            for key in requirements['Requirements']['Subject']:
                if key == 'keys':
                    Subject.keylist += [elmt for elmt in requirements['Requirements']['Subject']['keys']
                                        if elmt not in Subject.keylist]

    def check_requirements(self):

        def check_dict_from_req(sub_mod_list, mod_req, modality, sub_name):

            type_dict = mod_req['type']
            if isinstance(type_dict, dict):
                type_dict = [type_dict]

            amount = 0
            if sub_mod_list:
                for type_req in type_dict:
                    non_specif_keys = [key for key in type_req if type_req[key] == '_']
                    empty_keys = [key for key in eval(modality + '.keylist') if key not in type_req]
                    reduced_dict = {key: type_req[key] for key in type_req if not type_req[key] == '_'}
                    for sub_mod in sub_mod_list:
                        attr_dict = sub_mod.get_attributes(empty_keys)
                        if attr_dict == reduced_dict and not non_specif_keys or \
                                [key for key in non_specif_keys if key in eval(modality + '.keylist') and attr_dict[key]]:
                            amount += 1

            if amount == 0:
                str_issue = 'Subject ' + sub_name + ' does not have files of type: ' + str(type_dict) + '.'
            elif amount < mod_req['amount']:
                str_issue = 'Subject ' + sub_name + ' misses ' + str(mod_req['amount']-amount) \
                            + 'files of type: ' + str(type_dict) + '.'
            else:
                return True

            self.write_log(str_issue)
            return False

        if isinstance(self, BidsDataset) and self.requirements['Requirements']:
            key_words = self.requirements.keywords
            participant_idx = self['ParticipantsTSV'].header.index('participant_id')
            sub_list = [line[participant_idx] for line in self['ParticipantsTSV'][1:]]
            check_list = [[word.replace(key_words[0], ''), idx]
                          for idx, word in enumerate(self['ParticipantsTSV'].header) if word.endswith(key_words[0]) and
                          not word == 'Subject' + key_words[0]]
            subject_ready_idx = self['ParticipantsTSV'].header.index('Subject_ready')
            integrity_list = [[word.replace(key_words[1], ''), idx]
                              for idx, word in enumerate(self['ParticipantsTSV'].header) if word.endswith(key_words[1])]

            if sub_list and check_list:
                for bidsbrick_key in check_list:
                    if bidsbrick_key[0] in ModalityType.get_list_subclasses_names() + \
                            GlobalSidecars.get_list_subclasses_names():
                        for sub in sub_list:
                            self.is_subject_present(sub)
                            sub_index = self.curr_subject['index']
                            curr_sub_mod = self['Subject'][sub_index][bidsbrick_key[0]]
                            for mod_requirement in self.requirements['Requirements']['Subject'][bidsbrick_key[0]]:
                                flag_req = check_dict_from_req(curr_sub_mod, mod_requirement, bidsbrick_key[0], sub)
                                parttsv_idx = sub_list.index(sub)
                                self['ParticipantsTSV'][1+parttsv_idx][bidsbrick_key[1]] = str(flag_req)

            if sub_list and integrity_list:
                idx_elec_name = IeegElecTSV.header.index('group')
                idx_chan_name = IeegChannelsTSV.header.index('group')

                for bidsintegrity_key in integrity_list:
                    for sub in sub_list:
                        self.is_subject_present(sub)
                        sub_index = self.curr_subject['index']
                        curr_sub_mod = self['Subject'][sub_index][bidsintegrity_key[0]]
                        ref_elec = []
                        sdcr_list = self['Subject'][sub_index][bidsintegrity_key[0] + 'GlobalSidecars']

                        if not sdcr_list or not [brick['IeegElecTSV'] for brick in sdcr_list if
                                                 brick['modality'] == 'electrodes']:
                            str_issue = 'Subject ' + sub + ' does not have electrodes.tsv file for ' +\
                                        bidsintegrity_key[0] + '.'
                            self.write_log(str_issue)
                            self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]] = \
                                str(False)
                            continue

                        elect_tsv = [brick['IeegElecTSV'] for brick in sdcr_list if brick['modality'] == 'electrodes']
                        # several electrodes.tsv can be found (e.g. for several space)
                        for tsv in elect_tsv:
                            if not ref_elec:
                                elecname = [line[idx_elec_name] for line in tsv[1:]]
                                [ref_elec.append(name) for name in elecname if name not in ref_elec]
                            else:
                                curr_elec = []
                                [curr_elec.append(line[idx_elec_name]) for line in tsv[1:]
                                 if line[idx_elec_name] not in curr_elec]
                                if not curr_elec.sort() == ref_elec.sort():
                                    ref_elec = []

                        if not ref_elec:
                            str_issue = 'Subject ' + sub + ' has inconsistent electrodes.tsv files ' +\
                                        bidsintegrity_key[0] + '.'
                            self.write_log(str_issue)
                            self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]] = \
                                str(False)
                            continue

                        for mod in curr_sub_mod:
                            curr_elec = []
                            [curr_elec.append(line[idx_chan_name]) for line in mod['IeegChannelsTSV'][1:]
                             if line[idx_chan_name] not in curr_elec and
                             not line[idx_chan_name] == BidsSidecar.bids_default_unknown]
                            miss_matching_elec = [name for name in curr_elec if name not in ref_elec]
                            if miss_matching_elec:
                                channel_issues = ChannelIssue()
                                str_issue = 'File ' + mod.create_filename_from_attributes()[0] + \
                                            ' has inconsistent electrode name(s) ' + str(miss_matching_elec) + '.'
                                self.write_log(str_issue)
                                filepath = mod.create_filename_from_attributes()

                                channel_issues.update({'sub': sub,
                                                       'filepath': os.path.join(filepath[1], filepath[0]),
                                                       'RefElectrodes': ref_elec,
                                                       'MismatchedElectrodes': miss_matching_elec,
                                                       'mod': bidsintegrity_key[0]})
                                self.issues['ChannelIssue'] = channel_issues
                                self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]] = \
                                    str(False)

                        if self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]]\
                                == BidsSidecar.bids_default_unknown:
                            self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]] = \
                                str(True)

                if self.issues:
                    self.issues.save_as_json()

            for sub in sub_list:
                idx = [elmt for elmt in integrity_list + check_list
                       if self['ParticipantsTSV'][1 + sub_list.index(sub)][elmt[1]] == 'False']
                if not idx:
                    self.write_log('!!!!!!!!!!! Subject ' + sub + ' is ready !!!!!!!!!!!')
                    self['ParticipantsTSV'][1 + sub_list.index(sub)][subject_ready_idx] = str(True)
                else:
                    self['ParticipantsTSV'][1 + sub_list.index(sub)][subject_ready_idx] = str(False)

    def convert(self):
        filename, dirname = self.create_filename_from_attributes()

        if not Data2Import.data2import_dir or not Data2Import.data2import_dir:
            str_issue = 'Need import and bids directory to be set.'
            self.write_log(str_issue)
            raise NotADirectoryError(str_issue)
        if isinstance(self, Imagery):
            converter_path = 'D:/roehri/python/PycharmProjects/readFromUploader/dcm2niix.exe'
            conv_ext = ['.nii']
            # by default dcm2niix not do overwrite file with same names but adds a letter to it (inputnamea, inputnameb)
            # therefore one should firstly test whether a file with the same input name already exist and remove it to
            # avoid risking to import this one rather than the one which was converted and added a suffix
            for ext in conv_ext:
                if os.path.exists(os.path.join(Data2Import.data2import_dir, filename+ext)):
                    os.remove(os.path.join(Data2Import.data2import_dir, filename+ext))
            cmd_line_base = converter_path + " -b y -ba y -m y -z n -f "
            cmd_line = cmd_line_base + filename + ' -o "' + Data2Import.data2import_dir + '" "' + os.path.join(
                Data2Import.data2import_dir, self['fileLoc']) + '"'
        elif isinstance(self, Electrophy):
            converter_path = 'D:/roehri/AnyWave/AnyWave.exe'
            attr_dict = self.get_attributes(['fileLoc', 'modality'])
            name_cmd = ' '.join(['--bids_' + key + ' ' + attr_dict[key] for key in attr_dict if attr_dict[key]])

            cmd_line = converter_path + ' --seegBIDS "' + os.path.join(Data2Import.data2import_dir, self['fileLoc']) + \
                       '" ' + name_cmd + ' --bids_dir "' + Data2Import.data2import_dir + '" --bids_format vhdr'
            conv_ext = ['.vhdr', '.vmrk', '.dat']
        elif isinstance(self, GlobalSidecars):
            if self['modality'] == 'photo':
                shutil.copy2(os.path.join(Data2Import.data2import_dir, self['fileLoc']), os.path.join(
                    BidsDataset.bids_dir, dirname, filename + os.path.splitext(self['fileLoc'])[1]))
            return [filename + os.path.splitext(self['fileLoc'])[1]]
        else:
            str_issue = os.path.basename(self['fileLoc']) + ' cannot be converted!'
            self.write_log(str_issue)
            raise TypeError(str_issue)

        os.system(cmd_line)
        list_filename = [filename + ext for ext in conv_ext]
        self.get_sidecar_files(in_bids_dir=False, input_dirname=Data2Import.data2import_dir,
                               input_filename=filename)
        os.makedirs(os.path.join(BidsDataset.bids_dir, dirname), exist_ok=True)
        for fname in list_filename:
            if os.path.exists(os.path.join(Data2Import.data2import_dir, fname)):
                shutil.move(os.path.join(Data2Import.data2import_dir, fname),
                            os.path.join(BidsDataset.bids_dir, dirname, fname))
        return list_filename

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names

    @staticmethod
    def write_log(str2write):

        if BidsDataset.bids_dir:
            main_dir = BidsDataset.bids_dir
        elif Data2Import.data2import_dir:
            main_dir = Data2Import.data2import_dir
        else:
            main_dir = BidsBrick.cwdir

        log_path = os.path.join(main_dir, 'derivatives', 'log')
        log_filename = 'bids_' + BidsBrick.access_time.strftime("%Y-%m-%dT%H-%M") + '.log'
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        if not os.path.isfile(os.path.join(log_path, log_filename)):
            cmd = 'w'
        else:
            cmd = 'a'
        with open(os.path.join(log_path, log_filename), cmd) as file:
            file.write(str2write + '\n')
            BidsDataset.curr_log += str2write + '\n'
        print(str2write)


class BidsSidecar(object):
    bids_default_unknown = 'n/a'
    inheritance = True
    modality_field = []
    allowed_modalities = []

    def __init__(self, modality_field=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        self.is_complete = False
        if not modality_field:
            self.modality_field = self.__class__.modality_field
        else:
            self.modality_field = modality_field

    def read_file(self, filename):
        if os.path.isfile(filename):
            if isinstance(self, BidsJSON):
                if os.path.splitext(filename)[1] == '.json':
                    with open(filename, 'r') as file:
                        read_json = json.load(file)
                        for key in read_json:
                            if (key in self.keylist and self[key] == BidsSidecar.bids_default_unknown) or \
                                    key not in self.keylist:
                                self[key] = read_json[key]
                else:
                    raise TypeError('File is not ".json".')
            elif isinstance(self, BidsTSV):
                if os.path.splitext(filename)[1] == '.tsv':
                    with open(os.path.join(filename), 'r') as file:
                        tsv_header_line = file.readline()
                        tsv_header = tsv_header_line.strip().split("\t")
                        if len([word for word in tsv_header if word in self.required_fields]) < \
                                len(self.required_fields):
                            issue_str = 'Header of ' + os.path.basename(filename) +\
                                        ' does not contain the required fields.'
                            print(issue_str)
                        # self.header = tsv_header
                        self[:] = []  # not sure if useful
                        for line in file:
                            self.append({tsv_header[cnt]: val for cnt, val in enumerate(line.strip().split("\t"))})
                else:
                    raise TypeError('File is not ".tsv".')
            elif isinstance(self, BidsFreeFile):
                self.clear()
                with open(os.path.join(filename), 'r') as file:
                    for line in file:
                        self.append(line.replace('\n', ''))
            else:
                raise TypeError('Not readable class input ' + self.__class__.__name__ + '.')

    def simplify_sidecar(self, required_only=True):
        if isinstance(self, BidsJSON):
            list_key2del = []
            for key in self:
                if (self[key] == BidsJSON.bids_default_unknown and key not in self.required_keys) or \
                        (required_only and key not in self.required_keys):
                    list_key2del.append(key)
            for key in list_key2del:
                del(self[key])

    def copy_values(self, sidecar_elmt):
        if isinstance(self, BidsJSON):
            attr_dict = {key: sidecar_elmt[key] for _, key in enumerate(sidecar_elmt.keys()) if (key in self.keylist
                         and self[key] == BidsSidecar.bids_default_unknown) or key not in self.keylist}
            self.update(attr_dict)
        elif isinstance(self, BidsTSV) and isinstance(sidecar_elmt, list):
            if sidecar_elmt and len([word for word in sidecar_elmt[0] if word in self.required_fields]) >= \
                    len(self.required_fields):
                self.header = sidecar_elmt[0]
                for line in sidecar_elmt[1:]:
                    self.append({sidecar_elmt[0][cnt]: val for cnt, val in enumerate(line)})
        elif isinstance(self, BidsFreeFile) and isinstance(sidecar_elmt, list):
            for line in sidecar_elmt:
                self.append(line)
        self.simplify_sidecar(required_only=False)

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        if 'required_keys' in dir(self) and self.required_keys:
            for key in self.required_keys:
                if key not in self or self[key] == BidsSidecar.bids_default_unknown:
                    self.is_complete = False
        self.is_complete = True

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class BidsFreeFile(BidsSidecar, list):

    def write_file(self, freefilename):
        with open(os.path.join(freefilename), 'w') as file:
            for _, line in enumerate(self):
                file.write(line + '\n')


class BidsJSON(BidsSidecar, dict):

    extension = '.json'
    modality_field = ''
    keylist = []
    required_keys = []

    def __init__(self, keylist=None, required_keys=None, modality_field=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        # if not modality_field:
        #     self.modality_field = self.__class__.modality_field
        # else:
        #     self.modality_field = modality_field
        super().__init__(modality_field=modality_field)
        self.is_complete = False
        if not keylist:
            self.keylist = self.__class__.keylist
        else:
            self.keylist = keylist
        if not required_keys:
            self.required_keys = self.__class__.required_keys
        else:
            self.required_keys = required_keys
        for item in self.keylist:
            self[item] = BidsJSON.bids_default_unknown

    # def has_all_req_attributes(self):  # check if the required attributes are not empty
    #     if self.required_keys:
    #         for key in self.required_keys:
    #             if key not in self or self[key] == BidsJSON.bids_default_unknown:
    #                 self.is_complete = False
    #     self.is_complete = True

    # def simplify_sidecar(self, required_only=True):
    #     list_key2del = []
    #     for key in self:
    #         if (self[key] == BidsJSON.bids_default_unknown and key not in self.required_keys) or \
    #                 (required_only and key not in self.required_keys):
    #             list_key2del.append(key)
    #     for key in list_key2del:
    #         del(self[key])
        # for k in list_key_del:
        #     del()

    # def read_file(self, filename):
    #     if os.path.isfile(filename):
    #         if os.path.splitext(filename)[1] == '.json':
    #             read_json = json.load(open(filename))
    #             for key in read_json:
    #                 if (key in self.keylist and self[key] == BidsJSON.bids_default_unknown) or \
    #                         key not in self.keylist:
    #                     self[key] = read_json[key]

    def write_file(self, jsonfilename):
        if os.path.splitext(jsonfilename)[1] == '.json':
            with open(jsonfilename, 'w') as f:
                # json.dump(self, f, indent=2, separators=(',', ': '), ensure_ascii=False)
                json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
                f.write(json_str)
        else:
            raise TypeError('File ' + jsonfilename + ' is not ".json".')


class ModalityType(BidsBrick):
    pass


class Imagery(ModalityType):
    pass


class Electrophy(ModalityType):
    pass


class ImageryJSON(BidsJSON):
    keylist = ['Manufacturer', 'ManufacturersModelName', 'MagneticFieldStrength', 'DeviceSerialNumber', 'StationName',
               'SoftwareVersions', 'HardcopyDeviceSoftwareVersion', 'ReceiveCoilName', 'ReceiveCoilActiveElements',
               'GradientSetType', 'MRTransmitCoilSequence', 'MatrixCoilMode', 'CoilCombinationMethod',
               'PulseSequenceType', 'ScanningSequence', 'SequenceVariant', 'ScanOptions', 'PulseSequenceDetails',
               'NonlinearGradientCorrection', 'NumberShots', 'ParallelReductionFactorInPlane',
               'ParallelAcquisitionTechnique', 'PartialFourier', 'PartialFourierDirection', 'PhaseEncodingDirection',
               'EffectiveEchoSpacing', 'TotalReadoutTime', 'WaterFatShift', 'EchoTrainLength', 'EchoTime',
               'InversionTime', 'SliceTiming', 'SliceEncodingDirection', 'DwellTime', 'FlipAngle',
               'MultibandAccelerationFactor', 'AnatomicalLandmarkCoordinates', 'InstitutionName', 'InstitutionAddress',
               'InstitutionalDepartmentName']
    required_keys = []


class ElectrophyJSON(BidsJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']


class BidsTSV(BidsSidecar, list):

    extension = '.tsv'
    modality_field = ''
    header = []
    required_fields = []

    def __init__(self, header=None, required_fields=None, modality_field=None):
        """initiate a  table containing the header"""
        self.is_complete = False
        super().__init__(modality_field=modality_field)
        if not header:
            self.header = self.__class__.header
        else:
            self.header = header
        if not required_fields:
            self.required_fields = self.__class__.required_fields
        else:
            self.required_fields = required_fields

        super().append(self.header)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key.stop or key.step:
                raise NotImplementedError(type(self).__name__ + 'do not handle slice only integers.')
            elif not key.start:
                idx = 0
            elif key.start < len(self):
                idx = key.start
            else:
                raise IndexError('List index out of range; list length = ' + str(len(self)) + '.')
        elif isinstance(key, int) and key < len(self):
            idx = key
        else:
            raise IndexError('List index out of range; list length = ' + str(len(self)) + '.')
        if isinstance(value, dict):
            lines = self[key]
            for key in value:
                if key in self.header:
                    lines[self.header.index(key)] = str(value[key])
                else:
                    print('Key ' + str(key) + ' is not in the header')
            super().__setitem__(idx, lines)
        elif not value:
            del(self[:])
            # super().append(self.header)
        else:
            raise TypeError('Input should be a dict with at least keys in required_keys and not more than '
                            'those of the header.')

    def __delitem__(self, key):
        if isinstance(key, int) and key == 0:
            return
        elif isinstance(key, slice) and key.start == 0 or not key.start:
            super().__setitem__(0, self.header)
            key = slice(1, key.stop, key.step)
        super().__delitem__(key)

    def append(self, dict2append):
        if not isinstance(dict2append, dict):
            raise TypeError('The element to be appended has to be a dict instance.')
        lines = [self.bids_default_unknown]*len(self.header)
        for key in dict2append:
            if key in self.header:
                if not dict2append[key]:
                    dict2append[key] = BidsTSV.bids_default_unknown
                lines[self.header.index(key)] = str(dict2append[key])
        super().append(lines)

    def write_file(self, tsvfilename):
        if os.path.splitext(tsvfilename)[1] == '.tsv':
            with open(tsvfilename, 'w') as file:
                for _, line in enumerate(self):
                    file.write('\t'.join(line) + '\n')
        else:
            raise TypeError('File is not ".tsv".')

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        self.is_complete = False  # To be implemented, stay False for the moment

    @staticmethod
    def createalias(subname=None, numsyl=3):
        rnd.seed(subname)
        alias = ''
        consonants = 'zrtpdfklmvbn'
        consonants = consonants.upper()
        num_cons = len(consonants)-1
        vowels = 'aeiou'
        vowels = vowels.upper()
        num_voy = len(vowels)-1
        order = rnd.randint(0, 2)
        for syl in range(0, numsyl):
            if order == 1:
                alias = alias + consonants[rnd.randint(0, num_cons)]
                alias = alias + vowels[rnd.randint(0, num_voy)]
            else:
                alias = alias + vowels[rnd.randint(0, num_voy)]
                alias = alias + consonants[rnd.randint(0, num_cons)]
        alias = alias + datetime.now().strftime('%y')
        return alias


class EventsTSV(BidsTSV):

    header = ['onset', 'duration', 'trial_type', 'response_time', 'stim_file', 'HED']
    required_fields = ['onset', 'duration']
    modality_field = 'events'


class GlobalSidecars(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'space', 'modality', 'fileLoc']
    complementary_keylist = []
    required_keys = BidsBrick.required_keys
    allowed_file_formats = ['.tsv', '.json']

    # def __new__(cls, filename):
    #     pass

    def __init__(self, filename):
        """initiates a  dict var for ieeg info"""
        filename = filename.replace('.gz', '')
        filename, ext = os.path.splitext(filename)
        if ext.lower() in ['.json', '.tsv']:
            comp_key = [value for counter, value in enumerate(self.complementary_keylist) if value in
                        BidsSidecar.get_list_subclasses_names() and eval(value + '.modality_field') ==
                        filename.split('_')[-1]]
            super().__init__(keylist=self.__class__.keylist + comp_key,
                             required_keys=self.__class__.required_keys)
        # elif ext in self.allowed_file_formats and filename.split('_')[-1] == 'photo':
        else:
            photo_key = [value for counter, value in enumerate(self.complementary_keylist) if value in
                         BidsBrick.get_list_subclasses_names()][0]
            if ext.lower() in eval(photo_key + '.allowed_file_formats'):
                super().__init__(keylist=eval(photo_key + '.keylist'), required_keys=eval(photo_key + '.required_keys'))
                self['modality'] = 'photo'


class Photo(GlobalSidecars):
    keylist = BidsBrick.keylist + ['ses', 'acq', 'modality', 'fileLoc']
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_formats = ['.jpg', '.png', '.pdf', '.ppt', '.pptx']
    readable_file_format = allowed_file_formats
    modality_field = 'photo'

    def __init__(self):
        BidsBrick().__init__()
        self['modality'] = self.__class__.modality_field


''' A special class for setting the requirements of a given BIDS dataset '''


class Requirements(dict):
    keywords = ['_ready', '_integrity']

    def __init__(self, full_filename):

        self['Requirements'] = []
        if full_filename:
            with open(full_filename, 'r') as file:
                json_dict = json.load(file)
                if 'Requirements' in json_dict.keys():
                    self['Requirements'] = json_dict['Requirements']


''' The different modality bricks, subclasses of BidsBrick. '''

""" iEEG brick with its file-specific (IeegJSON, IeegChannelsTSV) and global sidecar 
(IeegCoordSysJSON, IeegElecTSV or IeegPhoto) files. """


class Ieeg(Electrophy):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'IeegJSON',
                                   'IeegChannelsTSV', 'IeegEventsTSV']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modalities = ['ieeg']
    allowed_file_formats = ['.edf', '.gdf', '.fif', '.vhdr']
    readable_file_formats = allowed_file_formats + ['.eeg', '.trc']

    def __init__(self):
        super().__init__()
        self['modality'] = 'ieeg'


class IeegJSON(BidsJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

    def __init__(self, modality_field):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegJSON.keylist, required_keys=IeegJSON.required_keys, modality_field=modality_field)


class IeegChannelsTSV(BidsTSV):
    """Store the info of the #_channels.tsv, listing amplifier metadata such as channel names, types, sampling
    frequency, and other information. Note that this may include non-electrode channels such as trigger channels."""

    header = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference', 'group',
              'description', 'status', 'status_description', 'software_filters']
    required_fields = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference']
    modality_field = 'channels'


class IeegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class IeegElecTSV(BidsTSV):
    header = ['name', 'x', 'y', 'z', 'size', 'type', 'material', 'tissue', 'manufacturer', 'grid_size', 'group',
              'hemisphere']
    required_fields = ['name', 'x', 'y', 'z', 'size']
    modality_field = 'electrodes'


class IeegCoordSysJSON(BidsJSON):
    keylist = ['iEEGCoordinateSystem', 'iEEGCoordinateUnits', 'iEEGCoordinateProcessingDescription', 'IntendedFor',
               'AssociatedImageCoordinateSystem', 'AssociatedImageCoordinateUnits',
               'AssociatedImageCoordinateSystemDescription', 'iEEGCoordinateProcessingReference']
    required_keys = ['iEEGCoordinateSystem', 'iEEGCoordinateUnits', 'iEEGCoordinateProcessingDescription',
                     'IntendedFor', 'AssociatedImageCoordinateSystem', 'AssociatedImageCoordinateUnits']
    modality_field = 'coordsystem'


class IeegPhoto(Photo):
    pass


class IeegGlobalSidecars(GlobalSidecars):
    complementary_keylist = ['IeegElecTSV', 'IeegCoordSysJSON', 'IeegPhoto']
    required_keys = BidsBrick.required_keys
    allowed_file_formats = ['.tsv', '.json'] + IeegPhoto.allowed_file_formats


""" Anat brick with its file-specific sidecar files."""


class Anat(Imagery):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'modality', 'fileLoc', 'AnatJSON']
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modalities = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'PD', 'Pdmap', 'PDT2', 'inplaneT1'
                          ,'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']

    def __init__(self):
        super().__init__()


class AnatJSON(ImageryJSON):
    pass


""" Func brick with its file-specific sidecar files. """


class Func(Imagery):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'modality', 'fileLoc', 'FuncJSON',
                                   'FuncEventsTSV']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modalities = ['bold', 'sbref']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']

    def __init__(self):
        super().__init__()


class FuncJSON(ImageryJSON):
    keylist = ImageryJSON.keylist + ['RepetitionTime', 'VolumeTiming', 'TaskName',
                                          'NumberOfVolumesDiscardedByScanner', 'NumberOfVolumesDiscardedByUser',
                                          'DelayTime', 'AcquisitionDuration', 'DelayAfterTrigger',
                                          'NumberOfVolumesDiscardedByScanner', 'NumberOfVolumesDiscardedByUser',
                                          'Instructions', 'TaskDescription', 'CogAtlasID', 'CogPOID']
    required_keys = ['RepetitionTime', 'VolumeTiming', 'TaskName']


class FuncEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


""" Fmap brick with its file-specific sidecar files. """


class Fmap(Imagery):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'modality', 'fileLoc', 'FmapJSON']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modalities = ['phasediff', 'phase1', 'phase2', 'magnitude1', 'magnitude2', 'magnitude', 'fieldmap', 'epi']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']

    def __init__(self):
        super().__init__()


class FmapJSON(ImageryJSON):

    required_keys = ['PhaseEncodingDirection', 'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime']


""" Fmap brick with its file-specific sidecar files. """


class Dwi(Imagery):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'run', 'modality', 'fileLoc', 'DwiJSON', 'Bval', "Bvec"]
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modalities = ['dwi']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']

    def __init__(self):
        super().__init__()
        self['modality'] = 'dwi'


class DwiJSON(ImageryJSON):
    pass


class Bval(BidsFreeFile):
    extension = '.bval'


class Bvec(BidsFreeFile):
    extension = '.bvec'


""" MEG brick with its file-specific sidecar files (To be finalized). """


class Meg(Electrophy):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'MegJSON',
                                   'MegEventsTSV']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modalities = ['meg']
    allowed_file_formats = ['.ctf', '.fif', '4D']
    readable_file_formats = allowed_file_formats

    def __init__(self):
        super().__init__()
        self['modality'] = 'meg'


class MegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


""" Behaviour brick with its file-specific sidecar files (To be finalized). """


class Beh(ModalityType):

    keylist = BidsBrick.keylist + ['ses', 'task', 'modality', 'fileLoc', 'BehEventsTSV']
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modalities = ['beh']
    allowed_file_formats = ['.tsv']
    readable_file_formats = allowed_file_formats

    def __init__(self):
        super().__init__()
        self['modality'] = 'beh'


class BehEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


''' Higher level bricks '''


class Subject(BidsBrick):

    keylist = BidsBrick.keylist + ['Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg',
                                   'Beh', 'IeegGlobalSidecars']
    required_keys = BidsBrick.required_keys

    def __init__(self):
        super().__init__()

    def get_attr_tsv(self, parttsv):
        if isinstance(parttsv, ParticipantsTSV):
            bln, sub_dict = parttsv.is_subject_present(self['sub'])
            if bln:
                sub_dict = {key: sub_dict[key] for key in parttsv.header if key in self.keylist}
                self.copy_values(sub_dict)


    # @classmethod
    # def get_list_modality_type(cls):
    #     return ['Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg', 'Beh']
        # [mod_type for cnt, mod_type in enumerate(cls.keylist) if cls.keybln[cnt]]


class SourceData(BidsBrick):

    keylist = ['Subject', 'SrcDataTrack']

    def __init__(self):
        super().__init__()


class Data2Import(BidsBrick):
    keylist = ['Subject', 'DatasetDescJSON', 'UploadDate']
    __filename = 'data2import.json'
    data2import_dir = None
    requirements = None

    def __init__(self, data2import_dir, requirements_fileloc=None):
        """initiate a  dict var for Subject info"""
        if os.path.isdir(data2import_dir):
            self._assign_import_dir(data2import_dir)
            self.data2import_dir = data2import_dir
            self.requirements = None
            super().__init__()
            if os.path.isfile(os.path.join(self.data2import_dir, Data2Import.__filename)):
                with open(os.path.join(self.data2import_dir, Data2Import.__filename)) as file:
                    inter_dict = json.load(file)
                    self.copy_values(inter_dict)
            else:
                self['UploadDate'] = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            self.get_requirements(requirements_fileloc)
        else:
            str_error = data2import_dir + 'is not a directory.'
            self.write_log(str_error)
            raise NotADirectoryError(str_error)

    def save_as_json(self, savedir=None, file_start=None, write_date=False, compress=False):
        super().save_as_json(savedir=self.data2import_dir, file_start=None, write_date=False, compress=False)

    @classmethod
    def _assign_import_dir(cls, data2import_dir):
        cls.data2import_dir = data2import_dir
        BidsBrick.cwdir = data2import_dir


class Pipeline(BidsBrick):

    keylist = ['name', 'Subject']

    def __init__(self):
        super().__init__()


class Derivatives(BidsBrick):

    keylist = ['Pipeline']

    def __init__(self):
        super().__init__()


class Code(BidsBrick):
    pass


class Stimuli(BidsBrick):
    pass


''' Dataset related JSON bricks '''


class DatasetDescJSON(BidsJSON):

    keylist = ['Name', 'BIDSVersion', 'License', 'Authors', 'Acknowledgements', 'HowToAcknowledge', 'Funding',
               'ReferencesAndLinks', 'DatasetDOI']
    required_keys = ['Name', 'BIDSVersion']
    filename = 'dataset_description.json'

    def __init__(self):
        super().__init__()

    def write_file(self, jsonfilename=None):
        jsonfilename = os.path.join(BidsDataset.bids_dir, DatasetDescJSON.filename)
        super().write_file(jsonfilename)

    def read_file(self, jsonfilename=None):
        jsonfilename = os.path.join(BidsDataset.bids_dir, DatasetDescJSON.filename)
        super().read_file(jsonfilename)


''' TSV bricks '''


class SrcDataTrack(BidsTSV):
    header = ['orig_filename', 'bids_filename', 'upload_date']
    required_fields = ['orig_filename', 'bids_filename', 'upload_date']
    __tsv_srctrack = 'source_data_trace.tsv'

    def __init__(self):
        super().__init__()

    def write_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, 'sourcedata', SrcDataTrack.__tsv_srctrack)
        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, 'sourcedata', SrcDataTrack.__tsv_srctrack)
        super().read_file(tsv_full_filename)

    def get_source_from_raw_filename(self, filename):
        filename, ext = os.path.splitext(os.path.basename(filename).replace('.gz', ''))

        bids_fname_idx = self.header.index('bids_filename')
        orig_fname_idx = self.header.index('orig_filename')
        orig_fname = [line[orig_fname_idx] for line in self[1:] if filename in line[bids_fname_idx]]
        if orig_fname:
            orig_fname = orig_fname[0]

        return orig_fname, filename


class ParticipantsTSV(BidsTSV):
    header = ['participant_id']
    required_fields = ['participant_id']
    __tsv_participants = 'participants.tsv'

    def __init__(self):
        super().__init__()

    def write_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, ParticipantsTSV.__tsv_participants)

        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, ParticipantsTSV.__tsv_participants)
        super().read_file(tsv_full_filename)

    def is_subject_present(self, sub_id):
        # if not sub_id.startswith('sub-'):
        #     sub_id = 'sub-' + sub_id
        participant_idx = self.header.index('participant_id')
        sub_line = [line for line in self[1:] if sub_id in line[participant_idx]]
        if sub_line:
            sub_info = {self.header[cnt]: val for cnt, val in enumerate(sub_line[0])}
            sub_info['sub'] = sub_info['participant_id']
            del(sub_info['participant_id'])
        else:
            sub_info = {}

        return bool(sub_info), sub_info

    def add_subject(self, sub_dict):
        if isinstance(sub_dict, Subject):
            if not self.is_subject_present(sub_dict['sub'])[0]:
                tmp_dict = sub_dict.get_attributes()
                tmp_dict['participant_id'] = tmp_dict['sub']
                tmp_dict['upload_date'] = BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S")
                if 'alias' in self.header and 'alias' in tmp_dict:
                    tmp_dict['alias'] = self.createalias(sub_dict['sub'])
                self.append(tmp_dict)


''' Main BIDS brick which contains all the information concerning the patients and the sidecars. It permits to parse a 
given bids dataset, request information (e.g. is a given subject is present, has a given subject a given modality), 
import new data or export a subset of the current dataset (not yet implemented ) '''


class BidsDataset(BidsBrick):

    keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDescJSON', 'ParticipantsTSV']
    # _keybln = BidsBrick.create_keytype(_keylist)
    bids_dir = None
    requirements = None
    curr_log = ''

    def __init__(self, bids_dir):
        """initiate a  dict var for patient info"""
        super().__init__()
        self.bids_dir = bids_dir
        self._assign_bids_dir(bids_dir)
        self.curr_subject = {}
        self.issues = IssueBrick()
        self.requirements = BidsDataset.requirements
        self.parse_bids()

    def parse_bids(self):

        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None, srcdata=False):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, srcdata=srcdata)
                    elif not mod_dir and file.name.capitalize() in ModalityType.get_list_subclasses_names() and \
                            file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.capitalize(),
                                           srcdata=srcdata)
                    elif mod_dir and file.is_file():
                        filename, ext = os.path.splitext(file)
                        if ext.lower() == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext.lower() in eval(mod_dir + '.allowed_file_formats') or \
                                (srcdata and ext.lower() in eval(mod_dir + '.readable_file_formats')):
                            subinfo[mod_dir] = eval(mod_dir + '()')
                            # create empty object for the given modality
                            subinfo[mod_dir][-1]['fileLoc'] = file.path
                            # here again, modified dict behaviour, it appends to a list therefore checking the last
                            # element is equivalent to checking the newest element
                            subinfo[mod_dir][-1].get_attributes_from_filename()
                            subinfo[mod_dir][-1].get_sidecar_files()
                            # need to find corresponding json file and import it in modality json class
                        elif mod_dir + 'GlobalSidecars' in BidsBrick.get_list_subclasses_names() and ext.lower() \
                                in eval(mod_dir + 'GlobalSidecars.allowed_file_formats') and filename.split('_')[-1]\
                                in [eval(value + '.modality_field') for _, value in
                                    enumerate(IeegGlobalSidecars.complementary_keylist)]:
                            subinfo[mod_dir + 'GlobalSidecars'] = eval(mod_dir + 'GlobalSidecars(filename+ext)')
                            subinfo[mod_dir + 'GlobalSidecars'][-1]['fileLoc'] = file.path
                            subinfo[mod_dir + 'GlobalSidecars'][-1].get_attributes_from_filename()
                            subinfo[mod_dir + 'GlobalSidecars'][-1].get_sidecar_files()
                    elif mod_dir and file.is_dir():
                        subinfo[mod_dir] = eval(mod_dir + '()')
                        subinfo[mod_dir][-1]['fileLoc'] = file.path

        def parse_bids_dir(bids_brick, currdir, sourcedata=False):

            with os.scandir(currdir) as it:
                for entry in it:
                    if entry.name.startswith('sub-') and entry.is_dir():
                        # bids_brick['Subject'] = Subject('derivatives' not in entry.path and 'sourcedata' not in
                        #                                 entry.path)
                        bids_brick['Subject'] = Subject()
                        bids_brick['Subject'][-1]['sub'] = entry.name.replace('sub-', '')
                        if isinstance(bids_brick, BidsDataset) and bids_brick['ParticipantsTSV']:
                            bids_brick['Subject'][-1].get_attr_tsv(bids_brick['ParticipantsTSV'])
                        parse_sub_bids_dir(entry.path, bids_brick['Subject'][-1], srcdata=sourcedata)
                        # since all Bidsbrick that are not string are append [-1] is enough
                    elif entry.name == 'sourcedata' and entry.is_dir():
                        bids_brick['SourceData'] = SourceData()
                        bids_brick['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()
                        bids_brick['SourceData'][-1]['SrcDataTrack'].read_file()
                        parse_bids_dir(bids_brick['SourceData'][-1], entry.path, sourcedata=True)
                    elif entry.name == 'derivatives' and entry.is_dir():
                        bids_brick['Derivatives'] = Derivatives()
                        parse_bids_dir(bids_brick['Derivatives'][-1], entry.path)
                    elif os.path.basename(currdir) == 'derivatives' and isinstance(bids_brick, Derivatives)\
                            and entry.is_dir():
                        bids_brick['Pipeline'] = Pipeline()
                        bids_brick['Pipeline'][-1]['name'] = entry.name
                        parse_bids_dir(bids_brick['Pipeline'][-1], entry.path)

        BidsBrick.access_time = datetime.now()
        self.clear()  # clear the bids variable before parsing to avoid rewrite the same things
        self.write_log('Current User: ' + self.curr_user)
        # First read requirements.json which should be in the code folder of bids dir.
        self.get_requirements()

        self['DatasetDescJSON'] = DatasetDescJSON()
        self['DatasetDescJSON'].read_file()
        self['ParticipantsTSV'] = ParticipantsTSV()
        self['ParticipantsTSV'].read_file()

        parse_bids_dir(self, self.bids_dir)
        self.check_requirements()
        self['ParticipantsTSV'].write_file()
        self.save_as_json()

    def is_subject_present(self, subject_label):
        """
        Method that look if a given subject is in the current dataset. It returns a tuple composed
        of a boolean, an integer. The boolean is True if the sub is present, the integer gives its indices in the
        subject list of the dataset.
        Ex: (True, 5) = bids.is_subject_present('05')
        """
        index = -1
        self.curr_subject = {'sub': subject_label, 'isPresent': False, 'index': index}
        for subject in self['Subject']:
            index += 1
            if subject['sub'] == subject_label:
                self.curr_subject.update({'isPresent': True, 'index': index})
                return
        if not self.curr_subject['isPresent']:
            self.curr_subject['index'] = None

    def has_subject_modality_type(self, subject_label, modality_type):
        """
        Method that look if a given subject has a given modality type (e.g. Anat, Ieeg). It returns a tuple composed
        of a boolean, an integer and a dict. The boolean is True if the sub has the mod type, the integer gives the
        number of recordings of the modality and the dict returns the number of recordings of each modality
        Ex: (True, 4, {'T1w': 2, 'T2w':2}) = bids.has_subject_modality_type('01', 'Anat')
        """
        modality_type = modality_type.capitalize()
        if modality_type in ModalityType.get_list_subclasses_names():
            if not self.curr_subject or not self.curr_subject['sub'] == subject_label:
                # check whether the required subject is the current subject otherwise make it the current one
                self.is_subject_present(subject_label)

            bln = self.curr_subject['isPresent']
            sub_index = self.curr_subject['index']

            if bln:
                _, ses_list = self.get_number_of_session4subject(subject_label)
                curr_sub = self['Subject'][sub_index]
                if curr_sub[modality_type]:
                    allowed_mod = eval(modality_type + '.allowed_modalities')
                    if ses_list:  # create a list of tuple to be used as keys ex: ('ses-01', 'T1w')
                        key_list = []

                        for ses_label in ses_list:
                            for key in allowed_mod:
                                key_list += [('ses-' + ses_label, key)]
                        resume_modality = {key: 0 for key in key_list}
                    else:
                        key_list = allowed_mod
                        resume_modality = {key: 0 for key in key_list}
                    for mod_dict in curr_sub[modality_type]:
                        if mod_dict['ses']:  # if at least one session exists
                            resume_modality[('ses-' + mod_dict['ses'], mod_dict['modality'])] += 1
                        else:
                            resume_modality[mod_dict['modality']] += 1
                    [resume_modality.__delitem__(key) for key in key_list
                     if resume_modality[key] == 0]
                    return True, len(curr_sub[modality_type]), resume_modality
                else:
                    return False, 0, {}
            else:
                raise NameError('subject: ' + subject_label + ' is not present in the database')
        else:
            raise NameError('modality_type: ' + modality_type + ' is not a correct modality type.\n'
                                                                'Check ModalityType.get_list_subclasses_names().')

    def get_number_of_session4subject(self, subject_label):
        if not self.curr_subject or not self.curr_subject['sub'] == subject_label:
            # check whether the required subject is the current subject otherwise make it the current one
            self.is_subject_present(subject_label)
        bln = self.curr_subject['isPresent']
        sub_index = self.curr_subject['index']

        if bln:
            ses_list = []
            sub = self['Subject'][sub_index]
            for mod_type in sub:
                if mod_type in ModalityType.get_list_subclasses_names():
                    mod_list = sub[mod_type]
                    for mod in mod_list:
                        if mod['ses'] and mod['ses'] not in ses_list:
                            # 'ses': '' means no session therefore does not count
                            ses_list.append(mod['ses'])
            return len(ses_list), ses_list
        else:
            raise NameError('subject: ' + subject_label + ' is not present in the database')

    def get_number_of_runs(self, mod_dict_with_attr):
        """
        Method that returns the number of runs if in key list in database for a schema of modality dict.
        Ex:
        func_schema = Func()
        func_schema['sub'] = '01'
        func_schema['ses'] = '01'
        func_schema['task'] = 'bapa'
        N = bids.get_number_of_runs(func_schema)
        """
        nb_runs = 0
        highest_run = 0
        if 'run' in mod_dict_with_attr.keylist:
            mod_type = mod_dict_with_attr.get_modality_type()
            if mod_type in ModalityType.get_list_subclasses_names():
                if not self.curr_subject or not self.curr_subject['sub'] == mod_dict_with_attr['sub']:
                    # check whether the required subject is the current subject otherwise make it the current one
                    self.is_subject_present(mod_dict_with_attr['sub'])
                bln = self.curr_subject['isPresent']
                sub_index = self.curr_subject['index']
                if bln:
                    if self['Subject'][sub_index][mod_type]:
                        mod_input_attr = mod_dict_with_attr.get_attributes(['fileLoc', 'run'])
                        # compare every attributes but fileLoc and run
                        for mod in self['Subject'][sub_index][mod_type]:
                            mod_attr = mod.get_attributes('fileLoc')
                            idx_run = int(mod_attr.pop('run'))
                            if mod_input_attr == mod_attr:
                                nb_runs += 1
                                highest_run = max(nb_runs, idx_run)
        return nb_runs, highest_run

    def import_data(self, data2import, keep_sourcedata=True, keep_file_trace=True):

        def push_into_dataset(bids_dst, mod_dict2import, keep_srcdata, keep_ftrack):
            filename, dirname = mod_dict2import.create_filename_from_attributes()

            fname2import, ext2import = os.path.splitext(mod_dict2import['fileLoc'])
            orig_ext = ext2import
            # bsname_bids_dir = os.path.basename(bids_dst.bids_dir)
            sidecar_flag = [value for _, value in enumerate(mod_dict2import.keylist) if value in
                            BidsSidecar.get_list_subclasses_names()]
            mod_type = mod_dict2import.get_modality_type()
            sub = bids_dst['Subject'][bids_dst.curr_subject['index']]

            # if ext2import == '.gz':
            #     fname2import, ext2import = os.path.splitext(fname2import)
            #     orig_ext = ext2import + orig_ext

            fnames_list = mod_dict2import.convert()
            tmp_attr = mod_dict2import.get_attributes()
            tmp_attr['fileLoc'] = os.path.join(BidsDataset.bids_dir, dirname, fnames_list[0])
            if isinstance(mod_dict2import, GlobalSidecars):
                sub[mod_type] = eval(mod_type + '(tmp_attr["fileLoc"])')
            else:
                sub[mod_type] = eval(mod_type + '()')
            sub[mod_type][-1].update(tmp_attr)

            if keep_srcdata and not isinstance(mod_dict2import, GlobalSidecars):
                scr_data_dirname = os.path.join(BidsDataset.bids_dir, 'sourcedata', dirname)
                os.makedirs(scr_data_dirname, exist_ok=True)
                path_src = os.path.join(Data2Import.data2import_dir, mod_dict2import['fileLoc'])
                path_dst = os.path.join(scr_data_dirname, mod_dict2import['fileLoc'])
                if os.path.isdir(path_src):
                    # use copytree for directories (e.g. DICOM)
                    shutil.copytree(path_src, path_dst)
                else:
                    # use copy2 for files
                    shutil.copy2(path_src, path_dst)
                src_data_sub = bids_dst['SourceData'][-1]['Subject'][bids_dst.curr_subject['index']]
                src_data_sub[mod_type] = eval(mod_type + '()')
                tmp_attr = mod_dict2import.get_attributes()
                tmp_attr['fileLoc'] = path_dst
                src_data_sub[mod_type][-1].update(tmp_attr)

                if keep_ftrack:
                    orig_fname = os.path.basename(mod_dict2import['fileLoc'])
                    upload_date = bids_dst.access_time.strftime("%Y-%m-%dT%H:%M:%S")
                    scr_track = bids_dst['SourceData'][-1]['SrcDataTrack']
                    scr_track.append({'orig_filename': orig_fname, 'bids_filename': filename,
                                      'upload_date': upload_date})

            if sidecar_flag:
                for sidecar_tag in sidecar_flag:
                    if mod_dict2import[sidecar_tag]:
                        if mod_dict2import[sidecar_tag].modality_field:
                            fname = filename.replace(mod_dict2import['modality'],
                                                     mod_dict2import[sidecar_tag].modality_field)
                        else:
                            fname = filename
                        fname2bewritten = os.path.join(BidsDataset.bids_dir, dirname, fname +
                                                       mod_dict2import[sidecar_tag].extension)
                        mod_dict2import[sidecar_tag].write_file(fname2bewritten)
                sub[mod_type][-1].get_sidecar_files()

            mod_dict2import.write_log(mod_dict2import['fileLoc'] + ' was imported as ' + filename)

        def have_data_same_source_file(bids_dict, mod_dict):
            if bids_dict['SourceData'] and bids_dict['SourceData'][-1]['SrcDataTrack']:
                filename, dirname = mod_dict.create_filename_from_attributes()
                original_src = bids_dict['SourceData'][-1]['SrcDataTrack'].get_source_from_raw_filename(filename)[0]
                return os.path.basename(mod_dict['fileLoc']) == original_src

            return False

        def have_data_same_attrs_and_sidecars(bids_dst, mod_dict2import, sub_idx):
            """
            Method that compares whether a given modality dict is the same as the ones present in the bids dataset.
            Ex: True = bids.have_data_same_attrs_and_sidecars(instance of Anat())
            """
            bids_mod_list = bids_dst['Subject'][sub_idx][mod_dict2import.get_modality_type()]
            mod_dict2import_attr = mod_dict2import.get_attributes('fileLoc')
            for mod in bids_mod_list:
                mod_in_bids_attr = mod.get_attributes('fileLoc')
                if mod_dict2import_attr == mod_in_bids_attr:  # check if both mod dict have same attributes
                    if 'run' in mod_dict2import_attr.keys() and mod_dict2import_attr['run']:
                        # if run if a key check the JSON and possibly increment the run integer of mod_
                        # dict2import to import it
                        mod_dict2import_dep = mod_dict2import.extract_sidecares_from_sourcedata()
                        numb_runs = bids_dst.get_number_of_runs(mod_dict2import)[0]
                        mod_in_bids_dep = mod.get_modality_sidecars()
                        if not mod_dict2import_dep == mod_in_bids_dep:
                            # check the sidecar files to verify whether they are the same data, in that the case
                            # add current nb_runs to 'run' if available otherwise do not import
                            mod_dict2import['run'] = str(1 + numb_runs).zfill(2)
                            return False

                    return True
            return False

        # if True:

        if issubclass(type(data2import), Data2Import) and data2import.has_all_req_attributes()[0]:

            '''Here we copy the data2import dictionary to pop all the imported data in order to avoid importing
            the same data twice in case there is an error and we have to launch the import procedure on the same
            folder again. The original data2import in rename by adding the date in the filename'''
            copy_data2import = Data2Import(Data2Import.data2import_dir)
            try:
                shutil.move(os.path.join(Data2Import.data2import_dir, Data2Import.__filename),
                            os.path.join(Data2Import.data2import_dir, self.access_time.strftime("%Y-%m-%dT%H:%M:%S")
                                         + Data2Import.__filename))
                if keep_sourcedata:
                    if not self['SourceData']:
                        self['SourceData'] = SourceData()
                        if keep_file_trace:
                            self['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()

                self._assign_bids_dir(self.bids_dir)  # make sure to import in the current bids_dir
                for sub in data2import['Subject']:
                    import_sub_idx = data2import['Subject'].index(sub)
                    [flag, missing_str] = sub.has_all_req_attributes()
                    if flag:
                        self['ParticipantsTSV'].add_subject(sub)
                        for modality_type in sub.keys():
                            if modality_type in BidsBrick.get_list_subclasses_names():
                                for modality in sub[modality_type]:
                                    if not self.curr_subject or not self.curr_subject['sub'] == sub['sub']:
                                        # check whether the required subject is the current subject otherwise make it the
                                        # current one
                                        self.is_subject_present(sub['sub'])
                                    sub_present = self.curr_subject['isPresent']
                                    sub_index = self.curr_subject['index']

                                    if sub_present:
                                        nb_ses, bids_ses = self.get_number_of_session4subject(sub['sub'])
                                        if modality['ses'] and bids_ses:
                                            # if subject is present, have to check if ses in the data2import matches
                                            # the session structures of the dataset (if ses-X already exist than
                                            # data2import has to have a ses)
                                            same_src_file_bln = have_data_same_source_file(self, modality)
                                            if not same_src_file_bln:
                                                same_attr_bln = have_data_same_attrs_and_sidecars(self, modality,
                                                                                                  sub_index)
                                                if same_attr_bln:
                                                    string_issue = 'Subject ' + sub['sub'] + '\'s file:' + modality[
                                                        'fileLoc'] \
                                                                   + ' was not imported because ' + \
                                                                   modality.create_filename_from_attributes()[0] + \
                                                                   ' is already present in the bids dataset ' + \
                                                                   self['DatasetDescJSON']['Name'] + '.'
                                                    self.write_log(string_issue)
                                                    continue
                                            else:
                                                string_issue = 'Subject ' + sub['sub'] + '\'s file:' + modality[
                                                    'fileLoc'] \
                                                               + ' was not imported because a source file with ' \
                                                                 'the same name is already present in the ' \
                                                                 'bids dataset ' + self['DatasetDescJSON']['Name'] + '.'
                                                self.write_log(string_issue)
                                                continue
                                        else:
                                            string_issue = 'Session structure of the data to be imported does not ' \
                                                           'match the one of the current dataset.\nSession label(s): '\
                                                           + ', '.join(bids_ses) + '.\nSubject ' + sub['sub'] + \
                                                           ' not imported.'
                                            self.write_log(string_issue)
                                            continue
                                    else:
                                        self['Subject'] = Subject()
                                        self['Subject'][-1].update(sub.get_attributes())
                                        self.is_subject_present(sub['sub'])
                                        if keep_sourcedata:
                                            self['SourceData'][-1]['Subject'] = Subject()
                                            self['SourceData'][-1]['Subject'][-1].update(sub.get_attributes())

                                    push_into_dataset(self, modality, keep_sourcedata, keep_file_trace)
                                    copy_data2import['Subject'][import_sub_idx][modality_type].pop(0)
                                    copy_data2import.save_as_json()

                    else:
                        self.write_log(missing_str)
                        raise ValueError(missing_str)

                    # copy_data2import['Subject'].pop(0)

                # with open(os.path.join(Data2Import.data2import_dir, 'data2import.json'), 'w') as file:
                #     # json.dump(copy_data2import, file, indent=1, separators=(',', ': '), ensure_ascii=False)
                #     json_str = json.dumps(copy_data2import, indent=1, separators=(',', ': '), ensure_ascii=False,
                #                           sort_keys=False)
                #     file.write(json_str)
                # copy_data2import.save

                if self['DatasetDescJSON']:
                    self['DatasetDescJSON'].write_file()
                if self['ParticipantsTSV']:
                    self['ParticipantsTSV'].write_file()
                if keep_sourcedata and keep_file_trace:
                    self['SourceData'][-1]['SrcDataTrack'].write_file()
                self.parse_bids()

            # shutil.rmtree(data2import.data2import_dir)
            except Exception as err:
                self.write_log(err)
                copy_data2import.save_as_json()

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):
        save_parsing_path = os.path.join(self.bids_dir, 'derivatives', 'parsing')
        os.makedirs(save_parsing_path, exist_ok=True)
        super().save_as_json(savedir=save_parsing_path, file_start='parsing', write_date=True, compress=True)

    @classmethod
    def _assign_bids_dir(cls, bids_dir):
        cls.bids_dir = bids_dir
        BidsBrick.cwdir = bids_dir

    # def __repr__(self):
    #     return 'bids = BidsDataset("C:/Users/datasetdir/your_bids_dir")'


''' Additional class to handle issues and relative actions '''


class RefElectrodes(BidsFreeFile):
    pass


class MismatchedElectrodes(BidsFreeFile):
    pass


class Comment(BidsBrick):
    keylist = ['date', 'user', 'description']

    def __init__(self, new_keys=None):
        if not new_keys:
            new_keys = []
        if isinstance(new_keys, str):
            new_keys = [new_keys]
        if isinstance(new_keys, list):
            super().__init__(keylist=new_keys + self.__class__.keylist)
            self['user'] = self.curr_user
            self['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        else:
            error_str = 'The new keys of ' + self.__class__.__name__ + ' should be either a list of a string.'
            self.write_log(error_str)
            raise TypeError(error_str)

    def formatting(self):
        return '==> ' + self.__class__.__name__ + ' by ' + self['user'] + ' at ' + self['date'] + ':\n'\
               + self['description']


class Action(Comment):
    keylist = Comment.keylist + ['command']

    def __init__(self, new_keys=None):
        super().__init__(new_keys=new_keys)


class ChannelIssue(BidsBrick):
    keylist = BidsBrick.keylist + ['mod', 'RefElectrodes', 'MismatchedElectrodes', 'filepath', 'Comment', 'Action']

    def add_action(self, elec_name, desc, command):
        """verify that the given electrode name is part of the mismatched electrodes"""
        if elec_name not in self['MismatchedElectrodes']:
            raise NameError(elec_name + 'is not an mismatched electrode.')
        """ check whether a mismatched electrode already has an action. Only one action per electrode is permitted"""
        idx2pop = None
        for act in self['Action']:
            if act['label'] == elec_name:
                idx2pop = self['Action'].index(act)
                break
        if idx2pop is not None:
            self['Action'].pop(idx2pop)
        """ add action for given mismatched electrodes """
        action = Action('label')
        action['label'] = elec_name
        action['description'] = desc
        action['command'] = command
        self['Action'] = action

    def add_comment(self,  elec_name, desc):
        """verify that the given electrode name is part of the mismatched electrodes"""
        if elec_name not in self['MismatchedElectrodes']:
            raise NameError(elec_name + 'is not an mismatched electrode.')
        """ add comment about a given mismatched electrodes """
        comment = Comment('label')
        comment['label'] = elec_name
        comment['description'] = desc
        self['Comment'] = comment

    def formatting(self, comment_type=None):
        if comment_type and (not isinstance(comment_type, str) or
                             comment_type.capitalize() not in Comment.get_list_subclasses_names() + ['Comment']):
            raise KeyError(comment_type + ' is not a recognized key of ' + self.__class__.__name__ + '.')
        if not comment_type:
            comment_type = Comment.get_list_subclasses_names() + ['Comment']
        else:
            comment_type = [comment_type.capitalize()]
        formatted_str = ''
        for cmnt_type in comment_type:
            for cmnt in self[cmnt_type]:
                formatted_str += cmnt.formatting()
        return formatted_str


class ImportIssue(BidsBrick):
    keylist = BidsBrick.keylist + ['filepath', 'Comment', 'Action']


class IssueBrick(BidsBrick):
    keylist = ['ChannelIssue', 'ImportIssue']

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):

        log_path = os.path.join(BidsDataset.bids_dir, 'derivatives', 'log')
        super().save_as_json(savedir=log_path, file_start='issue', write_date=True, compress=False)

    def formatting(self, specific_issue=None, comment_type=None):
        if specific_issue and specific_issue not in self.keys():
            raise KeyError(specific_issue + ' is not a recognized key of ' + self.__class__.__name__ + '.')
        if comment_type and (not isinstance(comment_type, str) or
                             comment_type.capitalize() not in Comment.get_list_subclasses_names() + ['Comment']):
            raise KeyError(comment_type + ' is not a reckognized key of ' + self.__class__.__name__ + '.')
        formatted_str = ''
        if specific_issue:
            key2check = [specific_issue]
        else:
            key2check = self.keylist
        for key in key2check:
            for issue in self[key]:
                formatted_str += issue.formatting(comment_type=comment_type)

        return formatted_str

