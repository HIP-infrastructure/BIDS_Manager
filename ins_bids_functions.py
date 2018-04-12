from numpy import random as rnd
import os
import datetime as dtm


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


def handle_participant_table(rootbidsfolder, input_list):

    def check_participant_table(rootfolder, header):
        patient_list = []
        bln = os.path.isfile(os.path.join(rootfolder, 'participants.tsv'))
        if bln:
            patient_list = read_participant_table(rootfolder)
        else:
            create_participant_table(rootfolder, header)
        return patient_list

    def create_participant_table(rootdir, head):
        file = open(os.path.join(rootdir, 'participants.tsv'), 'w')
        for idx_word in range(0, len(head)):
            if idx_word != len(head)-1:
                file.write(head[idx_word] + '\t')
            else:
                file.write(head[idx_word] + '\n')
        file.close()

    def update_participant_table(rootdir, header, input_list, curr_listpat):
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
                curr_id.append(pat['patID'])
                curr_alias.append(pat['alias'])
            for idx_pat in range(0, n_patients):
                if input_list[idx_pat]['patID'] not in curr_id:
                    pat_idx.append(idx_pat)

        for idx_pat in pat_idx:
            file.write(input_list[idx_pat]['patID'] + '\t')
            if not input_list[idx_pat]['sex']:
                file.write(bidsdefaultnan + '\t')
            else:
                file.write(input_list[idx_pat]['sex'] + '\t')
            if not input_list[idx_pat]['age']:
                file.write(bidsdefaultnan + '\t')
            else:
                file.write(input_list[idx_pat]['age'] + '\t')
            # assign an unique alias to the patient
            input_list[idx_pat]['alias'] = createalias()

            while input_list[idx_pat]['alias'] in curr_alias:
                input_list[idx_pat]['alias'] = createalias()

            file.write(input_list[idx_pat]['alias'] + '\t')
            file.write(input_list[idx_pat]['uploadDate'] + '\t')
            duedate = dtm.datetime.strptime(input_list[idx_pat]['uploadDate'], '%d-%m-%Y_%Hh%M')\
                      + dtm.timedelta(weeks=2)
            duedate = duedate.strftime('%d-%m-%Y_%Hh%M')
            file.write(duedate + '\t')  # due date
            file.write(bidsdefaultnan + '\t')
            file.write(bidsdefaultnan + '\t')
            file.write(bidsdefaultnan + '\t')
            file.write(bidsdefaultnan + '\n')
        file.close()

    def read_participant_table(rootdir):
        with open(os.path.join(rootdir, 'participants.tsv'), 'r') as file:
            file.readline()
            patlist = []
            for l in file:
                ln = l.strip().split("\t")
                pat = PatientInfo()
                pat['patID'] = ln[0]
                pat['alias'] = ln[3]
                patlist.append(pat)
        return patlist

    headerlist = ['participant_id', 'age', 'sex', 'alias', '1st_upload_date', 'due_date', 'report_date', 'EI_done',
                  'Gardel_done', 'Delphos_done']

    curr_listpat = check_participant_table(rootbidsfolder, headerlist)
    update_participant_table(rootbidsfolder, headerlist, input_list, curr_listpat)

