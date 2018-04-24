import os

dicom_dir = 'D:/roehri/PHRC/test/test_dcm2niix/CT_Cher_Jac'
dcm2niix = 'D:/roehri/python/PycharmProjects/readFromUploader/dcm2niix.exe'
cmd_line = dcm2niix + " -b y -ba y -z  y -m y -f %3s_%f_%p_%t " + dicom_dir

os.system(cmd_line)


