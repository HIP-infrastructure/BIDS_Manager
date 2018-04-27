import os
import json
from datetime import datetime
import ins_bids_class as util
import ins_bids_functions as bidsfunc

# while parsing do not forget to save the name of the original file before renaming it in bids
# pathTempPHRC = 'E:/PostDoc/PHRC/test/Temp_files_Uploader'
# pathPHRC = 'E:/PostDoc/PHRC/test/PHRC'

pathTempPHRC = 'D:/roehri/PHRC/test/Temp_files_Uploader'
pathPHRC = 'D:/roehri/PHRC/test/PHRC'

now = datetime.now()

raw_data = util.Data2Import(pathTempPHRC)
raw_data['uploadDate'] = now.strftime("%d-%m-%Y_%Hh%M")

for dirPatName in os.listdir(pathTempPHRC):
    # print('pat patID: %s' % patDict['patID'])
    if os.path.isdir(os.path.join(pathTempPHRC, dirPatName)):
        sub = util.Subject(is_in_main_dir=False)
        sub['sub'] = os.path.basename(dirPatName).split('_')[0]
        # patDict['alias'] = util.createalias()

        for dirModName in os.listdir(os.path.join(pathTempPHRC, dirPatName)):

            if os.path.isdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):
                # print('Found subPat directory: %s' % dirModName)

                if dirModName == 'MRI':

                    for dirModFiles in os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):

                        uidPatFile = os.path.splitext(dirModFiles.split('_')[-1])[0]
                        if os.path.isdir(os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles))\
                                and uidPatFile == sub['sub']:
                            MRIDict = util.Anat()
                            MRIDict['ses'] = str(1).zfill(2)
                            MRI_type = (dirModFiles.split('_')[1])
                            if MRI_type == 'Pre':
                                MRIDict['acq'] = 'preop'
                            elif MRI_type == 'Post':
                                MRIDict['acq'] = 'postop'
                            MRIDict['modality'] = 'T1w'
                            MRIDict['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)
                            sub['Anat'] = MRIDict

                elif dirModName == 'SEEG':
                    # First, check if SEEG is present
                    for dirModFiles in os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):
                        if not os.path.isdir(os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)):
                            uidPatFile = os.path.splitext(dirModFiles.split('_')[-1])[0]
                            if uidPatFile == sub['sub']:
                                SEEGDict = util.Ieeg()
                                SEEG_type = (dirModFiles.split('_')[1])
                                SEEGDict['ses'] = str(1).zfill(2)
                                if SEEG_type == 'Ictal':
                                    SEEGDict['task'] = 'seiz'
                                elif SEEG_type == 'Interictal':
                                    SEEGDict['task'] = 'interict'
                                SEEGDict['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)
                                sub['Ieeg'] = SEEGDict
                    # Then look for the pictures and the elec location, create empty Ieeg if not exist
                    for dirModFiles in os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):
                        if dirModFiles.startswith('Schema') and os.path.isdir(os.path.join(pathTempPHRC,
                                                                                           dirPatName, dirModName,
                                                                                           dirModFiles)):
                            for dirModPic in os.listdir(os.path.join(pathTempPHRC, dirPatName,
                                                                     dirModName, dirModFiles)):
                                implantschema = util.IeegElecPic()
                                implantschema['ses'] = str(1).zfill(2)
                                implantschema['acq'] = 'impl'
                                implantschema['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName,
                                                                        dirModFiles, dirModPic)
                                if sub['Ieeg']:
                                    for ieegIdx in range(0, len(sub['Ieeg'])):
                                        sub['Ieeg'][ieegIdx]['IeegElecPic'] = implantschema
                                else:
                                    sub['Ieeg'] = util.Ieeg()
                                    sub['Ieeg'][0]['IeegElecPic'] = implantschema
                        # if dirModFiles.startswith('Localisation'):
                        #     elecloc = util.IeegElec()
                        #     elecloc['space'] = 'CT'
                        #     if patDict['Ieeg']:
                        #         for ieegIdx in range(0, len(patDict['Ieeg'])):
                        #             patDict['Ieeg'][ieegIdx]['IeegElecLoc'] = elecloc
                        #     else:
                        #         patDict['Ieeg'] = util.Ieeg()
                        #         patDict['Ieeg'][0]['IeegElecLoc'] = elecloc

                elif dirModName == 'CT':
                    dirModFiles = os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName))[0]
                    uidPatFile = os.path.splitext(dirModFiles.split('_')[-1])[0]
                    if uidPatFile == sub['sub']:
                        CTDict = util.Anat()
                        CTDict['modality'] = 'CT'
                        CTDict['ses'] = str(1).zfill(2)
                        CTDict['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)
                        sub['Anat'] = CTDict

            elif os.path.splitext(dirModName)[1] == '.json':
                uidPatFile = os.path.splitext(dirModName)[0].split('_')[0]

                if uidPatFile == sub['sub']:
                    jsonFile = os.path.join(pathTempPHRC, dirPatName, dirModName)
                    jsonData = open(jsonFile)
                    data = json.load(jsonData)
                    sub['protocol'] = data['Protocol']
                    sub['institution'] = data['CodeCentre']
                    jsonData.close()

        raw_data['Subject'] = sub

print(raw_data)
# raw_data.save_json(raw_data.data2import_dir)

# with open(os.path.join(pathTempPHRC, 'reading_' + now.strftime("%d%m%Y_%Hh%M") + '.json'), 'w') as f:
#     json.dump(source_data, f, indent=2, separators=(',', ': '), ensure_ascii=False)
# source_data.convert_dcm2niix()
# source_data.save_json(pathTempPHRC)
# source_data.convert_dcm2niix()
# bidsfunc.handle_participant_table(pathPHRC, source_data['Subject'])



# print(subjectList[0])
# print(subjectList[1])
