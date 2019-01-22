#!/usr/bin/python3

import os
import json
import hashlib
import math
import csv
import re
from datetime import datetime

import ins_bids_class as util


class IeegElecCSV(dict):
    keylist = ['sub', 'ses', 'Manufacturer', 'model', 'fileLoc']
    allowed_file_formats = ['.csv']
    space_type = ['MNI', 'fsnative']

    def __init__(self):
        for key in self.keylist:
            self[key] = ''

    def __setitem__(self, key, value):
        if key in self.keylist:
            dict.__setitem__(self, key, value)

    def create_filename(self, space, modality, f_list):
        sub = 'sub-' + self['sub']
        ses = 'ses-' + self['ses']
        sp = 'space-'+space
        if modality == 'electrodes':
            filename = sub + '_' + ses + '_' + sp + '_' + modality + '.tsv'
        else:
            filename = sub + '_' + ses + '_' + sp + '_' + modality + '.json'

        f_list.append(filename)
        return filename

    def get_xyz(self, str):
        xyz = str.split('[')
        xyz = xyz[1].split(']')
        xyz = xyz[0].split(',')
        coord = list(xyz)
        x = coord[0]
        y = coord[1]
        z = coord[2]
        return x, y, z

    def get_the_size(self):
        m_split = self['model'].split('-')
        if m_split[0].lower() == 'dixi':
            ray_elec = 0.4
            h_elec = 2
        elif m_split[0].lower() == 'adtech':
            if m_split[1][0:2] == 'SD':
                ray_elec = 1.1 / 2
                h_elec = 2.4
            elif m_split[1] == 'ET':
                ray_elec = 1.1 / 2
                h_elec = 2.4
            elif m_split[1][0:2] == 'BF':
                if m_split[2] == '9P':
                    ray_elec = 1.1 / 2
                    h_elec = 2.4
                elif m_split[2] == 'SP51X_without2firstcontactsClose':
                    ray_elec = 1.1 / 2
                    h_elec = 1.57
                else:
                    ray_elec = 1.3 / 2
                    h_elec = 1.57
            elif m_split[1][0:3] == 'old':
                ray_elec = 1.1 / 2
                h_elec = 1.57
            else:
                ray_elec = 1.1 / 2
                h_elec = 2.4
        elif m_split[0].lower() == 'alcis':
            ray_elec = 0.8 / 2
            h_elec = 2
        elif m_split[0].lower() == 'alcys':
            ray_elec = 1 / 2
            h_elec = 1
        elif m_split[0].lower() == 'pmt':
            ray_elec = 0.8 / 2
            h_elec = 2
            if m_split[1] == '8Large':
                ray_elec = 1.2 / 2
                h_elec = 4
        elif m_split[0].lower() == 'medtronic':
            ray_elec = 1.3 / 2
            h_elec = 1
        elif m_split[0].lower() == 'montrealhomemade':
            ray_elec = 1 / 2
            h_elec = 1
        else:
            ray_elec = 0.4
            h_elec = 2

        size = round(2 * math.pi * ray_elec * h_elec, 2)
        return size

    def create_ElecTSV_file(self):

        def create_CoordSys_file(space, sub, ses):
            CoordSys = util.IeegCoordSysJSON()
            CoordSys['iEEGCoordinateSystem'] = space
            CoordSys['iEEGCoordinateUnits'] = 'mm'
            CoordSys['iEEGCoordinateProcessingDescription'] = 'SEEG contacts segmentation on MRI scan'
            #A modifier
            CoordSys['IntendedFor'] = 'sub-' + sub + '\\ses-' + ses + '\\anat\\sub-' + sub + '_ses-' + ses + '_acq-postimp_T1w.nii'

            CoordSys.simplify_sidecar(required_only=False)
            return CoordSys

        linecsv = []
        filetoconvert = self['fileLoc']
        with open(filetoconvert, 'r') as csvin:
            csvDict = csv.reader(csvin, delimiter='\t')
            for row in csvDict:
                linecsv.append(row)
        lengthR = linecsv.__len__()
        lengthC = linecsv[2].__len__()

        Header_TSV = util.IeegElecTSV.required_fields + ['type'] + linecsv[2][3:lengthC]
        fname_list = list()
        for sp_type in self.space_type:
            ElecTSV = util.IeegElecTSV()
            ElecTSV.header = Header_TSV
            ElecTSV.clear()
            dictElec = dict()

            size_type = self.get_the_size()
            for val in linecsv[3:lengthR - 13]:
                if not val:
                    pass
                else:
                    i = 0
                    while i < len(val):
                        if i == 0:
                            dictElec['name'] = val[i]
                        elif i == 1 and sp_type=='MNI':
                            x, y, z = self.get_xyz(val[i])
                            dictElec['x'] = x
                            dictElec['y'] = y
                            dictElec['z'] = z
                        elif i == 2 and sp_type=='fsnative':
                            x, y, z = self.get_xyz(val[i])
                            dictElec['x'] = x
                            dictElec['y'] = y
                            dictElec['z'] = z
                        elif i >= 3:
                            dictElec[Header_TSV[i+2]] = val[i]
                        i += 1

                    dictElec['size'] = size_type
                    dictElec['type'] = self['model']

                    ElecTSV.append(dictElec)

            #Write the TSV files and associate
            PathToWrite = os.path.dirname(self['fileLoc'])
            Elecname = self.create_filename(space=sp_type, modality='electrodes', f_list=fname_list)
            ElecTSV.write_file(os.path.join(PathToWrite, Elecname))
            Elecoord = create_CoordSys_file(space=sp_type, sub=self['sub'], ses=self['ses'])
            Elecoordname = self.create_filename(space=sp_type, modality='coordsystem', f_list=fname_list)
            Elecoord.write_file(os.path.join(PathToWrite, Elecoordname))

        return fname_list


class TabRecap(dict):
    keylist = ['sub', 'Session', 'SeizureRun']

    def __init__(self):
        for key in self.keylist:
            try:
                mod = eval(key)
                if issubclass(mod, dict):
                    self[key] = []
                else:
                    self[key] = ''
            except:
                self[key] = ''
                pass

    def __setitem__(self, key, value):
        if key in self.keylist:
            dict.__setitem__(self, key, value)

    def is_present(self, key, label):
        s_present=False
        s_index=None
        for elt in self[key]:
            if elt['label']==label:
                s_present = True
                s_index = self[key].index(elt)
        return s_present, s_index

    def get_the_number(self, key, label):
        label_present, label_index = self.is_present(key, label)
        if label_present:
            number = self[key][label_index]['Number']
        else:
            taille = len(self[key])
            self[key].append(eval(key+'()'))
            self[key][taille]['label']=label
            number = taille+1
            self[key][taille]['Number']=number
        return number

    def get_attributes(self):
        attr_dict = {key: self[key] for key in self.keylist if isinstance(key, str)}
        return attr_dict


class Session(dict):
    keylist = ['label', 'Number']

    def __init__(self):
        for key in self.keylist:
            self[key] = ''


class SeizureRun(dict):
    keylist = ['label', 'Number']

    def __init__(self):
        for key in self.keylist:
            self[key] = ''


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
    real_age = str(year) + ',' + str(month)
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
        if elt['Name'] == pip_name:
            pip_present = True
            index_pip = pip_list.index(elt)
    return pip_present, index_pip


def convert_txt_in_tsv(file):
    filename, ext = os.path.splitext(file)
    with open(file, 'r') as fichier:
        txt = fichier.readlines()
    tsvlist = list()
    txt[0] = txt[0].replace(' ', '')
    header = txt[0].replace('/', '\t')
    tsvlist.append(header)
    end = len(txt)-1
    for elt in txt[1:end]:
        if elt.isspace():
            pass
        else:
            size = elt.count(' ') - 1
            tsvlist.append(elt.replace(size*' ', '\t'))
    with open(filename+'.tsv', 'w') as wfile:
        for line in tsvlist:
            wfile.write(line)


def create_names_from_attributes(Idict):
    filename = ''
    dirname = ''
    ext = '.vhdr'
    lname = []
    ldirname = []
    keydir = ['sub', 'ses']
    keynot = ['proc', 'ProcessJSON', 'fileLoc', 'modality']
    for key in Idict:
        if not key in keynot and Idict[key]:
            name = key +'-'+Idict[key]
            lname.append(name)
            if key in keydir:
                ldirname.append(key +'-'+Idict[key])
        elif key == 'modality':
            lname.append(Idict[key])
            ldirname.append(Idict[key])
    filename = '_'.join(lname)
    dirname = os.path.join(*ldirname)
    return os.path.join(dirname, filename+ext)


def read_ftract_folders(pathTempMIP, RequirementFile=None, centres=None, sujets=None, flagIeeg=True, flagAnat=True, flagProc=True):
    now = datetime.now()
    if RequirementFile:
        raw_data = util.Data2Import(pathTempMIP, RequirementFile)
    else:
        raw_data = util.Data2Import(pathTempMIP)
    raw_data['UploadDate'] = now.strftime("%d-%m-%Y_%Hh%M")

    #ext accepted by bids
    ext_ieeg = ['.mat', '.eeg', '.TRC', '.edf', '.eab', '.vhdr', '.cnt']
    ext_process = ['.txt']

    #Create the ftract centre list
    ftract_site = ['ftract-'+site.lower() for site in centres]

    ###Go throught all the folders to find the ieeg and anat###
    subject_list = list()
    subject_tab = list()
    #Take the seizure from 01-uploads
    PathSeizure = os.path.join(pathTempMIP, '01-uploads')
    for dircentre in os.listdir(PathSeizure):
        if dircentre in ftract_site and flagIeeg:
            PathCentre = os.path.join(PathSeizure, dircentre, 'uploads')
            for Subdir in os.listdir(PathCentre):
                if Subdir in sujets:
                    PathSujet = os.path.join(PathCentre, Subdir, 'SEEG', 'CRA', 'Seizures')
                    hashed_sub = hash_object(Subdir)
                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                    if not subject_present:
                        sub = util.Subject()
                        sub['sub'] = hashed_sub
                    else:
                        sub = subject_list[index_subject]
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                    if not sub_tab_pres:
                        sub_tab = TabRecap()
                        sub_tab['sub'] = hashed_sub
                    else:
                        sub_tab = subject_tab[sub_tab_index]
                    with os.scandir(PathSujet) as it:
                        for entry in it:
                            label_run = re.findall(r'\d+', entry.name)
                            num_run = sub_tab.get_the_number('SeizureRun', label_run)
                            IeDict = util.Ieeg()
                            IeDict['sub'] = sub['sub']
                            IeDict['task'] = 'Seizure'
                            IeDict['ses'] = str(1).zfill(2)
                            IeDict['modality'] = 'ieeg'
                            IeDict['run'] = str(num_run).zfill(2)
                            IeDict['fileLoc'] = entry.path

                            sub['Ieeg'] = IeDict

                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                    if not subject_present:
                        subject_list.append(sub)
                    else:
                        subject_list[index_subject].update(sub.get_attributes())
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                    if not sub_tab_pres:
                        subject_tab.append(sub_tab)
                    else:
                        subject_tab[sub_tab_index].update(sub_tab.get_attributes())
    PathSEEG = os.path.join(pathTempMIP, '02-raw')
    for Subdir in os.listdir(PathSEEG):
        if Subdir in sujets and flagIeeg:
            hashed_sub = hash_object(Subdir)
            subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
            if not subject_present:
                sub = util.Subject()
                sub['sub'] = hashed_sub
            else:
                sub = subject_list[index_subject]
            sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
            if not sub_tab_pres:
                sub_tab = TabRecap()
                sub_tab['sub'] = hashed_sub
            else:
                sub_tab = subject_tab[sub_tab_index]
            # Get the Manufacturer
            Manufacturer = get_the_manufacturer(Subdir)
            with os.scandir(os.path.join(PathSEEG, Subdir)) as it:
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

                    elif entry.name.startswith('StimLF') and entry.is_dir():
                        [Stim, date] = entry.name.split('_')
                        num_ses = sub_tab.get_the_number('Session', date)
                        for dirRaw in os.listdir(entry.path):
                            if os.path.isdir(os.path.join(entry.path, dirRaw)) and dirRaw == 'BadChannels':
                                for filMod in os.listdir(os.path.join(entry.path, dirRaw)):
                                    if os.path.isfile(os.path.join(entry.path, dirRaw, filMod)):
                                        name, ext = os.path.splitext(filMod)
                                        if ext in ext_ieeg:
                                            contact, amplitude, frequency, time, run = split_stim_name(name)
                                            IeDict = util.Ieeg()
                                            IeDict['sub'] = sub['sub']
                                            IeDict['ses'] = str(num_ses).zfill(2)
                                            IeDict['task'] = 'Stimuli'
                                            IeDict['acq'] = contact
                                            IeDict['run'] = str(run).zfill(2)
                                            IeDict['fileLoc'] = os.path.join(entry.path, dirRaw, filMod)

                                            ieJ = util.IeegJSON()
                                            ieJ['TaskName'] = 'Stimuli'
                                            ieJ['Manufacturer'] = Manufacturer
                                            ieJ['TaskDescription'] = 'Epoch starting around 40s before the first stimulus and ending 2-3s after the stimuli block'
                                            ieJ['Stimulation'] = 'Electrodes stimulated = ' + contact + ', Amplitude = ' + amplitude + ', Frequency = ' + frequency + ', Pulse width = ' + time
                                            ieJ['RecordingDate'] = SeegDate
                                            ieJ.simplify_sidecar(required_only=False)
                                            IeDict['IeegJSON'] = ieJ

                                            ieChan = util.IeegChannelsTSV()
                                            #modify the entry in the function get_bad_channels and put the file
                                            Chan1, Chan2 = get_bad_channels(contact)
                                            ieChan.append(Chan1)
                                            ieChan.append(Chan2)
                                            IeDict['IeegChannelsTSV'] = ieChan

                                            sub['Ieeg'] = IeDict
                        sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                        if not sub_tab_pres:
                            subject_tab.append(sub_tab)
                        else:
                            subject_tab[sub_tab_index].update(sub_tab.get_attributes())
            sub['age'] = calculate_age_at_acquisition(birthDate, SeegDate)
            subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
            if not subject_present:
                subject_list.append(sub)
            else:
                subject_list[index_subject].update(sub.get_attributes())

    PathPreprocessed = os.path.join(pathTempMIP, '03-preprocessed')
    Dev_folder = util.Derivatives()
    pip_folder_list = list()
    for dirSoft in os.listdir(PathPreprocessed):
        if dirSoft == 'BrainVisa' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagIeeg:
            PathBrain = os.path.join(PathPreprocessed, dirSoft, 'Epilepsy')
            pip_folder = util.Pipeline()
            pip_folder['Name'] = 'BrainVisa'
            subj_brain_list = list()
            with os.scandir(PathBrain) as it:
                for entry in it:
                    name, date = entry.name.split('_')
                    if name in sujets:
                        hashed_sub = hash_object(name)
                        Manufacturer = get_the_manufacturer(name)
                        subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                        if not subject_present:
                            sub = util.Subject()
                            sub['sub'] = hashed_sub
                        else:
                            sub = subject_list[index_subject]
                        sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                        if not sub_tab_pres:
                            sub_tab = TabRecap()
                            sub_tab['sub'] = hashed_sub
                        else:
                            sub_tab = subject_tab[sub_tab_index]
                        num_ses = sub_tab.get_the_number('Session', date)
                        ieImplant = IeegElecCSV()
                        for fileSujet in os.listdir(os.path.join(entry.path, 'implantation')):
                            fname, ext = os.path.splitext(fileSujet)
                            if ext == '.csv':
                                ieImplant['fileLoc'] = os.path.join(entry.path, 'implantation', fileSujet)
                                ieImplant['sub'] = sub['sub']
                                ieImplant['Manufacturer'] = Manufacturer
                                ieImplant['ses'] = str(num_ses).zfill(2)
                            elif ext == '.elecimplant':
                                with open(os.path.join(entry.path, 'implantation', fileSujet)) as json_file:
                                    json_data = json.load(json_file)
                                ieImplant['model'] = json_data['electrodes'][-1]['model']
                        fname_list = ieImplant.create_ElecTSV_file()

                        for elecfile in fname_list:
                            ieSidecar = util.IeegGlobalSidecars(os.path.join(entry.path, 'implantation', elecfile))
                            ieSidecar.get_attributes_from_filename()
                            sub['IeegGlobalSidecars'] = ieSidecar

                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                    if not subject_present:
                        subject_list.append(sub)
                    else:
                        subject_list[index_subject].update(sub.get_attributes())
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                    if not sub_tab_pres:
                        subject_tab.append(sub_tab)
                    else:
                        subject_tab[sub_tab_index].update(sub_tab.get_attributes())

        elif dirSoft == 'FTRACT' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagProc:
            subj_imagin_list = list()
            for dirSujet in os.listdir(os.path.join(PathPreprocessed, dirSoft)):
                if dirSujet in sujets:
                    hashed_sub = hash_object(dirSujet)
                    subject_present, index_subject = check_subject_in_list(subj_imagin_list, hashed_sub)
                    if not subject_present:
                        sub_imagin = util.SubjectProcess()
                        sub_imagin['sub'] = hashed_sub
                    else:
                        sub_imagin = subj_imagin_list[index_subject]
                    '''pres_sub_raw, sub_raw_index = check_subject_in_list(subject_list, hashed_sub)
                    if pres_sub_raw:
                        sub_imagin['sex'] = subject_list[sub_raw_index]['sex']
                        sub_imagin['age'] = subject_list[sub_raw_index]['age']'''
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                    if not sub_tab_pres:
                        sub_tab = TabRecap()
                        sub_tab['sub'] = hashed_sub
                    else:
                        sub_tab = subject_tab[sub_tab_index]
                    with os.scandir(os.path.join(PathPreprocessed, dirSoft, dirSujet, 'SEEG')) as it:
                        for entry in it:
                            nom, date = entry.name.split('_')
                            num_ses = sub_tab.get_the_number('Session', date)
                            if nom == 'Ictal':
                                pip_folder = util.Pipeline()
                                pip_folder['Name'] = 'Brainstorm'
                                for dirEI in os.listdir(os.path.join(entry.path, 'EI')):
                                    SZ_list = ['SZGroup', 'SZGroup1', 'SZGroup2', 'SZGroup3']
                                    if dirEI in SZ_list:
                                        for fileEI in os.listdir(os.path.join(entry.path, 'EI', dirEI, 'ImaGIN_epileptogenicity')):
                                            sujet_run, ext = os.path.splitext(fileEI)
                                            if sujet_run.split('_')[0] == 'EI' and ext in ext_process:
                                                convert_txt_in_tsv(os.path.join(entry.path, 'EI', dirEI, 'ImaGIN_epileptogenicity', fileEI))
                                                #A modifier car prend aussi les paramètres alors que je veux juste le num
                                                label_run = re.findall(r'\d+', sujet_run)
                                                num_run = sub_tab.get_the_number('SeizureRun', label_run)
                                                IeDict = util.create_subclass_instance('IeegProcess', util.Process)
                                                IeDict['sub'] = sub_imagin['sub']
                                                IeDict['ses'] = str(num_ses).zfill(2)
                                                IeDict['proc'] = 'EpileptogenicityMapping'
                                                IeDict['run'] = str(num_run).zfill(2)
                                                IeDict['task'] = 'Seizure'
                                                IeDict['fileLoc'] = os.path.join(entry.path, 'EI', dirEI, 'ImaGIN_epileptogenicity', sujet_run+'.tsv')

                                                ieJ = util.ProcessJSON()
                                                ieJ['Description'] = 'Epileptogenicity mapping of the Seizure data'
                                                ieJ['Sources'] = create_names_from_attributes(IeDict)
                                                ieJ.modality_field = 'ieeg'
                                                ieJ.simplify_sidecar(required_only=False)
                                                IeDict['ProcessJSON'] = ieJ

                                                sub_imagin['IeegProcess'] = IeDict

                    subject_present, index_subject = check_subject_in_list(subj_imagin_list, sub_imagin['sub'])
                    if not subject_present:
                        subj_imagin_list.append(sub_imagin)
                    else:
                        subj_imagin_list[index_subject].update(sub_imagin.get_attributes())
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub_imagin['sub'])
                    if not sub_tab_pres:
                        subject_tab.append(sub_tab)
                    else:
                        subject_tab[sub_tab_index].update(sub_tab.get_attributes())

            for sub_dev in subj_imagin_list:
                pip_folder['SubjectProcess'].append(sub_dev)
            pip_present, pip_index = check_pipeline_in_list(pip_folder_list, pip_folder['Name'])
            if not pip_present:
                pip_folder_list.append(pip_folder)
            else:
                attr_dict = {key: pip_folder[key] for key in pip_folder.keys() if pip_folder[key]}
                pip_folder_list[pip_index].update(attr_dict)

        elif dirSoft == 'Deface' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagAnat:
            for dirSujet in os.listdir(os.path.join(PathPreprocessed, dirSoft)):
                if dirSujet in sujets:
                    hashed_sub = hash_object(dirSujet)
                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                    if not subject_present:
                        sub = util.Subject()
                        sub['sub'] = hashed_sub
                    else:
                        sub = subject_list[index_subject]
                    with os.scandir(os.path.join(PathPreprocessed, dirSoft, dirSujet)) as it:
                        for entry in it:
                            if entry.name.startswith('T1') and entry.is_dir():
                                for dirT1 in os.listdir(entry.path):
                                    if os.path.isdir(os.path.join(entry.path, dirT1)):
                                        #il faudra vérifier pour les sessions
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
                                            AnaDict['ce'] = 'gado'
                                            AnaDict['fileLoc'] = os.path.join(entry.path, dirT1)
                                            AnaJ = util.AnatJSON()
                                            AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                            AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)

                                            sub['Anat'] = AnaDict

                                        elif dirT1.split('_')[0] == 'T1pre':
                                            AnaDict = util.Anat()
                                            AnaDict['sub'] = sub['sub']
                                            AnaDict['ses'] = str(1).zfill(2)
                                            AnaDict['acq'] = 'preop'
                                            AnaDict['modality'] = 'T1w'
                                            AnaDict['fileLoc'] = os.path.join(entry.path, dirT1)

                                            sub['Anat'] = AnaDict
                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                    if not subject_present:
                        subject_list.append(sub)
                    else:
                        subject_list[index_subject].update(sub.get_attributes())

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
    PathToImport = r'D:\Data\Test_Ftract_Import\Original_deriv'
    RequirementFile = r'D:\Data\Test_Ftract_Import\Original_deriv\requirements.json'
    centre_select = ['GRE']
    subject_selected=['0137GRE']
    read_ftract_folders(PathToImport, RequirementFile, centres=centre_select, sujets=subject_selected)
