#!/usr/bin/python3
# -*-coding:Utf-8 -*

"""
   This module was written by Aude Jegou <aude.jegou@univ-amu.fr>.
   This module create the data2import for F-Tract database.
   v0.1 March 2019
"""

import os
import json
import hashlib
import math
import csv
import re
import datetime
import shutil

#pour les requêtes
#import sys
#sys.path.append('/home/audeciment/django')
import ftractdjango
ftractdjango.init()
from ftdata.models import *

import ins_bids_class as util

class IeegElecCSV(dict):
    keylist = ['sub', 'ses', 'Manufacturer', 'model', 'fileLoc']
    allowed_file_formats = ['.csv']
    space_type = ['MNI152Lin', 'other']

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

    def create_electsv_file(self, ctPresent):

        def create_coordsys_file(space, sub, ses, ct):
            coordsys = util.IeegCoordSysJSON()  
            if space == 'other':
                coordsys['iEEGCoordinateSystemDescription'] = 'Coordinate computed from the subject"s T1w/CT image'
            coordsys['iEEGCoordinateSystem'] = space
            coordsys['iEEGCoordinateUnits'] = 'mm'
            coordsys['iEEGCoordinateProcessingDescription'] = 'SEEG contacts segmentation on scan'
            if not ct:
                coordsys['IntendedFor'] = 'sub-' + sub + '/ses-' + ses + '/anat/sub-' + sub + '_ses-' + ses + '_T1w.nii'
            elif ct:
                coordsys['IntendedFor'] = 'sub-' + sub + '/ses-' + ses + '/anat/sub-' + sub + '_ses-' + ses + '_CT.nii'

            coordsys.simplify_sidecar(required_only=False)
            return coordsys

        linecsv = []
        filetoconvert = self['fileLoc']
        with open(filetoconvert, 'r') as csvin:
            csvdict = csv.reader(csvin, delimiter='\t')
            for row in csvdict:
                linecsv.append(row)
        lengthr = linecsv.__len__()
        lengthc = linecsv[2].__len__()

        header_tsv = util.IeegElecTSV.required_fields + ['type'] + linecsv[2][3:lengthc]
        fname_list = list()
        for sp_type in self.space_type:
            elec_tsv = util.IeegElecTSV()
            elec_tsv.header = header_tsv
            elec_tsv.clear()
            dictelec = dict()

            size_type = self.get_the_size()
            for val in linecsv[3:lengthr]:
                if not val:
                    pass
                elif len(val) < lengthc:
                    pass
                else:
                    i = 0
                    while i < len(val):
                        if i == 0:
                            dictelec['name'] = val[i]
                        elif i == 1 and sp_type=='MNI152Lin':
                            x, y, z = self.get_xyz(val[i])
                            dictelec['x'] = x
                            dictelec['y'] = y
                            dictelec['z'] = z
                        elif i == 2 and sp_type=='other':
                            x, y, z = self.get_xyz(val[i])
                            dictelec['x'] = x
                            dictelec['y'] = y
                            dictelec['z'] = z
                        elif i >= 3:
                            dictelec[header_tsv[i+3]] = val[i]
                        i += 1

                    dictelec['size'] = size_type
                    dictelec['type'] = self['model']

                    elec_tsv.append(dictelec)

            #Write the TSV files and associate
            pathtowrite = os.path.dirname(self['fileLoc'])
            elecname = self.create_filename(space=sp_type, modality='electrodes', f_list=fname_list)
            elec_tsv.write_file(os.path.join(pathtowrite, elecname))
            elecoord = create_coordsys_file(space=sp_type, sub=self['sub'], ses=self['ses'], ct=ctPresent)
            elecoordname = self.create_filename(space=sp_type, modality='coordsystem', f_list=fname_list)
            elecoord.write_file(os.path.join(pathtowrite, elecoordname))

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

    def is_present(self, key, label, ses=None):
        s_present=False
        s_index=None
        for elt in self[key]:
            if ses:
                if elt['label']==label and elt['Session']==ses:
                    s_present = True
                    s_index = self[key].index(elt) 
            else:                   
                if label in elt['label']:
                    s_present = True
                    s_index = self[key].index(elt)
                elif elt['label'] in label and len(label)==8:
                    elt['label'] = label
                    s_present = True
                    s_index = self[key].index(elt)
        return s_present, s_index

    def get_the_number(self, key, label, ses=None):
        if ses:
            label_present, label_index = self.is_present(key, label, ses=ses)
        else:
            label_present, label_index = self.is_present(key, label)
        if label_present:
            number = self[key][label_index]['Number']
        elif not label_present and ses:
            i=0
            taille = len(self[key])
            for elt in self[key]: 
                if elt['Session']==ses:
                    i+=1  
            number = i+1
            self[key].append(eval(key+'()'))
            self[key][taille]['label']=label
            self[key][taille]['Number']=number
            self[key][taille]['Session']=ses       
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
 
    def order_session(self):
        temp_label = []
        for elt in self['Session']:
            if len(elt['label'])==8:
                format_date = '%d%m%Y'
                temp_label = [datetime.datetime.strptime(elt['label'], format_date) for elt in self['Session']]
            elif len(elt['label'])==6:
                format_date = '%m%Y'
                temp_label = [datetime.datetime.strptime(elt['label'], format_date) for elt in self['Session']]
            elif len(elt['label'])==4:
                format_date = '%Y'
                temp_label = [datetime.datetime.strptime(elt['label'], format_date) for elt in self['Session']]
        temp_label.sort()
        for elt in self['Session']:
            for tp_label in temp_label:
                temp = datetime.datetime.strftime(tp_label, format_date)
                if temp in elt['label']:
                    elt['Number'] = temp_label.index(tp_label) + 1

    def get_closest_session(self, label):
        temp_label = [datetime.datetime.strptime(elt['label'], '%d%m%Y') for elt in self['Session']]
        label_date =  datetime.datetime.strptime(label, '%d%m%Y')
        temp_label.sort()
        min_list = []
        for elt in temp_label:
            min_list.append(abs(elt - label_date))
        idx = min_list.index(min(min_list))
        idx_label = datetime.datetime.strftime(temp_label[idx], '%d%m%Y')
        for elt in self['Session']:
            if idx_label == elt['label']:
                number = elt['Number']
        return number

class Session(dict):
    keylist = ['label', 'Number']

    def __init__(self):
        for key in self.keylist:
            self[key] = ''


class SeizureRun(dict):
    keylist = ['label', 'Number', 'Session']

    def __init__(self):
        for key in self.keylist:
            self[key] = ''


def calculate_age_at_acquisition(birth_date, seeg_date):
    bdate_year, bdate_month, bdate_day = birth_date.split('-')
    sdate_year, sdate_month, sdate_day = seeg_date.split('-')
    year = int(sdate_year) - int(bdate_year) - ((int(sdate_month), int(sdate_day)) < (int(bdate_month), int(bdate_day)))
    if int(bdate_month) > int(sdate_month):
        month = int(sdate_month) - int(bdate_month) + 12
    else:
        month = int(sdate_month) - int(bdate_month)
    if int(bdate_day) < int(sdate_day):
        month +=1
    else:
        month -=1
    real_age = str(year) + ',' + str(month)
    return real_age

def create_relative_date(seeg_date, exam_date):
    days = exam_date - seeg_date
    ini_seeg = datetime.date(1900, 1, 1)
    gap = ini_seeg + days
    relative_date = str(gap) + 'T00:00:00'
    
    return relative_date

def remove_unused_keys(dic):
    key = dic.keys()
    list_key_unused = []
    for k in key:
        if dic[k] == 'n/a':
            list_key_unused.append(k)
    for l in list_key_unused:
        del dic[l]
    return dic


def hash_object(obj):
    clef256 = hashlib.sha256(obj.encode())
    clefdigest = clef256.hexdigest()
    clef = clefdigest[0:12]
    return clef


def split_stim_name(name):
    contact = name.split('_')[1]
    contact = contact.split('-')[0] + contact.split('-')[1]
    amplitude = name.split('_')[2]
    frequency = name.split('_')[3]
    time = name.split('_')[4]
    run = name.split('_')[5]
    return contact, amplitude, frequency, time, run


def get_the_manufacturer(subject_name):
    centre = ''
    i = len(subject_name) - 3
    while i < len(subject_name):
        centre = centre + subject_name[i]
        i += 1
    if centre == 'GRE' or centre == 'LYO':
        manufacturer ='Micromed'
    elif centre == 'MAR':
        manufacturer = 'Deltamed'
    elif centre == 'MIL':
        manufacturer = 'Nihon-kohden'
    elif centre == 'FRE':
        manufacturer = 'Compumedics'
    return manufacturer


def get_bad_channels(file_name):
    with open(file_name, 'r') as fichier:
        txt = fichier.readlines()
    channel_list = list()
    for elt in txt:
        chan_dict = dict()
        chan = elt.split(' ')[1]
        chan_dict['name'] = chan.strip()
        chan_dict['status'] = 'bad'
        channel_list.append(chan_dict)
    return channel_list

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

def get_sub_attributes(subject_present, index_subject, subject_list, subject_name, flagtable=False, flagprocess=False):
    if not subject_present and not flagtable and not flagprocess:
        sub = util.Subject()
        sub['sub'] = subject_name
    elif not subject_present and flagtable:
        sub = TabRecap()
        sub['sub'] = subject_name
    elif not subject_present and flagprocess:
        sub = util.SubjectProcess()
        sub['sub'] = subject_name   
    else:
        sub = subject_list[index_subject]
    return sub

def update_subject_list(subject_present, index_subject, subject_list, sub):
    if not subject_present:
        subject_list.append(sub)
    else:
        subject_list[index_subject].update(sub.get_attributes())

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


def create_names_from_attributes(Idict, ext):
    filename = ''
    dirname = ''
    ext = ext
    lname = []
    ldirname = []
    keydir = ['sub', 'ses']
    keynot = ['proc', 'hemi', 'ProcessJSON', 'fileLoc', 'modality']
    for key in Idict:
        if not key in keynot and Idict[key]:
            name = key +'-'+Idict[key]
            lname.append(name)
            if key in keydir:
                ldirname.append(key +'-'+Idict[key])
        elif key == 'modality':
            if Idict[key]=='pial':
                lname.append('T1w')
                ldirname.append('anat')
            else:
                lname.append(Idict[key])
                ldirname.append(Idict[key])
    filename = '_'.join(lname)
    dirname = os.path.join(*ldirname)
    return os.path.join(dirname, filename+ext)


def read_ftract_folders(pathTempMIP, RequirementFile=None, centres=None, sujets=None, flagIeeg=True, flagAnat=True, flagProc=True):
    """
        Reads the directory to create the data2import with the selected subjects.
    """
    now = datetime.datetime.now()
    if RequirementFile:
        raw_data = util.Data2Import(pathTempMIP, RequirementFile)
    else:
        raw_data = util.Data2Import(pathTempMIP)
    raw_data['UploadDate'] = now.strftime("%d-%m-%Y_%Hh%M")

    #ext accepted by bids
    ext_ieeg = ['.mat', '.eeg', '.TRC', '.edf', '.eab', '.vhdr', '.cnt']
    ext_process = ['.txt', '.pial']
    ext_info = ['.jpg', '.jpeg', '.png', '.bmp', '.pdf', '.ppt', '.pptx']

    #Create the ftract centre list
    ftract_site = ['ftract-'+site.lower() for site in centres]

    ###Go throught all folders to find ieeg and anat data###
    subject_list = list()
    subject_tab = list()
    clinical_list = raw_data.requirements['Requirements']['Subject']['keys']

    #Get the clinical information for each subject
    for sub_elt in sujets:
        hashed_sub = hash_object(sub_elt)
        subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
        sub = get_sub_attributes(subject_present, index_subject, subject_list, hashed_sub)

        p_dob = Patient.objects.filter(patient_code=sub_elt).values('birth_date').get()
        p_gender = Patient.objects.filter(patient_code=sub_elt).values('gender').get()
        sub['sex'] = p_gender['gender']
        size_crf = len(CRF.objects.filter(patient__patient_code__contains=sub_elt))
        if size_crf == 1:
            crfs = CRF.objects.filter(patient__patient_code__contains=sub_elt).values().get()
            temp_seeg = crfs['SEEG_date']
            sub['age'] = calculate_age_at_acquisition(str(p_dob['birth_date']), str(temp_seeg))
        elif size_crf > 1:
            crfs_multiple = CRF.objects.filter(patient__patient_code__contains=sub_elt).values()
            crfs = crfs_multiple[0]
            temp_seeg = crfs['SEEG_date']
            sub['age'] = calculate_age_at_acquisition(str(p_dob['birth_date']), str(temp_seeg))
            i=1
            while i < size_crf:
                m_seeg = crfs_multiple.values('SEEG_date')[i]['SEEG_date']
                sub['age'] = sub['age'] + ' - ' + calculate_age_at_acquisition(str(p_dob['birth_date']), str(m_seeg))
                i+=1
        for key_req in crfs.keys():
            if key_req in clinical_list:
                if isinstance(crfs[key_req], datetime.date):
                    if key_req=='SEEG_date':
                        sub[key_req] = '1900-01-01T00:00:00'
                    elif crfs[key_req]:
                        sub[key_req] = create_relative_date(temp_seeg, crfs[key_req])
                elif crfs[key_req] == 'Y':
                    try:
                        sub[key_req] = crfs[key_req] + ' - ' + crfs[key_req+'_comment']
                    except KeyError:
                        try:
                            sub[key_req] = crfs[key_req] + ' - ' + crfs[key_req+'_other']
                        except:
                            continue
                elif not crfs[key_req]:
                    sub[key_req] = 'n/a'
                else:
                    sub[key_req] = str(crfs[key_req])  
            elif key_req.startswith('anat_lesion_classif') and crfs[key_req]==True:
                sub['anat_lesion_classif'] = sub['anat_lesion_classif'] + ' '.join(key_req.split('_')[3::])
            elif key_req.startswith('seizure_type_seeg_period') and crfs[key_req]==True:
                sub['seizure_type_seeg_period'] = sub['seizure_type_seeg_period'] +' '.join(key_req.split('_')[4::])+ ', '
            elif key_req.startswith('seizure_freq_seeg_period') and crfs[key_req]==True:
                sub['seizure_freq_seeg_period'] = ' '.join(key_req.split('_')[4::])
            elif key_req.startswith('epilepsy_type_after_seeg') and crfs[key_req]==True:
                sub['epilepsy_type_after_seeg'] = sub['epilepsy_type_after_seeg'] + ' '.join(key_req.split('_')[4::]) + ', ' 
            elif key_req == 'epilepsy_duration_unit':
                sub['epilepsy_duration'] = sub['epilepsy_duration'] + ' ' + crfs[key_req]
            elif key_req.startswith('age_first_seizure') and crfs[key_req]:
                sub['age_first_seizure'] = sub['age_first_seizure'] + ' ' + str(crfs[key_req])
            elif key_req.startswith('clinic_exam') and crfs[key_req]:
                sub['clinic_exam'] = sub['clinic_exam'] + ' ' + crfs[key_req]
            elif key_req.startswith('perso_history') and crfs[key_req]:
                if len(key_req)>27:
                    sub[key_req[0:22]] = sub[key_req[0:22]] + ' ' + crfs[key_req]
                else:
                    sub[key_req[0:19]] = sub[key_req[0:19]] + ' ' + crfs[key_req]        
            elif key_req.startswith('treatment_during_CCEP') and crfs[key_req]:
                sub['treatment_during_CCEP'] = sub['treatment_during_CCEP'] + ' ' + crfs[key_req]
            elif key_req.startswith('pre_iEEG') and crfs[key_req] and isinstance(crfs[key_req], datetime.date):
                sub['pre_iEEG_date'] =  create_relative_date(temp_seeg, crfs[key_req])
        for key in clinical_list:
            if not sub[key]:
                sub[key] = 'n/a'
        subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
        update_subject_list(subject_present, index_subject, subject_list, sub)

    #Take the seeg data from 02-raw
    PathSEEG = os.path.join(pathTempMIP, '02-raw')
    for Subdir in os.listdir(PathSEEG):
        if Subdir in sujets and flagIeeg:
            hashed_sub = hash_object(Subdir)
            subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
            sub = get_sub_attributes(subject_present, index_subject, subject_list, hashed_sub)
            sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
            sub_tab = get_sub_attributes(sub_tab_pres, sub_tab_index, subject_tab, hashed_sub, flagtable=True)

            # Get the Manufacturer
            manufacturer = get_the_manufacturer(Subdir)
            session_list = []
            for entry in os.listdir(os.path.join(PathSEEG, Subdir, 'SEEG')):
                if entry.startswith('StimLF') or entry.startswith('Seizure') or entry.startswith('Baseline'):
                    [stim, date] = entry.split('_')
                    [year, month, day] = date.split('-')
                    label_date = day+month+year
                    num_ses = sub_tab.get_the_number('Session', label_date)
                    session_list.append(entry)
            sub_tab.order_session()
            for entry in session_list:
                [stim, date] = entry.split('_')
                [year, month, day] = date.split('-')
                label_date = day+month+year
                num_ses = sub_tab.get_the_number('Session', label_date)
                if stim == 'StimLF':
                    tasktype = 'ccep'
                elif stim == 'Seizure':
                    tasktype = 'seizure'
                elif stim == 'Baseline':
                    tasktype = 'rest'
                for dirRaw in os.listdir(os.path.join(PathSEEG, Subdir, 'SEEG', entry)):
                    if os.path.isdir(os.path.join(PathSEEG, Subdir, 'SEEG', entry, dirRaw)) and dirRaw == 'BadChannels':
                        for filMod in os.listdir(os.path.join(PathSEEG, Subdir, 'SEEG', entry, dirRaw)):
                            if os.path.isfile(os.path.join(PathSEEG, Subdir, 'SEEG', entry, dirRaw, filMod)):
                                name, ext = os.path.splitext(filMod)
                                if ext in ext_ieeg:
                                    iedict = util.Ieeg()
                                    iedict['sub'] = sub['sub']
                                    iedict['ses'] = 'postimp'+str(num_ses).zfill(2)
                                    iedict['task'] = tasktype
                                    iedict['fileLoc'] = os.path.join(PathSEEG, Subdir, 'SEEG', entry, dirRaw, filMod)

                                    if tasktype == 'ccep':
                                        contact, amplitude, frequency, time, run = split_stim_name(name)
                                        iedict['acq'] = contact+amplitude+frequency+time
                                        iedict['run'] = str(run).zfill(2)
                                        ieJ = util.IeegJSON()
                                        ieJ['TaskName'] = tasktype
                                        ieJ['Manufacturer'] = manufacturer
                                        ieJ['TaskDescription'] = 'Epoch starting around 40s before the first stimulus and ending 2-3s after the stimuli block'
                                        ieJ['ElectricalStimulationParameters'] = 'Electrodes stimulated = ' + contact + ', Amplitude = ' + amplitude + ', Frequency = ' + frequency + ', Pulse width = ' + time
                                        ieJ.simplify_sidecar(required_only=False)
                                        iedict['IeegJSON'] = ieJ
                                        
                                        #Get the channel label considered as bad 
                                        iechan = util.IeegChannelsTSV()
                                        bchan_list = get_bad_channels(os.path.join(PathSEEG, Subdir, 'SEEG', entry, dirRaw, name+'_bChans.txt'))
                                        for badc in bchan_list:
                                            iechan.append(badc)
                                        iedict['IeegChannelsTSV'] = iechan
    
                                    elif tasktype == 'seizure':
                                        seizure, label_run = name.split('_')
                                        num_run = sub_tab.get_the_number('SeizureRun', label_run, num_ses)
                                        iedict['run'] = str(num_run).zfill(2)

                                    elif tasktype == 'rest':
                                        baseline = name.split('_')
                                        label_run = [elt for elt in baseline if elt.isdigit()]
                                        num_run = sub_tab.get_the_number('SeizureRun', label_run[0], num_ses)
                                        iedict['run'] = str(num_run).zfill(2)

                                    sub['Ieeg'] = iedict

                sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                update_subject_list(sub_tab_pres, sub_tab_index, subject_tab, sub_tab)
            subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
            update_subject_list(subject_present, index_subject, subject_list, sub)

            for fileInfo in os.listdir(os.path.join(PathSEEG, Subdir, 'Info')):
                name, ext = os.path.splitext(fileInfo)
                if os.path.isfile(os.path.join(PathSEEG, Subdir, 'Info', fileInfo)) and ext in ext_info:
                    [subject, chart, filenb, date] = name.split('_')
                    [year, month, day] = date.split('-')                
                    label_date = day+month+year
                    num_ses = sub_tab.get_closest_session(label_date)
                    shutil.copy(os.path.join(PathSEEG, Subdir, 'Info', fileInfo), os.path.join('/gin/data/database/temp_bids', fileInfo))
                    iephoto = util.IeegGlobalSidecars(os.path.join('/gin/data/database/temp_bids', fileInfo))
                    iephoto['sub'] = sub['sub']
                    iephoto['ses'] = 'preimp'+str(num_ses).zfill(2)
                    iephoto['acq'] = chart+filenb

                    sub['IeegGlobalSidecars'] = iephoto

                sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                update_subject_list(sub_tab_pres, sub_tab_index, subject_tab, sub_tab)

            subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
            update_subject_list(subject_present, index_subject, subject_list, sub)

    #Take the seizure from 01-uploads
    #Don't need after the transfer of the files in raw
    '''PathSeizure = os.path.join(pathTempMIP, '01-uploads')
    for dircentre in os.listdir(PathSeizure):
        if dircentre in ftract_site and (flagIeeg or flagProc):
            PathCentre = os.path.join(PathSeizure, dircentre, 'uploads')
            for Subdir in os.listdir(PathCentre):
                if Subdir in sujets:
                    PathSujet = os.path.join(PathCentre, Subdir, 'SEEG', 'CRA')
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
                    seizure_list = []
                    for seizure in os.listdir(PathSujet):
                        if seizure.lower().startswith('seizure'):
                    #import pdb; pdb.set_trace()
                            if os.path.isdir(os.path.join(PathSujet, seizure)):
                                seiz = seizure.split('_')
                            elif os.path.isfile(os.path.join(PathSujet, seizure)):
                                name, ext = os.path.splitext(seizure)
                                seiz = name.split('_')
                            if len(seiz)>=2:
                                num_ses = sub_tab.get_the_number('Session', seiz[1])
                            seizure_list.append(seizure)
                    sub_tab.order_session()
                    for seizure in seizure_list:
                        if os.path.isdir(os.path.join(PathSujet, seizure)):
                            seiz = seizure.split('_')
                            if len(seiz)<2:
                                num_ses = 1
                            else:
                                num_ses = sub_tab.get_the_number('Session', seiz[1])
                            for entry in os.listdir(os.path.join(PathSujet, seizure)):
                                nameE, ext = os.path.splitext(entry)
                                label_run = nameE.split('_')[1]
                                num_run = sub_tab.get_the_number('SeizureRun', label_run, num_ses)
                                if flagIeeg:
                                    iedict = util.Ieeg()
                                    iedict['sub'] = sub['sub']
                                    iedict['task'] = 'seizure'
                                    iedict['ses'] = 'postimp' + str(num_ses).zfill(2)
                                    iedict['modality'] = 'ieeg'
                                    iedict['run'] = str(num_run).zfill(2)
                                    iedict['fileLoc'] = os.path.join(PathSujet, seizure, entry)

                                    sub['Ieeg'] = iedict
                        else:
                            nameE, ext = os.path.splitext(seizure)
                            label_run = nameE.split('_')
                            if len(label_run)==2:
                                num_ses = sub_tab.get_the_number('Session', label_run[1])
                                num_run = 1
                            elif len(label_run)>2:
                                num_ses = sub_tab.get_the_number('Session', label_run[1])
                                num_run = sub_tab.get_the_number('SeizureRun', label_run, num_ses)
                            else:
                                num_run = 1
                                num_ses = 1

                            if flagIeeg:
                                iedict = util.Ieeg()
                                iedict['sub'] = sub['sub']
                                iedict['task'] = 'seizure'
                                iedict['ses'] = 'postimp' + str(num_ses).zfill(2)
                                iedict['modality'] = 'ieeg'
                                iedict['run'] = str(num_run).zfill(2)
                                iedict['fileLoc'] = os.path.join(PathSujet, seizure)

                                sub['Ieeg'] = iedict              

                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                    if not subject_present:
                        subject_list.append(sub)
                    else:
                        subject_list[index_subject].update(sub.get_attributes())
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                    if not sub_tab_pres:
                        subject_tab.append(sub_tab)
                    else:
                        subject_tab[sub_tab_index].update(sub_tab.get_attributes())'''


    #Take the processed data
    PathPreprocessed = os.path.join(pathTempMIP, '03-preprocessed')
    Dev_folder = util.Derivatives()
    pip_folder_list = list()
    for dirSoft in os.listdir(PathPreprocessed):
        if dirSoft == 'Brainvisa' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagIeeg:
            PathBrain = os.path.join(PathPreprocessed, dirSoft, 'Epilepsy')
            '''pip_present, pip_index = check_pipeline_in_list(pip_folder_list, 'Brain)
            if not pip_present:
                pip_folder_list.append(pip_folder)
            else:
                attr_dict = {key: pip_folder[key] for key in pip_folder.keys() if pip_folder[key]}
                pip_folder_list[pip_index].update(attr_dict)
            pip_folder = util.Pipeline()
            pip_folder['name'] = 'Brainvisa'''
            #subj_brain_list = list()
            for entry in os.listdir(PathBrain):
                if os.path.isdir(os.path.join(PathBrain, entry)) and entry!='trash':
                    name, date = entry.split('_')
                    if name in sujets:
                        hashed_sub = hash_object(name)
                        manufacturer = get_the_manufacturer(name)
                        subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                        sub = get_sub_attributes(subject_present, index_subject, subject_list, hashed_sub)
                        sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                        sub_tab = get_sub_attributes(sub_tab_pres, sub_tab_index, subject_tab, hashed_sub, flagtable=True)

                        num_ses = sub_tab.get_closest_session(date)
                        ieImplant = IeegElecCSV()
                        ct_present=False
                        for folder in os.listdir(os.path.join(PathBrain, entry)):
                            if os.path.isdir(os.path.join(PathBrain, entry, folder)) and folder == 'ct':
                                ct_present=True
                            elif os.path.isdir(os.path.join(PathBrain, entry, folder)) and folder == 'implantation':
                                ext_implant = []
                                for fileSujet in os.listdir(os.path.join(PathBrain, entry, folder)):
                                    fname, ext = os.path.splitext(fileSujet)
                                    ext_implant.append(ext)
                                    if ext == '.csv':
                                        ieImplant['fileLoc'] = os.path.join(PathBrain, entry, folder, fileSujet)
                                        ieImplant['sub'] = sub['sub']
                                        ieImplant['Manufacturer'] = manufacturer
                                        ieImplant['ses'] = 'postimp'+str(num_ses).zfill(2)
                                    elif ext == '.elecimplant':
                                        with open(os.path.join(PathBrain, entry, folder, fileSujet)) as json_file:
                                            json_data = json.load(json_file)
                                        ieImplant['model'] = json_data['electrodes'][-1]['model']
                        fname_list = ieImplant.create_electsv_file(ct_present)

                        for elecfile in fname_list:
                            ieSidecar = util.IeegGlobalSidecars(os.path.join(PathBrain, entry, 'implantation', elecfile))
                            ieSidecar.get_attributes_from_filename()
                            sub['IeegGlobalSidecars'] = ieSidecar

                        sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                        update_subject_list(sub_tab_pres, sub_tab_index, subject_tab, sub_tab)
                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                    update_subject_list(subject_present, index_subject, subject_list, sub)

        elif dirSoft == 'FTRACT' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagProc:
            subj_imagin_list = list()
            pip_present, pip_index = check_pipeline_in_list(pip_folder_list, 'brainstorm')
            if not pip_present:
                pip_folder = util.Pipeline()
                pip_folder['name'] = 'brainstorm'
                pip_folder['DatasetDescJSON'] = util.DatasetDescJSON()
                pip_folder['DatasetDescJSON']['Name'] = pip_folder['name']
                pip_folder['DatasetDescJSON']['AnalysisType'] = 'Calculate the seizures epileptogenicity mapping'                    
            else:
                pip_folder = pip_folder_list[pip_index]
            for dirSujet in os.listdir(os.path.join(PathPreprocessed, dirSoft)):
                if dirSujet in sujets:
                    hashed_sub = hash_object(dirSujet)
                    subject_present, index_subject = check_subject_in_list(subj_imagin_list, hashed_sub)
                    sub_imagin = get_sub_attributes(subject_present, index_subject, subj_imagin_list, hashed_sub, flagprocess=True)
                    
                    '''pres_sub_raw, sub_raw_index = check_subject_in_list(subject_list, hashed_sub)
                    if pres_sub_raw:
                        for key in sub_imagin.keylist:
                            if key in clinical_list: 
                                sub_imagin[key] = subject_list[sub_raw_index][key]'''
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                    sub_tab = get_sub_attributes(sub_tab_pres, sub_tab_index, subject_tab, hashed_sub, flagtable=True)
                    Pathentry = os.path.join(PathPreprocessed, dirSoft, dirSujet, 'SEEG')
                    for entry in os.listdir(Pathentry):
                        nom, date = entry.split('_')
                        [year, month, day] = date.split('-')
                        label_date = day+month+year
                        num_ses = sub_tab.get_the_number('Session', label_date)
                        if nom.startswith('Ictal'):
                            for dirEI in os.listdir(os.path.join(Pathentry, entry, 'EI')):
                                SZ_list = ['SZGroup', 'SZGroup1', 'SZGroup2', 'SZGroup3']
                                if dirEI in SZ_list:
                                    for fileEI in os.listdir(os.path.join(Pathentry, entry, 'EI', dirEI, 'ImaGIN_epileptogenicity')):
                                        sujet_run, ext = os.path.splitext(fileEI)
                                        if sujet_run.split('_')[0] == 'EI' and ext in ext_process:
                                            name_run, param_run = sujet_run.split('__')
                                            if ext=='.txt':
                                                convert_txt_in_tsv(os.path.join(Pathentry, entry, 'EI', dirEI, 'ImaGIN_epileptogenicity', fileEI))
                                            if sujet_run.split('_')[1] == 'Group':
                                                num_run = ''
                                            else:
                                                label_run = sujet_run.split('_')[2]
                                                num_run = sub_tab.get_the_number('SeizureRun', label_run)
                                            iedict = util.create_subclass_instance('IeegProcess', util.Process)
                                            iedict['sub'] = sub_imagin['sub']
                                            iedict['ses'] = 'postimp'+str(num_ses).zfill(2)
                                            iedict['proc'] = 'EM'
                                            iedict['run'] = str(num_run).zfill(2)
                                            iedict['task'] = 'seizure'
                                            iedict['fileLoc'] = os.path.join(Pathentry, entry, 'EI', dirEI, 'ImaGIN_epileptogenicity', sujet_run+'.tsv')
                                            fmin, fmax, win, inst = param_run.split('_')
                                            ieJ = util.ProcessJSON()
                                            ieJ['Description'] = 'Epileptogenicity mapping of seizure data'
                                            ieJ['Sources'] = create_names_from_attributes(iedict, '.vhdr')
                                            ieJ['Frequency band'] = fmin + '-' + fmax + 'Hz'
                                            ieJ['Window size'] = win + 's'
                                            ieJ['Start'] = inst
                                            ieJ['Date'] = str(now)
                                            ieJ.modality_field = 'ieeg'
                                            ieJ.simplify_sidecar(required_only=False)
                                            iedict['ProcessJSON'] = ieJ
                                            
                                            sub_imagin['IeegProcess'] = iedict
                        sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub_imagin['sub'])
                        update_subject_list(sub_tab_pres, sub_tab_index, subject_tab, sub_tab)
                    subject_present, index_subject = check_subject_in_list(subj_imagin_list, sub_imagin['sub'])
                    update_subject_list(subject_present, index_subject, subj_imagin_list, sub_imagin)

            for sub_dev in subj_imagin_list:
                pip_folder['SubjectProcess'].append(sub_dev)
            pip_present, pip_index = check_pipeline_in_list(pip_folder_list, pip_folder['name'])
            if not pip_present:
                pip_folder_list.append(pip_folder)
            else:
                attr_dict = {key: pip_folder[key] for key in pip_folder.keys() if pip_folder[key]}
                pip_folder_list[pip_index].update(attr_dict)

        elif dirSoft == 'Freesurfer' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagProc:
            subj_freesurfer_list = list()
            pip_present, pip_index = check_pipeline_in_list(pip_folder_list, 'FreeSurfer')
            if not pip_present:
                pip_folder = util.Pipeline()
                pip_folder['name'] = 'freesurfer'
                pip_folder['DatasetDescJSON'] = util.DatasetDescJSON()
                pip_folder['DatasetDescJSON']['Name'] = pip_folder['name']
                pip_folder['DatasetDescJSON']['AnalysisType'] = 'Extract pial surface'                               
            else:
                pip_folder = pip_folder_list[pip_index]
            for dirSujet in os.listdir(os.path.join(PathPreprocessed, dirSoft)):
                try:
                    subject_name, date_ses = dirSujet.split('_')
                except:
                    subject_name = 'NotInSubjectList'
                if subject_name in sujets:
                    hashed_sub = hash_object(subject_name)
                    subject_present, index_subject = check_subject_in_list(subj_freesurfer_list, hashed_sub)
                    sub_freesurfer = get_sub_attributes(subject_present, index_subject, subj_freesurfer_list, hashed_sub, flagprocess=True)
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                    sub_tab = get_sub_attributes(sub_tab_pres, sub_tab_index, subject_tab, hashed_sub, flagtable=True)

                    Pathentry = os.path.join(PathPreprocessed, dirSoft, dirSujet, 'surf')
                    file_list = ['rh.pial', 'lh.pial']
                    [day, month, year] = date_ses.split('-')
                    label_date = day+month+year
                    num_ses = sub_tab.get_the_number('Session', label_date)
                    for fpial in file_list:
                        try:
                            hem, ext = os.path.splitext(fpial)
                            AnaDict = util.create_subclass_instance('AnatProcess', util.Process)
                            AnaDict['sub'] = sub_freesurfer['sub']
                            AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                            AnaDict['hemi'] = hem[0].upper()
                            AnaDict['fileLoc'] = os.path.join(Pathentry, fpial)
                            AnaDict['modality'] = 'pial'
                            AnaJ = util.ProcessJSON()
                            if hem=='rh':
                                AnaJ['Description'] = 'Pial surface of right hemisphere'
                            elif hem=='lh':
                                AnaJ['Description'] = 'Pial surface of left hemisphere'
                            AnaJ['Sources'] = create_names_from_attributes(AnaDict, '.nii')
                            AnaJ.modality_field = 'anat'
                            AnaJ.simplify_sidecar(required_only=False)
                            AnaDict['ProcessJSON'] = AnaJ

                            sub_freesurfer['AnatProcess'] = AnaDict 
                        except:
                            continue

                    subject_present, index_subject = check_subject_in_list(subj_freesurfer_list, sub_freesurfer['sub'])
                    update_subject_list(subject_present, index_subject, subj_freesurfer_list, sub_freesurfer)
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub_freesurfer['sub'])
                    update_subject_list(sub_tab_pres, sub_tab_index, subject_tab, sub_tab)

            for sub_dev in subj_freesurfer_list:
                pip_folder['SubjectProcess'].append(sub_dev)
            pip_present, pip_index = check_pipeline_in_list(pip_folder_list, pip_folder['name'])
            if not pip_present:
                pip_folder_list.append(pip_folder)
            else:
                attr_dict = {key: pip_folder[key] for key in pip_folder.keys() if pip_folder[key]}
                pip_folder_list[pip_index].update(attr_dict)
                        

        elif dirSoft == 'defaced' and os.path.isdir(os.path.join(PathPreprocessed, dirSoft)) and flagAnat:
            for dirSujet in os.listdir(os.path.join(PathPreprocessed, dirSoft)):
                if dirSujet in sujets:
                    hashed_sub = hash_object(dirSujet)
                    subject_present, index_subject = check_subject_in_list(subject_list, hashed_sub)
                    sub = get_sub_attributes(subject_present, index_subject, subject_list, hashed_sub)
                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, hashed_sub)
                    sub_tab = get_sub_attributes(sub_tab_pres, sub_tab_index, subject_tab, hashed_sub, flagtable=True)
                    for entry in os.listdir(os.path.join(PathPreprocessed, dirSoft, dirSujet)):
                        if entry.startswith('T1') and os.path.isdir(os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)):
                            Pathentry = os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)
                            for dirT1 in os.listdir(Pathentry):
                                if os.path.isdir(os.path.join(Pathentry, dirT1)) and os.listdir(os.path.join(Pathentry, dirT1)):
                                    [AnatType, date] = dirT1.split('_')
                                    [year, month, day] = date.split('-')
                                    label_date = day+month+year
                                    num_ses = sub_tab.get_the_number('Session', label_date)
                                    if AnatType == 'T1post':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T1w'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT1)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T1pre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T1w'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT1)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T1postop':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postop'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T1w'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT1)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T1gadopre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T1w'
                                        AnaDict['ce'] = 'gado'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT1)
                                        AnaJ = util.AnatJSON()
                                        AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                        AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T1gadopostop':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postop'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T1w'
                                        AnaDict['ce'] = 'gado'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT1)
                                        AnaJ = util.AnatJSON()
                                        AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                        AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)
                                        sub['Anat'] = AnaDict

                        elif entry.startswith('T2') and os.path.isdir(os.path.join(PathPreprocessed, dirSoft, dirSujet, entry)):
                            Pathentry = os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)
                            for dirT2 in os.listdir(Pathentry):
                                if os.path.isdir(os.path.join(Pathentry, dirT2)):
                                    [AnatType, date] = dirT2.split('_')
                                    [year, month, day] = date.split('-')
                                    label_date = day+month+year
                                    num_ses = sub_tab.get_the_number('Session', label_date)
                                    if AnatType == 'T2post':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T2w'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT2)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T2pre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T2w'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT2)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T2postop':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postop'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T2w'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT2)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T2gadopre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T2w'
                                        AnaDict['ce'] = 'gado'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT2)
                                        AnaJ = util.AnatJSON()
                                        AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                        AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'T2gadopostop':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postop'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'T2w'
                                        AnaDict['ce'] = 'gado'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirT2)
                                        AnaJ = util.AnatJSON()
                                        AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                        AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)
                                        sub['Anat'] = AnaDict

                        elif entry.startswith('CT') and os.path.isdir(os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)):
                            Pathentry = os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)
                            for dirCT in os.listdir(Pathentry):
                                if os.path.isdir(os.path.join(Pathentry, dirCT)):
                                    [AnatType, date] = dirCT.split('_')
                                    [year, month, day] = date.split('-')
                                    label_date = day+month+year
                                    num_ses = sub_tab.get_the_number('Session', label_date)
                                    if AnatType == 'CTpost':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'CT'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirCT)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'CTpre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'CT'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirCT)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'CTpostop':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postop'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'CT'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirCT)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'CTgadopre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'CT'
                                        AnaDict['ce'] = 'gado'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirCT)
                                        AnaJ = util.AnatJSON()
                                        AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                        AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)
                                        sub['Anat'] = AnaDict

                        elif entry.startswith('Flair') and os.path.isdir(os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)):
                            Pathentry = os.path.join(PathPreprocessed, dirSoft, dirSujet,entry)
                            for dirFl in os.listdir(Pathentry):
                                if os.path.isdir(os.path.join(Pathentry, dirFl)):
                                    [AnatType, date] = dirFl.split('_')
                                    [year, month, day] = date.split('-')
                                    label_date = day+month+year
                                    num_ses = sub_tab.get_the_number('Session', label_date)
                                    if AnatType == 'Flairpost':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'FLAIR'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirFl)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'Flairpre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'FLAIR'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirFl)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'Flairpostop':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'postop'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'FLAIR'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirFl)
                                        sub['Anat'] = AnaDict

                                    elif AnatType == 'Flairgadopre':
                                        AnaDict = util.Anat()
                                        AnaDict['sub'] = sub['sub']
                                        AnaDict['ses'] = 'preimp'+str(num_ses).zfill(2)
                                        AnaDict['modality'] = 'FLAIR'
                                        AnaDict['ce'] = 'gado'
                                        AnaDict['fileLoc'] = os.path.join(Pathentry, dirFl)
                                        AnaJ = util.AnatJSON()
                                        AnaJ['ContrastBolusIngredient'] = 'Gadolinium'
                                        AnaDict['AnatJSON'] = remove_unused_keys(AnaJ)
                                        sub['Anat'] = AnaDict

                    sub_tab_pres, sub_tab_index = check_subject_in_list(subject_tab, sub['sub'])
                    update_subject_list(sub_tab_pres, sub_tab_index, subject_tab, sub_tab)
                    subject_present, index_subject = check_subject_in_list(subject_list, sub['sub'])
                    update_subject_list(subject_present, index_subject, subject_list, sub)

    for pip in pip_folder_list:
        Dev_folder['Pipeline'].append(pip)


    for sub_elt in subject_list:
        raw_data['Subject'] = sub_elt
    raw_data['Derivatives'] = Dev_folder
    DataName = util.DatasetDescJSON()
    DataName['Name'] = 'FTract'
    DataName['Authors'] = 'Aude'
    raw_data['DatasetDescJSON'] = remove_unused_keys(DataName)
    raw_data.save_as_json(savedir=os.path.join(pathTempMIP, 'temp_bids'))
    print('The data2import has been created')


if __name__ == '__main__':
    print('Create the data2import of a given folder !!!')
    PathToImport = r'/gin/data/database'
    RequirementFile = r'/home/audeciment/Documents/requirements.json'
    centre_select = ['GRE']
    #subject_selected=['0001GRE', '0002GRE', '0003GRE', '0004GRE', '0005GRE', '0006GRE', '0010GRE', '0011GRE', '0015GRE', '0016GRE', '0026GRE', '0030GRE', '0031GRE']
    subject_selected=['0009GRE']#, '0018GRE', '0024GRE']#, 
    read_ftract_folders(PathToImport, RequirementFile, centres=centre_select, sujets=subject_selected, flagIeeg=True, flagAnat=True, flagProc=True)

