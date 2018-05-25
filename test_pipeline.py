import ins_bids_class as util
import datetime as dtm
import shutil
import os


test_numb = 2

# Der = util.Derivatives()
# print(Der)


if test_numb == 0:
    '''Here try to parse the bids dataset and write in the derivatives the results of the parsing'''
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
    '''Here try to import data in an empty bids dataset and write in the derivatives the results of the import'''
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

elif test_numb == 2:
    '''Here try to import data of new patients in an existing bids dataset and write in the derivatives the results of 
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

'''Here try to import data of pre-existing patients (handle the run issues) in an existing bids dataset and write in the
 derivatives the results of the import'''


