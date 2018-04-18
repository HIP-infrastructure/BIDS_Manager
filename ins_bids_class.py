import os
import json
from datetime import datetime


class BidsBrick(dict):

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
                if value and eval('type(value) == ' + key + 'Info'):
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

    def has_all_req_attribute(self):  # check if the required attributes are not empty
        if self.required_keys:
            for key in self.required_keys:
                if not self[key]:
                    return False
        return True

    def get_attribute_from_filename(self):  # get the attribute from the filename

        def parse_filename(mod_dict, file):
            fname_pieces = file.split('_')
            for word in fname_pieces:
                w = word.split('-')
                if len(w) == 2 and w[0] in mod_dict.keys():
                    mod_dict[w[0]] = w[1]
            mod_dict['type'] = fname_pieces[-1]

        if issubclass(type(self), BidsBrick):
            if 'fileLoc' in self.keys():
                filename, ext = os.path.splitext(os.path.basename(self['fileLoc']))
                if ext == '.gz':
                    filename, ext = os.path.splitext(filename)
                if ext in self.allowed_file_format:
                    parse_filename(self, filename)

    def save_json(self, savedir):
        if os.path.isdir(savedir):
            now = datetime.now()
            with open(os.path.join(savedir, 'reading_' + type(self).__name__ + '_' +
                                            now.strftime("%Y-%m-%dT%H-%M-%S") + '.json'), 'w') as f:
                json.dump(self, f, indent=2, separators=(',', ': '), ensure_ascii=False)
        else:
            pass  # throw error


class IeegInfo(BidsBrick):

    keylist = ['ses', 'task', 'acq', 'run', 'proc', 'recording', 'type', 'fileLoc', 'IeegElecLoc', 'IeegElecPic']
    keybln = [False, False, False, False, False, False, False, False, True, True]
    required_keys = ['task']
    allowed_file_format = ['.edf', '.gdf', '.fif']
    readable_file_format = allowed_file_format + ['.eeg', '.trc']

    def __init__(self):
        """initiate a  dict var for ieeg info"""
        super().__init__(keylist=IeegInfo.keylist, keybln=IeegInfo.keybln, required_keys=IeegInfo.required_keys)


class IeegElecLocInfo(BidsBrick):

    keylist = ['ses', 'space', 'type', 'fileLoc']
    required_keys = []
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format + ['.txt']

    def __init__(self):
        """initiate a  dict var for ieeg electrode localisation info"""
        super().__init__(keylist=IeegElecLocInfo.keylist)


class IeegElecPicInfo(BidsBrick):

    keylist = ['ses', 'acq', 'type', 'fileLoc']
    required_keys = []
    allowed_file_format = ['.jpg', '.png', '.tif']
    readable_file_format = allowed_file_format + ['.ppt', '.pdf']

    def __init__(self):
        """initiate a  dict var for ieeg electrode pictures info"""
        super().__init__(keylist=IeegElecPicInfo.keylist)


class AnatInfo(BidsBrick):

    keylist = ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'type', 'fileLoc']
    required_keys = []
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for anatanomy info"""

        super().__init__(keylist=AnatInfo.keylist)


class FuncInfo(BidsBrick):

    keylist = ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'type', 'fileLoc']
    required_keys = ['task']
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for functional imagery info"""
        super().__init__(keylist=FuncInfo.keylist, required_keys=FuncInfo.required_keys)


class FmapInfo(BidsBrick):

    keylist = ['ses', 'acq', 'dir', 'run', 'type', 'fileLoc']
    required_keys = []
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for field map info"""
        super().__init__(keylist=FmapInfo.keylist)


class DwiInfo(BidsBrick):

    keylist = ['ses', 'acq', 'run', 'type', 'fileLoc']
    required_keys = []
    allowed_file_format = ['.nii']
    readable_file_format = allowed_file_format + ['.dcm']

    def __init__(self):
        """initiate a  dict var for diffusion weighted images info"""
        super().__init__(keylist=DwiInfo.keylist)


class MegInfo(BidsBrick):

    keylist = ['ses', 'task', 'acq', 'run', 'proc', 'type', 'fileLoc']
    required_keys = ['task']
    allowed_file_format = ['.ctf', '.fif', '4D']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=MegInfo.keylist, required_keys=MegInfo.required_keys)


class BehInfo(BidsBrick):

    keylist = ['ses', 'task', 'type', 'fileLoc']
    required_keys = ['task']
    allowed_file_format = ['.tsv']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=BehInfo.keylist, required_keys=BehInfo.required_keys)


class SubjectInfo(BidsBrick):

    keylist = ['sub', 'sex', 'date_of_birth', 'alias', 'uploadDate', 'Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Ieeg']
    keybln = [False, False, False, False, False, True, True, True, True, True, True]
    required_keys = ['sub']

    def __init__(self):
        """initiate a  dict var for patient info"""
        super().__init__(keylist=SubjectInfo.keylist, keybln=SubjectInfo.keybln, required_keys=SubjectInfo.required_keys)


class BidsDataset(BidsBrick):

    _keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli']
    _keybln = [True] * len(_keylist)

    def __init__(self, bids_dir):
        """initiate a  dict var for patient info"""
        super().__init__(keylist=BidsDataset._keylist, keybln=BidsDataset._keybln)
        self.bids_dir = bids_dir

    def parse_bids(self):

        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if not num_ses and file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses)
                    elif not mod_dir and file.name.title() in \
                            [value for counter, value in enumerate(subinfo.keyList) if subinfo.keyBln[counter]]\
                            and file.is_dir():  # enumerate permits to filter the key that corresponds to other subclass
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.title())
                    elif mod_dir and file.is_file():
                        filename, ext = os.path.splitext(file)
                        if ext == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext in eval(mod_dir + 'Info.allowed_file_format'):
                            # print(filename)
                            # handles file extension! add them to an object?!
                            subinfo[mod_dir.title()] = eval(mod_dir + 'Info()')
                            subinfo[mod_dir.title()][-1]['fileLoc'] = file.path
                            if num_ses:
                                subinfo[mod_dir.title()][-1]['ses'] = num_ses

                            subinfo[mod_dir.title()][-1].get_attribute_from_filename()

        def parse_bids_dir(bids_brick, currdir):

            with os.scandir(currdir) as it:
                for entry in it:
                    if entry.name.startswith('sub-') and entry.is_dir():
                        bids_brick['Subject'] = SubjectInfo()
                        bids_brick['Subject'][-1]['sub'] = entry.name.replace('sub-', '')
                        parse_sub_bids_dir(entry.path, bids_brick['Subject'][-1])
                        # since all Bidsbrick that are not string are append [-1] is enough
                    elif entry.name == 'source data' and entry.is_dir():
                        bids_brick['SourceData'] = SourceDataInfo()
                        parse_bids_dir(bids_brick['SourceData'][-1], entry.path)
                    elif entry.name == 'derivatives' and entry.is_dir():
                        bids_brick['Derivatives'] = DerivativesInfo()
                        parse_bids_dir(bids_brick['Derivatives'][-1], entry.path)
                    elif os.path.basename(currdir) == 'derivatives' and isinstance(bids_brick, DerivativesInfo)\
                            and entry.is_dir():
                        bids_brick['Pipeline'] = PipelineInfo()
                        bids_brick['Pipeline'][-1]['name'] = entry.name
                        parse_bids_dir(bids_brick['Pipeline'][-1], entry.path)
            return bids_brick

        parse_bids_dir(self, self.bids_dir)

    def __repr__(self):
        return 'bids = BidsDataset("C:/Users/datasetdir/your_bids_dir")'


class DatasetDescInfo(BidsBrick):

    keylist = ['Name', 'BIDSVersion', 'License', 'Authors', 'Acknowledgements', 'HowToAcknowledge', 'Funding',
               'ReferencesAndLinks', 'DatasetDOI']
    required_keys = ['Name', 'BIDSVersion']
    allowed_file_format = ['.json']
    readable_file_format = allowed_file_format

    def __init__(self):
        """initiate a  dict var for MEG info"""
        super().__init__(keylist=BehInfo.keylist, required_keys=DatasetDescInfo.required_keys)


class SourceDataInfo(BidsBrick):

    _keylist = ['Subject']
    _keybln = [True]

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=SourceDataInfo._keylist, keybln=SourceDataInfo._keybln)


class PipelineInfo(BidsBrick):

    _keylist = ['name', 'Subject']
    _keybln = [False, True]

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=PipelineInfo._keylist, keybln=PipelineInfo._keybln)


class DerivativesInfo(BidsBrick):

    _keylist = ['Pipeline']
    _keybln = [True]

    def __init__(self):
        """initiate a  dict var for patient info"""
        super().__init__(keylist=DerivativesInfo._keylist, keybln=DerivativesInfo._keybln)


class CodeInfo(BidsBrick):
    pass


class StimuliInfo(BidsBrick):
    pass


class ImageryJSONInfo(BidsBrick):
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

    def __init__(self, keylist=None, required_keys=None):
        """initiate a  dict of n/a strings for JSON imagery"""
        if not keylist:
            keylist = ImageryJSONInfo.keylist
        if not required_keys:
            required_keys = ImageryJSONInfo.required_keys
        super().__init__(keylist=keylist, required_keys=required_keys)
        for item in keylist:
            self[item] = 'n/a'


class FmapJSONInfo(ImageryJSONInfo):

    required_keys = ['PhaseEncodingDirection', 'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=super().keylist, required_keys=FmapJSONInfo.required_keys)


class IeegJSONInfo(BidsBrick):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegJSONInfo.keylist, required_keys=IeegJSONInfo.required_keys)


class IeegChannelInfo(BidsBrick):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = []

    def __init__(self):
        """initiate a  dict var for Subject info"""
        super().__init__(keylist=IeegJSONInfo.keylist, required_keys=IeegJSONInfo.required_keys)


# Fmap = FmapJSONInfo()
# bids = BidsDataset('D:/roehri/PHRC/test/PHRC')
# bids.parse_bids()
# bids.save_json(bids.bids_dir)
# pat1 = SubjectInfo()
# pat1['sub-ID'] = 'coucou'
# MRI = AnatInfo()
# MRI.has_all_req_attribute()
# MRI['fileLoc'] = 'G:/PostDoc/PHRC/test/PHRC/sub-01/anat/sub-01_acq-flipangle30_run-01_MEFLASH.nii.gz'
# MRI.get_attribute_from_filename()
# MRI.save_json('D:/roehri/PHRC/test/Temp_files_Uploader')

# SEEG = IeegInfo()
# SEEG.has_all_req_attribute()

# CT = AnatInfo()
# CT['mod'] = 'CT'
# pat1['Anat'] = CT
# pat1['Anat'] = MRI
# pat2 = SubjectInfo()
# pat2['sub-ID'] = 'gredf'
#
# bids['SubjectList'] = pat1
# bids['SubjectList'] = pat2
#
