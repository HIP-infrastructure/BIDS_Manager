class ModalityInfo(dict):

    def __init__(self, keylist, keybln=None):
        """initiate a  dict var for modality info"""
        self.keyList = keylist
        if keybln:
            self.keyBln = keybln
        else:
            self.keyBln = [False] * len(self.keyList)

        for k in range(0, len(self.keyList)):
            key = self.keyList[k]
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''

    def __setitem__(self, key, value):
        if key in self.keyList:
            # print(key)
            k = self.keyList.index(key)
            if self.keyBln[k] and eval('type(value) == ' + key + 'Info'):
                self[key].append(value)
            else:
                dict.__setitem__(self, key, value)
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def __delitem__(self, key):
        if key in self.keyList:
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def pop(self, key, val=None):
        if key in self.keyList:
            v = self[key]
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''
            return v
        else:
            print('/!\ Not recognize key: ' + str(key) + ', check class keyList /!\ ')

    def popitem(self):
        v = []
        for key in self.keyList:
            v.append(self[key])
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''
        return v

    def clear(self):
        for key in self.keyList:
            print(key)
            k = self.keyList.index(key)
            if self.keyBln[k]:
                self[key] = []
            else:
                self[key] = ''


class IeegInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for ieeg info"""
        keylist = ['ses', 'task', 'acq', 'proc', 'recording', 'fileLoc', 'IeegElecLoc', 'IeegElecPic']
        keybln = [False, False, False, False, False, False, True, True]
        ModalityInfo.__init__(self, keylist=keylist, keybln=keybln)


class IeegElecLocInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for ieeg electrode localisation info"""
        keylist = ['ses', 'space', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class IeegElecPicInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for ieeg electrode pictures info"""
        keylist = ['ses', 'acq', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class AnatInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for anatanomy info"""
        keylist = ['ses', 'acq', 'ce', 'rec', 'mod', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class FuncInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for functional imagery info"""
        keylist = ['ses', 'task', 'acq', 'rec', 'echo', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class FmapInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for field map info"""
        keylist = ['ses', 'acq', 'dir', 'mod', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class DwiInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for diffusion weighted images info"""
        keylist = ['ses', 'acq', 'type', 'task', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class MEGInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for MEG info"""
        keylist = ['ses', 'task', 'acq', 'proc', 'fileLoc']
        ModalityInfo.__init__(self, keylist=keylist)


class PatientInfo(ModalityInfo):

    def __init__(self):
        """initiate a  dict var for patient info"""
        _keylist = ['patID', 'sex', 'date_of_birth', 'alias', 'uploadDate', 'protocol', 'institution', 'Anat', 'Func',
                    'Fmap', 'Dwi', 'MEG', 'Ieeg']
        _keybln = [False, False, False, False, False, False, False, True, True, True, True, True, True]
        ModalityInfo.__init__(self, keylist=_keylist, keybln=_keybln)


