import ins_bids_class as util
import datetime as dtm
import shutil
import os


test_numb = 0

# Der = util.Derivatives()
# print(Der)


if test_numb == 0:
    '''Here try to parse the bids dataset and write in the derivatives the results of the parsing'''
    bids_dir = 'D:/roehri/PHRC/test/Made_up_dataset'
    # bids_dir = 'E:/PostDoc/PHRC/test/Neural_responses'
    bids = util.BidsDataset(bids_dir)
elif test_numb == 1:
    '''Here try to import data in an empty bids dataset and write in the derivatives the results of the import'''
    bids_dir = 'D:/roehri/PHRC/test/test_import/new_bids'
    pathTempdir = 'D:/roehri/PHRC/test/test_import/small_Neural_Response'
    pathsource = 'D:/roehri/PHRC/test/test_import/small_Neural_Response_orig'

    if os.path.isdir(bids_dir):
        shutil.rmtree(bids_dir)
    if os.path.isdir(pathTempdir):
        shutil.rmtree(pathTempdir)
    os.makedirs(bids_dir)
    os.makedirs(pathTempdir)

    shutil.copy2(os.path.join(pathsource, util.DatasetDescJSON.filename), os.path.join(pathTempdir,
                                                                                       util.DatasetDescJSON.filename))
    shutil.copy2(os.path.join(pathsource, 'task-beh_bold.json'), os.path.join(pathTempdir, 'task-beh_bold.json'))
    shutil.copy2(os.path.join(pathsource, 'task-tax_bold.json'), os.path.join(pathTempdir, 'task-tax_bold.json'))
    shutil.copytree(os.path.join(pathsource, 'sub-rid000001'), os.path.join(pathTempdir, 'sub-rid000001'))
    shutil.copytree(os.path.join(pathsource, 'sub-rid000012'), os.path.join(pathTempdir, 'sub-rid000012'))

    bids = util.BidsDataset(bids_dir)
    temp_bids = util.BidsDataset(pathTempdir)
    raw_data = util.Data2Import(pathTempdir)
    now = dtm.datetime.now()
    raw_data['uploadDate'] = now.strftime("%d-%m-%Y_%Hh%M")
    for sub in temp_bids['Subject']:
        raw_data['Subject'] = sub
    bids.import_data(raw_data)

'''Here try to import data of new patients in an existing bids dataset and write in the derivatives the results of 
the import'''


'''Here try to import data of pre-existing patients (handle the run issues) in an existing bids dataset and write in the
 derivatives the results of the import'''


