#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Manager collect, organise and manage data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Manager.
#
#     BIDS Manager is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     any later version
#
#     BIDS Manager is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with BIDS Manager.  If not, see <https://www.gnu.org/licenses/>
#
#     Authors: Aude Jegou, 2019-2020

import os
import shutil
from bids_manager.ins_bids_class import ModalityType, BidsDataset
from bids_manager.utils import handle_anywave_files, chmod_recursive


def handle_anywave_files(foldername, reverse=False):

    def parse_sub_dir(dirname, original_dirname=None, dirname_dest=None, reverse=False):
        with os.scandir(dirname) as it:
            for entry in it:
                [filename, ext] = os.path.splitext(entry.name)
                if entry.name.startswith('ses-') and entry.is_dir():
                    parse_sub_dir(entry.path, original_dirname=original_dirname, dirname_dest=dirname_dest, reverse=reverse)
                elif entry.name.capitalize() in ModalityType.get_list_subclasses_names() and entry.is_dir():
                    parse_sub_dir(entry.path, original_dirname=original_dirname, dirname_dest=dirname_dest, reverse=reverse)
                elif entry.is_file() and ext.lower() in BidsDataset.anywave_ext and not entry.name.endswith('_montage.mtg'):
                    if dirname_dest is None:
                        dirname_dest = BidsDataset.dirname
                    sub_dirname = os.path.dirname(entry.path)
                    sub_dirname = sub_dirname.replace(original_dirname + '\\', '')
                    dirname_dest_sub = os.path.normpath(os.path.join(dirname_dest, sub_dirname))
                    if reverse:
                        shutil.copy2(entry.path, os.path.join(dirname_dest_sub, entry.name))
                    else:
                        shutil.move(entry.path, os.path.join(dirname_dest_sub, entry.name))

    anywave_folder = os.path.join(BidsDataset.dirname, 'derivatives', 'anywave', foldername)
    if reverse:
        sublist = [sub for sub in os.listdir(BidsDataset.dirname) if sub.startswith(('sub-'))]
        with os.scandir(anywave_folder) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.name in sublist:
                    parse_sub_dir(entry.path, original_dirname=anywave_folder, reverse=True)
    else:
        with os.scandir(BidsDataset.dirname) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.is_dir():
                    parse_sub_dir(entry.path, original_dirname=BidsDataset.dirname, dirname_dest=anywave_folder)


def chmod_recursive(this_path, mode, debug=False):
    if os.getuid() == os.stat(this_path).st_uid:
        os.chmod(this_path, mode)
    elif debug:
        print(" Changing permission denied because the directory doesn't belong to the current user !")
    for root, dirs, files in os.walk(this_path):
        for this_dir in [os.path.join(root, d) for d in dirs]:
            if os.getuid() != os.stat(this_dir).st_uid:
                if debug:
                    print("{} can not change permissions of {} belonging to {}".format(os.getuid(), this_dir, os.stat(this_dir).st_uid))
                continue
            else:
                os.chmod(this_dir, mode)
                print("{} changed privileges to {}".format(this_dir, mode))
        for this_file in [os.path.join(root, f) for f in files]:
            if os.getuid() != os.stat(this_file).st_uid:
                if debug:
                    print("{} belongs to {}. So, {} can not set its permissions ".format(this_file, os.stat(this_file).st_uid, os.getuid()))
                continue
            else:
                os.chmod(this_file, mode)
                print("{} changed its privileges to {}".format(this_file, mode))


def convert_channels_in_montage_file(channelfile):
    f = open(channelfile, 'r')
    f_cont = f.readlines()
    f.close()
    for line in f_cont[1::]:
        pass