#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Pipeline select and analyse data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Pipeline. This file manages the exportation of BIDS data.
#
#     BIDS Pipeline is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     any later version
#
#     BIDS Pipeline is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with BIDS Pipeline.  If not, see <https://www.gnu.org/licenses/>
#
#     Authors: Aude Jegou, 2019-2021

import bids_manager.ins_bids_class as bids
# from .pipeline_class import DatasetDescPipeline
from .interface_class import Interface
from generic_uploader import deltamed, micromed, anonymize_edf, anonymizeDicom
from tkinter import messagebox
import hashlib
import os
import shutil

__param__ = ['import_in_bids', 'output_directory', 'select_session', 'select_modality', 'anonymise', 'derivatives']


def export_data(bids_data, output_select):
    log = ''
    anonymize = False
    #initiate the parameter value
    if isinstance(bids_data, str):
        bids_data = bids.BidsDataset(bids_data)
    #Get the value from user
    param = output_select['0_exp']['analysis_param']
    sub_selected = output_select['0_exp']['subject_selected']
    if 'output_directory' not in param:
        raise EOFError('The output directory is missing.')
    if 'anonymise' not in param:
        log += 'The anonymise key was not provided so by default the data won"t be anonymised'
        param['anonymise'] = None
    if 'import_in_bids' not in param:
        param['import_in_bids'] = False
    if 'sourcedata' not in param:
        param['sourcedata'] = None
    if 'derivatives' not in param:
        param['derivatives'] = 'None'
    #Errors if merge and the dataset selected is not Bids or if the session name are different
    if param['import_in_bids']:
        try:
            new_bids_data = bids.BidsDataset(param['output_directory'])
            ses = [elt['ses'] for sub in new_bids_data['Subject'] for mod in
                   bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if mod for elt
                   in sub[mod]]
            ses = list(set(ses))
            if 'all' in param['select_session']:
                ses_old = [elt['ses'] for sub in bids_data['Subject'] for mod in
                   bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if mod for elt
                   in sub[mod]]
                ses_old = list(set(ses_old))
            else:
                ses_old = param['select_session']
            if not all(so in ses for so in ses_old):
                raise EOFError('The BIDS dataset cannot be merged because the session names are different.')
        except:
            raise EOFError('The output directory is not BIDS dataset so it is not possible to merge data.')
    #Check if anonymisation is required
    if param['anonymise'] == 'pseudo-anonymisation' or param['anonymise'] == 'full-anonymisation':
        anonymize = True
        full = False
        if not param['import_in_bids']:
            secret_key = None
            other_part = None
        else:
            dataset = bids.DatasetDescJSON()
            dataset.read_file(os.path.join(param['output_directory'], dataset.filename))
            secret_key = dataset['Name']
            other_part = bids.ParticipantsTSV(header=['participant_id'], required_fields=['participant_id'])
            other_part.read_file(os.path.join(param['output_directory'], other_part.filename))
        if param['anonymise'] == 'full-anonymisation':
            full = True
        sub_anonymize, new_partTSV = anonymize_data(sub_selected, bids_data['ParticipantsTSV'], secret_key=secret_key, otherpart=other_part, full=full)
        if not sub_anonymize and not new_partTSV:
            return
    else:
        header = [elt for elt in bids_data['ParticipantsTSV'].header if not elt.endswith('_ready') and not elt.endswith('_integrity')]
        new_partTSV = bids.ParticipantsTSV(header=header, required_fields=['participant_id'])
        for sub in sub_selected:
            idx_part = [cnt for cnt, line in enumerate(bids_data['ParticipantsTSV']) if line[0].replace('sub-', '') == sub]
            tmp_dict = {elt: bids_data['ParticipantsTSV'][idx_part[0]][bids_data['ParticipantsTSV'][0].index(elt)] for elt in bids_data['ParticipantsTSV'].header}
            new_partTSV.append(tmp_dict)
    tmp_directory = os.path.join(bids_data.dirname, 'derivatives', 'bids_pipeline', 'tmp_directory')
    os.makedirs(tmp_directory, exist_ok=True)

    for sub in bids_data['Subject']:
        if sub['sub'] in sub_selected:
            new_name = sub['sub']
            if anonymize:
                new_name = sub_anonymize[sub['sub']]
            for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
                if ('all' in param['select_modality'] or mod in param['select_modality'] or mod.replace('GlobalSidecars', '') in param['select_modality']) and sub[mod]:
                    get_files(sub[mod], param['select_session'], param['output_directory'], sub['sub'], new_name, bids_data.dirname, sdcar=True)
                elif mod == 'Scans' and mod:
                    for elt in sub[mod]:
                        new_scans = bids.Scans()
                        new_scans['sub'] = new_name
                        new_scans['ses'] = elt['ses']
                        path, filename, ext = elt['fileLoc']
                        path = path.replace(sub['sub'], new_name)
                        filename = filename.replace(sub['sub'], new_name)
                        new_scans['fileLoc'] = os.path.join(param['output_directory'], path, filename+ext)
                        for line in elt['ScansTSV'][1:]:
                            tmp_dict = {}
                            tmp_dict['filename'] = line[0].replace(sub['sub'], new_name)
                            tmp_dict['acq_time'] = line[1]
                            new_scans['ScansTSV'].append(tmp_dict)
                        new_scans.write_file()
    if param['sourcedata']:
        for sub in bids_data['SourceData'][0]['Subject']:
            if sub['sub'] in sub_selected:
                new_name = sub['sub']
                if anonymize:
                    new_name = sub_anonymize[sub['sub']]
                for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
                    if ('all' in param['select_modality'] or mod in param['select_modality'] or mod.replace(
                            'GlobalSidecars', '') in param['select_modality']) and sub[mod]:
                        get_files(sub[mod], param['select_session'], tmp_directory, sub['sub'], new_name, bids_data.dirname,
                                  sdcar=True, anonymize=anonymize, in_src=True)
        os.makedirs(os.path.join(param['output_directory'], 'sourcedata'), exist_ok=True)
        for dir in os.listdir(os.path.join(tmp_directory, 'sourcedata')):
            shutil.move(os.path.join(tmp_directory, 'sourcedata', dir), os.path.join(param['output_directory'], 'sourcedata'))
        new_srctrck = bids.SrcDataTrack()
        srctrack_file = os.path.join(param['output_directory'], 'sourcedata', bids.SrcDataTrack.filename)
        if param['import_in_bids'] and os.path.exists(srctrack_file):
            new_srctrck.read_file(tsv_full_filename=srctrack_file)
        for line in bids_data['SourceData'][0]['SrcDataTrack'][1::]:
            file_split = line[1].split('_')
            sub = file_split[0].replace('sub-', '')
            if sub in sub_selected:
                tmp_dict = {}
                tmp_dict['orig_filename'] = line[0]
                if anonymize:
                    tmp_dict['bids_filename'] = line[1].replace(sub, sub_anonymize[sub])
                else:
                    tmp_dict['bids_filename'] = line[1]
                tmp_dict['upload_date'] = line[2]
                new_srctrck.append(tmp_dict)
        new_srctrck.write_file(tsv_full_filename=srctrack_file)

    if param['derivatives'] != 'None':
        for dev in bids_data['Derivatives'][0]['Pipeline']:
            if 'all' in param['derivatives'] or dev['name'] in param['derivatives'] and dev['name'] not in ['log', 'parsing', 'log_old', 'parsing_old']:
                for sub in dev['SubjectProcess']:
                    if sub['sub'] in sub_selected:
                        new_name = sub['sub']
                        if anonymize:
                            new_name = sub_anonymize[sub['sub']]
                        for mod in bids.ImagingProcess.get_list_subclasses_names() + bids.ElectrophyProcess.get_list_subclasses_names():
                            if ('all' in param['select_modality'] or mod.replace('Process', '') in param['select_modality']) and sub[mod]:
                                get_files(sub[mod], param['select_session'], param['output_directory'], sub['sub'], new_name, bids_data.dirname,
                                          sdcar=True)
                new_datsetdesc = bids.DatasetDescPipeline()
                for key in dev['DatasetDescJSON']:
                    if isinstance(dev['DatasetDescJSON'][key], bids.BidsBrick):
                        new_datsetdesc[key].copy_values(dev['DatasetDescJSON'][key])
                    else:
                        new_datsetdesc[key] = dev['DatasetDescJSON'][key]
                if 'SourceDataset' in dev['DatasetDescJSON']:
                    if anonymize:
                        new_datsetdesc['SourceDataset'] = [sub_anonymize[elt] for elt in dev['DatasetDescJSON']['SourceDataset'] if elt in sub_selected]
                    else:
                        new_datsetdesc['SourceDataset'] = [elt for elt in
                                                           dev['DatasetDescJSON']['SourceDataset'] if elt in sub_selected]
                new_datsetdesc.write_file(os.path.join(param['output_directory'], 'derivatives', dev['name'], new_datsetdesc.filename))

    new_partTSV.write_file(tsv_full_filename=os.path.join(param['output_directory'], bids.ParticipantsTSV.filename))
    if param['import_in_bids']:
        new_bids_data._assign_bids_dir(new_bids_data.dirname)
        new_bids_data.parse_bids()
        bids_data._assign_bids_dir(bids_data.dirname)


def get_files(mod_list, ses_list,  output_dir, sub_id, new_name, bidsdirname, sdcar=True, anonymize=False, in_src=False):
    for elt in mod_list:
        if (elt['ses'] in ses_list or 'all' in ses_list) or (in_src and not elt['ses']):
            path = os.path.dirname(elt['fileLoc'])
            file = os.path.basename(elt['fileLoc'])
            filename, ext = os.path.splitext(file)
            sub_dir = os.path.join(output_dir, path)
            new_filename = filename.replace(sub_id, new_name)
            sub_dir = sub_dir.replace(sub_id, new_name)
            os.makedirs(sub_dir, exist_ok=True)
            if ext == '.vhdr':
                extension = ['.vhdr', '.vmrk', '.eeg']
            else:
                extension = [ext]
            for ex in extension:
                out_file = os.path.join(sub_dir, new_filename + ex)
                shutil.copy2(os.path.join(bidsdirname, path, filename + ex),
                             out_file)
            if sdcar:
                sidecar = elt.get_modality_sidecars()
                for sidecar_key in sidecar:
                    if elt[sidecar_key]:
                        if elt[sidecar_key].modality_field:
                            sdcar_fname = filename.replace(elt['modality'],
                                                           elt[sidecar_key].modality_field)
                        else:
                            sdcar_fname = filename
                        new_sdcar_fname = sdcar_fname.replace(sub_id, new_name)
                        if os.path.exists(os.path.join(bidsdirname, path, sdcar_fname + elt[sidecar_key].extension)):
                            shutil.copy2(os.path.join(bidsdirname, path, sdcar_fname + elt[sidecar_key].extension),
                                         os.path.join(sub_dir, new_sdcar_fname + elt[sidecar_key].extension))
            if anonymize:
                if ext == ".trc":
                    micromed.anonymize_micromed(out_file)
                elif ext == ".eeg":
                    deltamed.anonymize_deltamed(out_file)
                elif ext == ".edf":
                    anonymize_edf.anonymize_edf(out_file)
                elif ext == '' and elt.classname() in bids.Imaging.get_list_subclasses_names():
                    anonymizeDicom.anonymize(out_file, out_file, new_name, new_name, True, False)


def anonymize_data(sub_selected, part_list, secret_key=None, otherpart=None, full=False):
    anonym_dict = {}
    if not full:
        header = [elt for elt in part_list.header if not elt.endswith('_ready') and not elt.endswith('_integrity')]
    elif full and otherpart is not None:
        yesno = messagebox.askyesno(title='Warning', message='Full-anonymisation is not possible with merging option.\n A pseudo-anonymisation will be done.\n Do you want to continue?')
        if yesno:
            header = [elt for elt in otherpart.header if not elt.endswith('_ready') and not elt.endswith('_integrity')]
        else:
            return {}, {}
    else:
        header = ['participant_id']
    if otherpart is None:
        otherpart = bids.ParticipantsTSV(header=header)
    if secret_key is None:
        secret_key = 'exportation'
    for sub in sub_selected:
        idx_part = [cnt for cnt, line in enumerate(part_list[1::]) if line[0].replace('sub-', '') == sub]
        new_id = hash_object(sub+secret_key)
        anonym_dict[sub] = new_id
        tmp_dict = {elt: part_list[idx_part[0]][part_list[0].index(elt)] for elt in header if elt in part_list[0]}
        tmp_dict['participant_id'] = 'sub-' + new_id
        otherpart.append(tmp_dict)
    return anonym_dict, otherpart


def hash_object(obj):
    clef256 = hashlib.sha256(obj.encode())
    clef_digest = clef256.hexdigest()
    clef = clef_digest[0:12]
    return clef


class ParametersInterface(Interface):
    def __init__(self, bids_data):
        self.bids_data = bids_data
        self.subject = [sub['sub'] for sub in self.bids_data['Subject']]
        self.dev = [dev['name'] for dev in bids_data['Derivatives'][0]['Pipeline']]
        ses = [elt['ses'] for sub in self.bids_data['Subject'] for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if mod for elt in sub[mod]]
        ses = list(set(ses))
        mod = [mod for sub in self.bids_data['Subject'] for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if sub[mod]]
        mod = list(set(mod))
        self.ses = ses + ['all']
        self.mod = mod +['all']
        self.vars_interface()

    def vars_interface(self):
        # self['algorithm'] = {}
        # self['algorithm']['attribut'] = 'Listbox'
        # self['algporithm']['value'] = ['Export', 'Merge', 'Anonymise']
        self['import_in_bids'] = {}
        self['import_in_bids']['attribut'] = 'Bool'
        self['import_in_bids']['value'] = False
        self['output_directory'] = {}
        self['output_directory']['attribut'] = 'File'
        self['output_directory']['value'] = ['dir']
        self['select_session'] = {}
        self['select_session']['attribut'] = 'Variable'
        self['select_session']['value'] = self.ses
        self['select_modality'] = {}
        self['select_modality']['attribut'] = 'Variable'
        self['select_modality']['value'] = self.mod
        self['anonymise'] = {}
        self['anonymise']['attribut'] = 'Listbox'
        self['anonymise']['value'] = ['full-anonymisation', 'pseudo-anonymisation', 'None']
        self['derivatives'] = {}
        self['derivatives']['attribut'] = 'Variable'
        self['derivatives']['value'] = self.dev + ['None', 'all']
        self['sourcedata'] = {}
        self['sourcedata']['attribut'] = 'Bool'
        self['sourcedata']['value'] = False
