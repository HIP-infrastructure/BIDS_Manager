import os
import json
from datetime import datetime
import pprint


class BidsBrick(dict):

    keylist = ['sub']
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
            mod_dict['type'] = fname_pieces[-1]

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

    def get_type(self):
        return type(self).__name__.lower()

    @staticmethod
    def create_keybln(keylist):
        keybln = []
        for key in keylist:
            keybln.append(key in BidsBrick.get_list_subclasses_names() + ModalityJSON.get_list_subclasses_names())
        return keybln

    @classmethod
    def get_list_subclasses_names(cls):
        return [noun.__name__ for noun in cls.__subclasses__()]


class ModalityJSON(dict):

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
            self[item] = ModalityJSON.bids_default_unknown

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        if self.required_keys:
            for key in self.required_keys:
                if key in self and not self[key]:
                    self.is_complete = False
        self.is_complete = True

    def simplify_json(self, required_only=True):
        list_key2del = []
        for key in self:
            if (self[key] == ModalityJSON.bids_default_unknown and key not in self.required_keys) or \
                    (required_only and key not in self.required_keys):
                list_key2del.append(key)
        for key in list_key2del:
            del(self[key])
        # for k in list_key_del:
        #     del()

    def read_json_file(self, filename):
        read_json = json.load(open(filename))
        for key in read_json:
            if (key in self.keylist and self[key] == ModalityJSON.bids_default_unknown) or key not in self.keylist:
                self[key] = read_json[key]

    @classmethod
    def get_list_subclasses_names(cls):
        return [noun.__name__ for noun in cls.__subclasses__()]


class Ieeg(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'recording', 'type', 'fileLoc', 'IeegJSON', 'IeegChannel',
               'IeegElecLoc', 'IeegElecPic']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'type']
    allowed_file_format = ['.edf', '.gdf', '.fif']
    readable_file_format = allowed_file_format + ['.eeg', '.trc']

    def __init__(self):
        """initiates a  dict var for ieeg info"""
        super().__init__(keylist=Ieeg.keylist, keybln=Ieeg.keybln, required_keys=Ieeg.required_keys)
        self['type'] = 'ieeg'


class IeegElec(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'space', 'type', 'fileLoc', 'IeegElecJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['type']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format + ['.txt']

    def __init__(self):
        """initiate a  dict var for ieeg electrode localisation info"""
        super().__init__(keylist=IeegElec.keylist)
        self['type'] = 'electrodes'


class IeegElecPic(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'type', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['type']
    allowed_file_format = ['.jpg', '.png', '.tif']
    readable_file_format = allowed_file_format + ['.ppt', '.pdf']

    def __init__(self):
        """initiate a  dict var for ieeg electrode pictures info"""
        super().__init__(keylist=IeegElecPic.keylist)
        self['type'] = 'photo'


class Anat(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'type', 'fileLoc', 'AnatJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['type']
    allowed_type = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'FLASH', 'PD', 'Pdmap', 'PDT2',
                    'inplaneT1', 'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiates a  dict var for anatanomy info"""
        super().__init__(keylist=Anat.keylist)


class Func(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'type', 'fileLoc', 'FuncJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'type']
    allowed_type = ['bold', 'sbref']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for functional imagery info"""
        super().__init__(keylist=Func.keylist, required_keys=Func.required_keys)


class Fmap(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'type', 'fileLoc', 'FmapJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['type']
    allowed_type = ['phasediff', 'phase1', 'phase2', 'magnitude1', 'magnitude2', 'magnitude', 'fieldmap', 'epi']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for field map info"""
        super().__init__(keylist=Fmap.keylist)


class Dwi(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'run', 'type', 'fileLoc', 'DwiJSON']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['type']
    allowed_type = ['dwi']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for diffusion weighted images info"""
        super().__init__(keylist=Dwi.keylist)
        self['type'] = 'dwi'


class Meg(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'type', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'type']
    allowed_type = ['meg']
    allowed_file_format = ['.ctf', '.fif', '4D']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=Meg.keylist, required_keys=Meg.required_keys)
        self['type'] = 'meg'


class Beh(BidsBrick):

    keylist = BidsBrick.keylist + ['ses', 'task', 'type', 'fileLoc']
    keybln = BidsBrick.create_keybln(keylist)
    required_keys = BidsBrick.required_keys + ['task', 'type']
    allowed_type = ['beh']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=Beh.keylist, required_keys=Beh.required_keys)
        self['type'] = 'beh'


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


class DatasetDesc(BidsBrick):

    keylist = ['Name', 'BIDSVersion', 'License', 'Authors', 'Acknowledgements', 'HowToAcknowledge', 'Funding',
               'ReferencesAndLinks', 'DatasetDOI']
    _keybln = BidsBrick.create_keybln(keylist)
    required_keys = ['Name', 'BIDSVersion']
    allowed_file_format = ['.json']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=DatasetDesc.keylist, required_keys=DatasetDesc.required_keys)


class SourceData(BidsBrick):

    _keylist = ['Subject']
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


class ImageryJSON(ModalityJSON):
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
        keylist = ImageryJSON.keylist
        if not required_keys:
            required_keys = ImageryJSON.required_keys
        super().__init__(keylist=keylist, required_keys=required_keys)

    def get_attribute_from_dcm2niix_json(self, filename):
        dcm2niix_json = json.load(open(filename))
        for key in self.keylist:
            if key in dcm2niix_json:
                self[key] = dcm2niix_json[key]


class AnatJSON(ImageryJSON):

    required_keys = []

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__()


class FuncJSON(ImageryJSON):
    keylist = ImageryJSON.keylist + ['RepetitionTime', 'VolumeTiming', 'TaskName', 'NumberOfVolumesDiscardedByScanner',
                                     'NumberOfVolumesDiscardedByUser', 'DelayTime', 'AcquisitionDuration',
                                     'DelayAfterTrigger', 'NumberOfVolumesDiscardedByScanner',
                                     'NumberOfVolumesDiscardedByUser', 'Instructions', 'TaskDescription', 'CogAtlasID',
                                     'CogPOID']
    required_keys = ['RepetitionTime', 'VolumeTiming', 'TaskName']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(required_keys=FuncJSON.required_keys)


class FmapJSON(ImageryJSON):

    required_keys = ['PhaseEncodingDirection', 'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(required_keys=FmapJSON.required_keys)


class DwiJSON(ImageryJSON):

    required_keys = []

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(required_keys=DwiJSON.required_keys)


class IeegJSON(ModalityJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegJSON.keylist, required_keys=IeegJSON.required_keys)


class IeegChannel(ModalityJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = []

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegChannel.keylist, required_keys=IeegChannel.required_keys)


class BidsDataset(BidsBrick):

    _keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDesc']
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
                    if not num_ses and file.name.startswith('ses-') and file.is_dir():
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

        parse_bids_dir(self, self.bids_dir)
        save_parsing_path = os.path.join(self.bids_dir, 'derivatives')
        os.makedirs(save_parsing_path, exist_ok=True)
        self.save_json(save_parsing_path)

    def is_file_present(self, filename):
        is_present = False
        is_present_in_another_format = False
        comment = ''
        if not filename.startswith('sub-'):
            raise SyntaxError('Filename should starts with "sub-"')
        sub_label = filename.split('_')[0].split('-')[1]
        if self.is_subject_present(sub_label):
            pass
        else:
            comment = 'Subject is not present'
        return is_present, is_present_in_another_format, comment

    def is_subject_present(self, subject_label):
        for subject in self['Subject']:
            if subject['sub'] == subject_label:
                return True
        return False

    def import_data(self, data2import, keep_sourcedata=True, keep_file_trace=True):

        def create_path_from_attributes(fname, bids_dir, folder_type):
            piece_dirname = [bids_dir]
            piece_dirname += [shrt_name for _, shrt_name in enumerate(fname.split('_')) if shrt_name.startswith('sub-')
                              or shrt_name.startswith('ses-')]
            piece_dirname += [folder_type]
            dirname = '/'.join(piece_dirname)
            return dirname

        def create_filename_from_attributes(bids_dict):
            filename = ''
            for key in bids_dict.keylist[0:bids_dict.keylist.index('type')]:
                if bids_dict[key]:
                    filename += key + '-' + bids_dict[key] + '_'
            filename += bids_dict['type']
            dirname = create_path_from_attributes(filename, BidsDataset.bids_dir, bids_dict.get_type())
            return filename, dirname

        if issubclass(type(data2import), Data2Import) and data2import.has_all_req_attributes()[0]:
            for sub in data2import['Subject']:
                [flag, missing_str] = sub.has_all_req_attributes()
                if flag:
                    for val in iter(sub.values()):
                        if type(val) == list and val:
                            if issubclass(type(val[0]), BidsBrick):
                                for mod in val:
                                    filename_without_ext, dirname = create_filename_from_attributes(mod)
                                    print(dirname + '\t' + filename_without_ext)
                else:
                    print(missing_str)

    @classmethod
    def _assign_bids_dir(cls, bids_dir):
        cls.bids_dir = bids_dir

    # def __repr__(self):
    #     return 'bids = BidsDataset("C:/Users/datasetdir/your_bids_dir")'


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
