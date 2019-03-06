#!/usr/bin/python3
# -*-coding:Utf-8 -*

"""
   This module was written by Aude Jegou <aude.jegou@univ-amu.fr>.   
   This module contains GUI to import subjects from F-Tract database in Bids format.
   v0.1 March 2019
"""

import ins_bids_class as bids
import os
from importlib import reload
import UploadFtract as upload
from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
import Pmw

reload(bids)
reload(upload)

def center(win):
    """
        Center the windows
    """
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

class BidsImportation(Frame):
    # Initiate the filename and path
    PathUploads = '/gin/data/database/01-uploads'
    PathBidsDir = '/gin/data/database/07-bids'
    PathImportData = '/gin/data/database'
    ConverterImageryFile = 'dcm2niix'
    ConverterElectrophyFile = 'anywave'
    RequirementsFile = '/home/audeciment/Documents/requirements.json'
    ProtocolName = 'FTract'
    version = '0.1'

    def __init__(self):
        super().__init__()
        self.subject_selected = []
        self.subjects_list = []
        self.centre_select = []
        self.label_ieeg = True
        self.label_anat = True
        self.label_process = True

        #Menu to set the different file
        menubar = Menu(root)
        menufichier = Menu(menubar, tearoff=0)
        menufichier.add_command(label='Set Bids Directory', command=lambda: self.open_file(file_type='BidsDirectory'))
        menufichier.add_command(label='Set Dataset Directory', command=lambda: self.open_file(file_type='DatasetDirectory'))
        menufichier.add_command(label='Set Converter', command=lambda: self.open_file(file_type='Converter'))
        menufichier.add_command(label='Set Requirements file', command=lambda: self.open_file(file_type='Requirements'))
        menubar.add_cascade(label='Files', menu=menufichier)
        menuaide = Menu(menubar, tearoff=0)
        menuaide.add_command(label="About", command=self.About)
        menubar.add_cascade(label="Help", menu=menuaide)
        root.config(menu=menubar)

        root.title('Ftract2Bids v' + self.version)
        self.center_choices = Variable(root, ('GRE', 'LYO', 'MIL', 'MAR', 'FRE'))
        self.select_center = Listbox(root, listvariable=self.center_choices, selectmode=MULTIPLE)
        self.select_center.pack(side=LEFT)

        # print(select_center.curselection())
        self.Okbutton = Button(root, text='OK', command=self.selected_center)
        self.Okbutton.pack(side=LEFT, padx=5, pady=5)

        self.select_subjects = Pmw.ScrolledListBox(root, items=self.subjects_list,
                                              vscrollmode='static', listbox_selectmod=EXTENDED)
        self.select_subjects.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=5)

        self.chosen = Pmw.ScrolledText(root, text_height=6, text_width=20)
        self.copyButton = Button(root, text=">>>", command=self.add_subjects)
        self.copyButton.pack(side=LEFT, padx=5, pady=5)

        self.chosen.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=5)

        self.TransferButton = Button(root, text='Import Subjects', command=self.Import_bids_data)
        self.TransferButton.pack(side=RIGHT, padx=5, pady=5)
    #Utiliser Listbox pour faire apparaître la sélection
    #Une fois les centre choisies, afficher les sujets
    #Garder quand mm la selection des centres à côté au cas où il voudrait modifier

    def open_file(self, file_type=None):
        """
            Select paths for different requirements
        """
        if file_type=='BidsDirectory':
            bids_dir = tkinter.filedialog.askdirectory(title='Select a Bids Directory', initialdir=self.PathBidsDir)
            if not bids_dir:
                return
            else:
                self.PathBidsDir = bids_dir
        elif file_type=='DatasetDirectory':
            data_dir = tkinter.filedialog.askdirectory(title='Select a Dataset Directory', initialdir=self.PathImportData)
            if not data_dir:
                return
            else:
                self.PathImportData = data_dir
        elif file_type=='Converter':
            img_file = tkinter.filedialog.askopenfilename(title='Select converter for imagery data type (dcm2niix)', initialdir=self.PathImportData)
            self.ConverterImageryFile = img_file
            elec_file = tkinter.filedialog.askopenfilename(title='Select converter for electrophy. data type (AnyWave)', initialdir=self.PathImportData)
            self.ConverterElectrophyFile = elec_file
        elif file_type=='Requirements':
            req_file = tkinter.filedialog.askopenfilename(title='Select a requirements file', filetypes=[('req.', "*.json")], initialdir=self.PathImportData)
            self.RequirementsFile = req_file
        elif not file_type:
            return

    def About(self):
        tkinter.messagebox.showinfo('About', 'GUI to select the subjects to import in your Bids Directory.\n In Files, you can select the Bids Directory and Dataset to import.\n If there is no selection, Bids directory and Dataset directory are set by default.' )

    def selected_center(self):
        self.centre_select =[]
        for index in self.select_center.curselection():
            self.centre_select.append(self.select_center.get(index))
        self.read_sujets()
        self.select_subjects.setlist(self.subjects_list)

    def read_sujets(self):
        """
            Create the subjects list according to selected center.
        """
        self.subjects_list = []
        for site in self.centre_select:
            ftract_center = 'ftract-' + site.lower()
            pathsubject = os.path.join(self.PathUploads, ftract_center, 'uploads')
            for entry in os.listdir(pathsubject):
                if os.path.isdir(os.path.join(pathsubject, entry)):
                    self.subjects_list.append(entry)
        self.subjects_list = tuple(self.subjects_list)

    def add_subjects(self):
        self.chosen.clear()
        #subject_list = listbox.get()
        for index in self.select_subjects.curselection():
            self.chosen.insert(END, self.select_subjects.get(index) + "\n")
            self.subject_selected.append(self.select_subjects.get(index))


    def Import_bids_data(self):

        root.destroy()
        mafenetre = Tk()
        #mafenetre.geometry('500x500')
        mafenetre.title('Select data type to import')
        ieeg_var = BooleanVar(mafenetre, '1')
        anat_var = BooleanVar(mafenetre, '1')
        proc_var = BooleanVar(mafenetre, '1')
        checkbox_ieeg = Checkbutton(mafenetre, text='Ieeg data', variable=ieeg_var)
        checkbox_anat = Checkbutton(mafenetre, text='Anat data', variable=anat_var)
        checkbox_process = Checkbutton(mafenetre, text='Processed data', variable=proc_var)

        #Place the checkbox on the window
        checkbox_ieeg.pack(side=LEFT, padx=5, pady=5)
        checkbox_anat.pack(side=LEFT, padx=5, pady=5)
        checkbox_process.pack(side=LEFT, padx=5, pady=5)
        BouttonOk = Button(mafenetre, text='OK', command=mafenetre.destroy)
        BouttonOk.pack(side=LEFT, padx=5, pady=5)
        center(mafenetre)
        mafenetre.mainloop()
        #print(ieeg_var.get(), anat_var.get(), proc_var.get())
        print('Everything has been set, we are ready to import the data')
        with os.scandir(os.path.join(self.PathImportData, 'temp_bids')) as it:
            for entry in it:
                if entry.name == 'data2import.json':
                    os.remove(entry)
        upload.read_ftract_folders(self.PathImportData, self.RequirementsFile, centres=self.centre_select, sujets=self.subject_selected, flagIeeg=ieeg_var.get(), flagAnat=anat_var.get(), flagProc=proc_var.get())

        os.makedirs(self.PathBidsDir, exist_ok=True)

        #Indicate the bids dir
        if os.path.isdir(self.PathBidsDir):
            req_dict = bids.Requirements(self.RequirementsFile)

            bids.BidsDataset.converters['Imagery']['path'] = self.ConverterImageryFile
            req_dict['Converters']['Imagery']['path'] = self.ConverterImageryFile
            bids.BidsDataset.converters['Electrophy']['path'] = self.ConverterElectrophyFile
            req_dict['Converters']['Electrophy']['path'] = self.ConverterElectrophyFile

            bids.BidsDataset.dirname = self.PathBidsDir
            req_dict.save_as_json(os.path.join(bids.BidsDataset.dirname, 'code', 'requirements.json'))

            datasetDes = bids.DatasetDescJSON()
            datasetDes['Name'] = self.ProtocolName
            datasetDes.write_file()

            curr_bids = bids.BidsDataset(self.PathBidsDir)

        #Import the data in the current bids directory
        curr_data2import = bids.Data2Import(self.PathImportData, os.path.join(bids.BidsDataset.dirname, 'code', 'requirements.json'))

        curr_bids.make_upload_issues(curr_data2import, force_verif=True)
        curr_bids.import_data(data2import=curr_data2import, keep_sourcedata=False, keep_file_trace=False)

        with os.scandir(os.path.join(self.PathImportData, 'temp_bids')) as it:
            for entry in it:
                if entry.name.startswith('sub') and entry.is_file():
                    os.remove(entry)

if __name__ == '__main__':
    root = Tk()
    my_gui = BidsImportation()
    center(root)
    root.mainloop()
