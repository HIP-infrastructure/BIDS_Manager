#!/usr/bin/python3
# -*-coding:Utf-8 -*

"""
    This module was written by Nicolas Roehri <nicolas.roehri@etu.uni-amu.fr>
    (with changes by Aude Jegou <aude.jegou@univ-amu.fr)
    This module is concerned by managing BIDS directory.
    v0.1.10 March 2019
"""

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
from sys import argv
from sys import modules
import json
import brainvision_hdr as bv_hdr
from datetime import datetime
from collections import OrderedDict
import pprint
import gzip
import shutil
import random as rnd
import getpass
import nibabel

standard_library.install_aliases()

''' Three main bricks: BidsBrick: to handles the modality and high level directories, BidsJSON: to handles the JSON 
sidecars, BidsTSV: to handle the tsv sidecars. '''


class BidsBrick(dict):

    keylist = ['sub']
    required_keys = ['sub']
    access_time = datetime.now()
    time_format = "%Y-%m-%dT%H-%M-%S"
    cwdir = os.getcwd()
    allowed_modalities = []
    state_list = ['valid', 'invalid', 'forced', 'ready']
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
                if value and isinstance(value, Process):
                    self[key].append(value)
                elif value and isinstance(value, eval(key)):
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
                        if os.path.isabs(value):
                            if BidsBrick.cwdir in value:
                                value = os.path.relpath(value, BidsBrick.cwdir)
                        else:
                            filename = os.path.join(BidsBrick.cwdir, value)
                        if not os.path.exists(filename):
                            str_issue = 'file: ' + str(filename) + ' does not exist.'
                            self.write_log(str_issue)
                            raise FileNotFoundError(str_issue)
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
                                    self.classname() + '.allowed_modalities().'
                        self.write_log(str_issue)
                        raise TypeError(str_issue)
                else:
                    dict.__setitem__(self, key, value)
            elif key == 'run':
                if value:
                    if isinstance(value, int):
                        dict.__setitem__(self, key, str(value).zfill(2))
                    elif value.__class__.__name__ in ['str', 'unicode'] and value.isdigit():
                        dict.__setitem__(self, key, value.zfill(2))
                    else:
                        str_issue = 'run value ' + str(value) + ' should be a digit (integer or string).'
                        self.write_log(str_issue)
                        raise TypeError(str_issue)
                else:
                    dict.__setitem__(self, key, value)
            elif isinstance(value, int):
                dict.__setitem__(self, key, str(value).zfill(2))
            elif value.__class__.__name__ in ['str', 'unicode'] and \
                    (not value or (value.isalnum() and isinstance(self, ModalityType))
                     or not isinstance(self, ModalityType)) or \
                    key in BidsFreeFile.get_list_subclasses_names():
                dict.__setitem__(self, key, value)
            else:
                str_issue = '/!\ key: ' + str(key) + ' should either be an alphanumeric string or an integer /!\ '
                self.write_log(str_issue)
                raise TypeError(str_issue)
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.classname() +\
                        ' class keylist /!\ '
            self.write_log(str_issue)
            raise KeyError(str_issue)

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
                        ' class keylist /!\ '
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
                        ' class keylist /!\ '
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

    def has_all_req_attributes(self, missing_elements=None, nested=True):
        # check if the required attributes are not empty to create
        # the filename (/!\ Json or coordsystem checked elsewhere)
        if not missing_elements:
            missing_elements = ''

        for key in self.keylist:
            if key in BidsDataset.keylist[1:] and key in BidsBrick.get_list_subclasses_names():
                ''' source data, derivatives, code do not have requirements yet'''
                continue
            if self.required_keys:
                if key in self.required_keys and (self[key] == '' or self[key] == []):
                    missing_elements += 'In ' + type(self).__name__ + ', key ' + str(key) + ' is missing.\n'
            if self[key] and isinstance(self[key], list) and nested:
                # check if self has modality brick, if not empty than
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
        ext = ''
        if isinstance(self, ModalityType) or isinstance(self, GlobalSidecars):
            for key in self.get_attributes(['fileLoc', 'modality']):
                if self[key]:
                    if isinstance(self[key], str):
                        str2add = self[key]
                    else:
                        str2add = str(self[key]).zfill(2)
                    filename += key + '-' + str2add + '_'
            filename += self['modality']
            piece_dirname = []
            piece_dirname += [shrt_name for _, shrt_name in enumerate(filename.split('_')) if
                              shrt_name.startswith('sub-') or shrt_name.startswith('ses-')]
            mod_type = self.classname()
            if isinstance(self, GlobalSidecars):
                mod_type = mod_type.lower().replace(GlobalSidecars.__name__.lower(), '')
            elif isinstance(self, Process):
                if self['modality'] == 'pial':
                    mod_type = 'anat'
                else:
                    mod_type = self['modality'].lower()
            else:
                mod_type = mod_type.lower()
            piece_dirname += [mod_type]
            dirname = os.path.join(*piece_dirname)
            if isinstance(self, Electrophy):
                ext = BidsDataset.converters['Electrophy']['ext'][0]
            elif isinstance(self, Imagery):
                ext = BidsDataset.converters['Imagery']['ext'][0]
            else:
                ext = os.path.splitext(self['fileLoc'])[1]
        return filename, dirname, ext

    def get_sidecar_files(self, in_bids_dir=True, input_dirname=None, input_filename=None):
        # find corresponding JSON file and read its attributes and save fileloc
        def find_sidecar_file(sidecar_dict, fname, drname, direct_search):
            if isinstance(sidecar_dict, IeegChannelsTSV):
                tmp_sidecar = sidecar_dict[:]
            #import pdb; pdb.set_trace()
            piece_fname = fname.split('_')
            if sidecar_dict.inheritance and not direct_search:
                while os.path.dirname(drname) != BidsDataset.dirname:
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
                                        #To put the status of channel as bad if it's written in data2import
                                        if isinstance(sidecar_dict, IeegChannelsTSV):
                                            idt = 1
                                            while idt < len(tmp_sidecar):
                                                ids = 1
                                                name_tmp = tmp_sidecar[idt][0]
                                                status_tmp = tmp_sidecar[idt][10]
                                                while ids < len(sidecar_dict):
                                                    if sidecar_dict[ids][0].lower() == name_tmp.lower():
                                                        sidecar_dict[ids][10] = status_tmp
                                                    ids+=1
                                                idt+=1
                                        has_broken = True
                                        break
                            if has_broken:
                                break
                if os.path.dirname(drname) == BidsDataset.dirname:
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
                                        if isinstance(sidecar_dict, IeegChannelsTSV):
                                            idt = 1
                                            while idt < len(tmp_sidecar):
                                                ids = 1
                                                name_tmp = tmp_sidecar[idt][0]
                                                status_tmp = tmp_sidecar[idt][10]
                                                while ids < len(sidecar_dict):
                                                    if sidecar_dict[ids][0].lower() == name_tmp.lower():
                                                        sidecar_dict[ids][10] = status_tmp
                                                    ids += 1
                                                idt += 1
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
                                    #To put the status of channel as bad if it's written in data2import
                                    if isinstance(sidecar_dict, IeegChannelsTSV):
                                        idt = 1
                                        while idt < len(tmp_sidecar):
                                            ids = 1
                                            name_tmp = tmp_sidecar[idt][0]
                                            status_tmp = tmp_sidecar[idt][10]
                                            while ids < len(sidecar_dict):
                                                if sidecar_dict[ids][0].lower() == name_tmp.lower():
                                                    sidecar_dict[ids][10] = status_tmp
                                                ids+=1
                                            idt+=1
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
                    main_dirname = BidsDataset.dirname
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
                    sdcr_tmp = eval(sidecar_tag + '(modality_field=self["modality"])')
                else:
                    sdcr_tmp = eval(sidecar_tag + '()')
                if self[sidecar_tag]:
                    #  if info are given in modJSON or TSV in data2import prior to importation
                    self[sidecar_tag].copy_values(sdcr_tmp, simplify_flag=False)
                else:
                    self[sidecar_tag] = sdcr_tmp

                find_sidecar_file(self[sidecar_tag], filename, os.path.join(main_dirname, rootdir, filename),
                                  direct_search=not in_bids_dir)
                self[sidecar_tag].simplify_sidecar(required_only=False)

    def save_as_json(self, savedir, file_start=None, write_date=True, compress=True):
        # \t*\[\n\t*(?P<name>[^\[])*?\n\t*\]
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
                date_string = '_' + BidsBrick.access_time.strftime(self.time_format)
            else:
                date_string = ''

            json_filename = file_start + type(self).__name__.lower() + date_string + '.json'

            output_fname = os.path.join(savedir, json_filename)
            with open(output_fname, 'w') as f:
                # json.dump(self, f, indent=1, separators=(',', ': '), ensure_ascii=False)
                json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
                # r"(?P<open_table>\[\n\t{1,}\[)(?P<content>.*?)(?P<close_table>\]\n\t{1,}\])"
                # This solution is way too slow. need to reimplemente a json writer...
                # if isinstance(self, BidsDataset):
                #     #  make the table more readible (otherwise each elmt is isolated on a line...)
                #     exp = r'\s*(?P<name>\[\n\s*[^\[\{\]]*?\n\s*\])'
                #     matched_exp = re.findall(exp, json_str)
                #     for elmt in matched_exp:
                #         json_str = json_str.replace(elmt, elmt.replace('\n', ''))
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

    def classname(self):
        return self.__class__.__name__

    def get_attributes(self, keys2remove=None):
        attr_dict = {key: self[key] for key in self.keys() if key not in
                     BidsBrick.get_list_subclasses_names() + BidsSidecar.get_list_subclasses_names()}
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
            if not input_dict[key]:
                continue
            if key in BidsBrick.get_list_subclasses_names():
                if key in GlobalSidecars.get_list_subclasses_names():
                    flag_globalsidecar = True
                else:
                    flag_globalsidecar = False
                if key in Process.get_list_subclasses_names():
                    flag_process = True
                else:
                    flag_process= False
                for elmt in input_dict[key]:
                    if flag_globalsidecar:
                        mod_dict = eval(key + '(elmt["fileLoc"])')
                    elif flag_process:
                        mod_dict = create_subclass_instance(key, Process)
                    else:
                        mod_dict = eval(key + '()')
                    mod_dict.copy_values(elmt)
                    self[key] = mod_dict
            elif key in BidsSidecar.get_list_subclasses_names():
                if 'modality' in self and not eval(key + '.modality_field'):
                    self[key] = eval(key + '(modality_field=self["modality"])')
                else:
                    self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            elif key in SubjectProcess.keyprocess:
                for elmt in input_dict[key]:
                    mod_dict = create_subclass_instance(key, Process)
                    mod_dict.copy_values(elmt)
                    self[key] = mod_dict
            else:
                self[key] = input_dict[key]

    def get_modality_sidecars(self, cls=None):
        if cls is None:
            sidecar_dict = {key: self[key] for key in self if key in BidsSidecar.get_list_subclasses_names()}
        elif issubclass(cls, BidsSidecar):
            sidecar_dict = {key: self[key] for key in self if key in cls.get_list_subclasses_names()}
        else:
            sidecar_dict = []
            print('Class input is not a subclass of BidsSidecars!')
        return sidecar_dict

    def extract_sidecares_from_sourcedata(self):
        filename, dirname, ext = self.create_filename_from_attributes()

        if not Data2Import.dirname or not Data2Import.dirname:
            str_issue = 'Need import and bids directory to be set.'
            self.write_log(str_issue)
            raise NotADirectoryError(str_issue)
        if isinstance(self, Imagery):
            converter_path = BidsDataset.converters['Imagery']['path']
            cmd_line_base = '""' + converter_path + '"' + " -b y -ba y -m y -z n -f "
            cmd_line = cmd_line_base + filename + ' -o ' + Data2Import.dirname + ' ' + \
                       os.path.join(Data2Import.dirname, self['fileLoc']) + '"'
        elif isinstance(self, Electrophy):
            converter_path = BidsDataset.converters['Electrophy']['path']
            attr_dict = self.get_attributes(['fileLoc', 'modality'])
            name_cmd = ' '.join(['--bids_' + key + ' ' + attr_dict[key] for key in attr_dict if attr_dict[key]])

            cmd_line = '""' + converter_path + '"' + ' --seegBIDS "' + \
                       os.path.join(Data2Import.dirname, self['fileLoc']) + '" ' + name_cmd + \
                       ' --bids_dir "' + Data2Import.dirname + '" --bids_output sidecars"'
        else:
            str_issue = 'Sidecars from ' + os.path.basename(self['fileLoc']) + ' cannot be extracted!!'
            self.write_log(str_issue)
            return

        os.system(cmd_line)
        # list_filename = [filename + ext for ext in conv_ext]
        dict_copy = eval(self.classname() + '()')
        set_cwd = BidsBrick.cwdir
        if not BidsBrick.cwdir == Data2Import.dirname:
            BidsBrick.cwdir = Data2Import.dirname

        dict_copy.copy_values(self)
        dict_copy.get_sidecar_files(in_bids_dir=False, input_dirname=os.path.join(Data2Import.dirname, 'temp_bids'),
                                    input_filename=filename)
        BidsBrick.cwdir = set_cwd

        return dict_copy.get_modality_sidecars()

    def check_requirements(self, specif_subs=None):

        def check_dict_from_req(sub_mod_list, mod_req, modality, sub_name):

            type_dict = mod_req['type']
            if isinstance(type_dict, dict):
                type_dict = [type_dict]

            amount = 0
            if sub_mod_list:
                for type_req in type_dict:
                    non_specif_keys = [key for key in type_req if type_req[key] == '_']
                    if 'modality' in type_req and type_req['modality'] == 'photo':
                        keylist = Photo.keylist
                    else:
                        keylist = eval(modality + '.keylist')
                    empty_keys = [key for key in keylist if key not in type_req]
                    reduced_dict = {key: type_req[key] for key in type_req if not type_req[key] == '_'}
                    for sub_mod in sub_mod_list:
                        attr_dict = sub_mod.get_attributes(empty_keys)
                        if attr_dict == reduced_dict and not non_specif_keys or \
                                [key for key in non_specif_keys if key in keylist and
                                                                   key in attr_dict and attr_dict[key]]:
                            amount += 1

            if amount == 0:
                str_iss = 'Subject ' + sub_name + ' does not have files of type: ' + str(type_dict) + '.'
            elif amount < mod_req['amount']:
                str_iss = 'Subject ' + sub_name + ' misses ' + str(mod_req['amount']-amount) \
                            + 'files of type: ' + str(type_dict) + '.'
            else:
                return True

            self.write_log(str_iss)
            return False

        if isinstance(self, BidsDataset) and self.requirements['Requirements']:
            self.write_log(10 * '=' + '\nCheck requirements\n' + 10 * '=')
            key_words = self.requirements.keywords
            participant_idx = self['ParticipantsTSV'].header.index('participant_id')
            present_sub_list = [line[participant_idx] for line in self['ParticipantsTSV'][1:]]
            sub_list = present_sub_list
            if specif_subs:
                # if one want to check the requirements for a specific subject only, then specif_sub should be in
                # sub_list and then sublist become the specific subject otherwise check each subject
                if isinstance(specif_subs, str) and specif_subs in present_sub_list:
                    sub_list = [specif_subs]
                elif isinstance(specif_subs, list) and all(sub in present_sub_list for sub in specif_subs):
                    sub_list = specif_subs
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
                idx_chan_type = IeegChannelsTSV.header.index('type')

                for bidsintegrity_key in integrity_list:
                    for sub in sub_list:
                        # initiate to True and mark False for any issue
                        self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]] = str(True)
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
                            curr_type = []
                            """ list all the channels of the modality type end check whether their are in the reference 
                            list of electrodes"""
                            [(curr_elec.append(line[idx_chan_name]), curr_type.append(line[idx_chan_type]))
                             for line in mod['IeegChannelsTSV'][1:] if line[idx_chan_name] not in curr_elec and
                             not line[idx_chan_name] == BidsSidecar.bids_default_unknown and
                             line[idx_chan_type] in mod.channel_type]
                            miss_matching_elec = [{'name': name, 'type': curr_type[cnt]}
                                                  for cnt, name in enumerate(curr_elec) if name not in ref_elec]
                            if miss_matching_elec:
                                str_issue = 'File ' + os.path.basename(mod['fileLoc']) + \
                                            ' has inconsistent electrode name(s) ' + str(miss_matching_elec) + '.'
                                self.write_log(str_issue)
                                # filepath = mod.create_filename_from_attributes()

                                self.issues.add_issue('ElectrodeIssue', sub=sub,
                                                      fileLoc=mod['fileLoc'],
                                                      RefElectrodes=ref_elec, MismatchedElectrodes=miss_matching_elec,
                                                      mod=bidsintegrity_key[0])
                                self['ParticipantsTSV'][1 + sub_list.index(sub)][bidsintegrity_key[1]] = str(False)

            self.issues.check_with_latest_issue()
            self.issues.save_as_json()

            for sub in sub_list:
                idx = [elmt for elmt in integrity_list + check_list
                       if self['ParticipantsTSV'][1 + present_sub_list.index(sub)][elmt[1]] == 'False']
                if not idx:
                    self.write_log('!!!!!!!!!!! Subject ' + sub + ' is ready !!!!!!!!!!!')
                    self.is_subject_present(sub)
                    self['Subject'][self.curr_subject['index']].curr_state = 'ready'
                    self['ParticipantsTSV'][1 + present_sub_list.index(sub)][subject_ready_idx] = str(True)
                else:
                    self['ParticipantsTSV'][1 + present_sub_list.index(sub)][subject_ready_idx] = str(False)
            self['ParticipantsTSV'].write_file()

    def convert(self, dest_change=None):
        filename, dirname, ext = self.create_filename_from_attributes()

        Nifti = 'False'
        if not Data2Import.dirname or not Data2Import.dirname:
            str_issue = 'Need import and bids directory to be set.'
            self.write_log(str_issue)
            raise NotADirectoryError(str_issue)
        if isinstance(self, Imagery):
            converter_path = BidsDataset.converters['Imagery']['path']
            conv_ext = BidsDataset.converters['Imagery']['ext']
            # by default dcm2niix not do overwrite file with same names but adds a letter to it (inputnamea, inputnameb)
            # therefore one should firstly test whether a file with the same input name already exist and remove it to
            # avoid risking to import this one rather than the one which was converted and added a suffix
            for ext in conv_ext:
                if os.path.exists(os.path.join(Data2Import.dirname, 'temp_bids', filename + ext)):
                    os.remove(os.path.join(Data2Import.dirname, 'temp_bids', filename + ext))

            #Test to move the anat without converting
            for anfile in os.listdir(os.path.join(Data2Import.dirname, self['fileLoc'])):
                if os.path.isfile(os.path.join(Data2Import.dirname, self['fileLoc'], anfile)):
                    name, ext = os.path.splitext(anfile)
                    if ext == '.nii':
                        old_name = os.path.join(Data2Import.dirname, self['fileLoc'], anfile)
                        new_name = os.path.join(Data2Import.dirname, 'temp_bids', filename + ext)
                        img = nibabel.load(old_name)
                        header = img.header
                        if not self['AnatJSON']:
                            self['AnatJSON'] = AnatJSON()
                        self['AnatJSON']['Manufacturer'] = 'n/a'
                        self['AnatJSON']['MagneticFieldStrength'] = 'n/a'
                        self['AnatJSON']['EchoTime'] = 'n/a'
                        self['AnatJSON']['RepetitionTime'] = 'n/a'
                        self['AnatJSON']['FlipAngle'] = 'n/a'
                        nibabel.save(img, new_name)
                        #shutil.copy(old_name, new_name)
                        Nifti = 'True'

            #Change the cmd_line for Linux system but not tested
            #cmd_line_base = '""' + converter_path + '"' + " -b y -ba y -m y -z n -f "
            #cmd_line = cmd_line_base + filename + ' -o "' + os.path.join(Data2Import.dirname, 'temp_bids') + '" "' + os.path.join(Data2Import.dirname, self['fileLoc']) + '"'
            cmd_line_base = converter_path + ' -b y -ba y -m y -z n -f '
            cmd_line = cmd_line_base + filename + ' -o ' + os.path.join(Data2Import.dirname, 'temp_bids') + ' ' + os.path.join(Data2Import.dirname, self['fileLoc']) 
        elif isinstance(self, Electrophy):
            converter_path = BidsDataset.converters['Electrophy']['path']
            conv_ext = BidsDataset.converters['Electrophy']['ext']
            attr_dict = self.get_attributes(['fileLoc', 'modality'])
            name_cmd = ' '.join(['--bids_' + key + ' ' + attr_dict[key] for key in attr_dict if attr_dict[key]])

            #cmd_line = '""' + converter_path + '"' + ' --seegBIDS "' +\
            #           os.path.join(Data2Import.dirname, self['fileLoc']) + '" ' +\
            #           name_cmd + ' --bids_dir "' + os.path.join(Data2Import.dirname, 'temp_bids') + '" --bids_format vhdr"'

            cmd_line = converter_path + ' --seegBIDS '+ os.path.join(Data2Import.dirname, self['fileLoc']) + ' ' + name_cmd + ' --bids_dir ' + os.path.join(Data2Import.dirname, 'temp_bids') + ' --bids_format vhdr'
        elif isinstance(self, GlobalSidecars):
            fname = filename + os.path.splitext(self['fileLoc'])[1]
            os.makedirs(os.path.join(BidsDataset.dirname, dirname), exist_ok=True)
            shutil.move(os.path.join(Data2Import.dirname, self['fileLoc']), os.path.join(
                BidsDataset.dirname, dirname, fname))
            return [fname]
        elif isinstance(self, Process):
            name, ext = os.path.splitext(self['fileLoc'])
            #Aude: To modify
            if ext=='.pial':
                #import pdb; pdb.set_trace()
                conv_ext = ['.pial', '.surf.gii']
                old_name = os.path.join(Data2Import.dirname, self['fileLoc'])
                new_path = os.path.join(Data2Import.dirname, 'temp_bids')
                os.makedirs(os.path.join(dest_change, dirname), exist_ok=True)
                [coord, face] = nibabel.freesurfer.io.read_geometry(old_name)
                coord_array = nibabel.gifti.GiftiDataArray(data=coord, intent=nibabel.nifti1.intent_codes['NIFTI_INTENT_POINTSET'], encoding='GIFTI_ENCODING_ASCII')                                           
                face_array = nibabel.gifti.GiftiDataArray(data=face, intent=nibabel.nifti1.intent_codes['NIFTI_INTENT_TRIANGLE'], encoding='GIFTI_ENCODING_ASCII')                                            
                gii = nibabel.gifti.GiftiImage(darrays=[coord_array, face_array])                                                                                              
                nibabel.save(gii, os.path.join(new_path, filename + '.surf.gii'))
                shutil.copy(old_name, os.path.join(new_path, filename + '.pial'))
                Nifti=True                 
            else:
                fname = filename + ext
                os.makedirs(os.path.join(dest_change, dirname), exist_ok=True)
                shutil.copy(os.path.join(Data2Import.dirname, self['fileLoc']), os.path.join(dest_change, dirname, fname))
                return [fname]
        else:
            str_issue = os.path.basename(self['fileLoc']) + ' cannot be converted!'
            self.write_log(str_issue)
            raise TypeError(str_issue)

        #To take into account the Nifti file
        if Nifti == 'False':
            os.system(cmd_line)
        list_filename = [filename + ext for ext in conv_ext]
        self.get_sidecar_files(in_bids_dir=False, input_dirname=os.path.join(Data2Import.dirname, 'temp_bids'),
                               input_filename=filename)
        os.makedirs(os.path.join(BidsDataset.dirname, dirname), exist_ok=True)
        if dest_change:
            os.makedirs(os.path.join(dest_change, dirname), exist_ok=True)
        for fname in list_filename:
            if os.path.exists(os.path.join(Data2Import.dirname, 'temp_bids', fname)):
                if dest_change:
                    shutil.move(os.path.join(Data2Import.dirname, 'temp_bids', fname),
                                os.path.join(dest_change, dirname, fname))
                else:
                    shutil.move(os.path.join(Data2Import.dirname, 'temp_bids', fname),
								os.path.join(BidsDataset.dirname, dirname, fname))

        return list_filename

    def is_empty(self):
        if isinstance(self, MetaBrick):
            for sub in self['Subject']:
                if not sub.is_empty():
                    return False
            return True
        else:
            if isinstance(self, GlobalSidecars):
                init_inst = type(self)(self['fileLoc'])
            else:
                init_inst = type(self)()
            return self == init_inst

    def difference(self, brick2compare, reverse=False):
        """ different compare two BidsBricks from the same type and returns a dictionary of the key and values of the
        brick2compare that are different from self. /!\ this operation is NOT commutative"""
        if type(self) is type(brick2compare) or (isinstance(brick2compare, dict) and
                                                 not isinstance(brick2compare, (BidsBrick, BidsSidecar))):
            if reverse:
                return {key: brick2compare[key] for key in brick2compare if key not in self or
                        not self[key] == brick2compare[key]}
            else:
                return {key: brick2compare[key] for key in self if key not in brick2compare or
                        not self[key] == brick2compare[key]}
        else:
            err_str = 'The type of the two instance to compare are different (' + self.classname() + ', '\
                      + type(brick2compare).__name__ + ')'
            self.write_log(err_str)
            raise TypeError(err_str)

    def write_command(self, brick2compare, added_info=None):
        if added_info and not isinstance(added_info, dict):
            print('added_info should be a dict. Set to None.')
            added_info = None
        diff = self.difference(brick2compare)
        cmd_str = ', '.join([str(k + '="' + diff[k] + '"') for k in diff])
        if added_info:
            cmd_str += ',' + ', '.join([str(k + '="' + str(added_info[k]) + '"') for k in added_info])
        return cmd_str

    def fileparts(self):
        if isinstance(self, ModalityType) and self['fileLoc']:
            filename, ext = os.path.splitext(os.path.basename(self['fileLoc']))
            dirname = os.path.dirname(self['fileLoc'])
            return dirname, filename, ext
        else:
            return None, None, None

    @classmethod
    def clear_log(cls):
        if cls == BidsDataset or cls == Data2Import:
            cls.curr_log = ''

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        #Duplicate suppresion in the list
        #sub_classes_names = list(set(sub_classes_names))
        return sub_classes_names

    @staticmethod
    def write_log(str2write):

        if BidsDataset.dirname:
            main_dir = BidsDataset.dirname
        elif Data2Import.dirname:
            main_dir = Data2Import.dirname
        else:
            main_dir = BidsBrick.cwdir

        log_path = os.path.join(main_dir, 'derivatives', 'log')
        log_filename = 'bids_' + BidsBrick.access_time.strftime(BidsBrick.time_format) + '.log'
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        if not os.path.isfile(os.path.join(log_path, log_filename)):
            cmd = 'w'
            str2write = 10*'=' + '\n' + 'Current User: ' + BidsBrick.curr_user + '\n' + \
                        BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S") + '\n' + 10*'=' + '\n' + str2write
        else:
            cmd = 'a'
        with open(os.path.join(log_path, log_filename), cmd) as file:
            file.write(str2write + '\n')
            BidsDataset.curr_log += str2write + '\n'
            Data2Import.curr_log += str2write + '\n'
        print(str2write)
        if BidsDataset.update_text:
            BidsDataset.update_text(str2write, delete_flag=False)


class BidsSidecar(object):
    bids_default_unknown = 'n/a'
    extension = ''
    inheritance = True
    modality_field = []
    allowed_modalities = []
    keylist = []
    required_keys = []

    def __init__(self, modality_field=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        self.is_complete = False
        if not modality_field:
            self.modality_field = self.__class__.modality_field
        else:
            self.modality_field = modality_field

    def read_file(self, filename):
        """read sidecar file and store in self according to its class (BidsJSON, BidsTSV, BidsFreeFile)"""
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
                        self.header = tsv_header
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
                raise TypeError('Not readable class input ' + self.classname() + '.')

    def simplify_sidecar(self, required_only=True):
        """remove fields that have 'n/a' and are not required or if required_only=True keep only required fields."""
        if isinstance(self, BidsJSON):
            list_key2del = []
            for key in self:
                if (self[key] == BidsJSON.bids_default_unknown and key not in self.required_keys) or \
                        (required_only and key not in self.required_keys):
                    list_key2del.append(key)
            for key in list_key2del:
                del(self[key])

    def copy_values(self, sidecar_elmt, simplify_flag=True):
        if isinstance(self, BidsJSON):
            # attr_dict = {key: sidecar_elmt[key] for key in sidecar_elmt.keys() if (key in self.keylist
            #              and self[key] == BidsSidecar.bids_default_unknown) or key not in self.keylist}
            # change into this otherwise cannot modify dataset_description.json (to test)
            attr_dict = {key: sidecar_elmt[key] for key in sidecar_elmt.keys() if sidecar_elmt[key]}
            for key in attr_dict.keys():
                if attr_dict[key] == 'n/a' and key in self.keys():
                    attr_dict[key] = self[key]
            self.update(attr_dict)
        elif isinstance(self, BidsTSV) and isinstance(sidecar_elmt, list):
            if sidecar_elmt and len([word for word in sidecar_elmt[0] if word in self.required_fields]) >= \
                    len(self.required_fields):
                self.header = sidecar_elmt[0]
                #Add to take into account the header for the first													   
                #if isinstance(self, ParticipantsTSV):
                #    self[:] = []
                for line in sidecar_elmt[1:]:
                    #import pdb; pdb.set_trace()
                    self.append({sidecar_elmt[0][cnt]: val for cnt, val in enumerate(line)})
        elif isinstance(self, BidsFreeFile):
            if not isinstance(sidecar_elmt, list):
                sidecar_elmt = [sidecar_elmt]
            for line in sidecar_elmt:
                self.append(line)
        if simplify_flag:
            self.simplify_sidecar(required_only=False)

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        self.is_complete = True
        missing_elements = ''
        if 'required_keys' in dir(self) and self.required_keys:
            for key in self.required_keys:
                if key not in self or self[key] == BidsSidecar.bids_default_unknown:
                    missing_elements += 'In ' + type(self).__name__ + ', key ' + str(key) + ' is missing.\n'
        self.is_complete = not bool(missing_elements)
        return [self.is_complete, missing_elements]

    def classname(self):
        return self.__class__.__name__

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
            for line in self:
                file.write(line + '\n')


class BidsJSON(BidsSidecar, dict):

    extension = '.json'
    modality_field = ''
    keylist = []

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

    def difference(self, brick2compare):
        """ different compare two BidsBricks from the same type and returns a dictionary of the key and values of the
        brick2compare that are different from self. /!\ this operation is NOT commutative"""
        if type(self) is type(brick2compare):
            return {key: brick2compare[key] for key in self if key in brick2compare and
                    not self[key] == brick2compare[key]}
        else:
            err_str = 'The type of the two instance to compare are different (' + self.classname() + ', '\
                      + type(brick2compare).__name__ + ')'
            self.write_log(err_str)
            raise TypeError(err_str)

    def write_command(self, brick2compare, added_info=None):
        if added_info and not isinstance(added_info, dict):
            print('added_info should be a dict. Set to None.')
            added_info = None
        diff = self.difference(brick2compare)
        cmd_list = []
        for k in diff:
            if isinstance(diff[k], str):
                cmd_list.append(str(k + '="' + diff[k] + '"'))
            else:
                cmd_list.append(str(k + '=' + str(diff[k])))
        cmd_str = ', '.join(cmd_list)
        if added_info:
            cmd_str += ',' + ', '.join([str(k + '="' + str(added_info[k]) + '"') for k in added_info])
        return cmd_str

    def write_file(self, jsonfilename):
        if os.path.splitext(jsonfilename)[1] == '.json':
            with open(jsonfilename, 'w') as f:
                # json.dump(self, f, indent=2, separators=(',', ': '), ensure_ascii=False)
                json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
                f.write(json_str)
        else:
            raise TypeError('File ' + jsonfilename + ' is not ".json".')


class ModalityType(BidsBrick):
    required_keys = BidsBrick.required_keys + ['fileLoc']


class Imagery(ModalityType):
    pass


class Process(ModalityType):
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'hemi', 'modality', 'fileLoc', 'ProcessJSON']
    required_keys = ModalityType.required_keys 
    allowed_file_formats = ['.tsv', '.txt', '.mat', '.nii', '.pial', '.gii']

    def __init__(self):
        super().__init__()


class ProcessJSON(BidsJSON):
    keylist = []
    required_keys = ['Description', 'Sources', 'User', 'Date']
    detrending_keys = ['Detendring']
    filter_keys = ['FilterType', 'HighCutoff', 'LowCutoff', 'HighCutoffDefinition', 'LowCutoffDefinition', 'FilterOrder', 'Direction', 'DirectionDescription']
    downsample_keys = ['SamplingFrequency', 'IsDownsampled']

    def __init__(self, flagfilter=False, flagdown=False, flagdetendring=False, modality_field=None):
        self.keylist = self.required_keys
        if flagfilter:
            self.keylist = self.keylist + self.filter_keys
        if flagdown:
            self.keylist = self.keylist + self.downsample_keys
        if flagdetendring:
            self.keylist = self.keylist + self.detrending_keys
        super().__init__(keylist=self.keylist, modality_field=modality_field)

class Electrophy(ModalityType):
    channel_type = ['ECG', 'EOG', 'EEG', 'SEEG', 'ECOG', 'MEG', 'OTHER']


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
        return [self.is_complete, '']

    def clear(self):
        super().clear()
        self.append({elmt: elmt for elmt in self.header})

    def __str__(self):
        str2print = super().__str__()
        str2print = str2print.replace('], [', '],\n[')
        return str2print

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


class ChannelsTSV(BidsTSV):
    """Store the info of the #_channels.tsv, listing amplifier metadata such as channel names, types, sampling
    frequency, and other information. Note that this may include non-electrode channels such as trigger channels."""

    header = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference', 'group',
              'description', 'status', 'status_description', 'software_filters']
    required_fields = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference']
    modality_field = 'channels'


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
            self['modality'] = getattr(modules[__name__], comp_key[0]).modality_field
            self['fileLoc'] = filename + ext
        # elif ext in self.allowed_file_formats and filename.split('_')[-1] == 'photo':
        else:
            photo_key = [value for value in self.complementary_keylist if value in
                         BidsBrick.get_list_subclasses_names()][0]
            if ext.lower() in eval(photo_key + '.allowed_file_formats'):
                super().__init__(keylist=eval(photo_key + '.keylist'), required_keys=eval(photo_key + '.required_keys'))
                self['modality'] = 'photo'
                self['fileLoc'] = filename + ext
            else:
                err_str = 'Not recognise file type for ' + self.classname() + '.'
                self.write_log(err_str)
                raise TypeError(err_str)


class Photo(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'acq', 'modality', 'fileLoc']
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.pdf', '.ppt', '.pptx']
    readable_file_format = allowed_file_formats
    modality_field = 'photo'

    def __init__(self):
        BidsBrick().__init__()
        self['modality'] = self.__class__.modality_field


''' A special class for setting the requirements of a given BIDS dataset '''


class Requirements(BidsBrick):
    keywords = ['_ready', '_integrity']

    def __init__(self, full_filename):

        if full_filename:
            self['Requirements'] = dict()
            with open(full_filename, 'r') as file:
                json_dict = json.load(file)
                if 'Requirements' in json_dict.keys():
                    self['Requirements'] = json_dict['Requirements']
                if 'Readers' in json_dict.keys():
                    BidsDataset.readers = json_dict['Readers']
                    self['Readers'] = json_dict['Readers']
                if 'Converters' in json_dict.keys():
                    BidsDataset.converters = json_dict['Converters']
                    self['Converters'] = json_dict['Converters']

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def update(self, input_dict, f=None):
        dict.update(input_dict, f=None)

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):
        savedir = os.path.join(BidsDataset.dirname, 'code')
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        super().save_as_json(savedir, file_start=None, write_date=False, compress=False)


''' The different modality bricks, subclasses of BidsBrick. '''

""" iEEG brick with its file-specific (IeegJSON, IeegChannelsTSV) and global sidecar 
(IeegCoordSysJSON, IeegElecTSV or IeegPhoto) files. """


'''class IeegAnalyzed(Process):

    allowed_file_formats = ['.tsv', '.txt']

    def __init__(self):
        super().__init__()
        self['modality'] ='ieeg'''


class Ieeg(Electrophy):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'IeegJSON',
                                   'IeegChannelsTSV', 'IeegEventsTSV']
    required_keys = Electrophy.required_keys + ['task', 'modality']
    allowed_modalities = ['ieeg']
    allowed_file_formats = ['.edf', '.gdf', '.fif', '.vhdr']
    readable_file_formats = allowed_file_formats + ['.eeg', '.trc']
    channel_type = ['SEEG', 'ECOG']

    def __init__(self):
        super().__init__()
        self['modality'] = 'ieeg'


class IeegJSON(BidsJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDate', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication', 'iEEGReference', 'SamplingFrequency', 'SoftwareFilters']
    required_keys = ['TaskName', 'iEEGReference', 'SamplingFrequency', 'PowerLineFrequency', 'SoftwareFilters']


class IeegChannelsTSV(ChannelsTSV):
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
    allowed_modalities = [eval(elmt).modality_field for elmt in complementary_keylist]


""" Anat brick with its file-specific sidecar files."""


class Anat(Imagery):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'modality', 'fileLoc', 'AnatJSON']
    required_keys = Imagery.required_keys + ['modality']
    allowed_modalities = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'PD', 'Pdmap', 'PDT2', 'inplaneT1'
                          , 'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']

    def __init__(self):
        super().__init__()


class AnatJSON(ImageryJSON):
    keylist = ImageryJSON.keylist + ['ContrastBolusIngredient', 'NiftiDescription']


""" Func brick with its file-specific sidecar files. """


class Func(Imagery):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'modality', 'fileLoc', 'FuncJSON',
                                   'FuncEventsTSV']
    required_keys = Imagery.required_keys + ['task', 'modality']
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
    required_keys = Imagery.required_keys + ['modality']
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
    required_keys = Imagery.required_keys + ['modality']
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
    required_keys = Imagery.required_keys + ['task', 'modality']
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
    required_keys = ModalityType.required_keys + ['task', 'modality']
    allowed_modalities = ['beh']
    allowed_file_formats = ['.tsv']
    readable_file_formats = allowed_file_formats

    def __init__(self):
        super().__init__()
        self['modality'] = 'beh'


class BehEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass

class Scans(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'fileLoc', 'ScansTSV']

    def add_modality(self, mod_dict, mod_type, bids_dir):
        #import pdb; pdb.set_trace()
        scan_name = os.path.join(mod_type.lower(), os.path.basename(mod_dict['fileLoc']))
        if not self['ScansTSV']:
            self['ScansTSV'] = ScansTSV()
        self['sub'] = mod_dict['sub']
        self['ses'] = mod_dict['ses']
        '''if mod_dict[mod_dict.classname()+'JSON']['RecordingISODate']:
            scan_time = mod_dict[mod_type + 'JSON']['RecordingISODate']
        elif mod_dict[mod_type+'JSON']['AcquisitionTime']:
            scan_time = '1900-01-01T'+ mod_dict[mod_dict.classname()+'JSON']['AcquisitionTime']'''
        if bids_dir['DatasetDescJSON']['Name'] == 'FTract' and mod_type=='Anat':
            ind_pre = bids_dir['ParticipantsTSV'][0].index('pre_iEEG_date')
            ind_post = bids_dir['ParticipantsTSV'][0].index('post_resection_MRI_date')
            for elt in bids_dir['ParticipantsTSV']:
               if self['sub'] in elt:
                   indeP = bids_dir['ParticipantsTSV'].index(elt)
            if self['ses'].startswith('pre'):
                scan_time = bids_dir['ParticipantsTSV'][indeP][ind_pre]
            elif self['ses'].startswith('post'):
                scan_time = bids_dir['ParticipantsTSV'][indeP][ind_post]
        else:
            scan_time = '1900-01-01T00:00:00'							 
        self['ScansTSV'].append({'filename': scan_name, 'acq_time': scan_time})

    def write_file(self):
        dirname_ses = os.path.join(BidsDataset.dirname, 'sub-'+self['sub'], 'ses-'+self['ses'])
        file_ses = 'sub-' + self['sub'] + '_ses-' + self['ses'] +'_scans.tsv'
        self['ScansTSV'].write_file(os.path.join(dirname_ses, file_ses))
        self['fileLoc'] = os.path.join(dirname_ses, file_ses)

    def compare_scanstsv(self, tmpScan):
        ls = [x[0] for x in self['ScansTSV']]
        ltemp = [y[0] for y in tmpScan]
        index_list = [[ls.index(elt), ltemp.index(elt)] for elt in ls if elt in ltemp]
        for i in index_list:
            if not tmpScan[i[1]][1] == 'acq_time':
                self['ScansTSV'][i[0]][1] = tmpScan[i[1]][1]

''' Higher level bricks '''


class Subject(BidsBrick):

    keylist = BidsBrick.keylist + ['Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg',
                                   'Beh', 'IeegGlobalSidecars', 'Scans']
    required_keys = BidsBrick.required_keys

    def __setitem__(self, key, value):
        if value and key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
            if value['sub'] and self['sub'] and not value['sub'] == self['sub']:
                err_str = value['fileLoc'] + ' cannot be added to ' + self['sub'] + ' since sub: ' + value['sub']
                self.write_log(err_str)
                raise KeyError(err_str)
        super().__setitem__(key, value)
        # if Subject 'sub' attribut changes than it changes all 'sub' of its Modality and globalsidecar objects
        '''if key == 'sub' and value:
            for subkey in self:
                if subkey in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                    if self[subkey]:
                        for modalityy in self[subkey]:
                            modalityy['sub'] = self['sub']'''

    def get_attr_tsv(self, parttsv):
        if isinstance(parttsv, ParticipantsTSV):
            bln, sub_dict, sub_idx = parttsv.is_subject_present(self['sub'])
            if bln:
                sub_dict = {key: sub_dict[key] for key in parttsv.header if key in self.keylist}
                self.copy_values(sub_dict)

    def is_empty(self):
        for key in self:
            if key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names() \
                    and self[key]:
                return False
        return True

    def check_file_in_scans(self, filename, mod_dir):
        scan_present=False
        ses_present =False
        name_pieces = filename.split('_')
        for word in name_pieces:
            w = word.split('-')
            if len(w) == 2 and w[0] == 'ses':
                ses_label = w[1]
            elif len(w) == 2 and w[0] == 'sub':
                sub_label = w[1]

						  
        for elt in self['Scans']:
            if elt['ses'] == ses_label:
                ses_present=True
                idx = self['Scans'].index(elt)
                for scans in self['Scans'][idx]['ScansTSV']:
                    scan_name = os.path.basename(scans[0])
                    if scan_name == filename:
                        scan_present = True
                if not scan_present:
                    self['Scans'][idx]['ScansTSV'].append({'filename': os.path.join(mod_dir.lower(), filename), 'acq_time': '1900-01-01T00:00:00'})

        if not ses_present:
            self['Scans'] = eval('Scans()')
            self['Scans'][-1]['sub'] = sub_label
            self['Scans'][-1]['ses'] = ses_label
            self['Scans'][-1]['ScansTSV'] = eval('ScansTSV()')
            self['Scans'][-1]['ScansTSV'].append({'filename': os.path.join(mod_dir.lower(), filename), 'acq_time': '1900-01-01T00:00:00'})



class SubjectProcess(Subject):

    keyprocess = [key + 'Process' for key in Subject.keylist if key in ModalityType.get_list_subclasses_names()]
    keylist = BidsBrick.keylist + keyprocess
    required_keys = BidsBrick.required_keys

    def __init__(self):
        for key in self.keylist:
            if key in self.keyprocess:
                self[key] = []
            else:
                self[key] = ''

    def __setitem__(self, key, value):
        if key in self.keyprocess:
            if value and isinstance(value, Process):
                # check whether the value is from the correct class when not empty
                self[key].append(value)
            else:
                dict.__setitem__(self, key, [])
        else:
            super().__setitem__(key, value)


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
    bids_version = '1.2.0'

    def __init__(self):
        super().__init__()
        self['BIDSVersion'] = self.bids_version

    def __setitem__(self, key, value):
        if key == 'Authors':
            value = self.check_authors_value(value)
        super().__setitem__(key, value)

    def write_file(self, jsonfilename=None):
        if not jsonfilename:
            jsonfilename = os.path.join(BidsDataset.dirname, DatasetDescJSON.filename)
        super().write_file(jsonfilename)

    def read_file(self, jsonfilename=None):
        if not jsonfilename:
            jsonfilename = os.path.join(BidsDataset.dirname, DatasetDescJSON.filename)
        super().read_file(jsonfilename)

    def copy_values(self, sidecar_elmt, simplify_flag=True):
        super().copy_values(sidecar_elmt, simplify_flag=simplify_flag)
        if 'Authors' in self.keys():
            self['Authors'] = self.check_authors_value(self['Authors'])

    @staticmethod
    def check_authors_value(value):
        if value.__class__.__name__ in ['str', 'unicode']:
            value = value.split(', ')
        elif isinstance(value, list):
            pass
        else:
            err_str = 'Authors key in dataset_description.json only allows string of comma separated authors,' \
                      ' ex: "John Doe, Jane Doe"'
            raise TypeError(err_str)
        return value


''' TSV bricks '''


class SrcDataTrack(BidsTSV):
    header = ['orig_filename', 'bids_filename', 'upload_date']
    required_fields = ['orig_filename', 'bids_filename', 'upload_date']
    filename = 'source_data_trace.tsv'

    def write_file(self, tsv_full_filename=None):
        if not os.path.exists(os.path.join(BidsDataset.dirname, 'sourcedata')):
            os.makedirs(os.path.join(BidsDataset.dirname, 'sourcedata'))
        tsv_full_filename = os.path.join(BidsDataset.dirname, 'sourcedata', SrcDataTrack.filename)
        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.dirname, 'sourcedata', SrcDataTrack.filename)
        super().read_file(tsv_full_filename)

    def get_source_from_raw_filename(self, filename):
        filename, ext = os.path.splitext(os.path.basename(filename).replace('.gz', ''))

        bids_fname_idx = self.header.index('bids_filename')
        orig_fname_idx = self.header.index('orig_filename')
        orig_fname = None
        idx = None
        for line in self[1:]:
            if filename in line[bids_fname_idx]:
                orig_fname = line[orig_fname_idx]
                idx = self.index(line)
                break
        # orig_fname = [line[orig_fname_idx] for line in self[1:] if filename in line[bids_fname_idx]]
        # if orig_fname:
        #     orig_fname = orig_fname[0]

        return orig_fname, filename, idx


class ParticipantsTSV(BidsTSV):
    header = ['participant_id']
    required_fields = ['participant_id']
    filename = 'participants.tsv'

    def __init__(self):
        super().__init__()

    def write_file(self, tsv_full_filename=None):
        if not tsv_full_filename:
            tsv_full_filename = os.path.join(BidsDataset.dirname, ParticipantsTSV.filename)

        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        if not tsv_full_filename:
            tsv_full_filename = os.path.join(BidsDataset.dirname, ParticipantsTSV.filename)
        super().read_file(tsv_full_filename)

    def is_subject_present(self, sub_id):
        participant_idx = self.header.index('participant_id')
        sub_line = [line for line in self[1:] if sub_id in line[participant_idx]]
        sub_idx = None
        sub_info = {}
        if sub_line:
            sub_idx = self.index(sub_line[0])
            sub_info = {self.header[cnt]: val for cnt, val in enumerate(sub_line[0])}
            sub_info['sub'] = sub_info['participant_id']
            del(sub_info['participant_id'])

        return bool(sub_info), sub_info, sub_idx

    def add_subject(self, sub_dict):
        if isinstance(sub_dict, Subject):
            if not self.is_subject_present(sub_dict['sub'])[0]:
                tmp_dict = sub_dict.get_attributes()
                tmp_dict['participant_id'] = tmp_dict['sub']
                tmp_dict['upload_date'] = BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S")
                if 'alias' in self.header and 'alias' in tmp_dict:
                    tmp_dict['alias'] = self.createalias(sub_dict['sub'])
                self.append(tmp_dict)


class ScansTSV(BidsTSV):
    header = ['filename', 'acq_time']
    required_fields = ['filename']


class MetaBrick(BidsBrick):
    curr_subject = {}
    curr_pipeline = {}
    dirname = None

    def is_subject_present(self, subject_label, flagProcess=False):
        """
        Method that look if a given subject is in the current dataset. It returns a tuple composed
        of a boolean, an integer. The boolean is True if the sub is present, the integer gives its indices in the
        subject list of the dataset.
        Ex: bids.is_subject_present('05') ->
        self.curr_subject = {'Subject': Suject(), 'isPresent': boolean, 'index': integer}
        """
        if flagProcess:
            self.curr_subject = {'SubjectProcess': SubjectProcess(), 'isPresent': False, 'index': None}
            sub_list = [sub['sub'] for sub in self['SubjectProcess']]
            if subject_label in sub_list:
                index = sub_list.index(subject_label)
                self.curr_subject['SubjectProcess'] = self['SubjectProcess'][index]
                self.curr_subject.update({'isPresent': True, 'index': index})
        else:
            self.curr_subject = {'Subject': Subject(), 'isPresent': False, 'index': None}
            sub_list = self.get_subject_list()
            if subject_label in sub_list:
                index = sub_list.index(subject_label)
                self.curr_subject['Subject'] = self['Subject'][index]
                self.curr_subject.update({'isPresent': True, 'index': index})

    def is_pipeline_present(self, pipeline):
        flagPipeline = False
        if isinstance(self, Pipeline):
            flagPipeline=True
        if not flagPipeline:
            self.curr_pipeline = {'Pipeline': Pipeline(), 'isPresent': False, 'index': None}
            pip_list = self.get_derpip_list()
            pipeline_label = pipeline['name']
            pipeline_subject = pipeline['SubjectProcess']
            if pipeline_label in pip_list:
                indexPip = pip_list.index(pipeline_label)
                self.curr_pipeline['Pipeline'] = self['Derivatives'][-1]['Pipeline'][indexPip]
                self.curr_pipeline.update({'isPresent': True, 'index': indexPip})
                #Add the subject of the pipeline in the self
                '''for sub in pipeline_subject:
                    sub_present = False
                    #Ajouter un index pour trouver le sujet et verifier sa présence car bcp de sujet et pas toujours -1
                    for sub_pip in self['Derivatives'][-1]['Pipeline'][indexPip]['SubjectProcess']:
                        if sub['sub'] == sub_pip['sub']:
                            sub_pip.update(sub.get_attributes())
                            sub_present = True
                        #Doit manquer un else pour modifier si présent
                    if not sub_present:
                        #self['Derivatives'][-1]['Pipeline'][indexPip]['Subject'][-1] = Subject()
                        self['Derivatives'][-1]['Pipeline'][indexPip]['SubjectProcess'].append(SubjectProcess())
                        self['Derivatives'][-1]['Pipeline'][indexPip]['SubjectProcess'][-1].update(sub.get_attributes())'''

    def get_derpip_list(self):
        der_list = list()
        pip_list = list()
        for der in self['Derivatives']:
            der_list.append(der['Pipeline'])
            for pip in der['Pipeline']:
                pip_list.append(pip['name'])
        return pip_list

    def get_subject_list(self):
        return [sub['sub'] for sub in self['Subject']]

    def get_object_from_filename(self, filename, sub_id=None):
        if isinstance(filename, str):
            sub_list = self.get_subject_list()
            if isinstance(self, BidsDataset):
                fname = os.path.splitext(os.path.basename(filename))[0]
                fname_pieces = fname.split('_')
                if 'sub-' in fname_pieces[0]:
                    sub_id = fname_pieces[0].split('-')[1]
                else:
                    error_str = 'Filename ' + filename + ' does not follow bids architecture.'
                    self.write_log(error_str)
                    return
                subclass = [subcls for subcls in Electrophy.__subclasses__() + Imagery.__subclasses__() +
                            GlobalSidecars.__subclasses__() if fname_pieces[-1] in subcls.allowed_modalities]
            else:
                if sub_id in sub_list:
                    sub_list = [sub_id]
                subclass = Electrophy.__subclasses__() + Imagery.__subclasses__() + GlobalSidecars.__subclasses__()
            # if fname_pieces[-1] in [for subclss in ModalityType.get_list_subclasses_names()]
            for sub_id in sub_list:
                self.is_subject_present(sub_id)
                if self.curr_subject['Subject'] and subclass:
                    for subclss in subclass:
                        for mod_elmt in self.curr_subject['Subject'][subclss.__name__]:
                            if os.path.basename(mod_elmt['fileLoc']) == os.path.basename(filename):
                                return mod_elmt
            error_str = 'Subject ' + sub_id + ' filename ' + str(filename) + ' is not found in '\
                        + self.dirname + '.'
        else:
            error_str = 'Filename ' + str(filename) + ' should be a string.'
        self.write_log(error_str)
        return

    def get_requirements(self, reqfiloc=None):

        if isinstance(self, BidsDataset) and BidsDataset.dirname and \
                os.path.exists(os.path.join(BidsDataset.dirname, 'code', 'requirements.json')):
            full_filename = os.path.join(BidsDataset.dirname, 'code', 'requirements.json')
        elif reqfiloc and os.path.exists(reqfiloc):
            full_filename = reqfiloc
        else:
            full_filename = None

        if isinstance(self, BidsDataset):
            self.requirements = Requirements(full_filename)
            BidsDataset.requirements = self.requirements
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
                        Subject.required_keys += [elmt for elmt in self.requirements['Requirements']['Subject']['keys']
                                                  if elmt not in Subject.required_keys
                                                  and elmt not in ['alias', 'upload_date']]
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
        elif isinstance(self, Data2Import):
            self.requirements = Requirements(full_filename)
            if 'Requirements' in self.requirements.keys() and 'Subject' in self.requirements['Requirements'].keys():
                for key in self.requirements['Requirements']['Subject']:
                    if key == 'keys':
                        Subject.keylist += [elmt for elmt in self.requirements['Requirements']['Subject'][key]
                                            if elmt not in Subject.keylist]
                        Subject.required_keys += [elmt for elmt in self.requirements['Requirements']['Subject'][key]
                                                  if elmt not in Subject.required_keys
                                                  and elmt not in ['alias', 'upload_date']]


''' BIDS brick which contains all the information about the data to be imported '''


class Data2Import(MetaBrick):
    #Add Derivatives in keylist
    keylist = ['Subject', 'Derivatives', 'DatasetDescJSON', 'UploadDate']
    filename = 'data2import.json'
    requirements = None
    curr_log = ''

    def __init__(self, data2import_dir=None, requirements_fileloc=None):
        """initiate a  dict var for Subject info"""
        self.__class__.clear_log()
        super().__init__()
        self.dirname = data2import_dir
        self.get_requirements(requirements_fileloc)
        if data2import_dir is None:
            return
        if os.path.isdir(data2import_dir):
            self._assign_import_dir(data2import_dir)
            # self.requirements = None
            if os.path.isfile(os.path.join(self.dirname, 'temp_bids', Data2Import.filename)):
                with open(os.path.join(self.dirname, 'temp_bids', Data2Import.filename)) as file:
                    inter_dict = json.load(file)
                    self.copy_values(inter_dict)
                    # self.write_log('Importation procedure ready!')
            else:
                self['UploadDate'] = datetime.now().strftime(self.time_format)
        else:
            str_error = data2import_dir + ' is not a directory.'
            self.write_log(str_error)
            raise NotADirectoryError(str_error)

    def save_as_json(self, savedir=None, file_start=None, write_date=False, compress=False):
        if savedir==None:
            savedir = self.dirname
        super().save_as_json(savedir=savedir, file_start=None, write_date=write_date, compress=False)

    @classmethod
    def _assign_import_dir(cls, data2import_dir):
        cls.dirname = data2import_dir
        BidsBrick.cwdir = data2import_dir


class SourceData(MetaBrick):
    keylist = ['Subject', 'SrcDataTrack']
    dirname = 'sourcedata'


''' Main BIDS brick which contains all the information concerning the patients and the sidecars. It permits to parse a 
given bids dataset, request information (e.g. is a given subject is present, has a given subject a given modality), 
import new data or export a subset of the current dataset (not yet implemented ) '''


class BidsDataset(MetaBrick):

    keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDescJSON', 'ParticipantsTSV']
    requirements = dict()
    curr_log = ''
    readers = dict()
    converters = {'Imagery': {'ext': ['.nii'], 'path': ''}, 'Electrophy': {'ext': ['.vhdr'], 'path': ''}}
    parsing_path = os.path.join('derivatives', 'parsing')
    log_path = os.path.join('derivatives', 'log')
    update_text = None

    def __init__(self, bids_dir, update_text=None):
        """initiate a  dict var for patient info"""
        self.__class__.clear_log()
        if update_text:
            self.__class__.update_text = update_text
        super().__init__()
        self.dirname = bids_dir
        self._assign_bids_dir(bids_dir)
        self.curr_subject = {}
        self.issues = Issue()
        self.access = Access()
        self.access['user'] = self.curr_user
        self.access['access_time'] = self.access_time.strftime("%Y-%m-%dT%H:%M:%S")
        self.requirements = BidsDataset.requirements
        # check if there is a parsing file in the derivatives and load it as the current dataset state
        flag = self.check_latest_parsing_file()
        if flag:
            self.parse_bids()
        if self.update_text:
            self.update_text(self.curr_log, delete_flag=False)

    def get_all_logs(self):
        logs = ''
        if os.path.exists(os.path.join(self.dirname, BidsDataset.parsing_path)):
            list_of_files = os.listdir(os.path.join(self.dirname, BidsDataset.log_path))
            list_of_log_files = [os.path.join(self.dirname, BidsDataset.log_path, file)
                                 for file in list_of_files if file.startswith('bids_') and file.endswith('.log')]
            if list_of_log_files:
                list_of_log_files = sorted(list_of_log_files, key=os.path.getctime)
                for log_file in list_of_log_files:
                    with open(log_file, 'r') as file:
                        for line in file:
                            logs += line
        return logs

    def check_latest_parsing_file(self):
        def read_file(filename):
            with gzip.open(filename, 'rb') as f_in, open(filename.replace('.gz', ''), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            with open(filename.replace('.gz', ''), 'r') as file:
                rd_json = json.load(file)
            os.remove(filename.replace('.gz', ''))
            return rd_json

        if os.path.exists(os.path.join(self.dirname, BidsDataset.parsing_path)):
            latest_parsing = latest_file(os.path.join(self.dirname, BidsDataset.parsing_path), 'parsing')
            if latest_parsing:
                BidsBrick.access_time = datetime.now()
                self.__class__.clear_log()
                # self.write_log('Current User: ' + self.curr_user)
                # First read requirements.json which should be in the code folder of bids dir.
                self.get_requirements()
                read_json = read_file(latest_parsing)
                self.copy_values(read_json)
                self.issues.check_with_latest_issue()
                # the latest log file may have been created after the latest parsing file (case of issues removing
                #  which does not affect parsing.json)
                log_file = latest_file(os.path.join(self.dirname, self.log_path), 'log')
                if log_file:
                    with open(log_file, 'r') as file:
                        for line in file:
                            self.__class__.curr_log += line
                    print(self.__class__.curr_log)
                return False  # no need to parse the dataset
        return True  # need to parse the dataset

    def parse_bids(self):

        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None, srcdata=False, flag_process=False):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, srcdata=srcdata, flag_process=flag_process)
                    elif not mod_dir and file.name.capitalize() in ModalityType.get_list_subclasses_names() and \
                            file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.capitalize(),
                                           srcdata=srcdata, flag_process=flag_process)
                    elif not mod_dir and file.name.endswith('_scans.tsv') and file.is_file():
                        tmp_scantsv = ScansTSV()
                        tmp_scantsv.read_file(file)
                        for scan in subinfo['Scans']:
                            scan.compare_scanstsv(tmp_scantsv)
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
                            subinfo.check_file_in_scans(file.name, mod_dir)
                        elif mod_dir + 'GlobalSidecars' in BidsBrick.get_list_subclasses_names() and ext.lower() \
                                in eval(mod_dir + 'GlobalSidecars.allowed_file_formats') and filename.split('_')[-1]\
                                in [eval(value + '.modality_field') for _, value in
                                    enumerate(IeegGlobalSidecars.complementary_keylist)]:
                            subinfo[mod_dir + 'GlobalSidecars'] = eval(mod_dir + 'GlobalSidecars(filename+ext)')
                            subinfo[mod_dir + 'GlobalSidecars'][-1]['fileLoc'] = file.path
                            subinfo[mod_dir + 'GlobalSidecars'][-1].get_attributes_from_filename()
                            subinfo[mod_dir + 'GlobalSidecars'][-1].get_sidecar_files()
                        elif flag_process and ext.lower() in Process.allowed_file_formats:
                            subinfo[mod_dir + 'Process'] = create_subclass_instance(mod_dir + 'Process', Process)
                            subinfo[mod_dir + 'Process'][-1]['fileLoc'] = file.path
                            subinfo[mod_dir + 'Process'][-1].get_attributes_from_filename()
                            subinfo[mod_dir + 'Process'][-1].get_sidecar_files()
                    elif mod_dir and file.is_dir():
                        subinfo[mod_dir] = eval(mod_dir + '()')
                        subinfo[mod_dir][-1]['fileLoc'] = file.path


        def parse_bids_dir(bids_brick, currdir, sourcedata=False, flag_process=False):

            with os.scandir(currdir) as it:
                for entry in it:
                    if entry.name.startswith('sub-') and entry.is_dir():
                        # bids_brick['Subject'] = Subject('derivatives' not in entry.path and 'sourcedata' not in
                        #                                 entry.path)
                        if not flag_process:
                            bids_brick['Subject'] = Subject()
                            bids_brick['Subject'][-1]['sub'] = entry.name.replace('sub-', '')
                            if isinstance(bids_brick, BidsDataset) and bids_brick['ParticipantsTSV']:
                                bids_brick['Subject'][-1].get_attr_tsv(bids_brick['ParticipantsTSV'])
                            parse_sub_bids_dir(entry.path, bids_brick['Subject'][-1], srcdata=sourcedata)
                        else:
                            bids_brick['SubjectProcess'] = SubjectProcess()
                            bids_brick['SubjectProcess'][-1]['sub'] = entry.name.replace('sub-', '')
                            if isinstance(bids_brick, BidsDataset) and bids_brick['ParticipantsTSV']:
                                bids_brick['SubjectProcess'][-1].get_attr_tsv(bids_brick['ParticipantsTSV'])
                            parse_sub_bids_dir(entry.path, bids_brick['SubjectProcess'][-1], srcdata=sourcedata, flag_process=True)
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
                        bids_brick['Pipeline'][-1]['DatasetDescJSON'] = DatasetDescJSON()
                        bids_brick['Pipeline'][-1]['DatasetDescJSON'].read_file(jsonfilename=os.path.join(entry.path, DatasetDescJSON.filename))
                        bids_brick['Pipeline'][-1]['ParticipantsTSV'] = ParticipantsTSV()
                        bids_brick['Pipeline'][-1]['ParticipantsTSV'].read_file(tsv_full_filename=os.path.join(entry.path, ParticipantsTSV.filename))
                        parse_bids_dir(bids_brick['Pipeline'][-1], entry.path, flag_process=True)

        BidsBrick.access_time = datetime.now()
        self.clear()  # clear the bids variable before parsing to avoid rewrite the same things
        self.__class__.clear_log()
        self.issues.clear()  # clear issue to only get the unsolved ones but
        # self.write_log('Current User: ' + self.curr_user + '\n' + BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S"))
        # First read requirements.json which should be in the code folder of bids dir.
        self.get_requirements()

        self['DatasetDescJSON'] = DatasetDescJSON()
        self['DatasetDescJSON'].read_file()
        self['ParticipantsTSV'] = ParticipantsTSV()
        self['ParticipantsTSV'].read_file()

        parse_bids_dir(self, self.dirname)
        self.check_requirements()
        #write the new scans.tsv file
        for sub in self['Subject']:
            for scan in sub['Scans']:
                scan.write_file()
        self.save_as_json()

    def has_subject_modality_type(self, subject_label, modality_type):
        """
        Method that look if a given subject has a given modality type (e.g. Anat, Ieeg). It returns a tuple composed
        of a boolean, an integer and a dict. The boolean is True if the sub has the mod type, the integer gives the
        number of recordings of the modality and the dict returns the number of recordings of each modality
        Ex: (True, 4, {'T1w': 2, 'T2w':2}) = bids.has_subject_modality_type('01', 'Anat')
        """
        modality_type = modality_type.capitalize()
        if modality_type in ModalityType.get_list_subclasses_names():
            if not self.curr_subject or not self.curr_subject['Subject']['sub'] == subject_label:
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

    def get_number_of_session4subject(self, subject_label, flag_process=False):
        str=''
        if not flag_process:
            if not self.curr_subject or not self.curr_subject['Subject']['sub'] == subject_label:
                # check whether the required subject is the current subject otherwise make it the current one
                self.is_subject_present(subject_label)
            bln = self.curr_subject['isPresent']
            sub_index = self.curr_subject['index']
        else:
            if not self.curr_subject or not self.curr_subject['SubjectProcess']['sub'] == subject_label:
                # check whether the required subject is the current subject otherwise make it the current one
                self.is_subject_present(subject_label, flagProcess=True)
            bln = self.curr_subject['isPresent']
            sub_index = self.curr_subject['index']
            str = 'Process'

        if bln:
            ses_list = []
            sub = self['Subject'+str][sub_index]
            #import pdb; pdb.set_trace()
            for mod_type in sub:
                if mod_type in ModalityType.get_list_subclasses_names():
                    mod_list = sub[mod_type]
                    for mod in mod_list:
                        if mod['ses'] and mod['ses'] not in ses_list:
                            # 'ses': '' means no session therefore does not count
                            ses_list.append(mod['ses'])
                elif mod_type in GlobalSidecars.get_list_subclasses_names():
                    mod_list = sub[mod_type]
                    for mod in mod_list:
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
        nb_runs = None
        highest_run = None
        if 'run' in mod_dict_with_attr.keylist:
            mod_type = mod_dict_with_attr.classname()
            if mod_type in ModalityType.get_list_subclasses_names():
                if not self.curr_subject or not self.curr_subject['Subject']['sub'] == mod_dict_with_attr['sub']:
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
                            idx_run = mod_attr.pop('run')
                            if mod_input_attr == mod_attr and idx_run:
                                if nb_runs is None:
                                    nb_runs = 0
                                idx_run = int(idx_run)
                                nb_runs += 1
                                highest_run = max(nb_runs, idx_run)
        return nb_runs, highest_run

    def import_data(self, data2import, keep_sourcedata=True, keep_file_trace=True):

        def push_into_dataset(bids_dst, mod_dict2import, keep_srcdata, keep_ftrack, flag_process=False): #dest_deriv=None, bids_orig=None):
            filename, dirname, ext = mod_dict2import.create_filename_from_attributes()

            fname2import, ext2import = os.path.splitext(mod_dict2import['fileLoc'])
            orig_ext = ext2import
            dest_deriv = None
            # bsname_bids_dir = os.path.basename(bids_dst.dirname)
            sidecar_flag = [value for _, value in enumerate(mod_dict2import.keylist) if value in
                            BidsSidecar.get_list_subclasses_names()]
            mod_type = mod_dict2import.classname()
            if flag_process:
                sub = bids_dst.curr_subject['SubjectProcess']
                dest_deriv = bids_dst.dirname
            else:
                sub = bids_dst.curr_subject['Subject']
            #import pdb; pdb.set_trace()
            fnames_list = mod_dict2import.convert(dest_deriv)
            tmp_attr = mod_dict2import.get_attributes()
            tmp_attr['fileLoc'] = os.path.join(bids_dst.dirname, dirname, fnames_list[0])

            if isinstance(mod_dict2import, GlobalSidecars):
                sub[mod_type] = eval(mod_type + '(tmp_attr["fileLoc"])')
            elif isinstance(mod_dict2import, Process):
                sub[mod_type] = create_subclass_instance(mod_type, Process)
            else:
                sub[mod_type] = eval(mod_type + '()')
            sub[mod_type][-1].update(tmp_attr)

            # To write the scans.tsv
            if not flag_process:
                ses_list = [scan['ses'] for scan in sub['Scans']]
                if tmp_attr['ses'] in ses_list:
                    ses_index = ses_list.index(tmp_attr['ses'])
                    sub['Scans'][ses_index].add_modality(tmp_attr, mod_type, bids_dst)
                else:
                    sub['Scans'].append(Scans())
                    sub['Scans'][-1].add_modality(tmp_attr, mod_type, bids_dst)

            if keep_srcdata and not isinstance(mod_dict2import, GlobalSidecars):
                scr_data_dirname = os.path.join(BidsDataset.dirname, 'sourcedata', dirname)
                os.makedirs(scr_data_dirname, exist_ok=True)
                path_src = os.path.join(Data2Import.dirname, mod_dict2import['fileLoc'])
                path_dst = os.path.join(scr_data_dirname, os.path.basename(mod_dict2import['fileLoc']))
                # if os.path.isdir(path_src):
                #     # use copytree for directories (e.g. DICOM)
                #     shutil.copytree(path_src, path_dst)
                # else:
                #     # use copy2 for files
                #     shutil.copy2(path_src, path_dst)
                shutil.move(path_src, path_dst)
                src_data_sub = bids_dst['SourceData'][-1]['Subject'][bids_dst.curr_subject['index']]
                src_data_sub[mod_type] = eval(mod_type + '()')
                tmp_attr = mod_dict2import.get_attributes()
                tmp_attr['fileLoc'] = path_dst
                src_data_sub[mod_type][-1].update(tmp_attr)

                if keep_ftrack:
                    orig_fname = src_data_sub[mod_type][-1]['fileLoc']
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
                        if flag_process:
                            fname2bewritten = os.path.join(bids_dst.dirname, dirname, fname +
                                                           mod_dict2import[sidecar_tag].extension)
                        else:
                            fname2bewritten = os.path.join(BidsDataset.dirname, dirname, fname +
                                                       mod_dict2import[sidecar_tag].extension)
                        mod_dict2import[sidecar_tag].write_file(fname2bewritten)
                if flag_process:
                    sub[mod_type][-1].get_sidecar_files(input_dirname=bids_dst.dirname, input_filename=fname)
                else:
                    sub[mod_type][-1].get_sidecar_files()

            mod_dict2import.write_log(mod_dict2import['fileLoc'] + ' was imported as ' + filename)

        def have_data_same_source_file(bids_dict, mod_dict):
            flg = False
            if bids_dict['SourceData']:
                src_dict = bids_dict['SourceData'][-1]
                input_basefname = os.path.basename(mod_dict['fileLoc'])
                if src_dict['SrcDataTrack']:
                    for line in src_dict['SrcDataTrack'][1:]:
                        word_grp = line[1].split('_')
                        sub_id = word_grp[0].split('-')[1]
                        flg = line[0] == input_basefname and sub_id == mod_dict['sub']
                        if flg and 'ses' in word_grp[1]:
                            ses_id = word_grp[1].split('-')[1]
                            flg = flg and ses_id == mod_dict['ses']
                        if flg:
                            break
                else:
                    src_dict.is_subject_present(mod_dict['sub'])
                    src_sub = src_dict.curr_subject['Subject']
                    flg = any(os.path.basename(mod_brick['fileLoc']) == input_basefname
                              for mod_brick in src_sub[mod_dict.classname()])
            return flg

        def have_data_same_attrs_and_sidecars(bids_dst, mod_dict2import, sub_idx, flag_process=False):
            """
            Method that compares whether a given modality dict is the same as the ones present in the bids dataset.
            Ex: True = bids.have_data_same_attrs_and_sidecars(instance of Anat())
            """
            if flag_process:
                bids_mod_list = bids_dst['SubjectProcess'][sub_idx][mod_dict2import.classname()]
            else:
                bids_mod_list = bids_dst['Subject'][sub_idx][mod_dict2import.classname()]
            mod_dict2import_attr = mod_dict2import.get_attributes('fileLoc')
            for mod in bids_mod_list:
                mod_in_bids_attr = mod.get_attributes('fileLoc')
                if mod_dict2import_attr == mod_in_bids_attr:  # check if both mod dict have same attributes
                    # if 'run' in mod_dict2import_attr.keys() and mod_dict2import_attr['run']:
                    #     # if run if a key check the JSON and possibly increment the run integer of mod_
                    #     # dict2import to import it
                    #     mod_dict2import_dep = mod_dict2import.extract_sidecares_from_sourcedata()
                    #     highest_run = bids_dst.get_number_of_runs(mod_dict2import)[1]
                    #     mod_in_bids_dep = mod.get_modality_sidecars()
                    #     if not mod_dict2import_dep == mod_in_bids_dep:
                    #         # check the sidecar files to verify whether they are the same data, in that the case
                    #         # add current nb_runs to 'run' if available otherwise do not import
                    #         mod_dict2import['run'] = str(1 + highest_run).zfill(2)
                    #         return False
                    return True
            return False

        # if True:
        self.__class__.clear_log()
        self.write_log(10*'=' + '\nImport of ' + data2import.dirname + '\n' + 10*'=')
        if not isinstance(data2import, Data2Import) or not data2import.has_all_req_attributes()[0]:
            flag, missing_str = data2import.has_all_req_attributes()
            self.write_log(missing_str)
            return

        if not self.verif_upload_issues(data2import.dirname):
            error_str = 'Some elements in ' + data2import.dirname + ' have not been verified.'
            self.write_log(error_str)
            return

        if not BidsDataset.converters['Electrophy']['path'] or \
                not BidsDataset.converters['Imagery']['path']:
            error_str = 'At least one converter path in requirements.json is wrongly set'
            self.issues.add_issue(issue_type='ImportIssue', description=error_str, brick=None)
            self.write_log(error_str)
            return

        if not data2import['DatasetDescJSON']['Name'] == self['DatasetDescJSON']['Name']:
            error_str = 'The data to be imported (' + data2import.dirname + ') belong to a different protocol (' \
                        + data2import['DatasetDescJSON']['Name'] + ') than the current bids dataset (' \
                        + self['DatasetDescJSON']['Name'] + ').'
            self.issues.add_issue(issue_type='ImportIssue', brick=data2import['DatasetDescJSON'],
                                  description=error_str)
            self.write_log(error_str)
            return

        '''Here we copy the data2import dictionary to pop all the imported data in order to avoid importing
        the same data twice in case there is an error and we have to launch the import procedure on the same
        folder again. The original data2import in rename by adding the date in the filename'''
        if not BidsBrick.cwdir == data2import.dirname:
            Data2Import._assign_import_dir(data2import.dirname)
        copy_data2import = Data2Import()
        copy_data2import.copy_values(data2import)
        copy_data2import.dirname = data2import.dirname
        try:
            data2import.save_as_json(savedir=os.path.join(data2import.dirname, 'temp_bids'), write_date=True)
            if keep_sourcedata:
                if not self['SourceData']:
                    self['SourceData'] = SourceData()
                    if keep_file_trace:
                        self['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()

            self._assign_bids_dir(self.dirname)  # make sure to import in the current bids_dir
            sublist = set()  # list to store subject who received new data
            for sub in data2import['Subject']:
                import_sub_idx = data2import['Subject'].index(sub)
                # test if subject is already present
                if not self.curr_subject or not self.curr_subject['Subject']['sub'] == sub['sub']:
                    # check whether the required subject is the current subject otherwise make it the
                    # current one
                    self.is_subject_present(sub['sub'])
                sub_present = self.curr_subject['isPresent']
                sub_index = self.curr_subject['index']

                # # test whether the subject data have all attributes required by bids
                # [flag, missing_str] = sub.has_all_req_attributes()
                # if not flag:
                #     self.issues.add_issue('ImportIssue', brick=sub,
                #                           description=missing_str + ' (' + data2import.dirname + ')')
                #     self.write_log(missing_str)
                #     continue

                # test whether the subject to be imported has the same attributes as the one already inside the
                # bids dataset
                if sub_present and not self.curr_subject['Subject'].get_attributes(['alias', 'upload_date']) == \
                                       sub.get_attributes(['alias', 'upload_date']):
                    error_str = 'The subject to be imported (' + data2import.dirname + \
                                ') has different attributes than the analogous subject in the bids dataset (' \
                                + str(sub.get_attributes()) + '=/=' + \
                                str(self.curr_subject['Subject'].get_attributes()) + ').'
                    self.issues.add_issue('ImportIssue', brick=sub, description=error_str)
                    self.write_log(error_str)
                    continue

                for modality_type in sub.keys():
                    if modality_type in BidsBrick.get_list_subclasses_names():
                        for modality in sub[modality_type]:
                            # flag, missing_str = modality.has_all_req_attributes()
                            # if not flag:
                            #     self.issues.add_issue('ImportIssue', brick=modality,
                            #                           description=missing_str + ' (' + data2import.dirname + ')')
                            #     self.write_log(missing_str)
                            #     continue
                            self.write_log('Start importing ' + modality['fileLoc'])
                            """check again if the subject is present because it could be absent at the beginning but
                            you could have added data from the subject in a previous iteration of the loop.
                            For instance, if you add a T1w and by mistake add the another T1w but with the same
                            attributes you need to know what was previously imported for the subject"""
                            self.is_subject_present(sub['sub'])
                            sub_present = self.curr_subject['isPresent']
                            sub_index = self.curr_subject['index']

                            if sub_present:

                                nb_ses, bids_ses = self.get_number_of_session4subject(sub['sub'])
                                if modality['ses'] and bids_ses:
                                    """ if subject is present, have to check if ses in the data2import matches
                                    the session structures of the dataset (if ses-X already exist than
                                    data2import has to have a ses)"""
                                    same_src_file_bln = have_data_same_source_file(self, modality)
                                    if not same_src_file_bln:
                                        same_attr_bln = have_data_same_attrs_and_sidecars(self, modality,
                                                                                          sub_index)
                                        if same_attr_bln:
                                            string_issue = 'Subject ' + sub['sub'] + '\'s file:' + modality[
                                                'fileLoc'] \
                                                           + ' was not imported from ' + data2import.dirname + \
                                                           ' because ' + \
                                                           modality.create_filename_from_attributes()[0] + \
                                                           ' is already present in the bids dataset ' + \
                                                           '(' + self['DatasetDescJSON']['Name'] + ').'
                                            self.issues.add_issue('ImportIssue', brick=modality,
                                                                  description=string_issue)
                                            self.write_log(string_issue)
                                            continue
                                    else:
                                        string_issue = 'Subject ' + sub['sub'] + '\'s file:' + \
                                                       modality['fileLoc'] + ' was not imported from ' + \
                                                       data2import.dirname +\
                                                       ' because a source file with the same name is already ' \
                                                       'present in the bids dataset ' + \
                                                       self['DatasetDescJSON']['Name'] + '.'
                                        self.issues.add_issue('ImportIssue', brick=modality,
                                                              description=string_issue)
                                        self.write_log(string_issue)
                                        continue
                                else:
                                    string_issue = 'Session structure of the data to be imported (' + \
                                                   data2import.dirname + ')does not ' \
                                                   'match the one of the current dataset.\nSession label(s): ' \
                                                   + ', '.join(bids_ses) + '.\nSubject ' + sub['sub'] + \
                                                   ' not imported.'
                                    self.issues.add_issue('ImportIssue', brick=modality,
                                                          description=string_issue)
                                    self.write_log(string_issue)
                                    continue
                            else:
                                self['Subject'] = Subject()
                                self['Subject'][-1].update(sub.get_attributes())
                                self['ParticipantsTSV'].add_subject(sub)
                                self.is_subject_present(sub['sub'])
                                if keep_sourcedata:
                                    self['SourceData'][-1]['Subject'] = Subject()
                                    self['SourceData'][-1]['Subject'][-1].update(sub.get_attributes())

                            self.issues.remove(modality)
                            # need to get the index before importing because push_into_dataset adds data from sidecars
                            try:
                                idx2pop = copy_data2import['Subject'][import_sub_idx][modality_type].index(modality)
                                push_into_dataset(self, modality, keep_sourcedata, keep_file_trace)

                                self.save_as_json()
                                self.issues.save_as_json()
                                copy_data2import['Subject'][import_sub_idx][modality_type].pop(idx2pop)
                                copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname, 'temp_bids'))
                                sublist.add(sub['sub'])
                            except FileNotFoundError as err:
                                self.write_log(str(err))
                                self.is_subject_present(sub['sub'])
                                sub_index = self.curr_subject['index']
                                self['Subject'][sub_index][modality_type].pop(idx2pop)
                                copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname, 'temp_bids'))
                    # if copy_data2import['Subject'][import_sub_idx].is_empty():
                    # pop empty subject
                for scan in self['Subject'][sub_index]['Scans']:
                    scan.write_file()

            #Add the derivatives folder
            for dev in data2import['Derivatives']:
                idxdev = data2import['Derivatives'].index(dev)
                if not os.path.exists(os.path.join(BidsDataset.dirname, 'derivatives')):
                    os.makedirs(os.path.join(BidsDataset.dirname, 'derivatives'))
                for pip in dev['Pipeline']:
                    idxpip = dev['Pipeline'].index(pip)
                    if not os.path.exists(os.path.join(BidsDataset.dirname, 'derivatives', pip['name'])):
                        os.makedirs(os.path.join(BidsDataset.dirname, 'derivatives', pip['name']))
                    self.is_pipeline_present(pip)
                    pip_present = self.curr_pipeline['isPresent']
                    pip_index = self.curr_pipeline['index']
                    pipDataset = Pipeline()
                    pipDataset['ParticipantsTSV'] = ParticipantsTSV()
                    pipDataset['ParticipantsTSV'].header = ['participant_id']
                    pipDataset['ParticipantsTSV'].required_fields = ['participant_id']												 
                    pipDataset['ParticipantsTSV'][:] =[]																  
                    pipDataset['DatasetDescJSON'] = pip['DatasetDescJSON']
                    if pip_present:
                        pipCurrent = self.curr_pipeline['Pipeline']
                        pipDataset['name'] = pipCurrent['name']
                        for sub in pipCurrent['SubjectProcess']:
                            pipDataset['SubjectProcess'].append(sub)
                        pipDataset['ParticipantsTSV'] = pipCurrent['ParticipantsTSV']
                    else:
                        pipDataset['SubjectProcess'] = Subject()
                        if not self['Derivatives']:
                            self['Derivatives'] = Derivatives()
                        pipDataset['name'] = pip['name']
                        size_pipeline = len(self['Derivatives'][0]['Pipeline'])
                        self['Derivatives'][0]['Pipeline'].append(Pipeline())
                        pip_dict = {key: pipDataset[key] for key in pipDataset.keys() if key not in BidsSidecar.get_list_subclasses_names()}
                        self['Derivatives'][0]['Pipeline'][size_pipeline].update(pip_dict)
                        self.is_pipeline_present(pip)
                    pipDataset.dirname = os.path.join(BidsDataset.dirname, 'derivatives', pip['name'])
                    #BidsDataset.dirname = os.path.join(self.dirname, 'Derivatives', pip['name'])
                    #import pdb; pdb.set_trace()
                    for sub in pip['SubjectProcess']:
                        import_sub_idx = pip['SubjectProcess'].index(sub)

                        # test if subject is already present
                        if not pipDataset.curr_subject or not pipDataset.curr_subject['SubjectProcess']['sub'] == sub['sub']:
                            # check whether the required subject is the current subject otherwise make it the
                            # current one
                            pipDataset.is_subject_present(sub['sub'], flagProcess=True)
                        sub_present = pipDataset.curr_subject['isPresent']
                        sub_index = pipDataset.curr_subject['index']

                        if sub_present and not pipDataset.curr_subject['SubjectProcess'].get_attributes(['alias', 'upload_date']) == \
                                               sub.get_attributes(['alias', 'upload_date']):
                            error_str = 'The subject to be imported (' + data2import.dirname + \
                                        ') has different attributes than the analogous subject in the bids dataset (' \
                                        + str(sub.get_attributes()) + '=/=' + \
                                        str(pipDataset.curr_subject['Subject'].get_attributes()) + ').'
                            self.issues.add_issue('ImportIssue', brick=sub, description=error_str)
                            self.write_log(error_str)
                            continue

                        for modality_type in sub.keys():
                            if modality_type in BidsBrick.get_list_subclasses_names():
                                for modality in sub[modality_type]:
                                    self.write_log('Start importing in Derivatives ' + modality['fileLoc'])
                                    """check again if the subject is present because it could be absent at the beginning but
                                    you could have added data from the subject in a previous iteration of the loop.
                                    For instance, if you add a T1w and by mistake add the another T1w but with the same
                                    attributes you need to know what was previously imported for the subject"""
                                    pipDataset.is_subject_present(sub['sub'], flagProcess=True)
                                    sub_present = pipDataset.curr_subject['isPresent']
                                    sub_index = pipDataset.curr_subject['index']

                                    if sub_present:
                                        nb_ses, bids_ses = pipDataset.get_number_of_session4subject(sub['sub'], flag_process=True)
                                        if modality['ses'] and bids_ses:
                                            same_attr_der = have_data_same_attrs_and_sidecars(pipDataset, modality, sub_index, flag_process=True)
                                            if same_attr_der:
                                                string_issue = 'Subject ' + sub['sub'] + '\'s file:' + modality[
                                                    'fileLoc'] \
                                                               + ' was not imported from ' + data2import.dirname + \
                                                               ' because ' + \
                                                               modality.create_filename_from_attributes()[0] + \
                                                               ' is already present in the bids dataset).'
                                                self.issues.add_issue('ImportIssue', brick=modality,
                                                                      description=string_issue)
                                                self.write_log(string_issue)
                                                continue
                                        else:
                                            string_issue = 'Session structure of the data to be imported (' + \
                                                            data2import.dirname + ')does not ' \
                                                                                     'match the one of the current dataset.\nSession label(s): ' \
                                                            + ', '.join(bids_ses) + '.\nSubject ' + sub['sub'] + \
                                                            ' not imported.'
                                            self.issues.add_issue('ImportIssue', brick=modality,
                                                                      description=string_issue)
                                            self.write_log(string_issue)
                                    else:
                                        pipDataset.add_subject(sub)
                                        pipDataset.is_subject_present(sub['sub'], flagProcess=True)

                                    self.issues.remove(modality)
                                    # need to get the index before importing because push_into_dataset adds data from sidecars
                                    try:
                                        idx2pop = copy_data2import['Derivatives'][idxdev]['Pipeline'][idxpip]['SubjectProcess'][import_sub_idx][modality_type].index(modality)
                                        push_into_dataset(pipDataset, modality, keep_sourcedata, keep_file_trace, flag_process=True)
                                        pipDataset.update_bids_original(self, modality)

                                        copy_data2import['Derivatives'][idxdev]['Pipeline'][idxpip]['SubjectProcess'][import_sub_idx][modality_type].pop(idx2pop)
                                        copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname, 'temp_bids'))
                                        #sublist.add(sub['sub'])
                                    except FileNotFoundError as err:
                                        self.write_log(str(err))
                                        copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname, 'temp_bids'))

                                    part_present, part_info, part_index = pipDataset['ParticipantsTSV'].is_subject_present(sub['sub'])
                                    if not part_present:
                                        pipDataset['ParticipantsTSV'].add_subject(sub)
                            # if copy_data2import['Subject'][import_sub_idx].is_empty():
                            # pop empty subject
                    self.is_pipeline_present(pip)
                    if pipDataset['DatasetDescJSON']:
                        pipDataset['DatasetDescJSON'].write_file(jsonfilename=os.path.join(pipDataset.dirname, 'dataset_description.json'))
                    pipDataset['ParticipantsTSV'].write_file(tsv_full_filename=os.path.join(pipDataset.dirname, 'participants.tsv'))
                    self.save_as_json()

            if copy_data2import.is_empty():
                if all(file.endswith('.json') or file.endswith('.tsv') or file.endswith('.flt') or file.endswith('.mtg')
                       or file.endswith('.mrk') or file.endswith('.levels')
                       for file in os.listdir(copy_data2import.dirname)):
                    # if there are only the data2import.json and the sidecar files created during conversions,
                    # (Anywave files) the import dir can be removed
                    shutil.rmtree(copy_data2import.dirname)
                    self.write_log(copy_data2import.dirname + ' is now empty and will be removed.')

            if self['DatasetDescJSON']:
                self['DatasetDescJSON'].write_file()

            if sublist:
                sublist = list(sublist)
                self.check_requirements(specif_subs=sublist)
            # data2import.clear()
            # self.parse_bids()

        # shutil.rmtree(data2import.data2import_dir)
        except Exception as err:
            self.write_log(str(err))
            copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname, 'temp_bids'))

        # could make it fast by just appending a new line instead of writing the whole file again
        self['ParticipantsTSV'].write_file()
        if self['SourceData'] and self['SourceData'][-1]['SrcDataTrack']:
            # could make it fast by just appending a new line instead of writing the whole file again
            self['SourceData'][-1]['SrcDataTrack'].write_file()

    def remove(self, element2remove, with_issues=True):
        """method to remove either the whole data set, a subject or a file (with respective sidecar files)"""
        # a bit bulky rewrite to make it nice
        if element2remove is self:
            shutil.rmtree(self.dirname)
            print('The whole Bids dataset ' + self['DatasetDescJSON']['Name'] + ' has been removed')
            BidsDataset.clear_log()
            self.issues.clear()
            self.clear()
        elif isinstance(element2remove, Subject):
            self.is_subject_present(element2remove['sub'])
            if self.curr_subject['isPresent']:
                # remove from sourcedata folder
                if self['SourceData']:
                    self['SourceData'][-1].is_subject_present(element2remove['sub'])
                    if self['SourceData'][-1].curr_subject['isPresent']:
                        shutil.rmtree(os.path.join(self.dirname, 'sourcedata', 'sub-' + element2remove['sub']))
                        self['SourceData'][-1]['Subject'].pop(self['SourceData'][-1].curr_subject['index'])
                        self.save_as_json()
                        self.write_log('Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                                       self['DatasetDescJSON']['Name'] + ' source folder.')
                        if self['SourceData'][-1]['SrcDataTrack']:
                            # remove from source_data_trace.tsv folder
                            src_tsv = self['SourceData'][-1]['SrcDataTrack']
                            bids_fname_idx = src_tsv.header.index('bids_filename')
                            src_tsv_copy = SrcDataTrack()
                            src_tsv_copy.copy_values([line for line in src_tsv
                                                      if not line[bids_fname_idx].startswith('sub-'
                                                                                             + element2remove['sub'])])
                            self['SourceData'][-1]['SrcDataTrack'] = src_tsv_copy
                            self['SourceData'][-1]['SrcDataTrack'].write_file()
                            self.save_as_json()
                            self.write_log('Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                                           self['DatasetDescJSON']['Name'] + ' ' + src_tsv_copy.filename + '.')
                # remove from ParticipantsTSV
                _, _, sub_idx = self['ParticipantsTSV'].is_subject_present(element2remove['sub'])
                if sub_idx:
                    self['ParticipantsTSV'].pop(sub_idx)
                    self['ParticipantsTSV'].write_file()
                    self.save_as_json()
                    self.write_log(
                        'Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                        self['DatasetDescJSON']['Name'] + ' ' + self['ParticipantsTSV'].filename + '.')
                if with_issues:
                    # remove issues related to this patient
                    self.issues.remove(element2remove)
                # remove from raw folder
                shutil.rmtree(os.path.join(self.dirname, 'sub-' + element2remove['sub']))
                self['Subject'].pop(self.curr_subject['index'])
                self.save_as_json()
                self.write_log('Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                               self['DatasetDescJSON']['Name'] + ' raw folder.')

        elif isinstance(element2remove, ModalityType) and element2remove.classname() in Subject.keylist:
            self.is_subject_present(element2remove['sub'])
            if self.curr_subject['isPresent'] and \
                    element2remove in self.curr_subject['Subject'][element2remove.classname()]:
                elmt_idx = self.curr_subject['Subject'][element2remove.classname()].index(element2remove)
                dirname, fname, ext = element2remove.fileparts()
                if self['SourceData']:
                    # remove file in sourcedata folder and in source_data_trace.tsv
                    self['SourceData'][-1].is_subject_present(element2remove['sub'])
                    if self['SourceData'][-1].curr_subject['isPresent'] and self['SourceData'][-1]['SrcDataTrack']:
                        # you have to have the sourcedatatrack to be able to remove the source file otherwise no way to
                        # know the link between the raw and the source file
                        src_tsv = self['SourceData'][-1]['SrcDataTrack']
                        src_sub = self['SourceData'][-1].curr_subject['Subject']
                        orig_fname, _, idx2remove = src_tsv.get_source_from_raw_filename(element2remove['fileLoc'])
                        if orig_fname:

                            full_orig_name = os.path.join(SourceData.dirname, dirname, orig_fname)

                            # remove info of file in source trace table
                            if idx2remove:  # if source data is present in the source_trace
                                src_tsv.pop(idx2remove)
                                src_tsv.write_file()
                                self.write_log(element2remove['fileLoc'] + '(' + orig_fname +
                                               ') has been removed from Bids dataset ' +
                                               self['DatasetDescJSON']['Name'] + ' in ' + src_tsv.filename + '.')
                                self.save_as_json()

                            # remove file in sourcedata folder
                            idx = [src_sub[element2remove.classname()].index(modal)
                                   for modal in src_sub[element2remove.classname()]
                                   if modal['fileLoc'] == full_orig_name]
                            if idx:  # if source data is present
                                if isinstance(element2remove, Imagery):
                                    shutil.rmtree(os.path.join(self.dirname, full_orig_name))
                                elif isinstance(element2remove, Electrophy):
                                    os.remove(os.path.join(self.dirname, full_orig_name))
                                src_sub[element2remove.classname()].pop(idx[0])
                                self.save_as_json()
                                self.write_log(element2remove['fileLoc'] + '(' + orig_fname +
                                               ') has been removed from Bids dataset ' +
                                               self['DatasetDescJSON']['Name'] + ' in source folder.')
                        else:
                            self.write_log(element2remove['fileLoc'] + ' has no source folder, it was probably manually'
                                                                       ' remove please refresh the bids dataset.')
                        
                # remove file in raw folder and its first level sidecar files (higher level may characterize
                # remaining files)
                sdcar_dict = element2remove.get_modality_sidecars()
                for sidecar_key in sdcar_dict:
                    if element2remove[sidecar_key]:
                        if element2remove[sidecar_key].modality_field:
                            sdcar_fname = fname.replace(element2remove['modality'],
                                                        element2remove[sidecar_key].modality_field)
                        else:
                            sdcar_fname = fname
                        if os.path.exists(os.path.join(BidsDataset.dirname, dirname,
                                                       sdcar_fname + element2remove[sidecar_key].extension)):
                            os.remove(os.path.join(BidsDataset.dirname, dirname, sdcar_fname +
                                                   element2remove[sidecar_key].extension))
                if with_issues:
                    self.issues.remove(element2remove)
                if isinstance(element2remove, Electrophy):
                    ext = self.converters['Electrophy']['ext']
                elif isinstance(element2remove, Imagery):
                    ext = self.converters['Imagery']['ext']
                ext.reverse()
                for ex in ext:
                    if os.path.join(self.dirname, dirname, fname+ex):
                        os.remove(os.path.join(self.dirname, dirname, fname+ex))
                self.curr_subject['Subject'][element2remove.classname()].pop(elmt_idx)
                self.write_log(element2remove['fileLoc'] +
                               ' and its sidecar files were removed from Bids dataset ' +
                               self['DatasetDescJSON']['Name'] + ' raw folder.')
                self.save_as_json()
        elif isinstance(element2remove, GlobalSidecars):
            self.is_subject_present(element2remove['sub'])
            if self.curr_subject['isPresent'] and \
                    element2remove in self.curr_subject['Subject'][element2remove.classname()]:
                elmt_idx = self.curr_subject['Subject'][element2remove.classname()].index(element2remove)
                os.remove(os.path.join(self.dirname, element2remove['fileLoc']))
                if with_issues:
                    self.issues.remove(element2remove)
                self.curr_subject['Subject'][element2remove.classname()].pop(elmt_idx)
                self.write_log(element2remove['fileLoc'] +
                               ' and its sidecar files were removed from Bids dataset ' +
                               self['DatasetDescJSON']['Name'] + ' raw folder.')
                self.save_as_json()

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):
        save_parsing_path = os.path.join(self.dirname, 'derivatives', 'parsing')
        os.makedirs(save_parsing_path, exist_ok=True)
        super().save_as_json(savedir=save_parsing_path, file_start='parsing', write_date=True, compress=True)
        self.issues.save_as_json()

    def apply_actions(self):

        def modify_electrodes_files(ch_issue):
            def change_electrode(**kwargs):  # appears unused because it is called from eval()
                type_bln = False
                name_bln = False
                if 'type' in kwargs.keys():  # have to change the electrode type
                    type_bln = True
                    input_key = 'type'
                if 'name' in kwargs.keys():  # have to change the electrode name
                    name_bln = True
                    input_key = 'name'
                if type_bln ^ name_bln:
                    #  XOR only one of them is true, cannot change both type and name!
                    dirname, mod_fname, ext=modality.fileparts()
                    sidecar = modality.get_modality_sidecars(BidsTSV)
                    # /!\ first change the name in .vhdr and .vmrk because those are ot read during check requirements!
                    if name_bln:
                        hdr = bv_hdr.BrainvisionHeader(os.path.join(self.dirname, dirname, mod_fname + ext))
                        hdr.modify_header(action['name'], kwargs['name'])
                        hdr.write_header()
                    for key in sidecar:
                        if type_bln and all(wrd in sidecar[key].header for wrd in ['type', 'group']):
                            idx_group = sidecar[key].header.index('group')
                            idx_type = sidecar[key].header.index('type')
                            """ replace current type by the new one for all channels from same electrode"""
                            for line in sidecar[key][1:]:
                                if line[idx_group] == action['name']:
                                    line[idx_type] = kwargs['type']
                            act_str = 'Change electrode type of ' + action['name'] + ' to ' + kwargs['type'] + \
                                      ' in the ' + mod_fname + sidecar[key].extension + '.'
                        elif name_bln and all(wrd in sidecar[key].header for wrd in ['name', 'group']):
                            idx_group = sidecar[key].header.index('group')
                            idx_name = sidecar[key].header.index('name')
                            """ replace current group by the new one for all channel from same electrode and rename 
                            the channel accordingly"""
                            for line in sidecar[key][1:]:
                                if line[idx_group] == action['name']:
                                    # need replace here to keep the number of the channel
                                    line[idx_name] = line[idx_name].replace(line[idx_group], kwargs['name'])
                                    line[idx_group] = kwargs['name']
                            act_str = 'Change electrode name from ' + action['name'] + ' to ' + kwargs['name'] + \
                                      ' in the ' + mod_fname + sidecar[key].extension + '.'
                        else:
                            continue
                        fname2bewritten = os.path.join(BidsDataset.dirname, dirname,
                                                       mod_fname.replace(modality['modality'],
                                                                         sidecar[key].modality_field)
                                                       + sidecar[key].extension)
                        sidecar[key].write_file(fname2bewritten)
                        # remove the mismatched electrode from the list, when empty the issue will be popped
                        [curr_iss_cpy['MismatchedElectrodes'].pop(curr_iss_cpy['MismatchedElectrodes'].index(mm_elec))
                         for mm_elec in ch_issue['MismatchedElectrodes'] if mm_elec['name'] == action['name']]
                        curr_iss_cpy['Action'].pop(curr_iss_cpy['Action'].index(action))
                        # modality[key] = []
                        # modality[key].copy_values(sidecar[key])  # sidecar is not in self but a copy
                        self.save_as_json()
                        modality.write_log(act_str)
                else:
                    err_str = 'One cannot modify the name and the type of the electrode at the same time'
                    ch_issue.write_log(err_str)

            modality = self.get_object_from_filename(ch_issue['fileLoc'])
            if not modality:  # no need to update the log since get_object_from_filename does it
                return
            for action in ch_issue['Action']:
                eval('change_electrode(' + action['command'] + ')')
                pass

        def modify_files(**kwargs):

            elmt_iss = issue.get_element()
            if 'remove_issue' in kwargs and kwargs['remove_issue']:
                # nothing else to do since the issue will be popped anyway ^_^ (except for UploaderIssues)
                if isinstance(issue, ImportIssue):
                    str_rmv = issue['description']
                else:
                    str_rmv = os.path.basename(elmt_iss['fileLoc'])
                self.write_log('Issue concerning "' + str_rmv + '" has been removed.')
                return
            if 'state' in kwargs and kwargs['state'] and isinstance(issue, UpldFldrIssue):
                # simple command to modify the state
                curr_iss = issues_copy['UpldFldrIssue'][issues_copy['UpldFldrIssue'].index(issue)]
                curr_iss['state'] = kwargs['state']
                curr_iss['Action'] = []
                self.write_log('State of file ' + elmt_iss['fileLoc'] + ' has been set to ' + curr_iss['state'] + '.')
                return
            if 'in_bids' in kwargs:
                if kwargs['in_bids'] == 'True' or kwargs['in_bids'] is True:
                    kwargs['in_bids'] = True
                    curr_brick = self
                    loc_str = ' in bids dir. ' + self.dirname + '.'
                else:
                    kwargs['in_bids'] = False
                    curr_brick = Data2Import(issue['path'])
                    curr_brick.save_as_json(write_date=True)
                    loc_str = ' in import dir. ' + issue['path'] + '.'
            else:
                err_str = 'No information about whether the change has to be made in bids or import directory.'
                self.write_log(err_str)
                return
            if 'pop' in kwargs and kwargs['pop'] and not kwargs['in_bids']:
                # if pop = True => not to import this element
                if isinstance(elmt_iss, (ModalityType, GlobalSidecars)):
                    idx = None
                    curr_brick.is_subject_present(elmt_iss['sub'])
                    curr_sub = curr_brick.curr_subject['Subject']
                    for elmt in curr_sub[elmt_iss.classname()]:
                        if elmt.get_attributes('fileLoc') == elmt_iss.get_attributes('fileLoc') and \
                                elmt['fileLoc'] == os.path.basename(elmt_iss['fileLoc']):
                            # remember that is issues the fileLoc are absolute path, therefore one has to tests the
                            # basename
                            idx = curr_sub[elmt_iss.classname()].index(elmt)
                            break
                    curr_sub[elmt_iss.classname()].pop(idx)
                    self.write_log('Element ' + elmt_iss['fileLoc'] + ' has been removed from the data to import'
                                   + loc_str + '.')
            elif isinstance(elmt_iss, DatasetDescJSON):
                for key in kwargs:
                    if key in curr_brick['DatasetDescJSON']:
                        curr_brick['DatasetDescJSON'][key] = kwargs[key]
                if kwargs['in_bids']:
                    # special case here since need also write the change in bids directory
                    curr_brick['DatasetDescJSON'].write_file()
                self.write_log('Modification of ' + DatasetDescJSON.filename + loc_str)
            elif isinstance(elmt_iss, Subject):
                curr_brick.is_subject_present(elmt_iss['sub'])
                curr_sub = curr_brick.curr_subject['Subject']
                for key in kwargs:
                    if key in curr_sub and key not in BidsBrick.get_list_subclasses_names() and not key == 'sub':
                        curr_sub[key] = kwargs[key]
                if kwargs['in_bids']:
                    # special case here since need also to update the participants.tsv
                    _, sub_info, idx = curr_brick['ParticipantsTSV'].is_subject_present(curr_sub['sub'])
                    curr_brick['ParticipantsTSV'].pop(idx)
                    sub_info.update({key: kwargs[key] for key in sub_info if key in kwargs})
                    sub_info['participant_id'] = sub_info['sub']
                    curr_brick['ParticipantsTSV'].append(sub_info)
                    curr_brick['ParticipantsTSV'].write_file()
                self.write_log('Modification of for ' + curr_sub['sub'] + loc_str)
            elif isinstance(elmt_iss, (ModalityType, GlobalSidecars)):
                if 'remove' in kwargs and kwargs['in_bids']:
                    mod_brick = curr_brick.get_object_from_filename(kwargs['remove'])
                    # check if element had other issues (ieeg file could have electrode issues)
                    #  to be checked before removing file because of the fileLoc safety (cf BidsBrick __setitem__)
                    issues_copy.remove(mod_brick)
                    # put with_issues=False because if affects self.issues and not the copy where the other issues are
                    # popped out
                    curr_brick.remove(mod_brick, with_issues=False)
                elif not kwargs['in_bids']:
                    curr_brick.is_subject_present(elmt_iss['sub'])
                    curr_sub = curr_brick.curr_subject['Subject']
                    idx = None
                    for elmt in curr_sub[elmt_iss.classname()]:
                        if elmt.get_attributes('fileLoc') == elmt_iss.get_attributes('fileLoc') and \
                                elmt['fileLoc'] == os.path.basename(elmt_iss['fileLoc']):
                            idx = curr_sub[elmt_iss.classname()].index(elmt)
                            break
                    elmt = curr_sub[elmt_iss.classname()][idx]
                    for key in kwargs:
                        if key in elmt and key not in ['sub', 'fileLoc']:
                            if isinstance(kwargs[key], str):
                                if kwargs[key].isdigit:
                                    val = kwargs[key].zfill(2)
                                else:
                                    val = kwargs[key]
                            else:
                                val = str(kwargs[key]).zfill(2)
                            elmt[key] = val
                    self.write_log('Modification of ' + elmt['fileLoc'] + ' has been done' + loc_str)
            if isinstance(issue, UpldFldrIssue):
                if 'pop' in kwargs:
                    # UpldFldrIssue are normally not popped, thus need to add this line
                    issues_copy['UpldFldrIssue'].pop(issues_copy['UpldFldrIssue'].index(issue))
                else:
                    curr_iss = issues_copy['UpldFldrIssue'][issues_copy['UpldFldrIssue'].index(issue)]
                    curr_iss['Action'] = []
            curr_brick.save_as_json()

        BidsBrick.access_time = datetime.now()
        self.clear_log()
        self._assign_bids_dir(self.dirname)
        # self.write_log('Current User: ' + self.curr_user + '\n' + BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S"))
        issues_copy = Issue()
        issues_copy.copy_values(self.issues)  # again have to copy to pop while looping
        file_removal = False
        try:
            self.write_log(10 * '=' + '\nApplying actions\n' + 10 * '=')
            # could optimize/make nicer
            # the order is important because you could remove a file and than its relative ElectrodeIssue
            for issue in self.issues['ElectrodeIssue']:
                if not issue['Action']:
                    continue
                curr_iss_cpy = issues_copy['ElectrodeIssue'][issues_copy['ElectrodeIssue'].index(issue)]
                modify_electrodes_files(issue)
                if not curr_iss_cpy['MismatchedElectrodes']:
                    # only remove the issue if no more mismatched electrodes (so it keeps comment from the remaining
                    # electrodes)
                    # have to empty these since this was modified in the copied versions
                    issue['MismatchedElectrodes'] = []
                    issue['Action'] = []
                    issues_copy['ElectrodeIssue'].pop(issues_copy['ElectrodeIssue'].index(issue))
                issues_copy.save_as_json()
            for issue in self.issues['ImportIssue']:
                if not issue['Action']:
                    continue
                eval('modify_files(' + issue['Action'][0]['command'] + ')')
                if 'remove' in issue['Action'][0]['command']:
                    file_removal = True
                issues_copy['ImportIssue'].pop(issues_copy['ImportIssue'].index(issue))
                issues_copy.save_as_json()
            for issue in self.issues['UpldFldrIssue']:
                if not issue['Action']:
                    continue
                eval('modify_files(' + issue['Action'][0]['command'] + ')')
                if 'remove_issue=True' in issue['Action'][0]['command']:
                    issues_copy['UpldFldrIssue'].pop(issues_copy['UpldFldrIssue'].index(issue))
                # here issues are not popped out because in import_data() they are checked to make sure files were
                # verified
                issues_copy.save_as_json()
        except Exception as ex:
            self.write_log(str(ex))
        if issues_copy['ElectrodeIssue'] == self.issues['ElectrodeIssue'] and not file_removal:
            elec_iss_bln = False
        else:
            elec_iss_bln = True
        self._assign_bids_dir(self.dirname)  # because of the data2import the cwdir could change
        self.issues = Issue()
        self.issues.copy_values(issues_copy)
        if elec_iss_bln:  # only check requirement if actions were made for ElectrodeIssues
            self.check_requirements()

    def make_upload_issues(self, data2import, force_verif=False):
        """ each time a data2import is instantiated, one has to create upload issues to force the user to verify that
        the files have the correct attributes. """
        if not isinstance(data2import, Data2Import):
            self.write_log('Current method takes instance of Data2Import.')
            return
        if force_verif is True:
            state = 'verified'
        else:
            state = 'not verified'
        self._assign_bids_dir(self.dirname)
        for sub in data2import['Subject']:
            for key in sub:
                if key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                    for mod_brick in sub[key]:
                        self.issues.add_issue('UpldFldrIssue', fileLoc=mod_brick['fileLoc'],
                                              sub=mod_brick['sub'], path=data2import.dirname,
                                              state=state)
        for dev in data2import['Derivatives']:
            for pip in dev['Pipeline']:
                for sub in pip['SubjectProcess']:
                    for key in sub:
                        if key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                            for mod_brick in sub[key]:
                                self.issues.add_issue('UpldFldrIssue', fileLoc=mod_brick['fileLoc'],
                                                      sub=mod_brick['sub'], path=data2import.dirname,
                                                      state=state)

    def verif_upload_issues(self, import_dir):
        return self.issues.verif_upload_issues(import_dir)

    @classmethod
    def _assign_bids_dir(cls, bids_dir):
        cls.dirname = bids_dir
        BidsBrick.cwdir = bids_dir


''' Concurrent access object '''


class Access(BidsJSON):
    keylist = ['user', 'access_time']

    def __init__(self):
        super().__init__()
        self.filename = os.path.join(BidsDataset.dirname, BidsDataset.log_path, 'access.json')

    def display(self):
        return 'This Bids dataset (' + BidsDataset.dirname + ') is in use by ' + self['user'] + ' since ' + \
               self['access_time'] + '.'

    def read_file(self, filename=None):
        super().read_file(self.filename)

    def write_file(self, jsonfilename=None):
        super().write_file(self.filename)

    def delete_file(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)


''' Additional class to handle issues and relative actions '''


class RefElectrodes(BidsFreeFile):
    pass


class MismatchedElectrodes(BidsBrick):
    keylist = ['name', 'type']
    required_keys = keylist


class Comment(BidsBrick):
    keylist = ['name', 'date', 'user', 'description']

    def __init__(self, new_keys=None):
        if not new_keys:
            new_keys = []
        if isinstance(new_keys, str):
            new_keys = [new_keys]
        if isinstance(new_keys, list):
            self.keylist = new_keys + self.keylist
            super().__init__(keylist=self.keylist)
            self['user'] = self.curr_user
            self['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        else:
            error_str = 'The new keys of ' + self.classname() + ' should be either a list of a string.'
            self.write_log(error_str)
            raise TypeError(error_str)

    def formatting(self):
        return '==> ' + self.classname() + ' by ' + self['user'] + ' at ' + self['date'] + ':\n'\
               + self['description']


class Action(Comment):
    keylist = Comment.keylist + ['command']


class IssueType(BidsBrick):

    def add_comment(self,  desc, elec_name=None):

        """verify that the given electrode name is part of the mismatched electrodes"""
        if isinstance(self, ElectrodeIssue) and elec_name not in self.list_mismatched_electrodes():
            print(elec_name + ' does not belong to the current mismatched electrode.')
            return

        comment = Comment()
        if elec_name:  # add comment about a given mismatched electrodes
            comment['name'] = elec_name
        comment['description'] = desc
        self['Comment'] = comment

    def get_element(self):
        if isinstance(self, ImportIssue):
            """get_element returns the brick which produced this issue. Since there is only one brick per ImportIssue,
            one can break the for loop when found"""
            for key in ImportIssue.keylist:
                if key == 'DatasetDescJSON' and self[key]:
                    return self[key]
                elif key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names() \
                        + ['Subject'] and self[key]:
                    return self[key][0]
        elif isinstance(self, UpldFldrIssue):
            tmp_data2import = Data2Import(self['path'])
            return tmp_data2import.get_object_from_filename(self['fileLoc'])
        return

    def formatting(self, comment_type=None, elec_name=None):
        if comment_type and (not isinstance(comment_type, str) or
                             comment_type.capitalize() not in Comment.get_list_subclasses_names() + ['Comment']):
            raise KeyError(comment_type + ' is not a recognized key of ' + self.classname() + '.')
        if not comment_type:
            comment_type = Comment.get_list_subclasses_names() + ['Comment']
        else:
            comment_type = [comment_type.capitalize()]
        formatted_list = []
        for cmnt_type in comment_type:
            for cmnt in self[cmnt_type]:
                if isinstance(self, ElectrodeIssue):
                    if elec_name and not cmnt['name'] == elec_name:
                        continue
                formatted_list.append(cmnt.formatting())
        return formatted_list

    def add_action(self, desc, command, elec_name=None):
        action = Action()
        if isinstance(self, ElectrodeIssue):
            """verify that the given electrode name is part of the mismatched electrodes"""
            if elec_name not in self.list_mismatched_electrodes():
                return
            """check whether a mismatched electrode already has an action. Only one action per electrode is permitted"""
            idx2pop = None
            for act in self['Action']:
                if act['name'] == elec_name:
                    idx2pop = self['Action'].index(act)
                    break
            if idx2pop is not None:
                self['Action'].pop(idx2pop)
            """ add action for given mismatched electrodes """
            action['name'] = elec_name
        else:
            """ImportIssue and UpldFldrIssue have only one issue per instance (different from channelIssue that can have
             as many actions as there are mismatched channels)"""
            if self['Action']:
                self['Action'].pop(0)
        """ add action for given mismatched electrodes """
        action['description'] = desc
        action['command'] = command
        self['Action'] = action


class UpldFldrIssue(IssueType):
    keylist = BidsBrick.keylist + ['path', 'state', 'fileLoc', 'Comment', 'Action']
    required_keys = BidsBrick.keylist + ['path', 'state', 'fileLoc']
    pass


class ElectrodeIssue(IssueType):
    keylist = BidsBrick.keylist + ['mod', 'RefElectrodes', 'MismatchedElectrodes', 'fileLoc', 'Comment', 'Action']
    required_keys = BidsBrick.keylist + ['RefElectrodes', 'MismatchedElectrodes', 'fileLoc']

    def list_mismatched_electrodes(self):
        return [miselec['name'] for miselec in self['MismatchedElectrodes']]


class ImportIssue(IssueType):
    """instance of ImportIssue allows storing information, comments and actions about issues encounter during
    importation. 'Subject' corresponds to a list of Subject(), the first one to be imported and the second to the
    current subject in the dataset and give info about subject related issue. Same for the modality keys."""
    keylist = ['DatasetDescJSON', 'Subject', 'SubjectProcess'] + \
              [key for key in Subject.keylist if key in ModalityType.get_list_subclasses_names()
               + GlobalSidecars.get_list_subclasses_names()] + \
              ['description', 'path', 'Comment', 'Action'] + \
              [key for key in SubjectProcess.keyprocess]



class Issue(BidsBrick):
    keylist = ['UpldFldrIssue', 'ImportIssue', 'ElectrodeIssue']

    def check_with_latest_issue(self):
        """ This method verified in the lastest issue.json if there are issues corresponding to the current Issue().
        If so, it loads previous Comments and Actions and State (for the upload issues) of the related issue."""
        def read_file(filename):
            with open(filename, 'r') as file:
                rd_json = json.load(file)
            return rd_json

        log_dir = os.path.join(BidsDataset.dirname, BidsDataset.log_path)
        if BidsDataset.dirname and os.path.isdir(log_dir):
            latest_issue = latest_file(log_dir, self.classname().lower())
            if latest_issue:
                # find the latest issue.json file
                read_json = read_file(latest_issue)

                # remove all import dir that were removed, it will raise an error in the fileLoc test otherwise
                # to avoid error read json as normal dict and then copy_value in the correct bids object
                cpy_read_json = read_file(latest_issue)
                for issue_key in cpy_read_json.keys():
                    for issue in read_json[issue_key]:
                        iss_test = getattr(modules[__name__], issue_key)()
                        try:
                            iss_test.copy_values(issue)
                        except FileNotFoundError: # is the only error that could occur
                            self.write_log('Related ' + issue_key + ' issues are removed')
                            read_json[issue_key].pop(read_json[issue_key].index(issue))

                if self == Issue():
                    self.copy_values(read_json)
                    if not read_json == cpy_read_json:
                        self.save_as_json()
                else:
                    prev_issues = Issue()
                    prev_issues.copy_values(read_json)

                    for issue_key in self.keys():
                        for issue in self[issue_key]:
                            """ find in the previous issue.json the comment and action concerning the same file; 
                            add_comment() and add_action() take care of the electrode matching."""
                            idx = None
                            for cnt, prev_iss in enumerate(prev_issues[issue_key]):
                                if prev_iss.get_attributes() == issue.get_attributes():
                                    idx = cnt
                                    break
                            # could pop prev_iss from prev_issues to make it fasted
                            comment_list = prev_issues[issue_key][idx]['Comment']
                            action_list = prev_issues[issue_key][idx]['Action']
                            for comment in comment_list:
                                issue.add_comment(comment['name'], comment['description'])
                            for action in action_list:
                                if issue_key == 'ElectrodeIssue':
                                    issue.add_action(action['name'], action['description'], action['command'])
                                else:
                                    issue.add_action(action['description'], action['command'])

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):

        log_path = os.path.join(BidsDataset.dirname, 'derivatives', 'log')
        super().save_as_json(savedir=log_path, file_start=None, write_date=True, compress=False)

    def formatting(self, specific_issue=None, comment_type=None, elec_name=None):
        if specific_issue and specific_issue not in self.keys():
            raise KeyError(specific_issue + ' is not a recognized key of ' + self.classname() + '.')
        if comment_type and (not isinstance(comment_type, str) or
                             comment_type.capitalize() not in Comment.get_list_subclasses_names() + ['Comment']):
            raise KeyError(comment_type + ' is not a reckognized key of ' + self.classname() + '.')
        formatted_list = []
        if specific_issue:
            key2check = [specific_issue]
        else:
            key2check = self.keylist
        for key in key2check:
            for issue in self[key]:
                formatted_list += issue.formatting(comment_type=comment_type, elec_name=elec_name)

        return formatted_list

    def add_issue(self, issue_type, **kwargs):
        # key used by kwarg:
        # ['sub', 'mod', 'RefElectrodes', 'MismatchedElectrodes', 'fileLoc', 'brick', 'description']
        if issue_type == 'ElectrodeIssue':
            issue = ElectrodeIssue()
            for key in kwargs:
                if key in issue.keylist:
                    if key == 'MismatchedElectrodes':
                        if isinstance(kwargs[key], list):
                            for elmt in kwargs[key]:
                                melec = MismatchedElectrodes()
                                melec.copy_values(elmt)
                                issue[key] = melec
                        else:
                            issue[key] = kwargs[key]
                    else:
                        issue[key] = kwargs[key]
        elif issue_type == 'ImportIssue' and kwargs['brick']:
            issue = ImportIssue()
            issue['path'] = Data2Import.dirname
            if kwargs['brick']:
                if isinstance(kwargs['brick'], DatasetDescJSON):
                    brick_imp_shrt = kwargs['brick']
                elif isinstance(kwargs['brick'], (ModalityType, GlobalSidecars)):
                    fname = os.path.join(Data2Import.dirname, kwargs['brick']['fileLoc'])
                    if isinstance(kwargs['brick'], ModalityType):
                        brick_imp_shrt = kwargs['brick'].__class__()
                    elif isinstance(kwargs['brick'], GlobalSidecars):
                        brick_imp_shrt = kwargs['brick'].__class__(fname)
                    brick_imp_shrt.update(kwargs['brick'].get_attributes('fileLoc'))
                    brick_imp_shrt['fileLoc'] = os.path.join(fname)
                elif isinstance(kwargs['brick'], Subject):
                    brick_imp_shrt = kwargs['brick'].__class__()
                    brick_imp_shrt.update(kwargs['brick'].get_attributes())
                issue[kwargs['brick'].classname()] = brick_imp_shrt
            if kwargs['description'] and isinstance(kwargs['description'], str):
                issue['description'] = kwargs['description']
        elif issue_type == 'UpldFldrIssue':
            issue = UpldFldrIssue()
            if 'fileLoc' in kwargs.keys() and 'path' in kwargs.keys():
                kwargs['fileLoc'] = os.path.join(kwargs['path'], kwargs['fileLoc'])
            for key in kwargs:
                if key in issue.keylist:
                    issue[key] = kwargs[key]
        else:
            return

        # check if the same issue is already in the Issue brick by testing all the keys except Comment, Action and State
        for prev_issue in self[issue_type]:
            if all(prev_issue[key] == issue[key] for key in prev_issue if key not in ['Comment', 'Action', 'state']):
                return

        # before adding the issue test whether it has all needed attributes
        flag, missing_str = issue.has_all_req_attributes()
        if not flag:
            raise AttributeError(missing_str)

        self[issue_type] = issue
        self.save_as_json()

    def remove(self, brick2remove):
        new_issue = self.__class__()
        new_issue.copy_values(self)
        # need a copy because we cannot loop over a list and pop its content at the same time
        for key in self:
            if isinstance(brick2remove, Subject) or isinstance(brick2remove, SubjectProcess):
                if key == 'ElectrodeIssue':
                    for issue in self[key]:
                        if issue['sub'] == brick2remove['sub']:
                            new_issue[key].pop(new_issue[key].index(issue))
                elif key == 'ImportIssue':
                    for issue in self[key]:
                        for k in issue:
                            if k in BidsBrick.get_list_subclasses_names() and issue[k] and \
                                    issue[k][0]['sub'] == brick2remove['sub']:
                                new_issue[key].pop(new_issue[key].index(issue))
                                break  # only one element is not empty, break when found
            elif isinstance(brick2remove, (ModalityType, GlobalSidecars)):
                if key == 'ImportIssue':
                    for issue in self[key]:
                        if issue[brick2remove.classname()] and \
                                issue[brick2remove.classname()][0]['fileLoc'] == brick2remove['fileLoc']:
                            new_issue[key].pop(new_issue[key].index(issue))
                            break
                else:
                    for issue in self[key]:
                        if os.path.basename(issue['fileLoc']) == os.path.basename(brick2remove['fileLoc']):
                            new_issue[key].pop(new_issue[key].index(issue))
                            break
            # elif not key == 'ElectrodeIssue' and (isinstance(brick2remove, Imagery) or
            #                                       isinstance(brick2remove, GlobalSidecars)):
            #     for issue in self[key]:
            #         if issue[brick2remove.classname()] and \
            #                 issue[brick2remove.classname()][0]['fileLoc'] == brick2remove['fileLoc']:
            #             new_issue[key].pop(new_issue[key].index(issue))
            #             break

        self.clear()
        self.copy_values(new_issue)

    def verif_upload_issues(self, import_dir):
        state_list = [up_iss['state'] == 'verified' for up_iss in self['UpldFldrIssue'] if up_iss['path'] == import_dir]
        if state_list:
            return all(state_list)
        else:  # all([]) => True; means that if verif issue was removed than you can import it, not the wanted behaviour
            return False

    @staticmethod
    def empty_dict():
        keylist = ['sub', 'mod', 'RefElectrodes', 'MismatchedElectrodes', 'fileLoc', 'brick', 'description']
        return {key: None for key in keylist}


''' Additional class to handle pipelines and relative actions '''


class Pipeline(BidsDataset):

    keylist = ['SubjectProcess', 'name', 'DatasetDescJSON', 'ParticipantsTSV']
    curr_name = None
    list_ext = ['.nii', '.vhdr', '.txt']

    def __init__(self):
        self.requirements = BidsDataset.requirements
        self.parsing_path = BidsDataset.parsing_path
        self.log_path = BidsDataset.log_path
        self.curr_subject = {'SubjectProcess': SubjectProcess(), 'isPresent': False, 'index': None}

        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsJSON.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

    def parse_filename_dervivatives(self, mod_dict, file):
        fname_pieces = file.split('_')
        for word in fname_pieces:
            w = word.split('-')
            if len(w) == 2 and w[0] in mod_dict.keys():
                mod_dict[w[0]] = w[1]
        if 'modality' in mod_dict and not mod_dict['modality']:
            mod_dict['modality'] = fname_pieces[-1]
        return mod_dict

    def get_attributes_from_BidsSource(self, index_sub, Bids_dir_source, subject_id):
        sub_list = Bids_dir_source.get_subject_list()
        for sub in sub_list:
            if sub == subject_id:
                index_source = sub_list.index(sub)
                self['SubjectProcess'][index_sub]['age'] = Bids_dir_source['Subject'][index_source]['age']
                self['SubjectProcess'][index_sub]['sex'] = Bids_dir_source['Subject'][index_source]['sex']

    def add_subject(self, sub):
        if not self['SubjectProcess']:
            self['SubjectProcess'] = SubjectProcess()
            self['SubjectProcess'][-1].update(sub.get_attributes())
        else:
            self['SubjectProcess'].append(SubjectProcess())
            self['SubjectProcess'][-1].update(sub.get_attributes())
        part_present, part_info, part_index = self['ParticipantsTSV'].is_subject_present(sub['sub'])
        if not part_present:
            self['ParticipantsTSV'].add_subject(sub)

    def update_bids_original(self, bids_origin, modality):
        pip = bids_origin.curr_pipeline['Pipeline']
        mod_type = modality.classname()
        for sub in self['SubjectProcess']:
            tmp_attr = modality.get_attributes()
            tmp_attr['fileLoc'] = sub[mod_type][-1]['fileLoc']
            for sub_origin in pip['SubjectProcess']:
                if sub['sub'] == sub_origin['sub']:
                    sub_origin[mod_type] = create_subclass_instance(mod_type, Process)
                    sub_origin[mod_type][-1].update(tmp_attr)


class Info(BidsFreeFile):
    pass


class Command(BidsBrick):
    keylist = ["tag", "Info"]
    required_keys = keylist


class Settings(BidsBrick):
    keylist = ["label", "fileLoc", "Command", 'automatic']
    required_keys = keylist[0:1]


class PipelineSettings(BidsBrick):
    keylist = ['Settings']
    required_keys = keylist
    recognised_keys = ['bids_dir', 'sub']

    def read_file(self):
        if os.path.exists('pipeline_settings.json'):
            with open('pipeline_settings.json', 'r') as file:
                rd_json = json.load(file)
            self.copy_values(rd_json)

    def propose_param(self, bidsdataset, idx):
        if not isinstance(bidsdataset, BidsDataset):
            return
        selected_pip = self['Settings'][idx]
        proposal = dict()
        for elmt in selected_pip['Command']:
            if 'sub' in elmt['Info']:
                proposal['sub'] = bidsdataset.get_subject_list()
        return proposal

    def launch_pipeline(self, idx):
        pass


def subclasses_tree(brick_class, nb_space=0):
    if nb_space:
        tree_str = '|--'
    else:
        tree_str = ''
    sub_classes_tree = nb_space * ' ' + tree_str + brick_class.__name__ + str(brick_class.keylist) + '\n'
    nb_space += 2
    for subcls in brick_class.__subclasses__():
        sub_classes_tree += subclasses_tree(subcls, nb_space=nb_space)
    return sub_classes_tree


def latest_file(folderpath, file_type):
    try:
        list_of_files = os.listdir(folderpath)

        if file_type == 'parsing':
            ext = '.json.gz'
            condition = lambda fname: fname.startswith('parsing')
        elif file_type == 'log':
            ext = '.log'
            condition = lambda fname: fname.endswith(ext)
        elif file_type == 'issue':
            ext = '.json'
            condition = lambda fname: fname.startswith('issue') and fname.endswith(ext)
        else:
            raise NotImplementedError()
        list_of_specific_files = [file for file in list_of_files if condition(file)]
        date_obj = [
            datetime.strptime(file.replace(ext, '').split('_')[-1], BidsBrick.time_format)
            for file in list_of_specific_files]

        latest_dt = max(dt for dt in date_obj)
        return os.path.join(folderpath, list_of_specific_files[date_obj.index(latest_dt)])

    except Exception as err:
        print(str(err))
        return None


def create_subclass_instance(name, superclasse):
    sucl_list = Process.get_list_subclasses_names()
    if name in sucl_list:
        ind_class = sucl_list.index(name)
        newclass = superclasse.__subclasses__()[ind_class]
    else:
        newclass = type(name, (superclasse,), {}) #To add a base key.capitalize()
        newclass.__module__ = superclasse.__module__
    str = name.split('P')[0]
    instance = newclass()
    instance['modality'] = str.lower()

    return instance


if __name__ == '__main__':

    if len(argv) == 1 or len(argv) > 3:
        cls_tree_str = subclasses_tree(BidsBrick)
        print(cls_tree_str)
        cls_tree_str = subclasses_tree(BidsSidecar)
        print(cls_tree_str)
        # exit('bidsification.py should be launched with at least on argument.\n bidsification.py bids_directory '
        #          '[import_directory]')
    elif len(argv) == 2:
        # parse the directory and initialise the bids_data instance
        bids_dataset = BidsDataset(argv[1])

    # if len(argv) == 3:
    #     # read the data2import folder and initialise the the data2import by reading the data2import.json
    #     data2import = Data2Import(argv[2])
    #     # import the data in the bids_directory
    #     bids_dataset.import_data(data2import)


