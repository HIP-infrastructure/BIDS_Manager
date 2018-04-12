import os
import json
from datetime import datetime
import ins_bids_class as util
import ins_bids_functions as bidsfunc


pathTempPHRC = 'D:/roehri/PHRC/test/Temp_files_Uploader'
pathPHRC = 'D:/roehri/PHRC/test/PHRC'
patientList = []
now = datetime.now()

for dirPatName in os.listdir(pathTempPHRC):
    # print('pat patID: %s' % patDict['patID'])
    if os.path.isdir(os.path.join(pathTempPHRC, dirPatName)):
        patDict = util.PatientInfo()
        patDict['patID'] = os.path.basename(dirPatName).split('_')[0]
        # patDict['alias'] = util.createalias()
        patDict['uploadDate'] = now.strftime("%d-%m-%Y_%Hh%M")
        for dirModName in os.listdir(os.path.join(pathTempPHRC, dirPatName)):

            if os.path.isdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):
                # print('Found subPat directory: %s' % dirModName)

                if dirModName == 'MRI':

                    for dirModFiles in os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):

                        uidPatFile = os.path.splitext(dirModFiles.split('_')[-1])[0]
                        if uidPatFile == patDict['patID']:
                            MRIDict = util.AnatInfo()
                            MRI_type = (dirModFiles.split('_')[1])
                            if MRI_type == 'Pre':
                                MRIDict['acq'] = 'preop'
                            elif MRI_type == 'Post':
                                MRIDict['acq'] = 'postop'
                            MRIDict['mod'] = 'T1w'
                            MRIDict['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)
                            patDict['Anat'] = MRIDict

                elif dirModName == 'SEEG':
                    # First, check if SEEG is present
                    for dirModFiles in os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):
                        if not os.path.isdir(os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)):
                            uidPatFile = os.path.splitext(dirModFiles.split('_')[-1])[0]
                            if uidPatFile == patDict['patID']:
                                SEEGDict = util.IeegInfo()
                                SEEG_type = (dirModFiles.split('_')[1])
                                if SEEG_type == 'Ictal':
                                    SEEGDict['task'] = 'seiz'
                                elif SEEG_type == 'Interictal':
                                    SEEGDict['task'] = 'interict'
                                SEEGDict['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)
                                patDict['Ieeg'] = SEEGDict
                    # Then look for the pictures and the elec location, create empty IeegInfo if not exist
                    for dirModFiles in os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName)):
                        if dirModFiles.startswith('Schema') and os.path.isdir(os.path.join(pathTempPHRC,
                                                                                           dirPatName, dirModName,
                                                                                           dirModFiles)):
                            for dirModPic in os.listdir(os.path.join(pathTempPHRC, dirPatName,
                                                                     dirModName, dirModFiles)):
                                implantschema = util.IeegElecPicInfo()
                                implantschema['acq'] = 'impl'
                                implantschema['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName,
                                                                        dirModFiles, dirModPic)
                                if patDict['Ieeg']:
                                    for ieegIdx in range(0, len(patDict['Ieeg'])):
                                        patDict['Ieeg'][ieegIdx]['IeegElecPic'] = implantschema
                                else:
                                    patDict['Ieeg'] = util.IeegInfo()
                                    patDict['Ieeg'][0]['IeegElecPic'] = implantschema
                        # if dirModFiles.startswith('Localisation'):
                        #     elecloc = util.IeegElecLocInfo()
                        #     elecloc['space'] = 'CT'
                        #     if patDict['Ieeg']:
                        #         for ieegIdx in range(0, len(patDict['Ieeg'])):
                        #             patDict['Ieeg'][ieegIdx]['IeegElecLoc'] = elecloc
                        #     else:
                        #         patDict['Ieeg'] = util.IeegInfo()
                        #         patDict['Ieeg'][0]['IeegElecLoc'] = elecloc

                elif dirModName == 'CT':
                    dirModFiles = os.listdir(os.path.join(pathTempPHRC, dirPatName, dirModName))[0]
                    uidPatFile = os.path.splitext(dirModFiles.split('_')[-1])[0]
                    if uidPatFile == patDict['patID']:
                        CTDict = util.AnatInfo()
                        CTDict['mod'] = 'CT'
                        CTDict['fileLoc'] = os.path.join(pathTempPHRC, dirPatName, dirModName, dirModFiles)
                        patDict['CT'] = CTDict

            elif os.path.splitext(dirModName)[1] == '.json':
                uidPatFile = os.path.splitext(dirModName)[0].split('_')[0]

                if uidPatFile == patDict['patID']:
                    jsonFile = os.path.join(pathTempPHRC, dirPatName, dirModName)
                    jsonData = open(jsonFile)
                    data = json.load(jsonData)
                    patDict['protocol'] = data['Protocol']
                    patDict['institution'] = data['CodeCentre']
                    jsonData.close()

        patientList.append(patDict)


with open(os.path.join(pathTempPHRC, 'reading_' + now.strftime("%d%m%Y_%Hh%M") + '.log'), 'w') as f:
    json.dump(patientList, f, indent=2, separators=(',', ': '), ensure_ascii=False)


bidsfunc.handle_participant_table(pathPHRC, patientList)

# print(patientList[0])
# print(patientList[1])
