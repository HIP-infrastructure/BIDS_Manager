import ins_bids_class as util
import datetime as dtm


# Der = util.Derivatives()
# print(Der)

'''Here try to parse the bids dataset and write in the derivatives the results of the parsing'''
#
# bids_dir = 'D:/roehri/PHRC/test/Neural_responses'
# bids_dir = 'E:/PostDoc/PHRC/test/Neural_responses'
# bids = util.BidsDataset(bids_dir)

'''Here try to import data in an empty bids dataset and write in the derivatives the results of the import'''

bids_dir = 'D:/roehri/PHRC/test/test_import/new_bids'
pathTempdir = 'D:/roehri/PHRC/test/test_import/small_Neural_Response'
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


