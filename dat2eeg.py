#!/usr/bin/python3
# -*-coding:Utf-8 -*

"""
   Script to turn the extension .dat in .eeg to fit the brainVision Core file format.
   Written by Aude Jegou March 2019.
"""

import os

Bidspath = '/gin/data/database/07-bids'
modality = ['ieeg', 'eeg']

for subject in os.listdir(Bidspath):
    if subject.startswith('sub') and os.path.isdir(os.path.join(Bidspath, subject)):
        for session in os.listdir(os.path.join(Bidspath, subject)):
            if os.path.isdir(os.path.join(Bidspath, subject, session)):
                for mod in os.listdir(os.path.join(Bidspath, subject, session)):
                    if mod in modality and os.path.isdir(os.path.join(Bidspath, subject, session, mod)):
                        with os.scandir(os.path.join(Bidspath, subject, session, mod)) as it:
                            for entry in it:
                                name, ext = os.path.splitext(entry.path)
                                header_ext = ['.vhdr', '.vmrk']
                                if ext == '.dat':
                                    os.rename(entry.path, name + '.eeg')
                                    #print(entry.name + ' has been renamed')
                                    for ext in header_ext:
                                        f = open(name + ext, 'r+')
                                        f_cont = f.readlines()
                                        try:
                                            idx = [f_cont.index(elt) for elt in f_cont if '.dat' in elt]
                                            ind= idx[0]
                                            f_cont[ind] = f_cont[ind].replace('.dat', '.eeg')
                                            f.seek(0)
                                            f.truncate()
                                            f.write(''.join(f_cont))
                                            print(entry.name + ' has been modified')
                                        except:
                                            print('There is no .dat in this file '+entry.name)
                                        f.close()

