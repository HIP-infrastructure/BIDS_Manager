import os
import json
from datetime import datetime
import pprint
import shutil
from numpy import random as rnd


class BidsBrick(dict):

    keylist = ['sub']
    keybln = [False]
    required_keys = ['sub']

    def __init__(self, keylist, keybln=None, required_keys=None):
        """initiate a  dict var for modality info"""
        self.keyList = keylist
        if keybln:
            self.keyBln = keybln
        else:
            self.keyBln = [False] * len(self.keyList)
        if required_keys:
            self.required_keys = required_keys
        else:
            self.required_keys = []

        for k in range(0, len(self.keyList)):
            key = self.keyList[k]
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''

    def __setitem__(self, key, value):

        if key in self.keyList:
            k = self.keyList.index(key)
            if self.keyBln[k]:
                # if value and eval('type(value) == ' + key):
                if value and issubclass(type(value), BidsBrick):
                    # check whether the value is from the correct class when not empty
                    self[key].append(value)
                else:
                    dict.__setitem__(self, key, [])
            else:
                dict.__setitem__(self, key, value)
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def __delitem__(self, key):
        if key in self.keyList:
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def pop(self, key, val=None):
        if key in self.keyList:
            v = self[key]
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''
            return v
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def popitem(self):
        v = []
        for key in self.keyList:
            v.append(self[key])
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''
        return v

    def clear(self):
        for key in self.keyList:
            print(key)
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''

    def has_all_req_attributes(self, missing_elements=None):  # check if the required attributes are not empty to create
        # the filename (/!\ Json or coordsystem checked elsewhere)
        if not missing_elements:
            missing_elements = ''

        for key in self.keyList:
            if self.required_keys:
                if key in self.required_keys and not self[key]:
                    missing_elements += 'In ' + type(self).__name__ + ', key ' + str(key) + ' is missing.\n'
            if self[key] and isinstance(self[key], list):  # check if self has modality brick, if not empty than
                # recursively check whether it has also all req attributes
                for item in self[key]:
                    if issubclass(type(item), BidsBrick):
                        missing_elements = item.has_all_req_attributes(missing_elements)[1]
        return [not bool(missing_elements), missing_elements]

    def get_attributes_from_filename(self):  # get the attribute from the filename, used when parsing pre-existing
        #  bids dataset

        def parse_filename(mod_dict, file):
            fname_pieces = file.split('_')
            for word in fname_pieces:
                w = word.split('-')
                if len(w) == 2 and w[0] in mod_dict.keys():
                    mod_dict[w[0]] = w[1]
            mod_dict['modality'] = fname_pieces[-1]

        if issubclass(type(self), BidsBrick):
            if 'fileLoc' in self.keys() and self['fileLoc']:
                filename, ext = os.path.splitext(os.path.basename(self['fileLoc']))
                if ext == '.gz':
                    filename, ext = os.path.splitext(filename)
                if ext.lower() in self.allowed_file_format:
                    parse_filename(self, filename)

    def get_json_file(self):  # find corresponding JSON file and read its attributes and save fileloc

        def find_json_file(jsondict, fname, dirname):
            piece_fname = fname.split('_')
            while os.path.dirname(dirname) != BidsDataset.bids_dir:
                dirname = os.path.dirname(dirname)
                has_broken = False
                with os.scandir(dirname) as it:
                    for entry in it:
                        for idx in range(1, len(piece_fname)):
                            # a bit greedy because some case are not possible but should work
                            j_name = '_'.join(piece_fname[0:-idx] + [piece_fname[-1]]) + '.json'
                            if entry.name == j_name:
                                jsondict['fileLoc'] = entry.path
                                jsondict.read_json_file(entry.path)
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
                        for idx in range(1, len(piece_fname)):
                            j_name = '_'.join(piece_fname[0:-idx] + [piece_fname[-1]]) + '.json'
                            if entry.name == j_name:
                                jsondict['fileLoc'] = entry.path
                                jsondict.read_json_file(entry.path)
                                has_broken = True
                                break
                        if has_broken:
                            break
            jsondict.has_all_req_attributes()

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

            else:
                print('Need fileLoc first!')

    def save_json(self, savedir):
        if os.path.isdir(savedir):
            now = datetime.now()
            with open(os.path.join(savedir, 'reading_' + type(self).__name__ + '_' +
                                            now.strftime("%Y-%m-%dT%H-%M-%S") + '.json'), 'w') as f:
                json.dump(self, f, indent=2, separators=(',', ': '), ensure_ascii=False)
        else:
            pass  # throw error

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

    @staticmethod
    def create_keybln(keylist):
        keybln = []
        for key in keylist:
            keybln.append(key in BidsBrick.get_list_subclasses_names() + BidsJSONBrick.get_list_subclasses_names())
        return keybln

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class BidsJSONBrick(dict):

    bids_default_unknown = 'n/a'

    def __init__(self, keylist=None, required_keys=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        self.is_complete = False
        if not keylist:
            self.keylist = []
        else:
            self.keylist = keylist
        if not required_keys:
            self.required_keys = []
        else:
            self.required_keys = required_keys
        for item in keylist:
            self[item] = BidsJSONBrick.bids_default_unknown

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        if self.required_keys:
            for key in self.required_keys:
                if key in self and not self[key]:
                    self.is_complete = False
        self.is_complete = True

    def simplify_json(self, required_only=True):
        list_key2del = []
        for key in self:
            if (self[key] == BidsJSONBrick.bids_default_unknown and key not in self.required_keys) or \
                    (required_only and key not in self.required_keys):
                list_key2del.append(key)
        for key in list_key2del:
            del(self[key])
        # for k in list_key_del:
        #     del()

    def read_json_file(self, filename):
        read_json = json.load(open(filename))
        for key in read_json:
            if (key in self.keylist and self[key] == BidsJSONBrick.bids_default_unknown) or key not in self.keylist:
                self[key] = read_json[key]

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


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
            super().__setitem__(0, self.__class__.header)
            key = slice(1, key.stop, key.step)
        super().__delitem__(key)

    def append(self, dict2append):
        if not isinstance(dict2append, dict):
            raise TypeError('The element to be appended has to be a dict instance.')
        lines = [self.bids_default_unknown]*len(self.header)
        for key in dict2append:
            if key in self.header:
                lines[self.header.index(key)] = str(dict2append[key])
        super().append(lines)

    def read_table(self, tsvfilename):
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
                        raise AttributeError('Header does not contain the required fields.')
            else:
                raise TypeError('File is not ".tsv".')

    def write_table(self, tsvfilename):
        if os.path.splitext(tsvfilename)[1] == '.tsv':
            with open(os.path.join(tsvfilename), 'w') as file:
                for _, line in enumerate(self):
                    file.write('\t'.join(line) + '\n')
        else:
            raise TypeError('File is not ".tsv".')

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


class Ieeg(BidsBrick):

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
        self['modality'] = 'ieeg'


class IeegElec(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'space', 'modality', 'fileLoc', 'IeegElecJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format + ['.txt']

    def __init__(self):
        """initiate a  dict var for ieeg electrode localisation info"""
        super().__init__(keylist=IeegElec.keylist)
        self['modality'] = 'electrodes'


class IeegElecPic(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'modality', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_format = ['.jpg', '.png']
    readable_file_format = allowed_file_format + ['.ppt', '.pdf']

    def __init__(self):
        """initiate a  dict var for ieeg electrode pictures info"""
        super().__init__(keylist=IeegElecPic.keylist)
        self['modality'] = 'photo'


class Anat(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'modality', 'fileLoc', 'AnatJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'FLASH', 'PD', 'Pdmap', 'PDT2',
                    'inplaneT1', 'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiates a  dict var for anatanomy info"""
        super().__init__(keylist=Anat.keylist)


class Func(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'modality', 'fileLoc', 'FuncJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['bold', 'sbref']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for functional imagery info"""
        super().__init__(keylist=Func.keylist, required_keys=Func.required_keys)


class Fmap(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'modality', 'fileLoc', 'FmapJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['phasediff', 'phase1', 'phase2', 'magnitude1', 'magnitude2', 'magnitude', 'fieldmap', 'epi']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for field map info"""
        super().__init__(keylist=Fmap.keylist)


class Dwi(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'run', 'modality', 'fileLoc', 'DwiJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_modality = ['dwi']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for diffusion weighted images info"""
        super().__init__(keylist=Dwi.keylist)
        self['modality'] = 'dwi'


class Meg(BidsBrick):

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


class Beh(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'task', 'modality', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'modality']
    allowed_modality = ['beh']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=Beh.keylist, required_keys=Beh.required_keys)
        self['modality'] = 'beh'


class Subject(BidsBrick):

    keylist = BidsBrick.keylist + ['sex', 'age', 'alias', 'Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg']
    keybln = BidsBrick.create_keybln(keylist)
    # keybln = [False, False, False, False, True, True, True, True, True, True]
    required_keys = BidsBrick.required_keys

    def __init__(self, is_in_main_dir=True):
        """initiate a  dict var for patient info"""
        super().__init__(keylist=Subject.keylist, keybln=Subject.keybln,
                         required_keys=Subject.required_keys)
        self.is_in_main_dir = is_in_main_dir

    @classmethod
    def get_list_modality_type(cls):
        return [mod_type for cnt, mod_type in enumerate(cls.keylist) if cls.keybln[cnt]]


class SourceData(BidsBrick):

    _keylist = ['Subject', 'SrcDataTrack']
    _keybln = BidsBrick.create_keybln(_keylist)
    # _keybln = [True]

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=SourceData._keylist, keybln=SourceData._keybln)


class Data2Import(BidsBrick):
    _keylist = ['uploadDate', 'Subject']
    _keybln = BidsBrick.create_keybln(_keylist)
    # _keybln = [False, True]

    def __init__(self, data2import_dir):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=Data2Import._keylist, keybln=Data2Import._keybln)
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

    _keylist = ['name', 'Subject']
    _keybln = BidsBrick.create_keybln(_keylist)
    # _keybln = [False, True]

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=Pipeline._keylist, keybln=Pipeline._keybln)


class Derivatives(BidsBrick):

    _keylist = ['Pipeline']
    _keybln = BidsBrick.create_keybln(_keylist)
    # _keybln = [True]

    def __init__(self):
        """initiate a  dict var for patient info"""
        super().__init__(keylist=Derivatives._keylist, keybln=Derivatives._keybln)


class Code(BidsBrick):
    pass


class Stimuli(BidsBrick):
    pass


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

    required_keys = []

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__()


class FuncJSON(ImageryJSONBrick):
    keylist = ImageryJSONBrick.keylist + ['RepetitionTime', 'VolumeTiming', 'TaskName', 'NumberOfVolumesDiscardedByScanner',
                                     'NumberOfVolumesDiscardedByUser', 'DelayTime', 'AcquisitionDuration',
                                     'DelayAfterTrigger', 'NumberOfVolumesDiscardedByScanner',
                                     'NumberOfVolumesDiscardedByUser', 'Instructions', 'TaskDescription', 'CogAtlasID',
                                     'CogPOID']
    required_keys = ['RepetitionTime', 'VolumeTiming', 'TaskName']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(required_keys=FuncJSON.required_keys)


class FmapJSON(ImageryJSONBrick):

    required_keys = ['PhaseEncodingDirection', 'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(required_keys=FmapJSON.required_keys)


class DwiJSON(ImageryJSONBrick):

    required_keys = []

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(required_keys=DwiJSON.required_keys)


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


class BidsDataset(BidsBrick):

    _keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDescJSON']
    _keybln = BidsBrick.create_keybln(_keylist)
    bids_dir = None

    def __init__(self, bids_dir):
        """initiate a  dict var for patient info"""
        super().__init__(keylist=BidsDataset._keylist, keybln=BidsDataset._keybln)
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
                    elif not mod_dir and file.name.title() in \
                            [value for counter, value in enumerate(subinfo.keyList) if subinfo.keyBln[counter]]\
                            and file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.title())
                    elif mod_dir and file.is_file():
                        filename, ext = os.path.splitext(file)
                        if ext == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext.lower() in eval(mod_dir + '.allowed_file_format'):
                            subinfo[mod_dir.title()] = eval(mod_dir + '()')
                            # create empty object for the given modality
                            subinfo[mod_dir.title()][-1]['sub'] = subinfo['sub']
                            subinfo[mod_dir.title()][-1]['fileLoc'] = file.path
                            # here again, modified dict behaviour, it appends to a list therefore checking the last
                            # element is equivalent to checking the newest element
                            if num_ses:
                                subinfo[mod_dir.title()][-1]['ses'] = num_ses
                            subinfo[mod_dir.title()][-1].get_attributes_from_filename()
                            subinfo[mod_dir.title()][-1].get_json_file()
                            # need to find corresponding json file and import it in modality json class

        def parse_bids_dir(bids_brick, currdir):

            with os.scandir(currdir) as it:
                for entry in it:
                    if entry.name.startswith('sub-') and entry.is_dir():
                        bids_brick['Subject'] = Subject('derivatives' not in entry.path and 'sourcedata' not in
                                                        entry.path)
                        bids_brick['Subject'][-1]['sub'] = entry.name.replace('sub-', '')
                        parse_sub_bids_dir(entry.path, bids_brick['Subject'][-1])
                        # since all Bidsbrick that are not string are append [-1] is enough
                    elif entry.name == 'sourcedata' and entry.is_dir():
                        bids_brick['SourceData'] = SourceData()
                        bids_brick['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()
                        bids_brick['SourceData'][-1]['SrcDataTrack'].read_table()
                        parse_bids_dir(bids_brick['SourceData'][-1], entry.path)
                    elif entry.name == 'derivatives' and entry.is_dir():
                        bids_brick['Derivatives'] = Derivatives()
                        parse_bids_dir(bids_brick['Derivatives'][-1], entry.path)
                    elif os.path.basename(currdir) == 'derivatives' and isinstance(bids_brick, Derivatives)\
                            and entry.is_dir():
                        bids_brick['Pipeline'] = Pipeline()
                        bids_brick['Pipeline'][-1]['name'] = entry.name
                        parse_bids_dir(bids_brick['Pipeline'][-1], entry.path)
            return bids_brick

        self.popitem()  # clear the bids variable before parsing to avoid rewrite the same things
        parse_bids_dir(self, self.bids_dir)
        save_parsing_path = os.path.join(self.bids_dir, 'derivatives')
        os.makedirs(save_parsing_path, exist_ok=True)
        self.save_json(save_parsing_path)

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
            if ext2import == '.gz':
                fname2import, ext2import = os.path.splitext(fname2import)
                orig_ext = ext2import + orig_ext

            if ext2import in mod_dict2import.allowed_file_format:
                filename = filename + orig_ext
                os.makedirs(dirname, exist_ok=True)
                # use shutil.move to handle the copy over different volumes
                shutil.move(mod_dict2import['fileLoc'], os.path.join(dirname, filename))
            else:
                raise NotImplementedError('Conversion will be implemented soon')
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

            if keep_sourcedata and keep_file_trace:
                self['SourceData'][-1]['SrcDataTrack'].write_table()

            self.popitem()
            self.parse_bids()

            shutil.rmtree(data2import.data2import_dir)



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
