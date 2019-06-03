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
import upload_ftract as upload
from tkinter import Tk, Menu, Variable, Listbox, Button, BooleanVar, Checkbutton, Frame, Label, MULTIPLE, LEFT, RIGHT, EXTENDED, YES, NO, BOTH, END, BOTTOM, TOP, GROOVE, messagebox
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

def change_seeg_in_ecg(Bidspath, sub_list):
    for subject in os.listdir(Bidspath):
        if subject.startswith('sub') and os.path.isdir(os.path.join(Bidspath, subject)):
            for session in os.listdir(os.path.join(Bidspath, subject)):
                ses, nameS = session.split('-')
                if os.path.isdir(os.path.join(Bidspath, subject, session)) and nameS.startswith('postimp'):
                    for mod in os.listdir(os.path.join(Bidspath, subject, session)):
                        if mod.startswith('ieeg') and os.path.isdir(os.path.join(Bidspath, subject, session, mod)):
                            with os.scandir(os.path.join(Bidspath, subject, session, mod)) as it:
                                for entry in it:
                                    split_name = entry.name.split('_')
                                    if split_name[-1].endswith('channels.tsv'):
                                        f = open(entry.path, 'r+')
                                        f_cont = f.readlines()
                                        idx = [f_cont.index(elt) for elt in f_cont if 'ecg' in elt]
                                        for ind in idx:
                                            f_cont[ind] = f_cont[ind].replace('SEEG', 'ECG')
                                        f.seek(0)
                                        f.truncate()
                                        f.write(''.join(f_cont))
                                        print(entry.name + ' has been modified')
                                        f.close()

class BidsImportation(Frame):
    # Initiate the filename and path
    PathUploads = '/gin/data/database/01-uploads'
    PathBidsDir = '/gin/data/database/07-bids'
    PathImportData = '/gin/data/database'
    ConverterImageryFile = 'dcm2niix'
    ConverterElectrophyFile = 'anywave'
    RequirementsFile = '/home/audeciment/Documents/requirements.json'
    ProtocolName = 'FTract'
    version = '0.2'

    def __init__(self):
        super().__init__()
        self.subject_selected = []
        self.subjects_list = []
        self.centre_select = []
        self.label_ieeg = True
        self.label_anat = True
        self.label_process = True
        #root.geometry('500x500')
        root.resizable(True, False)
        #Menu to set the different file
        menubar = Menu(root)
        menufichier = Menu(menubar, tearoff=0)
        menufichier.add_command(label='Set Bids Directory', command=lambda: self.open_file(file_type='BidsDirectory'))
        menufichier.add_command(label='Set Dataset Directory', command=lambda: self.open_file(file_type='DatasetDirectory'))
        menufichier.add_command(label='Set Converter', command=lambda: self.open_file(file_type='Converter'))
        menufichier.add_command(label='Set Requirements file', command=lambda: self.open_file(file_type='Requirements'))
        menubar.add_cascade(label='Files', menu=menufichier)
        menuaide = Menu(menubar, tearoff=0)
        menuaide.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=menuaide)
        root.config(menu=menubar)
        root.title('Ftract2Bids v' + self.version)

        frame_subject = Frame(root, relief=GROOVE, borderwidth=2)
        self.center_choices = Variable(frame_subject, ('GRE', 'LYO', 'MIL', 'MAR', 'FRE'))
        self.select_center = Listbox(frame_subject, listvariable=self.center_choices, selectmode=MULTIPLE)
        self.select_center.pack(side=LEFT)

        # print(select_center.curselection())
        self.Okbutton = Button(frame_subject, text='OK', command=self.selected_center)
        self.Okbutton.pack(side=LEFT, padx=5, pady=5)
        self.select_subjects = Pmw.ScrolledListBox(frame_subject, items=self.subjects_list,
                                              vscrollmode='static', listbox_selectmod=EXTENDED)
        self.select_subjects.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=5)
        self.chosen = Pmw.ScrolledText(frame_subject, text_height=6, text_width=20)
        self.copyButton = Button(frame_subject, text=">>>", command=self.add_subjects)
        self.copyButton.pack(side=LEFT, padx=5, pady=5)
        self.chosen.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=5)
        frame_subject.pack(side=LEFT)
        frame_data = Frame(root, relief=GROOVE, borderwidth=2)
        
        Label(frame_data, text='Select data type to import').pack(side=TOP)
        self.ieeg_var = BooleanVar(frame_data, '1')
        self.anat_var = BooleanVar(frame_data, '1')
        self.proc_var = BooleanVar(frame_data, '1')
        checkbox_ieeg = Checkbutton(frame_data, text='Ieeg data', variable=self.ieeg_var)
        checkbox_anat = Checkbutton(frame_data, text='Anat data', variable=self.anat_var)
        checkbox_process = Checkbutton(frame_data, text='Processed data', variable=self.proc_var)
        #Place the checkbox on the window
        checkbox_ieeg.pack(side=LEFT, padx=5, pady=5)
        checkbox_anat.pack(side=LEFT, padx=5, pady=5)
        checkbox_process.pack(side=LEFT, padx=5, pady=5)
        frame_data.pack(side=BOTTOM)
       
        self.TransferButton = Button(root, text='Import Subjects', command=self.import_bids_data)
        self.TransferButton.pack(side=LEFT, anchor= 'center', padx=5, pady=5)
        self.cancel = Button(root, text='Cancel', command=lambda: root.destroy())
        self.cancel.pack(side=LEFT, anchor='e')
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

    def about(self):
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


    def import_bids_data(self):
        if not self.subject_selected:
            messagebox.showerror('Error:',  'No subjects have been selected')
        elif not os.path.isdir(self.PathBidsDir):
            messagebox.showerror('Error:', 'The directory selects as Bids directory is not a directory')
        else:
            root.destroy()
            print('Everything has been set, we are ready to import the data')
            with os.scandir(os.path.join(self.PathImportData, 'temp_bids')) as it:
                for entry in it:
                    if entry.name == 'data2import.json':
                        os.remove(entry)
            sub_list = upload.read_ftract_folders(self.PathImportData, self.RequirementsFile, centres=self.centre_select, sujets=self.subject_selected, flagIeeg=self.ieeg_var.get(), flagAnat=self.anat_var.get(), flagProc=self.proc_var.get())

            os.makedirs(self.PathBidsDir, exist_ok=True)

            #Indicate the bids dir
            if not os.listdir(self.PathBidsDir):
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
            change_seeg_in_ecg(self.PathBidsDir, sub_list)
            curr_bids.parse_bids()

            with os.scandir(os.path.join(self.PathImportData, 'temp_bids')) as it:
                for entry in it:
                    if entry.name.startswith('sub') and entry.is_file():
                        os.remove(entry)

if __name__ == '__main__':
    root = Tk()
    my_gui = BidsImportation()
    center(root)
    root.mainloop()
