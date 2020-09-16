from pyedflib import highlevel
import os
# from datetime import datetime


def anonymize_edf(file):
    filename, file_extension = os.path.splitext(file)
    # now = datetime.now()
    # startdate = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
    if file_extension == '.EDF':
        os.rename(file, filename + '.edf')
    key_to_remove = ['patientname', 'birthdate', 'gender']
    new_values_for_anon = ['', '', '']

    # header = highlevel.read_edf_header(file)
    # if header['gender'] != '':
    #     idx_gender = key_to_remove.index('gender')
    #     key_to_remove.pop(idx_gender)
    #     new_values_for_anon.pop(idx_gender)

    highlevel.anonymize_edf(filename + '.edf', new_file=filename + '.edf',
                            to_remove=['patientname', 'birthdate', 'gender'],
                            new_values=['', '', ''], verify=True)
