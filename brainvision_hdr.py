import os
import re


class BrainvisionHeader(object):

    hdr_ext = '.vhdr'
    data_tag = '[Channel Infos]'
    expr = r'Ch\d{1,3}=(?P<label>.*?)(?P<num>\d{0,3}),'
    expr2besub = [r'Ch\d{1,3}=(?P<label>', r')(?P<num>\d{0,3}),']
    expr2sub = r''

    def __init__(self, filename=None):
        self.header = []
        self.channel_list = []
        self.electrode_list = []
        self.electrode_set = {}
        self.data_section = []
        self.filename = filename
        if self.filename:
            self.read_header(self.filename)

    def read_header(self, filename):
        if os.path.isfile(filename) and os.path.splitext(filename)[1] == self.hdr_ext:
            if not self.filename == filename:
                self.filename = filename
            with open(self.filename, 'r') as file:
                for line in file:
                    self.header.append(line)
            self.fill_data_section()
        else:
            raise FileNotFoundError(filename + ' was not found.')

    def fill_data_section(self):
        data_sect_starts = self.header.index(self.data_tag + '\n') + 1
        data_sect_ends = len(self.header)
        self.data_section = self.header[data_sect_starts:data_sect_ends]
        """search for expression that starts with 'Ch', is followed by one to three digits and '=' and finishes with a 
        comma. The first group is alphanumeric and the second can be made of  three digits"""
        for line in self.data_section:
            m = re.search(self.expr, line)
            self.channel_list.append(m['label'] + m['num'])
            self.electrode_list.append(m['label'])
        self.electrode_set = set(self.electrode_list)

    def modify_header(self, orig_name, new_name):
        if orig_name not in self.electrode_set:
            raise NameError(orig_name + ' electrode is not found in ' + self.filename + '.')
        # for line in self.header:
        #     re.sub(self.expr2besub[0] + orig_name + self.expr2besub[1], r'\g<>', "abcdef")
        ' ab cdef'


if __name__ == '__main__':
    bv_path = 'D:/roehri/BIDs/2048/sub-PaiJul/ses-01/ieeg/sub-PaiJul_ses-01_task-seizure_run-01_ieeg.vhdr'
    bv_hdr = BrainvisionHeader()
    bv_hdr.read_header(bv_path)
    print(bv_hdr.electrode_set)
    bv_hdr.modify_header("TP'", 'WWW')

