from bids_manager import ins_bids_class as bids
import shutil
import os
import json


class PipelineTester:

    step_str = ['Creation of empty Bids dataset',
                'Making first data2import.json for sub-01',
                'Importing previous data without checking (Issues)',
                'Importing previous data after check',
                'Making second data2import.json for sub-01 with elec,coordsys,photo',
                'Import with error + solving error',
                'Importing previous data after check',
                'Change electrode type'
                ]
    step_idx = 0
    data_dir = 'all_data_orig'
    curr_dir = ''
    curr_bids = None
    curr_data2import = None

    def check_step(self, bids_flag=True):
        if bids_flag:
            fname = 'parsing_bidsdataset_' + str(self.step_idx+1) + '.json'
            brick = self.curr_bids
        else:
            fname = 'data2import_' + str(self.step_idx + 1) + '.json'
            brick = self.curr_data2import
        step_file = self.read_json(os.path.join(self.curr_dir, self.data_dir, fname))
        diff = brick.difference(step_file, reverse=True)
        # all bricks that contain dates should be removed
        if 'UploadDate' in diff:
            diff.pop('UploadDate')
        if 'SourceData' in diff:
            diff.pop('SourceData')
        if 'ParticipantsTSV' in diff:
            diff.pop('ParticipantsTSV')
        if diff:
            err_str = '[Error step ' + str(self.step_idx+1) + '] ' + fname + \
                      ' is different from the current dataset.\n' + str(diff)
            self.curr_bids.write_log(err_str)
            raise AttributeError(err_str)
        self.step_idx += 1

    def print_init_step(self):
        print('/'*10 + self.step_str[self.step_idx] + '\\'*10)

    @staticmethod
    def read_json(filename):
        with open(filename, 'r') as file:
            rd_json = json.load(file)
        return rd_json


pipeline_tester = PipelineTester()
pipeline_tester.print_init_step()
anywave_path = r'D:\roehri\Anywave\AnyWave.exe'
dcm2nii_path = r'D:\roehri\python\PycharmProjects\readFromUploader\dcm2niix.exe'

'''Creation of empty Bids dataset'''

main_dir = r'D:\roehri\BIDs\sandbox'
dataset_name = 'Pipeline Testing'
pipeline_tester.curr_dir = main_dir
bids_dir = os.path.join(main_dir, 'new_bids')
if os.path.exists(bids_dir):
    shutil.rmtree(bids_dir)
os.makedirs(os.path.join(bids_dir, 'code'))
req_templ_path = os.path.join(main_dir, 'all_data_orig', 'requirements.json')
req_path = os.path.join(bids_dir, 'code', 'requirements.json')
shutil.copy2(req_templ_path, req_path)
bids.BidsDataset.dirname = bids_dir
datasetdesc = bids.DatasetDescJSON()
datasetdesc['Name'] = dataset_name
datasetdesc['Author'] = 'NR'
datasetdesc.write_file()

dataset = bids.BidsDataset(bids_dir)
bids.BidsDataset.converters['Imagery']['path'] = dcm2nii_path
bids.BidsDataset.converters['Electrophy']['path'] = anywave_path
pipeline_tester.curr_bids = dataset
pipeline_tester.check_step()

'''Making first data2import.json for sub-01'''
pipeline_tester.print_init_step()
import_dir = os.path.join(main_dir, 'import_folder')
if os.path.exists(import_dir):
    shutil.rmtree(import_dir)
# os.makedirs(import_dir)
shutil.copytree(os.path.join(main_dir, pipeline_tester.data_dir, 'pat1'), import_dir)

data2impt = bids.Data2Import(import_dir)
datadesc = bids.DatasetDescJSON()
datadesc['Name'] = dataset_name
data2impt['DatasetDescJSON'] = datadesc
pipeline_tester.curr_data2import = data2impt
sub01 = bids.Subject()
elmt_list = []
t1w = bids.Anat()
t1w.update({'ses': 1, 'acq': 'preop', 'modality': 'T1w', 'fileLoc': 'T1w'})
elmt_list.append(t1w)
ct = bids.Anat()
ct.update({'ses': '01', 'modality': 'CT', 'fileLoc': 'CT'})
elmt_list.append(ct)
dwi = bids.Dwi()
dwi.update({'ses': '01', 'acq': 'AP', 'fileLoc': 'dwi'})
elmt_list.append(dwi)
seiz1 = bids.Ieeg()
seiz2 = bids.Ieeg()
seiz3 = bids.Ieeg()
sws1 = bids.Ieeg()
seiz1.update({'ses': '01', 'task': 'seizure', 'run': 1, 'fileLoc': 'seizure_1.eeg'})
seiz2.update({'ses': '01', 'task': 'seizure', 'run': '02', 'fileLoc': 'seizure_2.eeg'})
seiz3.update({'ses': '01', 'task': 'seizure', 'run': 3, 'fileLoc': 'seizure_3.eeg'})
sws1.update({'ses': '01', 'task': 'SWS', 'run': 1, 'fileLoc': 'SWS_1.eeg'})
elmt_list += [seiz1, seiz2, seiz3, sws1]
for elmt in elmt_list:
    sub01.update({elmt.classname(): elmt})
sub01.update({'sub': 1, 'eCRF': 'MAR0080', 'sex': 'M', 'dateOfBirth': '01/01/01'})
data2impt['Subject'] = sub01
data2impt.save_as_json()
dataset.make_upload_issues(data2impt)
pipeline_tester.check_step(bids_flag=False)

'''Importing previous data without checking (Issues)'''
pipeline_tester.print_init_step()
dataset.import_data(data2impt)
pipeline_tester.check_step()

'''Importing previous data after check'''
for issues in pipeline_tester.curr_bids.issues['UpldFldrIssue']:
    issues.add_action('verified!', 'state="verified"')
dataset.apply_actions()
dataset.import_data(data2impt)
pipeline_tester.check_step()

'''Making second data2import.json for sub-01 with elec,coordsys,photo + impotr with error'''
pipeline_tester.print_init_step()
os.remove(os.path.join(import_dir, data2impt.filename))
data2impt = bids.Data2Import(import_dir)
datadesc = bids.DatasetDescJSON()
datadesc['Name'] = dataset_name
data2impt['DatasetDescJSON'] = datadesc
pipeline_tester.curr_data2import = data2impt
sub01 = bids.Subject()
elmt_list = []
elec = bids.IeegGlobalSidecars(os.path.join(import_dir, '_electrodes.tsv'))
coord_sys = bids.IeegGlobalSidecars(os.path.join(import_dir, '_coordsystem.json'))
photo = bids.IeegGlobalSidecars(os.path.join(import_dir, 'drawing1_photo.jpg'))
elec.update({'ses': '01', 'space': 'CT'})
coord_sys.update({'ses': '01', 'space': 'CT'})
photo.update({'ses': '01', 'acq': 'Drawing1'})
elmt_list += [elec, coord_sys, photo]
for elmt in elmt_list:
    sub01.update({elmt.classname(): elmt})
# put error in eCRF and sex
sub01.update({'sub': 1, 'eCRF': 'MAR0081', 'sex': 'F', 'dateOfBirth': '01/01/01'})
data2impt['Subject'] = sub01
data2impt.save_as_json()
# force the verification because tested above
dataset.make_upload_issues(data2impt, force_verif=True)
pipeline_tester.check_step(bids_flag=False)

'''Import with desc and sub errors'''
pipeline_tester.print_init_step()
dataset.import_data(data2impt)
imp_iss = dataset.issues['ImportIssue'][0]
imp_iss.add_action(desc='Modify attrib.', command='sex="M",eCRF="MAR0080",in_bids="False"')
dataset.apply_actions()
data2impt = bids.Data2Import(import_dir)
pipeline_tester.curr_data2import = data2impt
pipeline_tester.check_step(bids_flag=False)


'''Import correctly now'''
pipeline_tester.print_init_step()
dataset.import_data(data2impt)
pipeline_tester.check_step(bids_flag=True)

'''Change electrode type'''
pipeline_tester.print_init_step()
# to be finalized once back! (was already check with bidsmanager)