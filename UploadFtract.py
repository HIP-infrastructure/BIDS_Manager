import os
import json
import hashlib
from datetime import datetime

import ins_bids_class as util

#pathTempMIP = r'D:\Data\Test_Ftract_Import\Original_deriv'
#RequirementFile = r'D:\Data\Test_Ftract_Import\Original_deriv\requirements.json'


def calculate_age_at_acquisition(birthD, seegD):
    bDate = datetime.fromisoformat(birthD)
    sDate = datetime.fromisoformat(seegD)
    year = sDate.year - bDate.year - ((sDate.month, sDate.day) < (bDate.month, bDate.day))
    if bDate.month > sDate.month:
        month = sDate.month - bDate.month + 12
    else:
        month = sDate.month - bDate.month
    if bDate.day < sDate.day:
        month +=1
    else:
        month -=1
    real_age = str(year) + ' years and ' + str(month) +' months'
    return real_age


def remove_unused_keys(dic):
    key = dic.keys()
    lisKeyUnused = []
    for k in key:
        if dic[k] == 'n/a':
            lisKeyUnused.append(k)
    for l in lisKeyUnused:
        del dic[l]
    return dic


def hash_object(obj):
    clef256 = hashlib.sha256(obj.encode())
    clefDigest = clef256.hexdigest()
    clef = clefDigest[0:12]
    return clef


def split_stim_name(name):
    contact = name.split('_')[0]
    amplitude = name.split('_')[1]
    frequency = name.split('_')[2]
    time = name.split('_')[3]
    run = name.split('_')[4]
    return contact, amplitude, frequency, time, run


def get_the_manufacturer(subject_name):
    centre = ''
    i = len(subject_name) - 3
    while i < len(subject_name):
        centre = centre + subject_name[i]
        i += 1
    if centre == 'GRE' or centre == 'LYO':
        Manufacturer ='Micromed'
    elif centre == 'MAR':
        Manufacturer = 'Deltamed'
    elif centre == 'MIL':
        Manufacturer = 'Nihon-kohden'
    elif centre == 'FRE':
        Manufacturer = 'Compumedics'
    return Manufacturer


def get_bad_channels(contact):
    size = len(contact)
    elec = contact[0]
    if size == 3:
        num1 = contact[1]
        num2 = contact[2]
    elif size == 5:
        num1 = contact[1:3]
        num2 = contact[3:5]
    channel1 = elec + num1
    channel2 = elec + num2

    #Create the dict
    chan1_dict = dict()
    chan2_dict = dict()
    chan1_dict['name'] = channel1
    chan2_dict['name'] = channel2
    chan1_dict['status'] = 'bad'
    chan2_dict['status'] = 'bad'

    return chan1_dict, chan2_dict


def check_subject_in_list(subject_list, subject_name):
    subject_present = False
    index_subject=None
    for elt in subject_list:
        if elt['sub'] == subject_name:
            subject_present = True
            index_subject = subject_list.index(elt)
    return subject_present, index_subject


def check_pipeline_in_list(pip_list, pip_name):
    pip_present = False
    index_pip=None
    for elt in pip_list:
        if elt['name'] == pip_name:
            pip_present = True
            index_pip = pip_list.index(elt)
    return pip_present, index_pip


def read_ftract_folders(pathTempMIP, RequirementFile=None):
    now = datetime.now()
    if RequirementFile:
        raw_data = util.Data2Import(pathTempMIP, RequirementFile)
    else:
        raw_data = util.Data2Import(pathTempMIP)
    raw_data['UploadDate'] = now.strftime("%d-%m-%Y_%Hh%M")

    ###Go throught all the folders to find the ieeg and anat###
    subject_list = list()
    for dirPatName in os.listdir(pathTempMIP):
        if dirPatName == '01-upload' and os.path.isdir(os.path.join(pathTempMIP, dirPatName)):
            for Subdir in os.listdir(os.path.join(pathTempMIP, dirPatName)):
                if Subdir.split('_')[0] == 'Ftract' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, Subdir)):
                    for uploadir in os.listdir(os.path.join(pathTempMIP, dirPatName, Subdir)):
                        if uploadir == 'Upload' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir)):
                            for Subupload in os.listdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir)):
                                if os.path.isdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir, Subupload)):
                                    hashed_sub = hash_object(Subupload)
                                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                                    if not subject_present:
                                        sub = util.Subject()
                                        sub['sub'] = hashed_sub
                                    else:
                                        sub = subject_list[index_subject]
                                    for seegdir in os.listdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir, Subupload)):
                                        if os.path.isdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir, Subupload, seegdir)):
                                            for cradir in os.listdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir, Subupload, seegdir)):
                                                if os.path.isdir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir, Subupload, seegdir, cradir)):
                                                    with os.scandir(os.path.join(pathTempMIP, dirPatName, Subdir, uploadir, Subupload, seegdir, cradir)) as it:
                                                        i=1
                                                        for entry in it:
                                                            #devra rajouter un if pour prendre les .mat
                                                            IeDict = util.Ieeg()
                                                            IeDict['sub'] = sub['sub']
                                                            IeDict['task'] = 'Seizure'
                                                            IeDict['ses'] = str(1).zfill(2)
                                                            IeDict['modality'] = 'ieeg'
                                                            IeDict['run'] = str(i).zfill(2)
                                                            IeDict['fileLoc'] = os.path.join(dirPatName, Subdir, uploadir, Subupload, seegdir, cradir, entry.name)

                                                            sub['Ieeg'] = IeDict
                                                            i+=1
                                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                                    if not subject_present:
                                        subject_list.append(sub)
                                    else:
                                        #attr_dict = {key: sub[key] for key in sub.keys() if sub[key]}
                                        subject_list[index_subject].update(sub.get_attributes())

        elif dirPatName == '02-raw' and os.path.isdir(os.path.join(pathTempMIP, dirPatName)):
            for Subdir in os.listdir(os.path.join(pathTempMIP, dirPatName)):
                if os.path.isdir(os.path.join(pathTempMIP, dirPatName, Subdir)):

                    ###At this moment, we should loose the patient code and change it in unicode###
                    hashed_sub = hash_object(Subdir)
                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                    if not subject_present:
                        sub = util.Subject()
                        sub['sub'] = hashed_sub
                    else:
                        sub = subject_list[index_subject]
                    #Get the Manufacturer
                    Manu = get_the_manufacturer(Subdir)
                    with os.scandir(os.path.join(pathTempMIP, dirPatName, Subdir)) as it:
                        for entry in it:
                            if entry.name.startswith('patient') and entry.is_file():
                                with open(entry.path) as json_file:
                                    json_data = json.load(json_file)
                                sub['sex'] = json_data[0]['gender']
                                birthDate = json_data[0]['birth_date']

                            elif entry.name.startswith('crf') and entry.is_file():
                                with open(entry.path) as json_file:
                                    json_data = json.load(json_file)
                                SeegDate = json_data[0]['SEEG_date']

                            elif entry.name.startswith('T1') and entry.is_dir():
                                for dirT1 in os.listdir(entry.path):
                                    if os.path.isdir(os.path.join(entry.path, dirT1)):
                                        if dirT1.split('_')[0] == 'T1post':
                                            AnaDict = util.Anat()
                                            AnaDict['sub'] = sub['sub']
                                            AnaDict['ses'] = str(1).zfill(2)
                                            AnaDict['acq'] = 'postimp'
                                            AnaDict['modality'] = 'T1w'
                                            AnaDict['fileLoc'] = os.path.join(entry.path, dirT1)

                                            sub['Anat'] = AnaDict
                                        elif dirT1.split('_')[0] == 'T1postop':
                                            AnaDict = util.Anat()
                                            AnaDict['sub'] = sub['sub']
                                            AnaDict['ses'] = str(1).zfill(2)
                                            AnaDict['acq'] = 'postop'
                                            AnaDict['modality'] = 'T1w'
                                            AnaDict['fileLoc'] = os.path.join(entry.path, dirT1)

                                            sub['Anat'] = AnaDict

                                        elif dirT1.split('_')[0] == 'T1gadopre':
                                            AnaDict = util.Anat()
                                            AnaDict['sub'] = sub['sub']
                                            AnaDict['ses'] = str(1).zfill(2)
                                            AnaDict['acq'] = 'preop'
                                            AnaDict['modality'] = 'T1w'
                                            AnaDict['fileLoc'] = os.path.join(entry.path, dirT1)
                                            AnaJ = util.AnatJSON()
                                            AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                            AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)

                                            sub['Anat'] = AnaDict

                            elif entry.name.startswith('StimLF') and entry.is_dir():

                                for dirRaw in os.listdir(entry.path):
                                    if os.path.isdir(os.path.join(entry.path, dirRaw)) and dirRaw == 'BadChannels':
                                        for filMod in os.listdir(os.path.join(entry.path, dirRaw)):
                                            if os.path.isfile(os.path.join(entry.path, dirRaw, filMod)):
                                                    name, ext = os.path.splitext(filMod)
                                                    if ext == '.mat' or ext == '.eeg':
                                                        contact, amplitude, frequency, time, run = split_stim_name(name)
                                                        IeDict = util.Ieeg()
                                                        IeDict['sub'] = sub['sub']
                                                        IeDict['ses'] = str(1).zfill(2)
                                                        IeDict['task'] = 'Stimuli'
                                                        IeDict['acq'] = contact
                                                        IeDict['run'] = str(run).zfill(2)
                                                        IeDict['modality'] = 'ieeg'
                                                        IeDict['fileLoc'] = os.path.join(entry.path, dirRaw, filMod)

                                                        ieJ = util.IeegJSON()
                                                        ieJ['TaskName'] = 'Stimuli'
                                                        ieJ['Manufacturer'] = Manu
                                                        ieJ['TaskDescription'] = 'Epoch starting around 40s before the first stimulus and ending 2-3s after the stimuli block'
                                                        ieJ['Stimulation'] = 'Electrodes stimulated = ' + contact + ', Amplitude = ' + amplitude + ', Frequency = ' + frequency + ', Time = ' + time
                                                        ieJ['RecordingDate'] = SeegDate
                                                        ieJ.simplify_sidecar(required_only=False)
                                                        IeDict['IeegJSON'] = ieJ

                                                        ieChan = util.IeegChannelsTSV()
                                                        Chan1, Chan2 = get_bad_channels(contact)
                                                        ieChan.append(Chan1)
                                                        ieChan.append(Chan2)
                                                        IeDict['IeegChannelsTSV'] = ieChan

                                                        sub['Ieeg'] = IeDict

                                        sub['age'] = calculate_age_at_acquisition(birthDate, SeegDate)
                        subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                        if not subject_present:
                            subject_list.append(sub)
                        else:
                            #attr_dict = {key: sub[key] for key in sub.keys() if sub[key]}
                            subject_list[index_subject].update(sub.get_attributes())

        elif dirPatName == '03-preprocessed' and os.path.isdir(os.path.join(pathTempMIP, dirPatName)):
            Dev_folder = util.Derivatives()
            pip_folder_list = list()
            for dirDevname in os.listdir(os.path.join(pathTempMIP, dirPatName)):
                if dirDevname == 'BrainVisa' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname)):
                    pip_folder = util.Pipeline()
                    pip_folder['name'] = 'BrainVisa'
                    subj_brain_list = list()
                    for dirBrainvisa in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname)):
                        if dirBrainvisa == 'Epilepsy' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa)):
                            for dirEpilepsy in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa)):
                                if os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa, dirEpilepsy)):
                                    sujet, data = dirEpilepsy.split('_')
                                    hashed_sujet = hash_object(sujet)
                                    Manufact = get_the_manufacturer(sujet)
                                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sujet)
                                    sub_brain_present, index_sub_brain = check_subject_in_list(subj_brain_list, hashed_sujet)
                                    if not sub_brain_present:
                                        sub_brain = util.Subject()
                                        sub_brain['sub'] = hashed_sujet
                                    else:
                                        sub_brain = subj_brain_list[index_sub_brain]
                                    if not subject_present:
                                        sub = util.Subject()
                                        sub['sub'] = hashed_sujet
                                    else:
                                        sub = subject_list[index_subject]
                                        sub_brain['sex'] = subject_list[index_subject]['sex']
                                        sub_brain['age'] = subject_list[index_subject]['age']
                                    for dirSujet in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa, dirEpilepsy)):
                                        if dirSujet == 'implantation' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa, dirEpilepsy, dirSujet)):
                                            ieImplant = util.IeegElecCSV()
                                            with os.scandir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa, dirEpilepsy, dirSujet)) as it:
                                                for entry in it:
                                                    name, ext = os.path.splitext(entry)
                                                    if ext == '.csv':
                                                        ieImplant['fileLoc'] = entry.path
                                                        ieImplant['sub'] = hashed_sujet
                                                        ieImplant['Manufacturer'] = Manufact
                                                        ieImplant['modality'] = 'ieeg'
                                                        ieImplant['ses'] = str(1).zfill(2) #Voir pour determiner la session en fonction des dates
                                                    elif ext == '.elecimplant':
                                                        with open(entry.path) as json_file:
                                                            json_data = json.load(json_file)
                                                        ieImplant['model'] = json_data['electrodes'][-1]['model']
                                                sub['IeegElecCSV'] = remove_unused_keys(ieImplant)

                                        elif dirSujet == 't1mri' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa, dirEpilepsy, dirSujet)):
                                            '''with os.scandir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirBrainvisa, dirEpilepsy, dirSujet)) as it:
                                                for entry in it:
                                                    if entry.name.startswith('T1') and entry.is_dir():
                                                        type_t1 = entry.name.split('_')[0]
                                                        for mri_file in os.listdir(entry.path):
                                                            name, ext = os.path.splitext(mri_file)
                                                            if name.split('_')[0] == 'y' and ext == '.nii':
                                                                AnaDict = util.Anat()
                                                                AnaDict['sub'] = sub_brain['sub']
                                                                AnaDict['ses'] = str(1).zfill(2)
                                                                if type_t1 == 'T1post':
                                                                    AnaDict['acq'] = 'postimp'
                                                                elif type_t1 == 'T1postOp':
                                                                    AnaDict['acq'] = 'postop'
                                                                elif type_t1 == 'T1pre':
                                                                    AnaDict['acq'] = 'preop'
                                                                AnaDict['rec'] = 'warp'
                                                                AnaDict['modality'] = 'T1w'
                                                                AnaDict['fileLoc'] = os.path.join(entry.path)

                                                                sub_brain['Anat'] = AnaDict
                                                            elif name.split('_')[0][0] == 'w'and ext == '.nii':
                                                                AnaDict = util.Anat()
                                                                AnaDict['sub'] = sub_brain['sub']
                                                                AnaDict['ses'] = str(1).zfill(2)
                                                                if type_t1 == 'T1post':
                                                                    AnaDict['acq'] = 'postimp'
                                                                elif type_t1 == 'T1postOp':
                                                                    AnaDict['acq'] = 'postop'
                                                                elif type_t1 == 'T1pre':
                                                                    AnaDict['acq'] = 'preop'
                                                                AnaDict['rec'] = 'normalise'
                                                                AnaDict['modality'] = 'T1w'
                                                                AnaDict['fileLoc'] = os.path.join(entry.path, mri_file)

                                                                sub_brain['Anat'] = AnaDict'''
                                            pass
                                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                                    if not subject_present:
                                        subject_list.append(sub)
                                    else:
                                        if not sub['IeegElecCSV']:
                                            subject_list[index_subject]['IeegElecCSV'] = sub['IeegElecCSV']
                                    sub_brain_present, index_sub_brain = check_subject_in_list(subj_brain_list, sub_brain['sub'])
                                    if not sub_brain_present:
                                        subj_brain_list.append(sub_brain)
                                    else:
                                        #attr_dict = {key: sub_brain[key] for key in sub_brain.keys() if sub_brain[key]}
                                        subj_brain_list[index_sub_brain].update(sub_brain.get_attributes())
                    for sub_brain in subj_brain_list:
                        pip_folder['Subject'].append(sub_brain)
                    pip_brain_pres, index_pip_brain = check_pipeline_in_list(pip_folder_list, pip_folder['name'])
                    if not pip_brain_pres:
                        pip_folder_list.append(pip_folder)
                    else:
                        attr_dict = {key: pip_folder[key] for key in pip_folder.keys() if pip_folder[key]}
                        pip_folder_list[index_pip_brain].update(attr_dict)

                elif dirDevname == 'FTract' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname)):
                    pip_folder = util.Pipeline()
                    pip_folder['name'] = 'ImaGIN'
                    subj_imagin_list = list()
                    for dirImagin in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname)):
                        if os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin)):
                            sujet_hash = hash_object(dirImagin)
                            pres_sub, sub_index = check_subject_in_list(subj_imagin_list, sujet_hash)
                            if not pres_sub:
                                sub_imagin = util.Subject()
                                sub_imagin['sub'] = sujet_hash
                            else:
                                sub_imagin = subj_imagin_list[sub_index]
                            pres_sub_raw, sub_raw_index = check_subject_in_list(subject_list, sujet_hash)
                            if pres_sub_raw:
                                sub_imagin['sex'] = subject_list[sub_raw_index]['sex']
                                sub_imagin['age'] = subject_list[sub_raw_index]['age']
                            for dirSujet in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin)):
                                if dirSujet == 'SEEG' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet)):
                                    for dirSeeg in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet)):
                                        if dirSeeg.split('_')[0] == 'Ictal' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet, dirSeeg)):
                                            for dirIctal in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet, dirSeeg)):
                                                if dirIctal == 'EI' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet,dirSeeg, dirIctal)):
                                                    for dirEI in os.listdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet, dirSeeg, dirIctal)):
                                                        if dirEI == 'SZGroup1' and os.path.isdir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet, dirSeeg, dirIctal, dirEI)):
                                                            with os.scandir(os.path.join(pathTempMIP, dirPatName, dirDevname, dirImagin, dirSujet, dirSeeg, dirIctal, dirEI)) as it:
                                                                i = 1
                                                                for entry in it:
                                                                    name, ext = os.path.splitext(entry)
                                                                    if entry.name.startswith('EI') and ext == '.txt':
                                                                        IeDict = util.Ieeg()
                                                                        IeDict['sub'] = sub_imagin['sub']
                                                                        IeDict['ses'] = str(1).zfill(2)
                                                                        IeDict['proc'] = 'EI'
                                                                        IeDict['run'] = str(i).zfill(2)
                                                                        IeDict['modality'] = 'ieeg'
                                                                        IeDict['task'] = 'Seizure'
                                                                        IeDict['fileLoc'] = entry.path

                                                                        ieJ = util.IeegJSON()
                                                                        ieJ['TaskName'] = 'Carte EI'
                                                                        ieJ['TaskDescription'] = 'Analysis'
                                                                        ieJ['RecordingDate'] = SeegDate
                                                                        ieJ.simplify_sidecar(required_only=False)
                                                                        IeDict['IeegJSON'] = ieJ

                                                                        sub_imagin['Ieeg'] = IeDict
                                                                        i += 1
                            pres_sub, sub_index = check_subject_in_list(subj_imagin_list, sub_imagin['sub'])
                            if not pres_sub:
                                subj_imagin_list.append(sub_imagin)
                            else:
                                #attr_dict = {key: sub_imagin[key] for key in sub_imagin.keys() if sub_imagin[key]}
                                subj_imagin_list[sub_index].update(sub_imagin.get_attributes())
                    for sub_dev in subj_imagin_list:
                        pip_folder['Subject'].append(sub_dev)
            pip_present, pip_index = check_pipeline_in_list(pip_folder_list, pip_folder['name'])
            if not pip_present:
                pip_folder_list.append(pip_folder)
            else:
                attr_dict = {key: pip_folder[key] for key in pip_folder.keys() if pip_folder[key]}
                pip_folder_list[pip_index].update(attr_dict)

            for pip in pip_folder_list:
                Dev_folder['Pipeline'].append(pip)


    for sub_elt in subject_list:
        raw_data['Subject'] = sub_elt
    raw_data['Derivatives'] = Dev_folder
    DataName = util.DatasetDescJSON()
    DataName['Name'] = 'FTract'
    DataName['Authors'] = 'Aude'
    raw_data['DatasetDescJSON'] = remove_unused_keys(DataName)
    #print(raw_data)
    raw_data.save_as_json(savedir=pathTempMIP)
    print('Tha data2import has been created')


if __name__ == '__main__':
    print('This script allow to create the data2import of a given folder !!!')
