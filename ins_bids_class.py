import os
import json
from datetime import datetime
import pprint
<<<<<<< HEAD
import gzip
import shutil
from numpy import random as rnd

''' Three main bricks: BidsBrick: to handles the modality and high level directories, BidsBrickJSON: to handles the JSON 
sidecars, BidsBrickTSV: to handle the tsv sidecars. '''
=======
import shutil
from numpy import random as rnd
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class BidsBrick(dict):

    keylist = ['sub']
    keybln = [False]
    required_keys = ['sub']

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

        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

    def __setitem__(self, key, value):

        if key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names():
                # if value and eval('type(value) == ' + key):
                if value and isinstance(value, BidsBrick):
                    # check whether the value is from the correct class when not empty
                    self[key].append(value)
                else:
                    dict.__setitem__(self, key, [])
            elif key in BidsBrickJSON.get_list_subclasses_names():
                if value and isinstance(value, BidsBrickJSON):
                    # check whether the value is from the correct class when not empty
                    super().__setitem__(key, value)
                else:
                    dict.__setitem__(self, key, {})
            elif key in BidsBrickTSV.get_list_subclasses_names():
                # if value and eval('type(value) == ' + key):
                if value and isinstance(value, BidsBrickTSV):
                    # check whether the value is from the correct class when not empty
                    super().__setitem__(key, value)
                else:
                    dict.__setitem__(self, key, [])
            else:
                dict.__setitem__(self, key, value)
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def __delitem__(self, key):
        if key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def pop(self, key, val=None):
        if key in self.keylist:
            value = self[key]
            if key in BidsBrick.get_list_subclasses_names() or key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
            return value
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def popitem(self):
        value = []
        for key in self.keylist:
            value.append(self[key])
            if key in BidsBrick.get_list_subclasses_names() or key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        return value

    def clear(self):
        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsBrickTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

    def has_all_req_attributes(self, missing_elements=None):  # check if the required attributes are not empty to create
        # the filename (/!\ Json or coordsystem checked elsewhere)
        if not missing_elements:
            missing_elements = ''

        for key in self.keylist:
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
<<<<<<< HEAD
            if 'modality' in mod_dict and not mod_dict['modality']:
                mod_dict['modality'] = fname_pieces[-1]
=======
            mod_dict['modality'] = fname_pieces[-1]
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

        if isinstance(self, BidsBrick):
            if 'fileLoc' in self.keys() and self['fileLoc']:
                filename = self['fileLoc']
            elif not fname:
                filename = fname
            else:
                return
            filename, ext = os.path.splitext(os.path.basename(filename))
            if ext.lower() == '.gz':
                filename, ext = os.path.splitext(filename)
            if ext.lower() in self.allowed_file_formats:
                parse_filename(self, filename)

    def get_sidecar_files(self):  # find corresponding JSON file and read its attributes and save fileloc

        def find_sidecar_file(sidecar_dict, fname, dirname):
            piece_fname = fname.split('_')
            if sidecar_dict.inheritance:
                while os.path.dirname(dirname) != BidsDataset.bids_dir:
                    dirname = os.path.dirname(dirname)
                    has_broken = False
                    with os.scandir(dirname) as it:
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
                if os.path.dirname(dirname) == BidsDataset.bids_dir:
                    dirname = os.path.dirname(dirname)
                    piece_fname = [value for _, value in enumerate(piece_fname) if not (value.startswith('sub-') or
                                                                                        value.startswith('ses-'))]
                    has_broken = False
                    with os.scandir(dirname) as it:
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
                dirname = os.path.dirname(dirname)
                has_broken = False
                with os.scandir(dirname) as it:
                    for entry in it:
                        entry_fname, entry_ext = os.path.splitext(entry.name)
                        if entry_ext.lower() == '.gz':
                            entry_fname, entry_ext = os.path.splitext(entry.name)
                        if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                sidecar_dict.modality_field:
                            for idx in range(1, len(piece_fname)):
                                # a bit greedy because some case are not possible but should work
                                j_name = '_'.join(piece_fname[0:-idx] + [[sidecar_dict.modality_field]]) + \
                                         sidecar_dict.extension
                                if entry.name == j_name:
                                    # jsondict['fileLoc'] = entry.path
                                    sidecar_dict.read_file(entry.path)
                                    has_broken = True
                                    break
                        if has_broken:
                            break
            sidecar_dict.has_all_req_attributes()

<<<<<<< HEAD
        #  firstly, check whether the subclass needs a JSON or a TSV files
        sidecar_flag = [value for counter, value in enumerate(self.keylist) if 'TSV' in value or 'JSON' in value]
        print(sidecar_flag)
=======
        #  firstly, check whether the subclass needs a JSON file
        json_flag = [value for counter, value in enumerate(self.keyList) if 'JSON' in value]
        if issubclass(type(self), BidsBrick) and json_flag:
            if 'fileLoc' in self.keys() and self['fileLoc']:
                filename, ext = os.path.splitext(os.path.basename(self['fileLoc']))
                if ext == '.gz':
                    filename, ext = os.path.splitext(filename)
                self[json_flag[0]] = eval(json_flag[0] + '()')
                find_json_file(self[json_flag[0]], filename, self['fileLoc'])
                if filename:
                    self[json_flag[0]].simplify_json(required_only=False)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

        if issubclass(type(self), BidsBrick) and sidecar_flag:
            if 'fileLoc' in self.keys() and self['fileLoc']:
                root_dir = self['fileLoc'].replace(BidsDataset.bids_dir, '')
                if 'sourcedata' not in root_dir:
                    # only look for sidecar if in raw folder
                    filename, ext = os.path.splitext(os.path.basename(self['fileLoc']))
                    if ext.lower() == '.gz':
                        filename, ext = os.path.splitext(filename)
                    for sidecar_tag in sidecar_flag:
                        if 'modality' in self and not eval(sidecar_tag + '.modality_field'):
                            print(sidecar_tag)
                            self[sidecar_tag] = eval(sidecar_tag + '(modality_field=self["modality"])')
                        else:
                            self[sidecar_tag] = eval(sidecar_tag + '()')
                        find_sidecar_file(self[sidecar_tag], filename, self['fileLoc'])
                        self[sidecar_tag].simplify_sidecar(required_only=False)
            else:
                print('Need fileLoc first!')

    def save_json(self, savedir, file_start=None):
        if os.path.isdir(savedir):
            if not file_start:
                file_start = ''
            else:
                if isinstance(file_start, str):
                    if not file_start.endswith('_'):
                        file_start += '_'
                else:
                    TypeError('file_start should be a string.')

            now = datetime.now()
            output_fname = os.path.join(savedir, file_start + type(self).__name__ + '_' +
                                        now.strftime("%Y-%m-%dT%H-%M-%S") + '.json')
            with open(output_fname, 'w') as f:
                json.dump(self, f, indent=1, separators=(',', ': '), ensure_ascii=False)
            with open(output_fname, 'rb') as f_in, \
                    gzip.open(output_fname + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(output_fname)
        else:
            raise TypeError('savedir should be a directory.')

    def __str__(self):
        return pprint.pformat(self)

    def get_modality_type(self):
        return type(self).__name__.lower()

    def get_modality_attributes(self):
        if self.get_modality_type().capitalize() in Subject.get_list_modality_type():
            attr_dict = {key: self[key] for cnt, key in enumerate(self.keylist) if not self.keybln[cnt]}
            attr_dict.pop('fileLoc')
            return attr_dict
        return {}

    def get_modality_sidecars(self):
        if self.get_modality_type().capitalize() in Subject.get_list_modality_type():
                return {key: self[key] for key in self if isinstance(self[key], list) or isinstance(self[key], dict)}
        return {}

<<<<<<< HEAD
    # @staticmethod
    # def create_keytype(keylist):
    #     keytype = [0]*len(keylist)
    #     for key in keylist:
    #         keytype.append(key in BidsBrick.get_list_subclasses_names())
    #     return keytype
=======
    @staticmethod
    def create_keybln(keylist):
        keybln = []
        for key in keylist:
            keybln.append(key in BidsBrick.get_list_subclasses_names() + BidsJSONBrick.get_list_subclasses_names())
        return keybln
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


<<<<<<< HEAD
# class BidsBrickSidecar(dictr)


class BidsBrickJSON(dict):
=======
class BidsJSONBrick(dict):
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    bids_default_unknown = 'n/a'
    inheritance = True
    extension = '.json'
    modality_field = ''
    keylist = []
    required_keys = []

    def __init__(self, keylist=None, required_keys=None, modality_field=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        if not modality_field:
            self.modality_field = self.__class__.modality_field
        else:
            self.modality_field = modality_field
        self.is_complete = False
        if not keylist:
            self.keylist = self.__class__.keylist
        else:
            self.keylist = keylist
        if not required_keys:
            self.required_keys = self.__class__.required_keys
        else:
            self.required_keys = required_keys
<<<<<<< HEAD
        for item in self.keylist:
            self[item] = BidsBrickJSON.bids_default_unknown
=======
        for item in keylist:
            self[item] = BidsJSONBrick.bids_default_unknown
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        if self.required_keys:
            for key in self.required_keys:
                if key not in self or self[key] == BidsBrickJSON.bids_default_unknown:
                    self.is_complete = False
        self.is_complete = True

    def simplify_sidecar(self, required_only=True):
        list_key2del = []
        for key in self:
<<<<<<< HEAD
            if (self[key] == BidsBrickJSON.bids_default_unknown and key not in self.required_keys) or \
=======
            if (self[key] == BidsJSONBrick.bids_default_unknown and key not in self.required_keys) or \
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
                    (required_only and key not in self.required_keys):
                list_key2del.append(key)
        for key in list_key2del:
            del(self[key])
        # for k in list_key_del:
        #     del()

<<<<<<< HEAD
    def read_file(self, filename):
        if os.path.isfile(filename):
            if os.path.splitext(filename)[1] == '.json':
                read_json = json.load(open(filename))
                for key in read_json:
                    if (key in self.keylist and self[key] == BidsBrickJSON.bids_default_unknown) or \
                            key not in self.keylist:
                        self[key] = read_json[key]

    def write_file(self, jsonfilename):
        if os.path.splitext(jsonfilename)[1] == '.json':
            with open(os.path.join(jsonfilename), 'w') as f:
                json.dump(self, f, indent=2, separators=(',', ': '), ensure_ascii=False)
        else:
            raise TypeError('File is not ".json".')
=======
    def read_json_file(self, filename):
        read_json = json.load(open(filename))
        for key in read_json:
            if (key in self.keylist and self[key] == BidsJSONBrick.bids_default_unknown) or key not in self.keylist:
                self[key] = read_json[key]
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


<<<<<<< HEAD
class ImageryBrickJSON(BidsBrickJSON):
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

    def get_attribute_from_converter_json(self, filename):
        converter_json = json.load(open(filename))
        for key in self.keylist:
            if key in converter_json:
                self[key] = converter_json[key]


class ElectrophyBrickJSON(BidsBrickJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

    def get_attribute_from_converter_json(self, filename):  # To be implemented
        pass
        # dcm2niix_json = json.load(open(filename))
        # for key in self.keylist:
        #     if key in dcm2niix_json:
        #         self[key] = dcm2niix_json[key]


class BidsBrickTSV(list):

    bids_default_unknown = 'n/a'
    inheritance = True
    extension = '.tsv'
    modality_field = ''
    header = []
    required_fields = []

    def __init__(self, header=None, required_fields=None, modality_field=None):
        """initiate a  table containing the header"""
        self.is_complete = False
        if not header:
            self.header = self.__class__.header
        else:
            self.header = header
        if not required_fields:
            self.required_fields = self.__class__.required_fields
        else:
            self.required_fields = required_fields
        if not modality_field:
            self.modality_field = self.__class__.modality_field
        else:
            self.modality_field = modality_field
=======
class BidsTSVBrick(list):

    bids_default_unknown = 'n/a'

    def __init__(self, header=None, required_fields=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        self.is_complete = False
        if not header:
            self.header = []
        else:
            self.header = header
        if not required_fields:
            self.required_fields = []
        else:
            self.required_fields = required_fields
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
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
<<<<<<< HEAD
            super().__setitem__(0, self.header)
=======
            super().__setitem__(0, self.__class__.header)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
            key = slice(1, key.stop, key.step)
        super().__delitem__(key)

    def append(self, dict2append):
        if not isinstance(dict2append, dict):
            raise TypeError('The element to be appended has to be a dict instance.')
        lines = [self.bids_default_unknown]*len(self.header)
        for key in dict2append:
            if key in self.header:
<<<<<<< HEAD
                if not dict2append[key]:
                    dict2append[key] = BidsBrickTSV.bids_default_unknown
                lines[self.header.index(key)] = str(dict2append[key])
        super().append(lines)

    def simplify_sidecar(self, required_only=True):
        pass

    def read_file(self, tsvfilename):
=======
                lines[self.header.index(key)] = str(dict2append[key])
        super().append(lines)

    def read_table(self, tsvfilename):
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
        if os.path.isfile(tsvfilename):
            if os.path.splitext(tsvfilename)[1] == '.tsv':
                with open(os.path.join(tsvfilename), 'r') as file:
                    tsv_header_line = file.readline()
                    tsv_header = tsv_header_line.strip().split("\t")
                    if len([word for word in tsv_header if word in self.required_fields]) >= len(self.required_fields):
                        self.header = tsv_header
                        self[:] = []
                        for line in file:
                            self.append({tsv_header[cnt]: val for cnt, val in enumerate(line.strip().split("\t"))})
                    else:
<<<<<<< HEAD
                        raise AttributeError('Header of ' + os.path.basename(tsvfilename) +
                                             ' does not contain the required fields.')
            else:
                raise TypeError('File is not ".tsv".')

    def write_file(self, tsvfilename):
=======
                        raise AttributeError('Header does not contain the required fields.')
            else:
                raise TypeError('File is not ".tsv".')

    def write_table(self, tsvfilename):
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
        if os.path.splitext(tsvfilename)[1] == '.tsv':
            with open(os.path.join(tsvfilename), 'w') as file:
                for _, line in enumerate(self):
                    file.write('\t'.join(line) + '\n')
        else:
            raise TypeError('File is not ".tsv".')

<<<<<<< HEAD
    def has_all_req_attributes(self):  # check if the required attributes are not empty
        self.is_complete = False  # To be implemented, stay False for the moment

=======
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
    @staticmethod
    def createalias(numsyl=3):
        alias = ''
        consonants = 'zrtpdfklmvbn'
        consonants = consonants.upper()
        num_cons = len(consonants)
        vowels = "aeiou"
        vowels = vowels.upper()
        num_voy = len(vowels)
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

<<<<<<< HEAD
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class EventsTSV(BidsBrickTSV):

    header = ['onset', 'duration', 'trial_type', 'response_time', 'stim_file', 'HED']
    required_fields = ['onset', 'duration']
    modality_field = 'events'


''' The different modality bricks, subclasses of BidsBrick. '''

""" iEEG brick with its file-specific (IeegJSON, IeegChannelsTSV) and global sidecar 
(IeegCoordSysJSON, IeegElecTSV or IeegPhoto) files. """
=======
    def handle_tsv(self, filename, header=None):
        def create_tsv(self, filename, header=None):
            # file = open(os.path.join(rootdir, filename), 'w')
            # if header:
            #     for idx_word in range(0, len(header)):
            #         if idx_word != len(header) - 1:
            #             file.write(header[idx_word] + '\t')
            #         else:
            #             file.write(header[idx_word] + '\n')
            # file.close()
            pass
        pass
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class Ieeg(BidsBrick):

<<<<<<< HEAD
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'IeegJSON',
                                   'IeegChannelsTSV', 'IeegEventsTSV']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['ieeg']
    allowed_file_formats = ['.edf', '.gdf', '.fif']
    readable_file_format = allowed_file_formats + ['.eeg', '.trc']

    def __init__(self):
        super().__init__()
=======
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'recording', 'modality', 'fileLoc', 'IeegJSONBrick', 'IeegChannel',
               'IeegElecLoc', 'IeegElecPic']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['ieeg']
    allowed_file_format = ['.edf', '.gdf', '.fif']
    readable_file_format = allowed_file_format + ['.eeg', '.trc']

    def __init__(self):
        """initiates a  dict var for ieeg info"""
        super().__init__(keylist=Ieeg.keylist, keybln=Ieeg.keybln, required_keys=Ieeg.required_keys)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
        self['modality'] = 'ieeg'


class IeegJSON(BidsBrickJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

<<<<<<< HEAD
    def __init__(self, modality_field):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegJSON.keylist, required_keys=IeegJSON.required_keys, modality_field=modality_field)

=======
    keylist = BidsBrick.keylist + ['ses', 'space', 'modality', 'fileLoc', 'IeegElecJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format + ['.txt']

    def __init__(self):
        """initiate a  dict var for ieeg electrode localisation info"""
        super().__init__(keylist=IeegElec.keylist)
        self['modality'] = 'electrodes'
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

class IeegChannelsTSV(BidsBrickTSV):
    """Store the info of the #_channels.tsv, listing amplifier metadata such as channel names, types, sampling
    frequency, and other information. Note that this may include non-electrode channels such as trigger channels."""

    header = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference', 'group',
              'description', 'status', 'status_description', 'software_filters']
    required_fields = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference']
    modality_field = 'channels'


<<<<<<< HEAD
class IeegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class IeegElecTSV(BidsBrickTSV):
    header = ['name', 'x', 'y', 'z', 'size', 'type', 'material', 'tissue', 'manufacturer', 'grid_size', 'hemisphere']
    required_fields = ['name', 'x', 'y', 'z', 'size']
    modality_field = 'electrodes'


class IeegCoordSysJSON(BidsBrickJSON):
    keylist = ['iEEGCoordinateSystem', 'iEEGCoordinateUnits', 'iEEGCoordinateProcessingDescription', 'IntendedFor',
               'AssociatedImageCoordinateSystem', 'AssociatedImageCoordinateUnits',
               'AssociatedImageCoordinateSystemDescription', 'iEEGCoordinateProcessingReference']
    required_keys = ['iEEGCoordinateSystem', 'iEEGCoordinateUnits', 'iEEGCoordinateProcessingDescription',
                     'IntendedFor', 'AssociatedImageCoordinateSystem', 'AssociatedImageCoordinateUnits']
    modality_field = 'coordsystem'


class IeegPhoto(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'modality', 'fileLoc']
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_formats = ['.jpg', '.png']
    readable_file_format = allowed_file_formats
    modality_field = 'photo'

    def __init__(self):
        super().__init__()
        self['modality'] = self.__class__.modality_field


class IeegGlobalSidecars(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'space', 'fileLoc']
    complementary_keylist = ['IeegElecTSV', 'IeegCoordSysJSON', 'IeegPhoto']
    required_keys = BidsBrick.required_keys
    allowed_file_formats = ['.tsv', '.json'] + IeegPhoto.allowed_file_formats

    def __init__(self, filename):
        """initiates a  dict var for ieeg info"""
        filename = filename.replace('.gz', '')
        filename, ext = os.path.splitext(filename)
        if ext in ['.json', '.tsv']:
            comp_key = [value for counter, value in enumerate(IeegGlobalSidecars.complementary_keylist) if ext.replace
                        ('.', '').upper() in value]
            super().__init__(keylist=IeegGlobalSidecars.keylist + comp_key,
                             required_keys=IeegGlobalSidecars.required_keys)
        elif ext in IeegPhoto.allowed_file_formats and filename.split('_')[-1] == 'photo':
            super().__init__(keylist=IeegPhoto.keylist, required_keys=IeegPhoto.required_keys)
            self['modality'] = 'photo'


""" Anat brick with its file-specific sidecar files."""
=======
    keylist = BidsBrick.keylist + ['ses', 'acq', 'modality', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_format = ['.jpg', '.png']
    readable_file_format = allowed_file_format + ['.ppt', '.pdf']

    def __init__(self):
        """initiate a  dict var for ieeg electrode pictures info"""
        super().__init__(keylist=IeegElecPic.keylist)
        self['modality'] = 'photo'
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class Anat(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'modality', 'fileLoc', 'AnatJSON']
<<<<<<< HEAD
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'PD', 'Pdmap', 'PDT2',
                        'inplaneT1', 'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_formats = ['.nii']
    readable_file_format = allowed_file_formats + ['.dcm']
=======
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'FLASH', 'PD', 'Pdmap', 'PDT2',
                    'inplaneT1', 'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def __init__(self):
        super().__init__()


class AnatJSON(ImageryBrickJSON):
    pass


""" Func brick with its file-specific sidecar files. """


class Func(BidsBrick):

<<<<<<< HEAD
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'modality', 'fileLoc', 'FuncJSON',
                                   'FuncEventsTSV']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['bold', 'sbref']
    allowed_file_formats = ['.nii']
    readable_file_format = allowed_file_formats + ['.dcm']
=======
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'modality', 'fileLoc', 'FuncJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['bold', 'sbref']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def __init__(self):
        super().__init__()


class FuncJSON(ImageryBrickJSON):
    keylist = ImageryBrickJSON.keylist + ['RepetitionTime', 'VolumeTiming', 'TaskName',
                                          'NumberOfVolumesDiscardedByScanner', 'NumberOfVolumesDiscardedByUser',
                                          'DelayTime', 'AcquisitionDuration', 'DelayAfterTrigger',
                                          'NumberOfVolumesDiscardedByScanner', 'NumberOfVolumesDiscardedByUser',
                                          'Instructions', 'TaskDescription', 'CogAtlasID', 'CogPOID']
    required_keys = ['RepetitionTime', 'VolumeTiming', 'TaskName']


class FuncEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


""" Fmap brick with its file-specific sidecar files. """


class Fmap(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'modality', 'fileLoc', 'FmapJSON']
<<<<<<< HEAD
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['phasediff', 'phase1', 'phase2', 'magnitude1', 'magnitude2', 'magnitude', 'fieldmap', 'epi']
    allowed_file_formats = ['.nii']
    readable_file_format = allowed_file_formats + ['.dcm']
=======
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['phasediff', 'phase1', 'phase2', 'magnitude1', 'magnitude2', 'magnitude', 'fieldmap', 'epi']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def __init__(self):
        super().__init__()


class FmapJSON(ImageryBrickJSON):

    required_keys = ['PhaseEncodingDirection', 'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime']


""" Fmap brick with its file-specific sidecar files. """


class Dwi(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'run', 'modality', 'fileLoc', 'DwiJSON']
<<<<<<< HEAD
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['dwi']
    allowed_file_formats = ['.nii']
    readable_file_format = allowed_file_formats + ['.dcm']

    def __init__(self):
        super().__init__()
        self['modality'] = 'dwi'


class DwiJSON(ImageryBrickJSON):
    pass


""" MEG brick with its file-specific sidecar files (To be finalized). """
=======
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['dwi']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for diffusion weighted images info"""
        super().__init__(keylist=Dwi.keylist)
        self['modality'] = 'dwi'
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class Meg(BidsBrick):

<<<<<<< HEAD
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'MegJSON',
                                   'MegEventsTSV']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['meg']
    allowed_file_formats = ['.ctf', '.fif', '4D']
    readable_file_format = allowed_file_formats

    def __init__(self):
        super().__init__()
        self['modality'] = 'meg'


class MegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


""" Behaviour brick with its file-specific sidecar files (To be finalized). """
=======
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['meg']
    allowed_file_format = ['.ctf', '.fif', '4D']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=Meg.keylist, required_keys=Meg.required_keys)
        self['modality'] = 'meg'
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class Beh(BidsBrick):

<<<<<<< HEAD
    keylist = BidsBrick.keylist + ['ses', 'task', 'modality', 'fileLoc', 'BehEventsTSV']
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['beh']
    allowed_file_formats = ['.tsv']
    readable_file_format = allowed_file_formats

    def __init__(self):
        super().__init__()
=======
    keylist = BidsBrick.keylist + ['ses', 'task', 'modality', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['beh']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=Beh.keylist, required_keys=Beh.required_keys)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
        self['modality'] = 'beh'


class BehEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


''' Higher level bricks '''

<<<<<<< HEAD

class Subject(BidsBrick):

    keylist = BidsBrick.keylist + ['age', 'sex', 'alias', 'group', 'Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg', 'Beh',
                                   'IeegGlobalSidecars']
    required_keys = BidsBrick.required_keys

    def __init__(self):
        super().__init__()

    @classmethod
    def get_list_modality_type(cls):
        return ['Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg', 'Beh']
        # [mod_type for cnt, mod_type in enumerate(cls.keylist) if cls.keybln[cnt]]
=======
    @classmethod
    def get_list_modality_type(cls):
        return [mod_type for cnt, mod_type in enumerate(cls.keylist) if cls.keybln[cnt]]
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class SourceData(BidsBrick):

<<<<<<< HEAD
    keylist = ['Subject', 'SrcDataTrack']
=======
    _keylist = ['Subject', 'SrcDataTrack']
    _keybln = BidsBrick.create_keybln(_keylist)
    # _keybln = [True]
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def __init__(self):
        super().__init__()


class Data2Import(BidsBrick):
    keylist = ['uploadDate', 'Subject']

    def __init__(self, data2import_dir):
        """initiate a  dict var for Subject info"""
        super().__init__()
        self.data2import_dir = data2import_dir

    def convert_dcm2niix(self):
        dcm2niix = 'D:/roehri/python/PycharmProjects/readFromUploader/dcm2niix.exe'
        cmd_line_base = dcm2niix + " -b y -ba y -m y -z y -f "
        for pat in self['Subject']:
            for anat in pat['Anat']:
                if os.path.isdir(anat['fileLoc']):
                    # print(cmd_line_base + os.path.basename(anat['fileLoc']) + ' -o ' +
                    #       os.path.split(anat['fileLoc'])[-2]
                    #       + ' ' + anat['fileLoc'])
                    cmd_line = cmd_line_base + os.path.basename(anat['fileLoc']) + ' -o ' + os.path.split(
                        anat['fileLoc'])[-2] + ' ' + anat['fileLoc']
                    os.system(cmd_line)


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


<<<<<<< HEAD
''' Dataset related JSON bricks '''


class DatasetDescJSON(BidsBrickJSON):
=======
class DatasetDescJSON(BidsJSONBrick):

    keylist = ['Name', 'BIDSVersion', 'License', 'Authors', 'Acknowledgements', 'HowToAcknowledge', 'Funding',
               'ReferencesAndLinks', 'DatasetDOI']
    required_keys = ['Name', 'BIDSVersion']

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=DatasetDescJSON.keylist, required_keys=DatasetDescJSON.required_keys)


class ImageryJSONBrick(BidsJSONBrick):
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

    def __init__(self, required_keys=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        keylist = ImageryJSONBrick.keylist
        if not required_keys:
            required_keys = ImageryJSONBrick.required_keys
        super().__init__(keylist=keylist, required_keys=required_keys)

    def get_attribute_from_dcm2niix_json(self, filename):
        dcm2niix_json = json.load(open(filename))
        for key in self.keylist:
            if key in dcm2niix_json:
                self[key] = dcm2niix_json[key]


class AnatJSON(ImageryJSONBrick):
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    keylist = ['Name', 'BIDSVersion', 'License', 'Authors', 'Acknowledgements', 'HowToAcknowledge', 'Funding',
               'ReferencesAndLinks', 'DatasetDOI']
    required_keys = ['Name', 'BIDSVersion']
    filename = 'dataset_description.json'

    def __init__(self):
        super().__init__()

    def write_file(self, jsonfilename=None):
        jsonfilename = os.path.join(BidsDataset.bids_dir, DatasetDescJSON.filename)
        super().write_file(jsonfilename)

<<<<<<< HEAD
    def read_file(self, jsonfilename=None):
        jsonfilename = os.path.join(BidsDataset.bids_dir, DatasetDescJSON.filename)
        super().read_file(jsonfilename)
=======
class FuncJSON(ImageryJSONBrick):
    keylist = ImageryJSONBrick.keylist + ['RepetitionTime', 'VolumeTiming', 'TaskName', 'NumberOfVolumesDiscardedByScanner',
                                     'NumberOfVolumesDiscardedByUser', 'DelayTime', 'AcquisitionDuration',
                                     'DelayAfterTrigger', 'NumberOfVolumesDiscardedByScanner',
                                     'NumberOfVolumesDiscardedByUser', 'Instructions', 'TaskDescription', 'CogAtlasID',
                                     'CogPOID']
    required_keys = ['RepetitionTime', 'VolumeTiming', 'TaskName']
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


''' TSV bricks '''

<<<<<<< HEAD
=======
class FmapJSON(ImageryJSONBrick):
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

class SrcDataTrack(BidsBrickTSV):
    header = ['orig_filename', 'bids_filename', 'upload_date']
    required_fields = ['orig_filename', 'bids_filename', 'upload_date']
    __tsv_srctrack = 'source_data_trace.tsv'

    def __init__(self):
        super().__init__()

<<<<<<< HEAD
    def write_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, 'sourcedata', SrcDataTrack.__tsv_srctrack)
        super().write_file(tsv_full_filename)
=======
class DwiJSON(ImageryJSONBrick):
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def read_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, 'sourcedata', SrcDataTrack.__tsv_srctrack)
        super().read_file(tsv_full_filename)


<<<<<<< HEAD
class ParticipantsTSV(BidsBrickTSV):
    header = ['participant_id', 'age', 'sex', 'alias', 'group', 'upload_date', 'due_date', 'report_date', 'EI_done',
              'Gardel_done', 'Delphos_done']
    required_fields = ['participant_id', 'age']
    __tsv_participants = 'participants.tsv'

    def __init__(self):
        super().__init__()
=======

class IeegJSONBrick(BidsJSONBrick):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegJSONBrick.keylist, required_keys=IeegJSONBrick.required_keys)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def write_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, ParticipantsTSV.__tsv_participants)
        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, ParticipantsTSV.__tsv_participants)
        super().read_file(tsv_full_filename)

    def is_subject_present(self, sub_id):
        if not sub_id.startswith('sub-'):
            sub_id = 'sub-' + sub_id
        participant_idx = self.header.index('participant_id')
        return bool([line for line in self[1:] if sub_id in line[participant_idx]])

    def add_subject(self, sub_dict):
        if isinstance(sub_dict, Subject):
            if not self.is_subject_present(sub_dict['sub']):
                if 'alias' in self.header:
                    alias = self.createalias()
                    self.append({'participant_id': sub_dict['sub'], 'age': sub_dict['age'], 'sex': sub_dict['sex'],
                                 'alias': alias})
                else:
                    self.append({'participant_id': sub_dict['sub'], 'age': sub_dict['age'], 'sex': sub_dict['sex']})

<<<<<<< HEAD

''' Main BIDS brick which contains all the information concerning the patients and the sidecars. It permits to parse a 
given bids dataset, request information (e.g. is a given subject is present, has a given subject a given modality), 
import new data or export a subset of the current dataset (not yet implemented ) '''
=======
class IeegChannel(BidsTSVBrick):
    header = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
              'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
              'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
              'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
              'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
              'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_fields = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(header=IeegChannel.header, required_fields=IeegChannel.required_fields)


class SrcDataTrack(BidsTSVBrick):
    header = ['orig_filename', 'bids_filename', 'upload_date']
    required_fields = ['orig_filename', 'bids_filename', 'upload_date']
    __tsv_srctrack = 'source_data_trace.tsv'

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(header=SrcDataTrack.header, required_fields=SrcDataTrack.required_fields)

    def write_table(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, 'sourcedata', SrcDataTrack.__tsv_srctrack)
        super().write_table(tsv_full_filename)

    def read_table(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, 'sourcedata', SrcDataTrack.__tsv_srctrack)
        super().read_table(tsv_full_filename)


class ParticipantsTSV(BidsTSVBrick):
    header = ['participant_id', 'age', 'sex', 'alias', 'group', 'upload_date', 'due_date', 'report_date', 'EI_done',
              'Gardel_done', 'Delphos_done']
    required_fields = ['participant_id', 'age', 'upload_date']
    __tsv_participants = 'participants.tsv'

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(header=SrcDataTrack.header, required_fields=SrcDataTrack.required_fields)

    def write_table(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, ParticipantsTSV.__tsv_participants)
        super().write_table(tsv_full_filename)

    def read_table(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.bids_dir, ParticipantsTSV.__tsv_participants)
        super().read_table(tsv_full_filename)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1


class BidsDataset(BidsBrick):

<<<<<<< HEAD
    keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDescJSON', 'ParticipantsTSV']
    # _keybln = BidsBrick.create_keytype(_keylist)
=======
    _keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDescJSON']
    _keybln = BidsBrick.create_keybln(_keylist)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
    bids_dir = None

    def __init__(self, bids_dir):
        """initiate a  dict var for patient info"""
        super().__init__()
        self.bids_dir = bids_dir
        self._assign_bids_dir(bids_dir)
        self.parse_bids()

    def parse_bids(self):

        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses)
                    elif not mod_dir and file.name.capitalize() in Subject.get_list_modality_type() and file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.capitalize())
                    elif mod_dir and file.is_file():
                        filename, ext = os.path.splitext(file)
                        if ext.lower() == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext.lower() in eval(mod_dir + '.allowed_file_formats'):
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

        def parse_bids_dir(bids_brick, currdir):

            with os.scandir(currdir) as it:
                for entry in it:
                    if entry.name.startswith('sub-') and entry.is_dir():
                        # bids_brick['Subject'] = Subject('derivatives' not in entry.path and 'sourcedata' not in
                        #                                 entry.path)
                        bids_brick['Subject'] = Subject()
                        bids_brick['Subject'][-1]['sub'] = entry.name.replace('sub-', '')
                        parse_sub_bids_dir(entry.path, bids_brick['Subject'][-1])
                        # since all Bidsbrick that are not string are append [-1] is enough
                    elif entry.name == 'sourcedata' and entry.is_dir():
                        bids_brick['SourceData'] = SourceData()
                        bids_brick['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()
<<<<<<< HEAD
                        bids_brick['SourceData'][-1]['SrcDataTrack'].read_file()
=======
                        bids_brick['SourceData'][-1]['SrcDataTrack'].read_table()
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
                        parse_bids_dir(bids_brick['SourceData'][-1], entry.path)
                    elif entry.name == 'derivatives' and entry.is_dir():
                        bids_brick['Derivatives'] = Derivatives()
                        parse_bids_dir(bids_brick['Derivatives'][-1], entry.path)
                    elif os.path.basename(currdir) == 'derivatives' and isinstance(bids_brick, Derivatives)\
                            and entry.is_dir():
                        bids_brick['Pipeline'] = Pipeline()
                        bids_brick['Pipeline'][-1]['name'] = entry.name
                        parse_bids_dir(bids_brick['Pipeline'][-1], entry.path)

        self.popitem()  # clear the bids variable before parsing to avoid rewrite the same things

        self['DatasetDescJSON'] = DatasetDescJSON()
        self['DatasetDescJSON'].read_file()
        self['ParticipantsTSV'] = ParticipantsTSV()
        self['ParticipantsTSV'].read_file()

        self.popitem()  # clear the bids variable before parsing to avoid rewrite the same things
        parse_bids_dir(self, self.bids_dir)
        save_parsing_path = os.path.join(self.bids_dir, 'derivatives', 'parsing')
        os.makedirs(save_parsing_path, exist_ok=True)
<<<<<<< HEAD
        self.save_json(save_parsing_path, 'parsing')
=======
        self.save_json(save_parsing_path)
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    def is_subject_present(self, subject_label):
        """
        Method that look if a given subject is in the current dataset. It returns a tuple composed
        of a boolean, an integer. The boolean is True if the sub is present, the integer gives its indices in the
        subject list of the dataset.
        Ex: (True, 5) = bids.is_subject_present('05')
        """
        index = -1
        for subject in self['Subject']:
            index += 1
            if subject['sub'] == subject_label:
                return True, index
        index = -1
        return False, index

    def has_subject_modality_type(self, subject_label, modality_type):
        """
        Method that look if a given subject has a given modality type (e.g. Anat, Ieeg). It returns a tuple composed
        of a boolean, an integer and a dict. The boolean is True if the sub has the mod type, the integer gives the
        number of recordings of the modality and the dict returns the number of recordings of each modality
        Ex: (True, 4, {'T1w': 2, 'T2w':2}) = bids.has_subject_modality_type('01', 'Anat')
        """
        modality_type = modality_type.capitalize()
        if modality_type in Subject.get_list_modality_type():
            bln, sub_index = self.is_subject_present(subject_label)
            if bln:
                _, ses_list = self.get_number_of_session4subject(subject_label)
                curr_sub = self['Subject'][sub_index]
                if curr_sub[modality_type]:
                    allowed_mod = eval(modality_type + '.allowed_modality')
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
                                                                'Check Subject.get_list_modality_type().')

    def get_number_of_session4subject(self, subject_label):
        bln, sub_index = self.is_subject_present(subject_label)
        if bln:
            ses_list = []
            sub = self['Subject'][sub_index]
            for mod_type in Subject.get_list_modality_type():
                mod_list = sub[mod_type]
                for mod in mod_list:
                    if mod['ses'] and mod['ses'] not in ses_list:  # 'ses': '' means no session therefore does not count
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
        N = bids.have_data_same_attributes(func_schema)
        """
        nb_runs = 0
        if 'run' in mod_dict_with_attr.keylist:
            mod_type = mod_dict_with_attr.get_modality_type().capitalize()
            if mod_type in Subject.get_list_modality_type():
                bln, sub_index = self.is_subject_present(mod_dict_with_attr['sub'])
                if bln:
                    if self.has_subject_modality_type(mod_dict_with_attr['sub'], mod_type)[0]:
                        mod_input_attr = mod_dict_with_attr.get_modality_attributes()
                        mod_input_attr.pop('run')  # compare every attributes but run
                        for mod in self['Subject'][sub_index][mod_dict_with_attr.get_modality_type().capitalize()]:
                            mod_attr = mod.get_modality_attributes()
                            if mod_attr.pop('run'):
                                if mod_input_attr == mod_attr:
                                    nb_runs += 1

        return nb_runs

    def import_data(self, data2import, keep_sourcedata=True, keep_file_trace=True):

        def push_into_dataset(bids_dst, mod_dict2import, keep_srcdata, keep_ftrack):
            filename, dirname = create_filename_from_attributes(mod_dict2import)
            fname2import, ext2import = os.path.splitext(mod_dict2import['fileLoc'])
            orig_ext = ext2import
            bsname_bids_dir = os.path.basename(bids_dst.bids_dir)
<<<<<<< HEAD
            json_flag = [value for counter, value in enumerate(mod_dict2import.keylist) if 'JSON' in value]
            tsv_flag = [value for counter, value in enumerate(mod_dict2import.keylist) if 'TSV' in value]

=======
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
            if ext2import == '.gz':
                fname2import, ext2import = os.path.splitext(fname2import)
                orig_ext = ext2import + orig_ext

<<<<<<< HEAD
            if ext2import in mod_dict2import.allowed_file_formats:
=======
            if ext2import in mod_dict2import.allowed_file_format:
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
                filename = filename + orig_ext
                os.makedirs(dirname, exist_ok=True)
                # use shutil.move to handle the copy over different volumes
                shutil.move(mod_dict2import['fileLoc'], os.path.join(dirname, filename))
            else:
                raise NotImplementedError('Conversion will be implemented soon')
<<<<<<< HEAD

            if json_flag:
                for json_tag in json_flag:
                    if mod_dict2import[json_tag]:
                        mod_dict2import[json_tag].write_file(
                            os.path.join(dirname, filename.replace(orig_ext, mod_dict2import[json_tag].extension)))
            if tsv_flag:
                for tsv_tag in tsv_flag:
                    if mod_dict2import[tsv_tag]:
                        mod_dict2import[tsv_tag].write_file(
                            os.path.join(dirname, filename.replace(orig_ext, mod_dict2import[tsv_tag].extension)))

=======
>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
            if keep_srcdata:
                scr_data_dirname = dirname.replace(bsname_bids_dir, os.path.join(bsname_bids_dir, 'sourcedata'))
                os.makedirs(scr_data_dirname, exist_ok=True)
                shutil.copy2(os.path.join(dirname, filename),
                             os.path.join(scr_data_dirname, filename))
                if keep_ftrack:
                    now = datetime.now()

                    orig_fname = os.path.basename(mod_dict2import['fileLoc'])
                    upload_date = now.strftime("%Y-%m-%dT%H:%M:%S")
                    scr_track = bids_dst['SourceData'][-1]['SrcDataTrack']
                    scr_track.append({'orig_filename': orig_fname, 'bids_filename': filename,
                                      'upload_date': upload_date})

        def have_data_same_attrs_and_sidecars(bids_dst, mod_dict2import):
            """
            Method that compares whether a given modality dict is the same as the ones present in the bids dataset.
            Ex: True = bids.have_data_same_attrs_and_sidecars(instance of Anat())
            """
            if isinstance(mod_dict2import, BidsBrick) and 'sub' in mod_dict2import.keylist:
                bln, sub_index = bids_dst.is_subject_present(mod_dict2import['sub'])
                if bln:
                    bids_mod_list = bids_dst['Subject'][sub_index][mod_dict2import.get_modality_type().capitalize()]
                    mod_dict2import_attr = mod_dict2import.get_modality_attributes()
                    mod_dict2import_dep = mod_dict2import.get_modality_sidecars()
                    numb_runs = bids_dst.get_number_of_runs(mod_dict2import)
                    for mod in bids_mod_list:
                        mod_in_bids_attr = mod.get_modality_attributes()
                        if mod_dict2import_attr == mod_in_bids_attr:  # check if both mod dict have same attributes
                            if 'run' in mod_dict2import_attr.keys() and mod_dict2import_attr['run']:
                                # if run if a key check the JSON and possibly increment the run integer of mod_
                                # dict2import to import it
                                mod_in_bids_dep = mod.get_modality_sidecars()
                                if not mod_dict2import_dep == mod_in_bids_dep:
                                    # check the sidecar files to verify whether they are the same data, in that the case
                                    # add current nb_runs to 'run' if available otherwise do not import
                                    mod_dict2import_dep['run'] = str(int(mod_dict2import_dep['run'])
                                                                     + numb_runs).zfill(2)
                                    return False
                        else:
                            return False

            else:
                TypeError('Modality to import is not from the correct type. Check BidsBrick.get_list_subclasses_names()')

        def create_path_from_attributes(fname, bids_dir, folder_type):
            piece_dirname = [bids_dir]
            piece_dirname += [shrt_name for _, shrt_name in enumerate(fname.split('_')) if shrt_name.startswith('sub-')
                              or shrt_name.startswith('ses-')]
            piece_dirname += [folder_type]
            dirname = '/'.join(piece_dirname)
            return dirname

        def create_filename_from_attributes(bids_dict):
            filename = ''
            for key in bids_dict.keylist[0:bids_dict.keylist.index('modality')]:
                if bids_dict[key]:
                    filename += key + '-' + bids_dict[key] + '_'
            filename += bids_dict['modality']
            dirname = create_path_from_attributes(filename, BidsDataset.bids_dir, bids_dict.get_modality_type())
            return filename, dirname

        self._assign_bids_dir(self.bids_dir)  # make sure to import in the current bids_dir
        if issubclass(type(data2import), Data2Import) and data2import.has_all_req_attributes()[0]:

            if keep_sourcedata:
                if not self['SourceData']:
                    self['SourceData'] = SourceData()
                    if keep_file_trace:
                        self['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()

            for sub in data2import['Subject']:
                [flag, missing_str] = sub.has_all_req_attributes()
                if flag:
<<<<<<< HEAD
                    self['ParticipantsTSV'].add_subject(sub)
=======

>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1
                    sub_present, sub_index = self.is_subject_present(sub['sub'])
                    if sub_present:
                        nb_ses, bids_ses = self.get_number_of_session4subject(sub['sub'])
                        # print(self.has_subject_modality_type(sub['sub'], 'anat')[-1])
                        for mod_type in Subject.get_list_modality_type():
                            for mod in sub[mod_type]:
                                if mod:
                                    if mod['ses'] and bids_ses:
                                        # if subject is present, have to check if ses in the data2import matches
                                        # the session structures of the dataset (if ses-X already exist than data2import
                                        #  has to have a ses)
                                        bln = have_data_same_attrs_and_sidecars(self, mod)
                                        if not bln:
                                            push_into_dataset(self, mod, keep_sourcedata, keep_file_trace)
                                    else:
                                        print(
                                            'Session structure of the data to be imported does not match the one '
                                            'of the current dataset.\nSession label(s): ' + ', '.join(bids_ses)
                                            + '.\nSubject ' + sub['sub'] + ' ' + mod_type + ' not imported.')
                    else:
                        # if subject is not present, simply import the data
                        for mod_type in Subject.get_list_modality_type():
                            for mod in sub[mod_type]:
                                if mod:
                                    push_into_dataset(self, mod, keep_sourcedata, keep_file_trace)
                else:
                    raise ValueError(missing_str)

<<<<<<< HEAD
            if self['DatasetDescJSON']:
                self['DatasetDescJSON'].write_file()
            if self['ParticipantsTSV']:
                self['ParticipantsTSV'].write_file()
            if keep_sourcedata and keep_file_trace:
                self['SourceData'][-1]['SrcDataTrack'].write_file()
            self.parse_bids()

            shutil.rmtree(data2import.data2import_dir)
=======
            if keep_sourcedata and keep_file_trace:
                self['SourceData'][-1]['SrcDataTrack'].write_table()

            self.popitem()
            self.parse_bids()

            shutil.rmtree(data2import.data2import_dir)


>>>>>>> 1a48678a7229f265ea0d78ae6a1eb83cbc7854d1

    @classmethod
    def _assign_bids_dir(cls, bids_dir):
        cls.bids_dir = bids_dir

    # def __repr__(self):
    #     return 'bids = BidsDataset("C:/Users/datasetdir/your_bids_dir")'


# tsvfilename = 'D:/roehri/PHRC/test/test_import/test.tsv'
# tbl = SrcDataTrack()
# tbl.read_table(tsvfilename)
# del(tbl[:])
# print(tbl)

# print(Ieeg())
# SEEG = Ieeg()
# sub = Subject()
# sub['Ieeg'] = SEEG
# msg_str = sub.has_all_req_attribute()[1]
# print(msg_str)
# bids = BidsDataset('D:/roehri/PHRC/test/PHRC')
# bids.parse_bids()
# bids.save_json(bids.bids_dir)
# pat1 = Subject()
# pat1['sub-ID'] = 'coucou'
# MRI = Anat()
# MRI.has_all_req_attribute()
# MRI['fileLoc'] = 'G:/PostDoc/PHRC/test/PHRC/sub-01/anat/sub-01_acq-flipangle30_run-01_MEFLASH.nii.gz'
# MRI.get_attribute_from_filename()
# MRI.save_json('D:/roehri/PHRC/test/Temp_files_Uploader')

# SEEG = Ieeg()
# SEEG.has_all_req_attribute()

# CT = Anat()
# CT['mod'] = 'CT'
# pat1['Anat'] = CT
# pat1['Anat'] = MRI
# pat2 = Subject()
# pat2['sub-ID'] = 'gredf'
#
# bids['SubjectList'] = pat1
# bids['SubjectList'] = pat2
#
