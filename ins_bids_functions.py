from numpy import random as rnd
import os
import datetime as dtm
import ins_bids_class as util
import json


def createalias(numsyl=3):

    alias = ''

    consonnes = 'zrtpdfklmvbn'
    consonnes = consonnes.upper()
    num_cons = len(consonnes)
    voyelles = "aeiou"
    voyelles = voyelles.upper()
    num_voy = len(voyelles)
    order = rnd.randint(0, 2)

    for syl in range(0, numsyl):
        if order == 1:
            alias = alias + consonnes[rnd.randint(0, num_cons)]
            alias = alias + voyelles[rnd.randint(0, num_voy)]
        else:
            alias = alias + voyelles[rnd.randint(0, num_voy)]
            alias = alias + consonnes[rnd.randint(0, num_cons)]
    alias = alias + dtm.datetime.now().strftime('%y')
    return alias


def create_tsv(rootdir, filename, header=None):
    file = open(os.path.join(rootdir, filename), 'w')
    if header:
        for idx_word in range(0, len(header)):
            if idx_word != len(header) - 1:
                file.write(header[idx_word] + '\t')
            else:
                file.write(header[idx_word] + '\n')
    file.close()


def check_participant_table(rootfolder, header):
    patient_list = []
    bln = os.path.isfile(os.path.join(rootfolder, 'participants.tsv'))
    if bln:
        patient_list = read_participant_table(rootfolder)
    else:
        create_participant_table(rootfolder, header)

    return patient_list


def create_participant_table(rootdir, head):

    create_tsv(rootdir, 'participants.tsv', header=head)


def read_participant_table(rootdir):
    with open(os.path.join(rootdir, 'participants.tsv'), 'r') as file:
        file.readline()
        patlist = []
        for l in file:
            ln = l.strip().split("\t")
            pat = util.SubjectInfo()
            pat['sub'] = ln[0]
            pat['alias'] = ln[3]
            patlist.append(pat)
    file.close()
    return patlist


def update_participant_table(rootdir, input_list, curr_listpat):
    bidsdefaultnan = 'n/a'
    file = open(os.path.join(rootdir, 'participants.tsv'), 'a')
    n_patients = len(input_list)
    curr_alias = []
    if not curr_listpat:
        pat_idx = range(0, n_patients)
    else:
        curr_id = []

        pat_idx = []
        for pat in curr_listpat:
            curr_id.append(pat['sub'])
            curr_alias.append(pat['alias'])
        for idx_pat in range(0, n_patients):
            if input_list[idx_pat]['sub'] not in curr_id:
                pat_idx.append(idx_pat)

    for idx_pat in pat_idx:
        file.write(input_list[idx_pat]['sub'] + '\t')
        if not input_list[idx_pat]['sex']:
            file.write(bidsdefaultnan + '\t')
        else:
            file.write(input_list[idx_pat]['sex'] + '\t')
        if not input_list[idx_pat]['date_of_birth']:
            file.write(bidsdefaultnan + '\t')
        else:
            file.write(input_list[idx_pat]['date_of_birth'] + '\t')
        # assign an unique alias to the patient
        input_list[idx_pat]['alias'] = createalias()

        while input_list[idx_pat]['alias'] in curr_alias:
            input_list[idx_pat]['alias'] = createalias()

        file.write(input_list[idx_pat]['alias'] + '\t')
        file.write(input_list[idx_pat]['uploadDate'] + '\t')
        duedate = dtm.datetime.strptime(input_list[idx_pat]['uploadDate'],
                                        '%d-%m-%Y_%Hh%M') + dtm.timedelta(weeks=4)
        duedate = duedate.strftime('%d-%m-%Y_%Hh%M')
        file.write(duedate + '\t')  # due date
        file.write(bidsdefaultnan + '\t')
        file.write(bidsdefaultnan + '\t')
        file.write(bidsdefaultnan + '\t')
        file.write(bidsdefaultnan + '\n')
    file.close()


def handle_participant_table(rootbidsfolder, input_list):

    headerlist = ['participant_id', 'date_of_birth', 'sex', 'alias', '1st_upload_date', 'due_date',
                  'report_date', 'EI_done', 'Gardel_done', 'Delphos_done']

    curr_listpat = check_participant_table(rootbidsfolder, headerlist)
    update_participant_table(rootbidsfolder, input_list, curr_listpat)


def parse_bids_dir(bidsdir, bids_dataset=None, pipeline_list=None, pipeline_label=None):

    if not bids_dataset:
        bids_dataset = util.BidsDataset()

    if pipeline_label:
        bids_dataset['name'] = pipeline_label

    with os.scandir(bidsdir) as it:
        for entry in it:
            if entry.name.startswith('sub-') and entry.is_dir():
                sub = util.SubjectInfo()
                sub['sub'] = entry.name.replace('sub-', '')
                sub = parse_sub_bids_dir(entry.path, sub)
                bids_dataset['Subject'] = sub
            elif entry.name == 'source data' and entry.is_dir():
                bids_dataset['SourceData'] = parse_bids_dir(entry.path, bids_dataset=util.SourceDataInfo())
            elif entry.name == 'derivatives' and entry.is_dir():
                bids_dataset['Derivatives'] = parse_bids_dir(entry.path, bids_dataset=util.DerivativesInfo(),
                                                             pipeline_list=pipeline_list)
            elif pipeline_list and entry.name in pipeline_list and entry.is_dir():
                bids_dataset['Pipeline'] = parse_bids_dir(entry.path, bids_dataset=util.PipelineInfo(),
                                                          pipeline_label=entry.name)

    return bids_dataset


def parse_sub_bids_dir(sub_bidsdir, subinfo, num_ses=None, mod_dir=None):

    with os.scandir(sub_bidsdir) as it:
        for entry in it:
            if not num_ses and entry.name.startswith('ses-') and entry.is_dir():
                num_ses = entry.name.replace('ses-', '')
                subinfo = parse_sub_bids_dir(entry.path, subinfo, num_ses=num_ses)
            elif not mod_dir and entry.name.title() in subinfo.keyList[7:] and entry.is_dir():
                subinfo = parse_sub_bids_dir(entry.path, subinfo, num_ses=num_ses, mod_dir=entry.name.title())
            elif mod_dir and entry.is_file():  # handles file extension! add them to an object?!
                print(os.path.splitext(entry.name))
                # subinfo[mod_dir] = eval('util.' + mod_dir + 'Info()')
    return subinfo

#
# bids = parse_bids_dir('D:/roehri/PHRC/test/PHRC', pipeline_list=['Epitools'])
#
# now = dtm.datetime.now()
# with open(os.path.join('D:/roehri/PHRC/test/PHRC', 'parsing_test_' + now.strftime("%d%m%Y_%Hh%M") + '.json'), 'w') as f:
#     json.dump(bids, f, indent=2, separators=(',', ': '), ensure_ascii=False)
# # parse_bis_dir('D:/roehri/PHRC/test/PHRC')

# Seems to be an handy functions to create
# os.makedirs('D:/roehri/PHRC/test/PHRC/sub-c2429a5cfd4a/ses-01/anat', exist_ok=True)
