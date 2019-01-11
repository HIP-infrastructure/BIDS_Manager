import ins_bids_class as bids
import os
from importlib import reload
import UploadFtract as upload

reload(bids)
reload(upload)
#Initiate the filename and path
PathBidsDir = r'D:\Data\Test_Ftract_Import\Bids_Ftract_mult_subject'
PathImportData = r'D:\Data\Test_Ftract_Import\Original_deriv'
ConverterImageryFile = r'D:\Software\Bids_Manager\dcm2niix.exe'
ConverterElectrophyFile = r'C:\anywave_december\AnyWave\AnyWave.exe'
req_fname = r'D:\Data\Test_Ftract_Import\Original_deriv\requirements.json'
ProtocolName = 'FTract'
First_implantation = True

if First_implantation:
    with os.scandir(PathImportData) as it:
        for entry in it:
            if entry.name == 'data2import.json':
                os.remove(entry)
    upload.read_ftract_folders(PathImportData)

if not os.path.exists(PathBidsDir):
    os.makedirs(PathBidsDir)

#Indicate the bids dir
if os.path.isdir(PathBidsDir):
    req_dict = bids.Requirements(req_fname)

    bids.BidsDataset.converters['Imagery']['path'] = ConverterImageryFile
    req_dict['Converters']['Imagery']['path'] = ConverterImageryFile
    bids.BidsDataset.converters['Electrophy']['path'] = ConverterElectrophyFile
    req_dict['Converters']['Electrophy']['path'] = ConverterElectrophyFile

    bids.BidsDataset.dirname = PathBidsDir
    req_dict.save_as_json(os.path.join(bids.BidsDataset.dirname, 'code', 'requirements.json'))

    datasetDes = bids.DatasetDescJSON()
    datasetDes['Name'] = ProtocolName
    datasetDes.write_file()

    curr_bids = bids.BidsDataset(PathBidsDir)

curr_data2import = bids.Data2Import(PathImportData, os.path.join(bids.BidsDataset.dirname, 'code', 'requirements.json'))

curr_bids.make_upload_issues(curr_data2import, force_verif=True)
curr_bids.import_data(data2import=curr_data2import, keep_sourcedata=False, keep_file_trace=False)

with os.scandir(PathImportData) as it:
    for entry in it:
        if entry.name.startswith('sub') and entry.is_file():
            os.remove(entry)
