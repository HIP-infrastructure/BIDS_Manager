import ins_bids_class as util
import datetime as dtm
import shutil
import os
import copy


test_numb = 3

# Der = util.Derivatives()
# print(Der)


if test_numb == 0:
    '''Here, try to parse the bids dataset and write in the derivatives the results of the parsing'''
    bids_dir = 'D:/roehri/PHRC/test/test_import/new_bids'
    # bids_dir = 'E:/PostDoc/PHRC/test/Neural_responses'
    bids = util.BidsDataset(bids_dir)
    seeg = util.Ieeg()
    seeg['sub'] = 'test'
    seeg['ses'] = '01'
    seeg['task'] = 'interictal'
    print('How many runs is there currently for ' + str(seeg.get_attributes(['fileLoc', 'run'])) + '?\n' +
          str(bids.get_number_of_runs(seeg)))
    print('Has sub-test Ieeg modalities?\n' + str(bids.has_subject_modality_type('test', 'Ieeg')))
elif test_numb == 1:
    '''Here, try to create a folder to import that can be further read and imported in a bids dataset'''
    pathsource = 'D:/roehri/PHRC/test/test_import/import_test_orig'
    # subject info are entered
    pat_UID = 'c2429a5cfd4a'
    age = '22'
    sex = 'F'
    dict_tempdir = {'EPINOV': 'D:/roehri/PHRC/test/test_import/create_import_dir' + '_EPINOV_' + pat_UID,
                    'SPREAD': 'D:/roehri/PHRC/test/test_import/create_import_dir' + '_SPREAD_' + pat_UID}

    # remove folders for testing purposes
    for key in dict_tempdir:
        if os.path.isdir(dict_tempdir[key]):
            shutil.rmtree(dict_tempdir[key])
    #######

    raw_data = {}
    for key in dict_tempdir:
        os.makedirs(dict_tempdir[key], exist_ok=True)
        # instantiates an object
        raw_data[key] = util.Data2Import(dict_tempdir[key])
        raw_data[key]['DatasetDescJSON'] = util.DatasetDescJSON()
        raw_data[key]['DatasetDescJSON'].update({'Name': key, 'BIDSVersion': '1.0.1'})

        raw_data[key]['Subject'] = util.Subject()
        raw_data[key]['Subject'][-1].update({'sub': pat_UID, 'age': age, 'sex': sex})
        # optional, nice for debugging
        raw_data[key].save_as_json()

    # the user select a CT
    for key in dict_tempdir:
    # always assign the import directory you are working on before creating and filling an instance. Because when
    # filling fileLoc, the class test whether the file is present as a sanity check
        util.Data2Import._assign_import_dir(raw_data[key].data2import_dir)
        if key == 'EPINOV':
            shutil.copytree(os.path.join(pathsource, 'CT'), os.path.join(raw_data[key].data2import_dir, 'CT'))
        else:
            shutil.copytree(os.path.join(raw_data['EPINOV'].data2import_dir, 'CT'), os.path.join(raw_data[key].
                                                                                                 data2import_dir, 'CT'))
        # do your anonymization and test whether protocol SPREAD needs it
        raw_data[key]['Subject'][-1]['Anat'] = util.Anat()
        raw_data[key]['Subject'][-1]['Anat'][-1].update({'sub': raw_data[key]['Subject'][-1]['sub'], 'ses': '01',
                                                         'modality': 'CT', 'fileLoc': 'CT'})
        raw_data[key].save_as_json()

    # the user select a preop MRI
    for key in dict_tempdir:
        util.Data2Import._assign_import_dir(raw_data[key].data2import_dir)
        if key == 'EPINOV':
            shutil.copytree(os.path.join(pathsource, 'MRI'), os.path.join(raw_data[key].data2import_dir, 'MRI'))
        else:
            shutil.copytree(os.path.join(raw_data['EPINOV'].data2import_dir, 'MRI'), os.path.join(
                raw_data[key].data2import_dir, 'MRI'))
        # do your anonymization and test whether protocol SPREAD needs it
        raw_data[key]['Subject'][-1]['Anat'] = util.Anat()
        raw_data[key]['Subject'][-1]['Anat'][-1].update({'sub': raw_data[key]['Subject'][-1]['sub'], 'ses': '01',
                                                         'acq': 'preop', 'modality': 'MRI', 'fileLoc': 'MRI'})
        raw_data[key].save_as_json()

        # the user select a type1 SEEG seizure
    for key in dict_tempdir:
        util.Data2Import._assign_import_dir(raw_data[key].data2import_dir)
        if key == 'EPINOV':
            shutil.copy2(os.path.join(pathsource, '180219U-CEX_0000.eeg'), os.path.join(
                raw_data[key].data2import_dir, '180219U-CEX_0000.eeg'))
        else:
            shutil.copy2(os.path.join(raw_data['EPINOV'].data2import_dir, '180219U-CEX_0000.eeg'), os.path.join(
                raw_data[key].data2import_dir, '180219U-CEX_0000.eeg'))
        # do your anonymization and test whether protocol SPREAD needs it
        raw_data[key]['Subject'][-1]['Ieeg'] = util.Ieeg()
        raw_data[key]['Subject'][-1]['Ieeg'][-1].update({'sub': raw_data[key]['Subject'][-1]['sub'], 'ses': '01',
                                                         'acq': 'type1', 'task': 'seizure', 'fileLoc':
                                                             '180219U-CEX_0000.eeg'})
        raw_data[key].save_as_json()

    # the user select a XRay seizure
    for key in dict_tempdir:
        util.Data2Import._assign_import_dir(raw_data[key].data2import_dir)
        if key == 'EPINOV':
            shutil.copy2(os.path.join(pathsource, 'TM001.png'), os.path.join(
                raw_data[key].data2import_dir, 'TM001.png'))
        else:
            shutil.copy2(os.path.join(raw_data['EPINOV'].data2import_dir, 'TM001.png'), os.path.join(
                raw_data[key].data2import_dir, 'TM001.png'))
        # do your anonymization and test whether protocol SPREAD needs it
        raw_data[key]['Subject'][-1]['IeegGlobalSidecars'] = util.IeegGlobalSidecars('TM001.png')
        raw_data[key]['Subject'][-1]['IeegGlobalSidecars'][-1].update({'sub': raw_data[key]['Subject'][-1]['sub'],
                                                                       'ses': '01', 'acq': 'Xray1', 'fileLoc':
                                                                           'TM001.png'})
        raw_data[key].save_as_json()


elif test_numb == 2:
    '''Here, try to import data in an empty bids dataset and write in the derivatives the results of the import'''
    bids_dir = 'D:/roehri/PHRC/test/test_import/new_bids'
    pathTempdir = 'D:/roehri/PHRC/test/test_import/import_test'
    pathsource = 'D:/roehri/PHRC/test/test_import/import_test_orig'

    if os.path.isdir(bids_dir):
        shutil.rmtree(bids_dir)
    # if os.path.isdir(pathTempdir):
    #     shutil.rmtree(pathTempdir)
    os.makedirs(bids_dir)

    # shutil.copytree(pathsource, pathTempdir)

    bids = util.BidsDataset(bids_dir)
    raw_data = util.Data2Import(pathTempdir)
    bids.import_data(raw_data)

elif test_numb == 3:
    '''Here, try to import data of new patients in an existing bids dataset and write in the derivatives the results of 
    the import'''
    bids_dir = 'D:/roehri/PHRC/test/test_import/new_bids1'
    pathTempdir = ['D:/roehri/PHRC/test/test_import/import_test_1', 'D:/roehri/PHRC/test/test_import/import_test_2']
    # pathsource = 'D:/roehri/PHRC/test/test_import/import_test_orig'

    if os.path.isdir(bids_dir):
        shutil.rmtree(bids_dir)
    # if os.path.isdir(pathTempdir):
    #     shutil.rmtree(pathTempdir)
    os.makedirs(bids_dir)

    # shutil.copytree(pathsource, pathTempdir)

    bids = util.BidsDataset(bids_dir)
    for import_dir in pathTempdir:
        raw_data = util.Data2Import(import_dir)
        bids.import_data(raw_data)

'''Here, try to import data of pre-existing patients (handle the run issues) in an existing bids dataset and write in the
 derivatives the results of the import'''


