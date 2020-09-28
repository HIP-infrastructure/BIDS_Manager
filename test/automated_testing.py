#!/usr/bin/python3
# -*-coding:Utf-8 -*

"""
    This script was written by Nicolas Roehri <nicolas.roehri@etu.uni-amu.fr>
    This module is concerned by managing BIDS directory.
    v0.2 June 2019
"""

import unittest
import os
from bids_manager import bids_manager as __bm__, ins_bids_class as bids
import json
import shutil
from importlib import reload
from datetime import datetime

__main_dir__ = r'D:\Data\testing\Test_BM_BP' #r'\\139.124.150.47\dynamap\users\Roehri\BIDs\Bids_testing'
__dataset_name__ = 'Pipeline Testing'
__authors__ = 'Nicolas Roehri'
__copy_flag__ = True


class TestBidsBrickSafety(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """set up the bids diraectory"""
        bids_dataset_dir = 'Made_up_dataset'
        cls.bids_dir = os.path.join(__main_dir__, bids_dataset_dir)

    def test_key_safety(self):
        for mod_type in bids.BidsBrick.get_list_subclasses_names():
            print(mod_type)
            if mod_type in bids.GlobalSidecars.get_list_subclasses_names():
                mod_tmp = getattr(bids, mod_type)(filename=os.path.join(self.bids_dir, 'sub-01', 'ieeg',
                                                                        'sub-01_space-T1w_electrodes.tsv'))
            elif mod_type == 'GlobalSidecars':
                # this method is not usable as such
                return
            else:
                mod_tmp = getattr(bids, mod_type)()
            # verify that one cannot set a key that is not allowed
            with self.assertRaises(KeyError):
                mod_tmp['blublabli'] = '12316'
            # verify that one cannot set non alphanumeric values (otherwise bids path broken,
            # i.e. 'sub-John_Doe' not allowed)
            with self.assertRaises(TypeError):
                mod_tmp['sub'] = '#1234'
            with self.assertRaises(TypeError):
                mod_tmp['sub'] = 'John_Doe'
            with self.assertRaises(TypeError):
                mod_tmp['sub'] = '*test*'
            mod_tmp['sub'] = 5
            self.assertEqual(mod_tmp['sub'], '05')

    def test_modality(self):
        # verify that one cannot set a modality is not allowed
        for mod_type in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names():
            mod_tmp = getattr(bids, mod_type)()
            with self.assertRaises(TypeError):
                mod_tmp['modality'] = 'blublabli'

    def test_run(self):
        # verify that the run value results in a 2 digit string
        for mod_type in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names():
            mod_tmp = getattr(bids, mod_type)()
            mod_tmp['run'] = '05'
            self.assertEqual(mod_tmp['run'], '05')
            mod_tmp['run'] = '5'
            self.assertEqual(mod_tmp['run'], '05')
            mod_tmp['run'] = 5
            self.assertEqual(mod_tmp['run'], '05')
            with self.assertRaises(TypeError):
                mod_tmp['run'] = [4]

    def test_fileLoc(self):
        mr_tmp = bids.Anat()
        # verify that one cannot set a file path to an non-existent file
        with self.assertRaises(FileNotFoundError):
            mr_tmp['fileLoc'] = os.path.join(__main_dir__, 'some_MR.nii')
        # verify that one can only set string as input (even '' for __init__)
        with self.assertRaises(TypeError):
            mr_tmp['fileLoc'] = []
        with self.assertRaises(TypeError):
            mr_tmp['fileLoc'] = 0
        with self.assertRaises(TypeError):
            mr_tmp['fileLoc'] = set()
        with self.assertRaises(TypeError):
            mr_tmp['fileLoc'] = bids.BidsBrick()
        mr_tmp['fileLoc'] = os.path.join(self.bids_dir, 'sub-01', 'anat', 'sub-01_T1w.nii.gz')

    def test_delitem(self):
        for k in range(0, 2):
            sub = bids.Subject()
            mr_tmp = bids.Anat()
            mr_json = bids.AnatJSON()
            mr_tmp['AnatJSON'] = mr_json
            sub['Anat'] = mr_tmp
            mr_tmp.update({'sub': "test", 'run': 1, 'ses': '01', 'modality': 'T1w'})
            if k == 1:
                del (sub['Anat'])
            else:
                pop_item = sub.pop('Anat')
                self.assertEqual(pop_item[0], mr_tmp)
            self.assertEqual(sub['Anat'], [])
            if k == 1:
                del(mr_tmp['run'])
            else:
                pop_item = mr_tmp.pop('run')
                self.assertEqual(pop_item, '01')
            self.assertEqual(mr_tmp['run'], '')
            if k == 1:
                del (mr_tmp['AnatJSON'])
            else:
                pop_item = mr_tmp.pop('AnatJSON')
                self.assertEqual(pop_item, mr_json)
            self.assertEqual(mr_tmp['AnatJSON'], {})
            mr_tmp.clear()
            self.assertEqual(mr_tmp, bids.Anat())

    def test_has_req_attributes(self):
        sub = bids.Subject()
        mr_tmp = bids.Anat()
        mr_json = bids.AnatJSON()
        mr_tmp['AnatJSON'] = mr_json
        sub['Anat'] = mr_tmp
        mr_tmp.update({'run': 1, 'ses': '01', 'modality': 'T1w'})
        flag, miss_elt = sub.has_all_req_attributes()
        self.assertFalse(flag)
        self.assertIsNot(miss_elt, '')
        mr_tmp['fileLoc'] = os.path.join(self.bids_dir, 'sub-01', 'anat', 'sub-01_T1w.nii.gz')
        sub['sub'] = 'test'
        flag, miss_elt = sub.has_all_req_attributes()
        self.assertTrue(flag)
        self.assertIs(miss_elt, '')

    def test_subject_sanity(self):
        sub = bids.Subject()
        sub['sub'] = 'test'
        mr_tmp = bids.Anat()
        mr_json = bids.AnatJSON()
        mr_tmp['AnatJSON'] = mr_json
        sub['Anat'] = mr_tmp
        mr_tmp.update({'sub': 'toto', 'run': 1, 'ses': '01', 'modality': 'T1w'})
        with self.assertRaises(KeyError):
            sub['Anat'] = mr_tmp


class TestParsingBids(unittest.TestCase):
    """This test aims at checking whether ins_bids_class correctly parse an existing Bids directory that was either
    never parse by ins_bids_class (test_existing_bids, i.e. without parsing.json) or already parsed and correctly
    recover information (test_parsingjson_recovery)"""

    @classmethod
    def setUpClass(cls):
        """Read the expected answer in a json and clean up the Made_up_dataset"""
        bids_dataset_dir = 'Made_up_dataset'
        cls.bids_dir = os.path.join(__main_dir__, bids_dataset_dir)
        filename = os.path.join(__main_dir__, 'all_data_orig', 'TestParsing', 'parsing_made_up_dataset.json')
        with open(filename, 'r') as file:
            cls.correct_parsing = json.load(file)
        if os.path.exists(os.path.join(cls.bids_dir, 'derivatives', 'parsing')):
            shutil.rmtree(os.path.join(cls.bids_dir, 'derivatives', 'parsing'))
        if os.path.exists(os.path.join(cls.bids_dir, 'derivatives', 'log')):
            shutil.rmtree(os.path.join(cls.bids_dir, 'derivatives', 'log'))
        if os.path.exists(os.path.join(cls.bids_dir, 'code')):
            shutil.rmtree(os.path.join(cls.bids_dir, 'code'))

    def test_existing_bids(self):
        curr_bids = bids.BidsDataset(self.bids_dir)
        self.assertEqual(curr_bids, self.correct_parsing, "Parsing is wrong.")

    def test_parsing_writing(self):
        parsing_presence = os.path.exists(os.path.join(self.bids_dir, 'derivatives', 'parsing'))
        self.assertTrue(parsing_presence, 'A parsing.json was not written')

    def test_parsingjson_recovery(self):
        curr_bids = bids.BidsDataset(self.bids_dir)
        self.assertEqual(curr_bids, self.correct_parsing, "Parsing was wrongly recovered.")

    def test_small_requests(self):
        curr_bids = bids.BidsDataset(self.bids_dir)
        # test whether subject is present (using participantsTSV)
        for sub in curr_bids['Subject']:
            flag_pres, sub_info, sub_idx = curr_bids['ParticipantsTSV'].is_subject_present(sub['sub'])
            sub_info.pop('Subject_ready')
            self.assertEqual((flag_pres, sub_info, sub_idx), (True, sub.get_attributes(),
                                                              curr_bids['Subject'].index(sub)+1))
        # request if subject has modality of given type and its amount
        for sub in curr_bids['Subject']:
            for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names():
                flag_mod, number, resume = curr_bids.has_subject_modality_type(sub['sub'], mod)
                curr_sub = curr_bids.curr_subject['Subject']
                self.assertEqual((flag_mod, number), (bool(curr_sub[mod]), len(curr_sub[mod])))
        with self.assertRaises(NameError):
            curr_bids.has_subject_modality_type('toto', 'Anat')
        with self.assertRaises(NameError):
            curr_bids.has_subject_modality_type('01', 'Hodpmsoe')
        # request number of run of a given modality
        for sub in curr_bids['Subject']:
            for mod in ['Ieeg', 'Func', 'Fmap', 'Anat']:
                number, max_numb = curr_bids.get_number_of_runs(sub[mod][0])
                curr_sub = curr_bids.curr_subject['Subject']
                act_numb = len([f for f in curr_sub[mod] if f['run']])
                if act_numb == 0:
                    act_numb = None
                self.assertEqual((number, max_numb), (act_numb, act_numb))


class TestImport(unittest.TestCase):
    """This test aims at checking the import system of ins_bids_class"""

    @classmethod
    def setUpClass(cls):
        """Prepare the data2import folder and set up the different path that will be used"""
        reload(bids)
        cls.bids_dir = os.path.join(__main_dir__, 'new_bids')
        cls.import_dir = os.path.join(__main_dir__, 'import_folder')

        if os.path.exists(cls.bids_dir):
            shutil.rmtree(cls.bids_dir)
        if __copy_flag__ and os.path.exists(cls.import_dir):
            shutil.rmtree(cls.import_dir)
        os.makedirs(os.path.join(cls.bids_dir, 'code'))
        # copy to code folder in bids dir the requirements
        req_templ_path = os.path.join(__main_dir__, 'all_data_orig', 'TestImport', 'requirements.json')
        cls.req_filoc = os.path.join(cls.bids_dir, 'code', 'requirements.json')
        shutil.copy2(req_templ_path, cls.req_filoc)
        with open(cls.req_filoc, 'r') as file:
            cls.requirements = json.load(file)
        if __copy_flag__:
            # copy the folder to be imported in import_dir
            shutil.copytree(os.path.join(__main_dir__, 'all_data_orig', 'TestImport', 'pat1'), cls.import_dir)
        bids.BidsDataset.dirname = cls.bids_dir
        datasetdesc = bids.DatasetDescJSON()
        datasetdesc['Name'] = __dataset_name__
        datasetdesc['Authors'] = __authors__
        datasetdesc.write_file()
        fname = os.path.join(__main_dir__, 'all_data_orig', 'TestImport', 'data2import_1.json')
        with open(fname, 'r') as file:
            cls.correct_data2import = json.load(file)
        cls.correct_data2import['UploadDate'] = ''
        fname = os.path.join(__main_dir__, 'all_data_orig', 'TestImport', 'parsing_after_import_1.json')
        with open(fname, 'r') as file:
            cls.correct_parsing = json.load(file)
        if os.path.exists(os.path.join(cls.import_dir, 'data2import.json')):
            os.remove(os.path.join(cls.import_dir, 'data2import.json'))

    def test_writing_data2import(self):
        # give the bids requirements file to update subject keys
        data2impt = bids.Data2Import(self.import_dir, requirements_fileloc=self.req_filoc)
        # check that Subject keys were updated
        flag = all(k for k in self.requirements['Requirements']['Subject']['keys'] if k in bids.Subject.keylist)
        self.assertTrue(flag)
        # write data2import manually
        datadesc = bids.DatasetDescJSON()
        datadesc['Authors'] = __authors__
        datadesc['Name'] = __dataset_name__

        data2impt['DatasetDescJSON'] = datadesc
        # create subject object
        sub01 = bids.Subject()
        elmt_list = []
        # create T1w object
        t1w = bids.Anat()
        t1w.update({'ses': 1, 'acq': 'preop', 'modality': 'T1w', 'fileLoc': 'T1w'})
        # check that integer 1 is stored as '01'
        self.assertEqual(t1w['ses'], '01', "Single digit should be preceded by one zero ('01' instead of '1')")
        elmt_list.append(t1w)
        # create CT object
        ct = bids.Anat()
        ct.update({'ses': '01', 'modality': 'CT', 'fileLoc': 'CT'})
        elmt_list.append(ct)
        # create DWI object
        dwi = bids.Dwi()
        dwi.update({'ses': '01', 'acq': 'AP', 'fileLoc': 'dwi'})
        elmt_list.append(dwi)
        #create pet object
        pet = bids.Pet()
        pet.update({'ses': '01', 'task': 'rest', 'run': '01', 'modality': 'pet', 'fileLoc': 'pet_dicom'})
        elmt_list.append(pet)
        # create meg object
        meg = bids.Meg()
        meg.update({'ses': '01', 'task': 'rest', 'run': '01', 'fileLoc': os.path.join('meg', '1')})
        elmt_list.append(meg)
        # create eeg object
        eeg = bids.Eeg()
        eeg.update({'ses': '01', 'task': 'rest', 'run': '01', 'fileLoc': '32v_EMG_0003.vhdr'})
        elmt_list.append(eeg)
        # create ieeg objects
        seiz1 = bids.Ieeg()
        seiz2 = bids.Ieeg()
        seiz3 = bids.Ieeg()
        sws1 = bids.Ieeg()
        seiz1.update({'ses': '01', 'task': 'seizure', 'run': 1, 'fileLoc': 'seizure_1.eeg'})
        seiz2.update({'ses': '01', 'task': 'seizure', 'run': '02', 'fileLoc': 'seizure_2.eeg'})
        seiz3.update({'ses': '01', 'task': 'seizure', 'run': 3, 'fileLoc': 'seizure_3.eeg'})
        sws1.update({'ses': '01', 'task': 'SWS', 'run': 1, 'fileLoc': 'SWS_1.eeg'})
        elmt_list += [seiz1, seiz2, seiz3, sws1]
        # create coord_sys object
        coord_sys = bids.IeegGlobalSidecars('_coordsystem.json')
        coord_sys.update({'ses': '01', 'space': 'CT'})
        # create electrodes object
        elec = bids.IeegGlobalSidecars('_electrodes.tsv')
        elec.update({'ses': '01', 'space': 'CT'})
        # create photo object
        photo = bids.IeegGlobalSidecars('drawing1_photo.jpg')
        photo.update({'ses': '01', 'acq': 'Drawing1'})
        elmt_list += [elec, coord_sys, photo]
        #create Pet sidecar
        blood_tsv = bids.PetGlobalSidecars('pet_continuous_blood.tsv')
        blood_tsv.update({'ses': '01', 'task': 'rest', 'recording': 'continuous'})
        blood_json = bids.PetGlobalSidecars('pet_continuous_blood.json')
        blood_json.update({'ses': '01', 'task': 'rest', 'recording': 'continuous'})
        elmt_list += [blood_tsv, blood_json]
        for elmt in elmt_list:
            sub01.update({elmt.classname(): elmt})
        #create process import
        anatprocess = bids.AnatProcess()
        anatprocess.update({'sub': '01', 'ses': '01', 'hemi': 'L', 'modality': 'pial', 'fileLoc': 'anat_process_hemi_left.pial'})
        funcprocess = bids.FuncProcess()
        funcprocess.update({'sub': '01', 'ses': '01', 'acq': 'b0', 'modality': 'mean', 'fileLoc': 'func_process'})
        dwiprocess = bids.DwiProcess()
        dwiprocess.update({'sub': '01', 'ses': '01', 'acq': 'b0', 'dir': 'pa', 'modality': 'dwi', 'fileLoc': 'dwi_process'})
        ieegprocess = bids.IeegProcess()
        ieegprocess.update({'sub': '01', 'ses': '01', 'task': 'ccep', 'run': '01', 'desc': 'count', 'modality': 'ieeg', 'fileLoc': 'ieeg_process.tsv'})
        process_list = [anatprocess, funcprocess, dwiprocess, ieegprocess]
        #create dreiv and pipeline
        dev = bids.Derivatives()
        dev['Pipeline'] = bids.Pipeline()
        dev['Pipeline'][-1]['name'] = 'importderiv'
        dev['Pipeline'][-1]['SubjectProcess'] = bids.SubjectProcess()
        dev['Pipeline'][-1]['SubjectProcess'][-1]['sub'] = '01'
        for process in process_list:
            dev['Pipeline'][-1]['SubjectProcess'][-1].update({process.classname(): process})
        dev['Pipeline'][-1]['DatasetDescJSON'] = bids.DatasetDescJSON()
        dev['Pipeline'][-1]['DatasetDescJSON']['Name'] = 'importderiv'
        sub01.update({'sub': 1, 'eCRF': 'MAR0080', 'sex': 'M', 'dateOfBirth': '01/01/01'})
        data2impt['Subject'] = sub01
        data2impt['Derivatives'] = dev
        data2impt['UploadDate'] = ''
        self.assertEqual(data2impt, self.correct_data2import)
        # save data2import.json to make the folder importable for next session (here test)
        data2impt.save_as_json(self.import_dir)

    def test_import_pat1(self):

        # recover the data2import as if it was send by someone
        data2impt = bids.Data2Import(self.import_dir)
        data2impt['UploadDate'] = ''
        self.assertEqual(data2impt, self.correct_data2import)
        # set fixed date to avoid raising error du to different import time
        bids.BidsBrick.access_time = datetime.strptime("2019-01-01T00-00-00", bids.BidsBrick.time_format)
        # import the data in new_bids
        new_bids = bids.BidsDataset(self.bids_dir)
        # import without manually checking the data to import
        new_bids.make_upload_issues(data2impt, force_verif=True)
        new_bids.import_data(data2impt)
        self.update_to_current_date()
        self.assertEqual(new_bids, self.correct_parsing, 'Import 1 went wrong!')

    def test_check_data2import_isempty(self):
        # after each successful file import, the corresponding line of the data2import should be pop out, data2import
        # should be empty at this point
        data2impt = bids.Data2Import(self.import_dir)
        self.assertTrue(data2impt.is_empty(), 'data2import was not emptied')

    def update_to_current_date(self):
        update_idx = self.correct_parsing['ParticipantsTSV'][0].index('upload_date')
        for line in self.correct_parsing['ParticipantsTSV'][1:]:
            line[update_idx] = bids.BidsBrick.access_time.strftime('%Y-%m-%dT%H:%M:%S')

        update_idx = self.correct_parsing['SourceData'][0]['SrcDataTrack'][0].index('upload_date')
        for line in self.correct_parsing['SourceData'][0]['SrcDataTrack'][1:]:
            line[update_idx] = bids.BidsBrick.access_time.strftime('%Y-%m-%dT%H:%M:%S')


class TestIssueImport(unittest.TestCase):
    """This test aims at checking the implemented security during import. Here we won't test the remove method which
    removes data from bids directory which will be handles in its own test"""

    @classmethod
    def setUpClass(cls):
        """Prepare the data2import folder and set up the different path that will be used"""
        reload(bids)
        cls.bids_dir = os.path.join(__main_dir__, 'new_bids')
        cls.import_dir = os.path.join(__main_dir__, 'import_folder')
        if os.path.exists(cls.import_dir):
            if __copy_flag__:
                shutil.rmtree(cls.import_dir)
            else:
                if os.path.exists(os.path.join(cls.import_dir, 'data2import.json')):
                    os.remove(os.path.join(cls.import_dir, 'data2import.json'))
        if os.path.exists(os.path.join(cls.bids_dir, cls.bids_dir, 'derivatives', 'log')):
            # remove previous issue.json
            shutil.rmtree(os.path.join(cls.bids_dir, cls.bids_dir, 'derivatives', 'log'))
        os.makedirs(os.path.join(cls.bids_dir, cls.bids_dir, 'derivatives', 'log'))
        cls.curr_bids = bids.BidsDataset(cls.bids_dir)
        if __copy_flag__:
            shutil.copytree(os.path.join(__main_dir__, 'all_data_orig', 'TestImport', 'pat1'), cls.import_dir)
        data2impt = bids.Data2Import(cls.import_dir)
        # modify data2import manually
        datadesc = bids.DatasetDescJSON()
        datadesc['Authors'] = __authors__
        datadesc['Name'] = 'Some_Name'
        # set different protocol
        data2impt['DatasetDescJSON'] = datadesc
        # create subject object
        sub01 = bids.Subject()
        # create T1w object
        t1w = bids.Anat()
        t1w.update({'ses': 1, 'acq': 'preop', 'modality': 'T1w', 'fileLoc': 'T1w'})
        sub01['Anat'] = t1w
        sub01.update({'sub': 1, 'dateOfBirth': '01/01/01', 'sex': 'F', 'eCRF': 'test'})
        data2impt['Subject'] = sub01
        data2impt.save_as_json()
        cls.data2import = data2impt

    def wrong_protocol(self):
        data2impt = self.data2import
        datadesc = data2impt['DatasetDescJSON']
        self.curr_bids.make_upload_issues(data2impt, force_verif=True)
        self.curr_bids.import_data(data2impt)
        # check that import issue was created
        self.assertTrue(len(self.curr_bids.issues['ImportIssue']) == 1)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # check that the import issue corresponds to the DatasetDescJSON (protocol name differs)
        self.assertTrue(curr_issue['DatasetDescJSON'])
        # case 1: the error is in bids directory, thus change its protocol name
        # case 2: the error is in data2import, thus change its protocol name
        # case 1:
        in_bids = True
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['DatasetDescJSON'], self.curr_bids, in_bids)
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['DatasetDescJSON'], ipt_dict,
                                 otp_dict, in_bids)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.assertEqual(self.curr_bids['DatasetDescJSON']['Name'], datadesc['Name'])
        # check that it was also modified in the file
        self.curr_bids.parse_bids()
        self.assertEqual(self.curr_bids['DatasetDescJSON']['Name'], datadesc['Name'])
        # set it back to real name
        self.curr_bids['DatasetDescJSON']['Name'] = __dataset_name__
        self.curr_bids['DatasetDescJSON'].write_file()
        self.curr_bids.save_as_json()
        # case 2:
        self.curr_bids.make_upload_issues(data2impt, force_verif=True)
        self.curr_bids.import_data(data2impt)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        in_bids = False
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['DatasetDescJSON'], self.curr_bids, in_bids)
        # create an action that will rename the protocol in the data2import
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['DatasetDescJSON'], ipt_dict, otp_dict, in_bids)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.__class__.data2import = bids.Data2Import(self.import_dir)
        self.assertEqual(self.data2import['DatasetDescJSON']['Name'], __dataset_name__)

    def wrong_session_struct(self):
        pass

    def wrong_patient_charac(self):
        self.curr_bids.import_data(self.data2import)
        self.assertTrue(len(self.curr_bids.issues['ImportIssue']) == 1)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # check that the import issue corresponds to a subject issue
        self.assertTrue(curr_issue['Subject'])
        self.curr_bids.is_subject_present(curr_issue['Subject'][0]['sub'])
        # case 1: the error is in bids directory, thus change the subject attributes
        # case 2: the error is in data2import, thus change the subject attributes
        # case 1:
        in_bids = True
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['Subject'][0], self.curr_bids, in_bids)
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['Subject'][0], ipt_dict, otp_dict, in_bids)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        curr_sub_attr = self.curr_bids.curr_subject['Subject'].get_attributes(['alias', 'upload_date'])
        self.assertEqual(curr_sub_attr, otp_dict)
        # check that it was also modified in participants.tsv file
        self.curr_bids.parse_bids()
        self.curr_bids.is_subject_present(curr_issue['Subject'][0]['sub'])
        curr_sub_attr = self.curr_bids.curr_subject['Subject'].get_attributes(['alias', 'upload_date'])
        self.assertEqual(curr_sub_attr, otp_dict)
        # set it back to real name
        # first recreate the previous issue to change back the sub's attributes
        self.curr_bids.issues.add_issue('ImportIssue', brick=self.data2import['Subject'][0], description='')
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['Subject'][0], otp_dict, ipt_dict, True)
        self.curr_bids.apply_actions()
        # case 2:
        # create an action that will set the subject attributes correctly
        in_bids = False
        # recreate the previous issue
        self.curr_bids.issues.add_issue('ImportIssue', brick=self.data2import['Subject'][0], description='')
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['Subject'][0], self.curr_bids, in_bids)
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['Subject'][0], ipt_dict, otp_dict, in_bids)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.__class__.data2import = bids.Data2Import(self.import_dir)
        new_sub_attr = self.data2import['Subject'][0].get_attributes(['alias', 'upload_date', 'fileLoc'])
        self.assertEqual(new_sub_attr, otp_dict)

    def same_source_data(self):

        def rename4next_test(obj):
            if not os.path.exists(os.path.join(obj.import_dir, 'T1w_new')):
                shutil.copytree(os.path.join(obj.import_dir, 'T1w'), os.path.join(obj.import_dir, 'T1w_new'))
            t1w = bids.Anat()
            t1w.update({'sub': 1, 'ses': 1, 'acq': 'preop', 'modality': 'T1w', 'fileLoc': 'T1w_new'})
            obj.data2import['Subject'][0]['Anat'] = t1w
            obj.data2import.save_as_json()
            obj.__class__.data2import = bids.Data2Import(obj.import_dir)

        self.curr_bids.make_upload_issues(self.data2import, force_verif=True)
        self.curr_bids.import_data(self.data2import)
        self.assertTrue(len(self.curr_bids.issues['ImportIssue']) == 1)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # check that the issue is related to the T1w
        self.assertTrue(curr_issue['Anat'])
        # check that the source files have the same names
        str2check = 'a source file with the same name is already present'
        self.assertTrue(str2check in curr_issue['description'])
        # chose not to import this file
        __bm__.make_cmd4pop(curr_issue)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        # load the modified data2import
        self.__class__.data2import = bids.Data2Import(self.import_dir)
        self.assertFalse(self.data2import['Subject'][0]['Anat'])
        rename4next_test(self)

    def file_with_same_attr(self):
        self.curr_bids.import_data(self.data2import)
        self.assertTrue(len(self.curr_bids.issues['ImportIssue']) == 1)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # check that the issue is related to the T1w
        self.assertTrue(curr_issue['Anat'])
        # check that the source files have the same names
        fname, _, _ = self.data2import['Subject'][0]['Anat'][0].create_filename_from_attributes()
        str2check = fname + ' is already present'
        self.assertTrue(str2check in curr_issue['description'])
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['Anat'][0], self.curr_bids, False)
        otp_dict['ses'] = otp_dict['ses'][0]
        otp_dict['modality'] = otp_dict['modality'][6]
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['Anat'][0], ipt_dict, otp_dict, False)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.__class__.data2import = bids.Data2Import(self.import_dir)
        self.assertEqual(self.data2import['Subject'][0]['Anat'][0].get_attributes('fileLoc'), otp_dict)
        self.curr_bids.import_data(self.data2import)

    def wrong_derivatives_protocol_name(self):
        self.curr_bids.parse_bids()
        data2impt = bids.Data2Import(self.import_dir)
        del data2impt['Subject']
        data2impt['DatasetDescJSON']['Name'] = __dataset_name__
        # initiate the value
        bids_dev_name = 'importderiv'
        dat_dev_name = 'deriv'
        dev = bids.Derivatives()
        dev['Pipeline'] = bids.Pipeline()
        dev['Pipeline'][-1]['name'] = 'importderiv'
        dev['Pipeline'][-1]['SubjectProcess'] = bids.SubjectProcess()
        dev['Pipeline'][-1]['SubjectProcess'][-1]['sub'] = '01'
        anatprocess = bids.AnatProcess()
        anatprocess.update({'sub': '01', 'ses': '01', 'hemi': 'L', 'modality': 'pial', 'fileLoc': 'anat_process_hemi_left.pial'})
        dev['Pipeline'][-1]['SubjectProcess'][-1].update({anatprocess.classname(): anatprocess})
        dev['Pipeline'][-1]['DatasetDescJSON'] = bids.DatasetDescJSON()
        dev['Pipeline'][-1]['DatasetDescJSON']['Name'] = dat_dev_name
        data2impt['Derivatives'] = dev
        data2impt.save_as_json()
        self.data2import = data2impt
        self.curr_bids.make_upload_issues(data2impt, force_verif=True)
        self.curr_bids.import_data(data2impt)
        # check that import issue was created
        self.assertTrue(len(self.curr_bids.issues['ImportIssue']) == 1)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # if curr_issue['description'].startswith('Derivatives folder'):
        #     deriv_dir = curr_issue['description'].split(' ')[2]
        # check that the import issue corresponds to the DatasetDescJSON (protocol name differs)
        self.assertTrue(curr_issue['DatasetDescJSON'])
        # case 1: the error is in bids directory, thus change its protocol name
        # case 2: the error is in data2import, thus change its protocol name
        # case 1:
        in_bids = True
        deriv_dir = 'importderiv'
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['DatasetDescJSON'], self.curr_bids, in_bids, deriv_dir)
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['DatasetDescJSON'], ipt_dict,
                                 otp_dict, in_bids, deriv_dir)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.curr_bids.is_pipeline_present(deriv_dir)
        idx_bids = self.curr_bids.curr_pipeline['index']
        self.assertEqual(self.curr_bids['Derivatives'][-1]['Pipeline'][idx_bids]['DatasetDescJSON']['Name'], dat_dev_name)
        self.assertEqual(self.curr_bids['DatasetDescJSON']['Name'], __dataset_name__)
        # check that it was also modified in the file
        self.curr_bids.parse_bids()
        self.assertEqual(self.curr_bids['Derivatives'][-1]['Pipeline'][idx_bids]['DatasetDescJSON']['Name'], dat_dev_name)
        self.assertEqual(self.curr_bids['DatasetDescJSON']['Name'], __dataset_name__)
        # set it back to real name
        self.curr_bids['Derivatives'][-1]['Pipeline'][idx_bids]['DatasetDescJSON']['Name'] = bids_dev_name
        self.curr_bids['Derivatives'][-1]['Pipeline'][idx_bids]['DatasetDescJSON'].write_file(os.path.join(__main_dir__, 'new_bids', 'derivatives', deriv_dir, 'dataset_description.json'))
        self.curr_bids.save_as_json()
        # case 2:
        self.curr_bids.make_upload_issues(data2impt, force_verif=True)
        self.curr_bids.import_data(data2impt)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # if curr_issue['description'].startswith('Derivatives folder'):
        #     deriv_dir = curr_issue['description'].split(' ')[2]
        in_bids = False
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['DatasetDescJSON'], self.curr_bids, in_bids, deriv_dir)
        # create an action that will rename the protocol in the data2import
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['DatasetDescJSON'], ipt_dict, otp_dict, in_bids, deriv_dir)
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.data2import = bids.Data2Import(self.import_dir)
        self.data2import.is_pipeline_present(deriv_dir)
        idx_data = self.data2import.curr_pipeline['index']
        self.assertEqual(self.data2import['Derivatives'][-1]['Pipeline'][idx_data]['DatasetDescJSON']['Name'], bids_dev_name)
        self.assertEqual(self.curr_bids['Derivatives'][-1]['Pipeline'][idx_bids]['DatasetDescJSON']['Name'], bids_dev_name)
        self.assertEqual(self.curr_bids['DatasetDescJSON']['Name'], __dataset_name__)

    def file_with_same_attr_deriv(self):
        data2impt = bids.Data2Import(self.import_dir)
        del data2impt['Subject']
        data2impt['DatasetDescJSON']['Name'] = __dataset_name__
        # initiate the value
        dev = bids.Derivatives()
        dev['Pipeline'] = bids.Pipeline()
        dev['Pipeline'][-1]['name'] = 'importderiv'
        dev['Pipeline'][-1]['SubjectProcess'] = bids.SubjectProcess()
        dev['Pipeline'][-1]['SubjectProcess'][-1]['sub'] = '01'
        anatprocess = bids.AnatProcess()
        anatprocess.update(
            {'sub': '01', 'ses': '01', 'hemi': 'L', 'modality': 'pial', 'fileLoc': 'anat_process_hemi_left.pial'})
        dev['Pipeline'][-1]['SubjectProcess'][-1].update({anatprocess.classname(): anatprocess})
        dev['Pipeline'][-1]['DatasetDescJSON'] = bids.DatasetDescJSON()
        dev['Pipeline'][-1]['DatasetDescJSON']['Name'] = 'importderiv'
        data2impt['Derivatives'] = dev
        data2impt.save_as_json()
        self.data2import = data2impt
        self.curr_bids.make_upload_issues(data2impt, force_verif=True)
        self.curr_bids.import_data(data2impt)
        self.assertTrue(len(self.curr_bids.issues['ImportIssue']) == 1)
        curr_issue = self.curr_bids.issues['ImportIssue'][0]
        # check that the issue is related to the AnatProcess
        self.assertTrue(curr_issue['AnatProcess'])
        # check that the files have the same names
        fname, _, _ = data2impt['Derivatives'][-1]['Pipeline'][-1]['SubjectProcess'][0]['AnatProcess'][0].create_filename_from_attributes()
        str2check = fname + ' is already present'
        self.assertTrue(str2check in curr_issue['description'])
        ipt_dict, otp_dict = __bm__.prepare_chg_attr(curr_issue['AnatProcess'][0], self.curr_bids, False, deriv_folder='importderiv')
        otp_dict['ses'] = otp_dict['ses'][0]
        otp_dict['modality'] = otp_dict['modality'][0]
        __bm__.make_cmd4chg_attr(curr_issue, curr_issue['AnatProcess'][0], ipt_dict, otp_dict, False, deriv_folder='importderiv')
        self.assertTrue(curr_issue['Action'])
        # apply the action
        self.curr_bids.apply_actions()
        self.data2import = bids.Data2Import(self.import_dir)
        self.assertEqual(self.data2import['Derivatives'][-1]['Pipeline'][-1]['SubjectProcess'][0]['AnatProcess'][0].get_attributes('fileLoc'), otp_dict)
        self.curr_bids.import_data(self.data2import)

    def check_issue_file_created(self):
        pass


class TestElectrodeIssues(unittest.TestCase):
    """ these tests aims at handling the potential labelling error that can occur in Ieeg recordings. It does so by
    comparing the 'reference labels' from the electrodes.tsv and the channels.tsv. The user can then either modify the
    mismatched label by choosing from the reference labels, modify the type of channel (EEG channel wrongly tagged as
    SEEG should not appear in electrodes.tsv) or remove the current electrodes.tsv which contains a mistake. """

    @classmethod
    def setUpClass(cls):
        """ reload ins_bids_class and set bids directory """
        reload(bids)
        cls.bids_dir = os.path.join(__main_dir__, 'new_bids')
        cls.curr_bids = bids.BidsDataset(cls.bids_dir)
        cls.issues = cls.curr_bids.issues

    def setUp(self):
        # to update the current bids variable instead of looking at the old class variable
        self.curr_bids.parse_bids()
        self.curr_bids['Subject'][0]['Ieeg'][1]['IeegChannelsTSV'][124][1] = 'SEEG'
        self.curr_bids['Subject'][0]['Ieeg'][1]['IeegChannelsTSV'][126][1] = 'SEEG'
        self.curr_bids.check_requirements()

    def modify_channel_type(self):
        ex_elec_iss = self.issues['ElectrodeIssue'][0]
        # take the electrode OCU which is set as SEEG and turn it to OCU (2nd electrode, first one is EEG)
        mismatch_el = ex_elec_iss['MismatchedElectrodes'][0]['name']
        input_dict, opt_dict = __bm__.prepare_chg_eletype(ex_elec_iss, mismatch_el)
        output_dict = {'type': opt_dict['type'][11]}
        __bm__.make_cmd4electypechg(output_dict, input_dict, ex_elec_iss, mismatch_el)
        self.assertTrue(ex_elec_iss['Action'])
        self.assertEqual(ex_elec_iss['Action'][0]['command'], 'type="EOG"')
        # apply the action
        self.curr_bids.apply_actions()
        # check channels.tsv of corresponding file was change
        # firstly in bids variable
        obj = self.curr_bids.get_object_from_filename(ex_elec_iss['fileLoc'], sub_id=ex_elec_iss['sub'])
        channels = obj['IeegChannelsTSV']
        elmts = channels.find_lines_which('type', 'EOG', 'group')
        self.assertIn('OCU', elmts)
        # secondly in the actual electrode file
        channels = bids.IeegChannelsTSV()
        chnl_file = ex_elec_iss['fileLoc'].replace('_ieeg.vhdr', '_channels.tsv')
        channels.read_file(os.path.join(self.bids_dir, chnl_file))
        elmts = channels.find_lines_which('type', 'EOG', 'group')
        self.assertIn('OCU', elmts)

    def modify_channel_name(self):
        ex_elec_iss = self.curr_bids.issues['ElectrodeIssue'][0]
        # take the electrode MEN rename it in AXG
        mismatch_el = ex_elec_iss['MismatchedElectrodes'][0]['name']
        nw_nme = 'AXG'
        __bm__.make_cmd4elecnamechg(nw_nme, ex_elec_iss, mismatch_el)
        self.assertTrue(ex_elec_iss['Action'])
        self.assertEqual(ex_elec_iss['Action'][0]['command'], 'name="' + nw_nme + '"')
        # apply the action
        self.curr_bids.apply_actions()
        # check channels.tsv of corresponding file was change (both at the group and name level)
        nm_idx = bids.IeegChannelsTSV.header.index('name')
        # firstly in bids variable
        obj = self.curr_bids.get_object_from_filename(ex_elec_iss['fileLoc'], sub_id=ex_elec_iss['sub'])
        channels = obj['IeegChannelsTSV']
        elmts = channels.find_lines_which('group', nw_nme)
        self.assertTrue(elmts)
        self.assertTrue(all(el for el in elmts if nw_nme == el[nm_idx]))
        # secondly in the actual channels.tsv file
        channels = bids.IeegChannelsTSV()
        chnl_file = ex_elec_iss['fileLoc'].replace('_ieeg.vhdr', '_channels.tsv')
        channels.read_file(os.path.join(self.bids_dir, chnl_file))
        elmts = channels.find_lines_which('group', nw_nme)
        self.assertTrue(elmts)
        self.assertTrue(all(el for el in elmts if nw_nme == el[nm_idx]))
        # thirdly in the actual BrainVision file
        hdr = bids.bv_hdr.BrainvisionHeader(os.path.join(self.bids_dir, ex_elec_iss['fileLoc']))
        self.assertIn(nw_nme, hdr.electrode_list)
        channel_names = [hdr.channel_list[cnt]
                         for cnt, el in enumerate(hdr.electrode_list) if el == nw_nme]
        self.assertTrue(all(ch for ch in channel_names if nw_nme == ch))

    def add_to_bidsignore(self):
        ex_bids_issue = self.curr_bids.issues['ValidatorIssue'][1]
        #Add the _CT.nii to bidsignore
        opt_dict = bids.ValidatorIssue.possibility[1]
        str_info = 'The ' + opt_dict + ' of ' + ex_bids_issue['fileLoc'] + ' will be added to bidsignore.\n'
        command = 'type="' + opt_dict + '"'
        ex_bids_issue.add_action(str_info, command)
        self.assertTrue(ex_bids_issue['Action'])
        self.assertEqual(ex_bids_issue['Action'][0]['command'], 'type="' + opt_dict + '"')
        self.curr_bids.apply_actions()
        self.assertIn('*_CT.nii', self.curr_bids.issues.bidsignore)


class TestObjectRemoval(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ reload ins_bids_class and set bids directory """
        reload(bids)
        cls.bids_dir = os.path.join(__main_dir__, 'new_bids')
        cls.curr_bids = bids.BidsDataset(cls.bids_dir)
        cls.issues = cls.curr_bids.issues

    def remove_modality_file(self):
        # remove sub 01 T1w
        t1w = self.curr_bids['Subject'][0]['Anat'][0]
        self.curr_bids.remove(t1w)
        self.check_rmvd_obj(t1w['fileLoc'])
        # parse the bids directory to check that the file were removed
        self.curr_bids.parse_bids()
        self.check_rmvd_obj(t1w['fileLoc'])
        # remove sub 01 first ieeg file
        ieeg = self.curr_bids['Subject'][0]['Ieeg'][0]
        self.curr_bids.remove(ieeg)
        self.check_rmvd_obj(ieeg['fileLoc'])
        # parse the bids directory to check that the file were removed
        self.curr_bids.parse_bids()
        self.check_rmvd_obj(ieeg['fileLoc'])

    def check_rmvd_obj(self, filename):
        obj = self.curr_bids.get_object_from_filename(filename=filename)
        # obj should be None as it does not exist anymore
        self.assertIsNone(obj)
        orig_fname, _, _ = self.curr_bids['SourceData'][0]['SrcDataTrack'].\
            get_source_from_raw_filename(filename=filename)
        # orig_fname should be None as it should be removed from SrcDataTrack
        self.assertIsNone(orig_fname)
        curr_sub = self.curr_bids.curr_subject['Subject']
        line = []
        for elmt in curr_sub['Scans']:
            # strip the subject folder from the full filename
            dirname, fname = os.path.split(filename)
            dirname, mod = os.path.split(dirname)
            subrel_fname = os.path.join(mod, fname)
            line = elmt['ScansTSV'].find_lines_which('filename', subrel_fname)
            if line:  # if line is not empty for any scans object, this means the file was wrongly removed
                break
        # line should be [] as filename should be removed from scans.tsv
        self.assertFalse(line)

    def remove_glbsidecar_file(self):
        self.curr_bids.parse_bids()
        # remove the IeegGlobalSidecars
        ieeglbsdcr = self.curr_bids['Subject'][0]['IeegGlobalSidecars']
        for elmt in ieeglbsdcr:
            self.curr_bids.remove(elmt)
            self.check_rmvd_obj(elmt['fileLoc'])
            # parse the bids directory to check that the file were removed
            self.curr_bids.parse_bids()
            self.check_rmvd_obj(elmt['fileLoc'])

    def remove_subject(self):
        self.curr_bids.parse_bids()
        # remove subject 1
        sub = self.curr_bids['Subject'][0]
        self.curr_bids.remove(sub)
        self.curr_bids.is_subject_present('01')
        self.assertFalse(self.curr_bids.curr_subject['isPresent'])
        # parse the bids directory to check that the file were removed
        self.curr_bids.parse_bids()
        self.curr_bids.is_subject_present('01')
        self.assertFalse(self.curr_bids.curr_subject['isPresent'])

    def remove_bids(self):
        self.curr_bids.parse_bids()
        # remove the whole bids dataset
        self.curr_bids.remove(self.curr_bids)
        self.assertTrue(self.curr_bids.is_empty())
        self.assertFalse(os.path.exists(self.bids_dir))


def suite_init():

    suite = unittest.TestSuite()
    # basic tests
    suite.addTest(unittest.makeSuite(TestBidsBrickSafety))
    # parsing related  tests
    suite.addTest(TestParsingBids('test_existing_bids'))
    suite.addTest(TestParsingBids('test_parsing_writing'))
    suite.addTest(TestParsingBids('test_parsingjson_recovery'))
    suite.addTest(TestParsingBids('test_small_requests'))
    # import related  tests
    suite.addTest(TestImport('test_writing_data2import'))
    suite.addTest(TestImport('test_import_pat1'))
    # Import issue tests
    suite.addTest(TestIssueImport('wrong_protocol'))
    suite.addTest(TestIssueImport('wrong_patient_charac'))
    suite.addTest(TestIssueImport('same_source_data'))
    suite.addTest(TestIssueImport('file_with_same_attr'))
    suite.addTest(TestIssueImport('wrong_derivatives_protocol_name'))
    suite.addTest(TestIssueImport('file_with_same_attr_deriv'))
    # Electrode name issue tests
    suite.addTest(TestElectrodeIssues('modify_channel_type'))
    suite.addTest(TestElectrodeIssues('modify_channel_name'))
    suite.addTest(TestElectrodeIssues('add_to_bidsignore'))
    # object removal tests
    suite.addTest(TestObjectRemoval('remove_modality_file'))
    suite.addTest(TestObjectRemoval('remove_glbsidecar_file'))
    suite.addTest(TestObjectRemoval('remove_subject'))
    suite.addTest(TestObjectRemoval('remove_bids'))
    return suite


# Somehow PyCharm if script run with unittest does not follow the chosen order of testing (run with Alt+Shift+F10)
# Pycharm does
if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True, verbosity=3)
    curr_suite = suite_init()
    results = runner.run(curr_suite)
    print()
