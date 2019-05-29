#!/usr/bin/python3

"""
    This module was written by Nicolas Roehri <nicolas.roehri@etu.uni-amu.fr>
    (with minor changes by Aude Jegou <aude.jegou@univ-amu.fr)
    This module is GUI to explore bids dataset.
    v0.1.10 March 2019
""" 
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import super
from builtins import round
from builtins import range
from builtins import dict
from builtins import str
from builtins import object
from future import standard_library
from copy import deepcopy
import ins_bids_class as bids
import pipeline_analysis as pip
import os
import platform
from tkinter import ttk, Tk, Menu, messagebox, filedialog, Frame, Listbox, scrolledtext, simpledialog, Toplevel, \
    Label, Button, Entry, StringVar, BooleanVar, IntVar, DISABLED, NORMAL, END, W, N, S, E, INSERT, BOTH, X, Y, RIGHT, LEFT,\
    TOP, BOTTOM, BROWSE, SINGLE, MULTIPLE, EXTENDED, ACTIVE, RIDGE, Scrollbar, CENTER, OptionMenu, Checkbutton, GROOVE, YES, Variable, Canvas, font
try:
    from importlib import reload
except:
    pass
standard_library.install_aliases()


class BidsManager(Frame, object):  # !!!!!!!!!! object is used to make the class Py2 compatible
    # (https://stackoverflow.com/questions/18171328/python-2-7-super-error) While it is true that Tkinter uses
    # old-style classes, this limitation can be overcome by additionally deriving the subclass Application from object
    # (using Python multiple inheritance) !!!!!!!!!
    version = '0.1.10'
    bids_startfile = r'D:\Data\Test_Ftract_Import'
    import_startfile = r'D:\Data\Test_Ftract_Import\Original_deriv'
    folder_software = r'D:\ProjectPython\SoftwarePipeline'

    def __init__(self):
        super().__init__()
        self.master.title("BidsManager " + BidsManager.version)
        self.master.geometry("500x500")

        self.curr_bids = None
        self.curr_data2import = None
        self.curr_import_folder = None
        self.bids_dir = None
        self.upload_dir = None
        self.main_frame = dict()
        # make menu
        menu_bar = Menu(self.master)
        root['menu'] = menu_bar
        # settings menu
        bids_menu = Menu(menu_bar, tearoff=0)
        self.bids_menu = bids_menu
        uploader_menu = Menu(menu_bar, tearoff=0)
        self.uploader_menu = uploader_menu
        bids_menu = Menu(menu_bar, tearoff=0)
        self.bids_menu = bids_menu
        issue_menu = Menu(menu_bar, tearoff=0)
        self.issue_menu = issue_menu
        pipeline_menu = Menu(menu_bar, tearoff=0)
        self.pipeline_menu = pipeline_menu
        # fill up the bids menu
        bids_menu.add_command(label='Create new BIDS directory', command=lambda: self.ask4bidsdir(True))
        bids_menu.add_command(label='Set BIDS directory', command=self.ask4bidsdir)
        bids_menu.add_command(label='Refresh BIDS dataset', command=self.refresh, state=DISABLED)
        bids_menu.add_command(label='Show current log', command=lambda: self.show_logs(),
                              state=DISABLED)
        bids_menu.add_command(label='Show previous logs', command=lambda: self.show_logs(all=True), state=DISABLED)
        bids_menu.add_command(label='Show dataset_description.json', state=DISABLED)
        bids_menu.add_command(label='Explore Bids dataset', state=DISABLED)
        # fill up the upload/import menu
        uploader_menu.add_command(label='Set Upload directory', command=self.ask4upload_dir, state=DISABLED)
        uploader_menu.add_command(label='Add elements to import', command=self.add_elmt2data2import, state=DISABLED)
        uploader_menu.add_command(label='Import', command=self.import_data, state=DISABLED)
        # fill up the issue menu
        issue_menu.add_command(label='Verify upload folder content',
                               command=lambda: self.solve_issues('UpldFldrIssue'), state=DISABLED)
        issue_menu.add_command(label='Solve importation issues',
                               command=lambda: self.solve_issues('ImportIssue'), state=DISABLED)
        issue_menu.add_command(label='Solve channel issues',
                               command=lambda: self.solve_issues('ElectrodeIssue'), state=DISABLED)
        # fill up the pipeline menu

        with os.scandir(self.folder_software) as it:
            for entry in it:
                name, ext = os.path.splitext(entry.name)
                if ext == '.json':
                    pipeline_menu.add_command(label=name, command=lambda nm=name: self.run_analysis(nm), state=DISABLED)
        #self.pipeline_settings = bids.PipelineSettings()
        #self.pipeline_settings.read_file()
        #for cnt, pipl in enumerate(self.pipeline_settings['Settings']):
        #    pipeline_menu.add_command(label=pipl['label'], command=lambda idx=cnt: self.launch_pipeline(idx), state=DISABLED)
        # settings_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label="BIDS", underline=0, menu=bids_menu)
        menu_bar.add_cascade(label="Uploader", underline=0, menu=uploader_menu)
        menu_bar.add_cascade(label="Issues", underline=0, menu=issue_menu)
        menu_bar.add_cascade(label="Pipelines", underline=0, menu=pipeline_menu)

        # area to print logs
        self.main_frame['text'] = DisplayText(master=self.master)

        # area to print lists
        self.main_frame['list'] = Listbox(master=self.master, font=("Arial", 12))

        # area to print double linked list
        self.main_frame['double_list'] = IssueList(self.master, self.apply_actions, self.delete_actions)

        # little band to print small infos
        self.banner_label = StringVar()
        self.banner_label.set('Please set/create a Bids directory')
        self.banner_color = StringVar()
        self.banner = Label(self.master, textvariable=self.banner_label, bg="blue", fg="white", font=("Arial", 15))
        self.banner.pack(fill=X, side=TOP)
        # self.pack_element(self.main_frame['text'])
        # self.update_text('\n'.join(make_splash()))

    def launch_pipeline(self, idx):
        self.pipeline_settings.propose_param(self.curr_bids, idx)
        self.curr_bids.write_log('Launching: ' + self.pipeline_settings['Settings'][idx]['label'] + '(to be set!!!!!)')

    def pack_element(self, element, side=None, remove_previous=True):

        if not element.winfo_ismapped():

            if side not in [TOP, BOTTOM, LEFT, RIGHT]:
                side = None

            if remove_previous:
                for widget_name in self.main_frame:
                    if self.main_frame[widget_name].winfo_ismapped():
                        self.main_frame[widget_name].pack_forget()
            if isinstance(element, DoubleListbox):
                element.pack_elements()
            else:
                element.pack(fill=BOTH, expand=1, side=side, padx=5, pady=5)

    def update_text(self, str2show, delete_flag=True, location=None):
        if str2show and not str2show.endswith('\n'):
            str2show = str2show + '\n'
        self.main_frame['text'].update_text(str2show, delete_flag=delete_flag, location=location)
        self.update()

    def apply_actions(self):
        flag = messagebox.askyesno('Apply all actions', 'Are you sure you want to apply actions of all issues?')
        if flag:
            self.make_idle('Appling actions')
            self.curr_bids.apply_actions()
            if self.upload_dir:
                self.curr_data2import = bids.Data2Import(self.upload_dir)
            self.update_text(self.curr_bids.curr_log)
            self.pack_element(self.main_frame['text'])
            self.make_available()

    def delete_actions(self):
        flag = messagebox.askyesno('DELETE All Actions', 'Are you sure you want to DELETE all planned actions?')
        if flag:
            for issue_type in self.curr_bids.issues:
                for issue in self.curr_bids.issues[issue_type]:
                    issue['Action'] = []
            issue_list = self.main_frame['double_list'].elements['list1']
            action_list = self.main_frame['double_list'].elements['list2']
            for list_idx in range(0, action_list.size()-1):
                action_list.delete(list_idx)
                action_list.insert(list_idx, '')
                issue_list.itemconfig(list_idx, foreground='black')
            info_str = 'All actions were deleted'
            self.curr_bids.write_log(info_str)
            self.curr_bids.issues.save_as_json()
            messagebox.showinfo('Delete actions', info_str)

    def add_elmt2data2import(self):
        self.curr_data2import._assign_import_dir(self.curr_data2import.dirname)
        self.curr_data2import.save_as_json(write_date=True)
        results = BidsBrickDialog(root, self.curr_data2import,
                                  disabled=self.curr_data2import['DatasetDescJSON'].keylist,
                                  title=self.curr_data2import.classname()).apply()
        if results is not None and messagebox.askyesno('Change ' + self.curr_data2import.classname() + '?',
                                                       'You are about to permanently modify ' +
                                                       self.curr_data2import.classname() + '.\nAre you sure?'):
            self.curr_data2import.save_as_json()
            if self.curr_data2import.is_empty():
                self.update_text('There is no file to import in ' + self.upload_dir)
                self.upload_dir = None
                self.curr_data2import = None
            else:
                self.curr_bids.make_upload_issues(self.curr_data2import)
                self.solve_issues('UpldFldrIssue')
            # self.update_text(self.curr_data2import)

    def show_logs(self, all=False):
        if self.curr_bids:
            if all:
                logs_str = self.curr_bids.get_all_logs()
                self.update_text(logs_str)
            else:
                self.update_text(self.curr_bids.curr_log)
            self.pack_element(self.main_frame['text'])

    def refresh(self):
        self.pack_element(self.main_frame['text'])
        self.make_idle('Parsing BIDS directory.')
        self.curr_bids._assign_bids_dir(self.curr_bids.dirname)
        try:
            if self.curr_bids:
                self.curr_bids.parse_bids()
                self.update_text(self.curr_bids.curr_log)
        except Exception as err:
            self.banner_label._default = 'Please set/create a Bids directory'
            self.curr_bids = None
            self.change_menu_state(self.bids_menu, start_idx=2, state=DISABLED)
            self.change_menu_state(self.uploader_menu, state=DISABLED)
            self.change_menu_state(self.issue_menu, state=DISABLED)
            self.update_text(str(err))
        self.make_available()

    @staticmethod
    def populate_list(list_object, input_list):
        for item in input_list:
            list_object.insert(END, item)

    def show_bids_desc(self, input_dict):

        if isinstance(input_dict, bids.BidsBrick):
            output_dict = FormDialog(root, input_dict,
                                     required_keys=input_dict.required_keys,
                                     title='Fill up the ' + input_dict.__class__.__name__ + 'attributes').apply()
        elif isinstance(input_dict, bids.DatasetDescJSON):
            temp_dict = input_dict.__class__()
            temp_dict.copy_values(input_dict, simplify_flag=False)
            output_dict = FormDialog(root, temp_dict,
                                     required_keys=input_dict.required_keys,
                                     title='Fill up the ' + input_dict.__class__.filename).apply()
            if output_dict:
                if 'Authors' in output_dict:
                    # tkinter modifies the author list ['NR' , 'FB', 'CGB'] into a string '{NR} {FB} {CGB}'
                    tmp_str = output_dict['Authors'].replace('} {', ', ')
                    tmp_str = tmp_str.replace('{', '').replace('}', '')
                    output_dict['Authors'] = tmp_str
                if not output_dict == temp_dict and \
                        messagebox.askyesno('Change ' + input_dict.__class__.filename + '?',
                                            'You are about to modify ' + input_dict.__class__.filename +
                                            '.\nAre you sure?'):
                    input_dict.copy_values(output_dict)
                    input_dict.write_file()
                    self.curr_bids.save_as_json()

    @staticmethod
    def change_menu_state(menu, start_idx=0, end_idx=None, state=None):
        if state is None or state not in [NORMAL, DISABLED]:
            state = NORMAL
        if end_idx is None:
            end_idx = menu.index(END)
            if end_idx is None:
                return
        if end_idx and end_idx > menu.index(END):
            raise IndexError('End index is out of range (' + str(end_idx) + '>' + str(menu.index(END)) + ').')
        if start_idx > end_idx:
            raise IndexError('Start index greater than the end index (' + str(start_idx) + '>' + str(end_idx) + ').')
        for i in range(start_idx, end_idx+1):
            menu.entryconfigure(i, state=state)

    def ask4bidsdir(self, isnew_dir=False):
        """Either set (isnew_dir = False) or create Bids directory (isnew_dir=True)"""

        def create_new_bidsdataset(parent, bids_dir):
            error_str = ''
            if os.listdir(bids_dir):
                error_str += 'The folder is not empty!'
                return error_str
            # create a dataset description file
            datasetdesc = bids.DatasetDescJSON()
            output_dict = FormDialog(root, datasetdesc,
                                     required_keys=bids.DatasetDescJSON.required_keys,
                                     title='Fill up the ' + bids.DatasetDescJSON.filename).apply()
            if output_dict:
                datasetdesc.copy_values(output_dict)
                datasetdesc.has_all_req_attributes()
            if not datasetdesc.is_complete and \
                    datasetdesc['Name'] == bids.DatasetDescJSON.bids_default_unknown:
                error_str += bids.DatasetDescJSON.filename + ' needs at least these elements: ' + \
                            str(bids.DatasetDescJSON.required_keys) + 'to be filled.'
                return error_str
            # Select type of requirements
            error_str = RequirementsDialog(parent, bids_dir).error_str

            return error_str


        def check_access():
            if os.path.isfile(self.curr_bids.access.filename):
                acss = bids.Access()
                acss.read_file(self.curr_bids.access.filename)
            else:
                acss = False
                self.curr_bids.access.write_file()
            return acss

        bids_dir = filedialog.askdirectory(title='Please select a BIDS dataset directory',
                                           initialdir=BidsManager.bids_startfile)
        if not bids_dir:
            return
        reload(bids)
        self.pack_element(self.main_frame['text'])
        self.upload_dir = None
        self.curr_data2import = None
        self.update_text('')
        if self.curr_bids:
            self.curr_bids.access.delete_file()
            self.curr_bids = None
        if isnew_dir:
            # if new bids directory than create dataset_desc.json and but the requirements in code
            error_str = create_new_bidsdataset(self, bids_dir)
            if error_str:
                messagebox.showerror('Error', error_str)
                self.change_menu_state(self.uploader_menu, state=DISABLED)
                self.change_menu_state(self.issue_menu, state=DISABLED)
                return
            else:
                self.curr_bids = bids.BidsDataset(bids_dir, update_text=self.update_text)
        else:
            ''' if bids directory already exits, check if there is a dataset_description.json otherwise stop 
            (it should be present to avoid nesting bids dir unintentionally)'''
            if os.path.isfile(os.path.join(bids_dir, bids.DatasetDescJSON.filename)):

                self.banner_label._default = 'Current BIDS directory: ' + bids_dir
                self.make_idle('Parsing BIDS directory.')
                self.curr_bids = bids.BidsDataset(bids_dir, update_text=self.update_text)
                access = check_access()
                if access:
                    messagebox.showerror('Error', access.display())
                    self.banner_label._default = 'Please set/create a Bids directory'
                    self.curr_bids = None
                    self.change_menu_state(self.uploader_menu, state=DISABLED)
                    self.change_menu_state(self.issue_menu, state=DISABLED)
                    self.make_available()
                    return

            else:
                self.change_menu_state(self.uploader_menu, state=DISABLED)
                self.change_menu_state(self.issue_menu, state=DISABLED)
                self.update_text('Error: No ' + bids.DatasetDescJSON.filename + ' was found. Please set a correct ' +
                                 'path to a BIDS directory or create a new one.')
                return

        # enable all bids sub-menu
        self.change_menu_state(self.bids_menu)
        self.change_menu_state(self.pipeline_menu)
        self.bids_menu.entryconfigure(5, command=lambda: self.show_bids_desc(self.curr_bids['DatasetDescJSON']))
        self.bids_menu.entryconfigure(6, command=self.explore_bids_dataset)
        # enable selection of upload directory
        self.change_menu_state(self.uploader_menu, end_idx=0)
        # enable all issue sub-menu
        self.change_menu_state(self.issue_menu)
        # enalbe all pipelines
        self.change_menu_state(self.pipeline_menu)
        # self.update_text(self.curr_bids.curr_log)
        self.make_available()

    def explore_bids_dataset(self):
        self.pack_element(self.main_frame['text'])
        BidsBrickDialog(self, self.curr_bids)
        self.curr_bids.save_as_json()

    def ask4upload_dir(self):
        self.pack_element(self.main_frame['text'])
        self.upload_dir = filedialog.askdirectory(title='Please select a upload/import directory',
                                                  initialdir=BidsManager.import_startfile)
        if not self.upload_dir:
            return
        self.make_idle()
        try:
            if os.path.isfile(os.path.join(self.upload_dir, bids.Data2Import.filename)):
                req_path = os.path.join(self.curr_bids.dirname, 'code', 'requirements.json')
                self.curr_data2import = bids.Data2Import(self.upload_dir, req_path)
                if self.curr_data2import.is_empty():
                    self.update_text('There is no file to import in ' + self.upload_dir)
                    self.upload_dir = None
                    self.curr_data2import = None
                else:
                    self.change_menu_state(self.uploader_menu)
                    self.curr_bids.make_upload_issues(self.curr_data2import)
                    # self.update_text(self.curr_data2import.curr_log)
                    # self.update_text(self.curr_data2import, delete_flag=False)
                    self.solve_issues('UpldFldrIssue')
            else:
                self.update_text('Error: data2import.json not found in ' + self.upload_dir)
                self.upload_dir = None
                self.curr_data2import = None
                self.change_menu_state(self.uploader_menu, state=DISABLED, start_idx=1)

        except Exception as err:
            self.update_text(str(err))
        self.make_available()

    def print_participants_tsv(self):
        self.pack_element(self.main_frame['text'])
        self.update_text(self.make_table(self.curr_bids['ParticipantsTSV']))

    def print_srcdata_tsv(self):
        self.pack_element(self.main_frame['text'])
        if self.curr_bids['SourceData'] and self.curr_bids['SourceData'][-1]['SrcDataTrack']:
            self.update_text(self.make_table(self.curr_bids['SourceData'][-1]['SrcDataTrack']))
        else:
            self.update_text('Source Data Track does not exist')

    def update_issue_list(self, iss_ict, list_idx, info):
        if not isinstance(iss_ict, bids.IssueType):
            raise TypeError('First argument should be an instance of IssueType class.')
        issue_list = self.main_frame['double_list'].elements['list1']
        action_list = self.main_frame['double_list'].elements['list2']
        action_list.delete(list_idx)
        if iss_ict['Action']:
            action_list.insert(list_idx, iss_ict['Action'][-1].formatting())
        else:
            action_list.insert(list_idx, '')
        issue_list.itemconfig(list_idx, foreground='green')
        self.curr_bids.issues.save_as_json()

    def remove_file(self, list_idx, info):
        flag = messagebox.askyesno('Remove file in BIDS', 'Are you sure that you want to remove ' +
                                   str(info['Element'].get_attributes('fileLoc')) + 'from BIDS ?')
        if flag:
            idx = info['index']
            curr_dict = self.curr_bids.issues['ImportIssue'][idx]
            fname, dirn, ext = info['Element'].create_filename_from_attributes()
            cmd = 'remove="' + fname + ext + '", in_bids=True'
            curr_dict.add_action(desc='Remove element ' + str(info['Element'].get_attributes('fileLoc')) +
                                      ' from data to import.', command=cmd)
            self.update_issue_list(curr_dict, list_idx, info)

    def remove_issue(self, iss_key, list_idx, info):
        flag = messagebox.askyesno('Remove issue', 'Are you sure that you want to remove this issue?')
        if flag:
            idx = info['index']
            curr_dict = self.curr_bids.issues[iss_key][idx]
            cmd = 'remove_issue=True'
            curr_dict.add_action(desc='Remove issue from the list.', command=cmd)
            self.update_issue_list(curr_dict, list_idx, info)

    def do_not_import(self, iss_key, list_idx, info):
        flag = messagebox.askyesno('Do Not Import', 'Are you sure that you do not want to import this element' +
                                   str(info['Element'].get_attributes()) + '?')
        if flag:
            idx = info['index']
            curr_dict = self.curr_bids.issues[iss_key][idx]
            cmd = 'pop=True, in_bids=False'
            curr_dict.add_action(desc='Remove from element to import.', command=cmd)
            self.update_issue_list(curr_dict, list_idx, info)

    def modify_attributes(self, iss_key, list_idx, info, in_bids=False):
        if isinstance(info['Element'], bids.DatasetDescJSON):
            bids_dict = type(info['Element'])()
            bids_dict.copy_values(self.curr_bids['DatasetDescJSON'])
            imp_dict = info['Element']
        elif isinstance(info['Element'], bids.BidsBrick):
            self.curr_bids.is_subject_present(info['Element']['sub'])
            if isinstance(info['Element'], bids.Subject):
                bids_dict = self.curr_bids.curr_subject['Subject'].get_attributes(['alias', 'upload_date'])
            else:
                fname, dirn, ext = info['Element'].create_filename_from_attributes()
                bids_obj = self.curr_bids.get_object_from_filename(os.path.join(dirn, fname+ext))
                if bids_obj:
                    bids_dict = bids_obj.get_attributes('fileLoc')
                else:
                    bids_dict = dict()

                if 'run' in bids_dict.keys():
                    tmp_brick = type(info['Element'])()
                    tmp_brick.copy_values(bids_dict)
                    _, highest = self.curr_bids.get_number_of_runs(tmp_brick)
                    if highest:
                        bids_dict['run'] = highest + 1
                if 'ses' in bids_dict.keys():
                    _, ses_list = self.curr_bids.get_number_of_session4subject(bids_dict['sub'])
                    bids_dict['ses'] = ses_list
                if 'modality' in bids_dict:
                    bids_dict['modality'] = info['Element'].allowed_modalities
            imp_dict = info['Element'].get_attributes(['alias', 'upload_date', 'fileLoc'])
        else:
            return

        if in_bids:
            input_dict = bids_dict
            option_dict = imp_dict
        else:
            input_dict = imp_dict
            option_dict = bids_dict
        output_dict = FormDialog(self, input_dict, options=option_dict,
                                 required_keys=info['Element'].required_keys).apply()
        if output_dict and not output_dict == input_dict:
            idx = info['index']
            curr_dict = self.curr_bids.issues[iss_key][idx]
            if isinstance(info['Element'], bids.DatasetDescJSON) and 'Authors' in output_dict:
                # tkinter modifies the author list ['NR' , 'FB', 'CGB'] into a string '{NR} {FB} {CGB}'
                tmp_str = output_dict['Authors'].replace('} {', ', ')
                tmp_str = tmp_str.replace('{', '').replace('}', '')
                output_dict['Authors'] = tmp_str

            if in_bids:
                dir_str = ' in BIDS dir'
            else:
                dir_str = ' in import dir'
            if isinstance(info['Element'], bids.GlobalSidecars):
                input_brick = type(info['Element'])(info['Element']['fileLoc'])
                output_brick = type(info['Element'])(info['Element']['fileLoc'])
            else:
                input_brick = type(info['Element'])()
                output_brick = type(info['Element'])()
            input_brick.copy_values(input_dict)

            output_brick.copy_values(output_dict)
            cmd = input_brick.write_command(output_brick, {'in_bids': in_bids})
            curr_dict.add_action(desc='Modify attrib. into ' + str(output_dict) + dir_str, command=cmd)
            self.update_issue_list(curr_dict, list_idx, info)

    def select_correct_name(self, list_idx, info):

        idx = info['index']
        mismtch_elec = info['Element']
        curr_dict = self.curr_bids.issues['ElectrodeIssue'][idx]
        results = ListDialog(self.master, curr_dict['RefElectrodes'], 'Rename ' + mismtch_elec + ' as :').apply()
        if results:
            str_info = mismtch_elec + ' has to be renamed as ' + results + ' in the files related to ' + \
                       os.path.basename(curr_dict['fileLoc']) + ' (channels.tsv, events.tsv, .vmrk and .vhdr).\n'
            command = 'name="' + results + '"'
            curr_dict.add_action(str_info, command, elec_name=mismtch_elec)
            self.update_issue_list(curr_dict, list_idx, info)

    def change_elec_type(self, list_idx, info):
        idx = info['index']
        mismtch_elec = info['Element']

        curr_dict = self.curr_bids.issues['ElectrodeIssue'][idx]
        input_dict = {'type': mism_elec['type'] for mism_elec in curr_dict['MismatchedElectrodes']
                      if mism_elec['name'] == mismtch_elec}
        opt_dict = {'type': bids.Electrophy.channel_type}
        output_dict = FormDialog(self, input_dict, title='Modify electrode type of ' + mismtch_elec + ' into:',
                                 options=opt_dict, required_keys=input_dict).apply()
        if output_dict and not output_dict['type'] == input_dict['type']:
            str_info = 'Change electrode type of ' + mismtch_elec + ' from ' + input_dict['type'] + ' to ' + \
                       output_dict['type'] + ' in the electrode file related to ' + \
                       os.path.basename(curr_dict['fileLoc']) + '.\n'
            # self.pack_element(self.main_frame['text'], side=LEFT, remove_previous=False)
            # to fancy, used for others
            # command = ', '.join([str(k + '="' + output_dict[k] + '"') for k in output_dict])
            command = 'type="' + output_dict['type'] + '"'
            curr_dict.add_action(str_info, command, elec_name=mismtch_elec,)
            self.update_issue_list(curr_dict, list_idx, info)

    def get_entry(self, issue_key, list_idx, info):
        idx = info['index']
        if issue_key == 'ElectrodeIssue':
            mismtch_elec = info['Element']
        else:
            mismtch_elec = None
        curr_dict = self.curr_bids.issues[issue_key][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        prev_comm = '\n'.join(curr_dict.formatting(comment_type='Comment', elec_name=mismtch_elec))
        new_comments = CommentDialog(self.master, prev_comm).apply()
        if new_comments:
            curr_dict.add_comment(new_comments, elec_name=mismtch_elec)
            issue_list.itemconfig(list_idx, bg='yellow')
            self.curr_bids.issues.save_as_json()

    def cancel_action(self, issue_key, list_idx, info):
        idx = info['index']
        mismtch_elec = info['Element']
        curr_dict = self.curr_bids.issues[issue_key][idx]
        if issue_key == 'ElectrodeIssue':
            for action in curr_dict['Action']:
                if action['name'] == mismtch_elec:
                    curr_dict['Action'].pop(curr_dict['Action'].index(action))
                    break  # there is only one action per channel so break when found
        elif issue_key == 'ImportIssue' and curr_dict['Action']:
            curr_dict['Action'].pop(-1)
        self.update_issue_list(curr_dict, list_idx, info)

    def open_file(self, issue_key, list_idx, info):
        curr_iss = self.curr_bids.issues[issue_key][info['index']]
        if issue_key == 'ElectrodeIssue':
            os.startfile(os.path.normpath(os.path.join(self.curr_bids.dirname, curr_iss['fileLoc'])))
        else:
            os.startfile(os.path.normpath(os.path.join(curr_iss['path'], info['Element']['fileLoc'])))

    def mark_as_verified(self, list_idx, info, state_str):
        idx = info['index']
        curr_dict = self.curr_bids.issues['UpldFldrIssue'][idx]
        str_info = os.path.basename(info['Element']['fileLoc']) + ' will be marked as ' + state_str + '.'
        command = 'state="' + state_str + '"'
        curr_dict.add_action(str_info, command)
        self.update_issue_list(curr_dict, list_idx, info)

    def solve_issues(self, issue_key):

        def what2domenu(iss_key, dlb_lst, line_map, event):

            if not dlb_lst.elements['list1'].curselection():
                return
            curr_idx = dlb_lst.elements['list1'].curselection()[0]

            pop_menu = Menu(self.master, tearoff=0)

            if iss_key == 'ElectrodeIssue':
                pop_menu.add_command(label='Open file',
                                     command=lambda: self.open_file(issue_key, curr_idx, line_map[curr_idx]))
                pop_menu.add_command(label='Change electrode name',
                                     command=lambda: self.select_correct_name(curr_idx, line_map[curr_idx]))
                pop_menu.add_command(label='Change electrode type',
                                     command=lambda: self.change_elec_type(curr_idx, line_map[curr_idx]))
            else:
                if isinstance(line_map[curr_idx]['Element'], bids.DatasetDescJSON):
                    # if issue arise from DatasetDescJSON change the DatasetDescJSON object in data2import.json
                    pop_menu.add_command(label='Modify ' + bids.DatasetDescJSON.filename + ' in current BIDS directory',
                                         command=lambda: self.modify_attributes(issue_key, curr_idx, line_map[curr_idx],
                                                                                in_bids=True))
                    pop_menu.add_command(label='Modify ' + bids.DatasetDescJSON.filename +
                                               ' in current Upload directory',
                                         command=lambda: self.modify_attributes(issue_key, curr_idx, line_map[curr_idx],
                                                                                in_bids=False))
                elif isinstance(line_map[curr_idx]['Element'], bids.BidsBrick):
                    if isinstance(line_map[curr_idx]['Element'], bids.Subject):
                        """
                        if issue arise from Subject, it means that its attributes are incomplete or wrong (e.g. age 
                        does not matched the age of this patient in bids dataset). One can either change the attributes
                        of the subject to be imported or the ones of the already imported subject (in participatns.tsv)
                        """
                        pop_menu.add_command(label='Change subject\'s attribute in ' + bids.Data2Import.filename,
                                             command=lambda: self.modify_attributes(issue_key, curr_idx,
                                                                                    line_map[curr_idx], in_bids=False))
                        pop_menu.add_command(label='Change subject\'s attribute in ' + bids.ParticipantsTSV.filename,
                                             command=lambda: self.modify_attributes(issue_key, curr_idx,
                                                                                    line_map[curr_idx], in_bids=True))
                    else:
                        """if issue arise from a modality, it means that the attributes of the modality are incomplete
                        or wrong and has to be changed according to the description or the file remove from the list of
                         file that will be imported"""
                        pop_menu.add_command(label='Open file',
                                             command=lambda: self.open_file(issue_key, curr_idx, line_map[curr_idx]))
                        pop_menu.add_command(label='Change modality attributes',
                                             command=lambda: self.modify_attributes(issue_key, curr_idx,
                                                                                    line_map[curr_idx], in_bids=False))
                        if iss_key == 'ImportIssue':
                            pop_menu.add_command(label='Remove file in BIDS',
                                                 command=lambda: self.remove_file(curr_idx, line_map[curr_idx]))
                        else:
                            idx = line_map[curr_idx]['index']
                            curr_dict = self.curr_bids.issues['UpldFldrIssue'][idx]
                            if curr_dict['state'] == 'verified':
                                state_str = 'not verified'
                            else:
                                state_str = 'verified'
                                pop_menu.add_command(label='Mark as verified',
                                                     command=lambda: self.mark_as_verified(curr_idx, line_map[curr_idx],
                                                                                           state_str))

                    pop_menu.add_command(label='Do not import',
                                         command=lambda: self.do_not_import(issue_key, curr_idx, line_map[curr_idx]))
                    # in case you wrongly chose a folder
                    pop_menu.add_command(label='Remove issue',
                                         command=lambda: self.remove_issue(issue_key, curr_idx,
                                                                           line_map[curr_idx]))

            pop_menu.add_command(label='Read or add comment',
                                 command=lambda: self.get_entry(issue_key, curr_idx, line_map[curr_idx]))
            pop_menu.add_command(label='Cancel action',
                                 command=lambda: self.cancel_action(issue_key, curr_idx, line_map[curr_idx]))
            pop_menu.post(event.x_root, event.y_root)

        dlb_list = self.main_frame['double_list']
        dlb_list.clear_list()
        self.pack_element(dlb_list)

        issue_dict = self.curr_bids.issues[issue_key]
        issue_list2write = []
        action_list2write = []
        line_mapping = []
        if issue_key == 'ElectrodeIssue':
            label_str = 'electrode issue'
            for issue in issue_dict:
                for mismatch_el in issue.list_mismatched_electrodes():
                    issue_list2write.append('In file ' + os.path.basename(issue['fileLoc']) + ' of subject ' +
                                            issue['sub'] + ', ' + mismatch_el +
                                            ' does not match electrodes.tsv reference.')
                    act_str = issue.formatting(comment_type='Action', elec_name=mismatch_el)

                    line_mapping.append({'index': issue_dict.index(issue), 'Element': mismatch_el,
                                         'IsComment': bool(issue.formatting(comment_type='Comment',
                                                                            elec_name=mismatch_el)),
                                         'IsAction': False})
                    if act_str:
                        action_list2write.append(act_str[0])
                        # you can write act_str[0] because there is only one action per channel
                        line_mapping[-1]['IsAction'] = True
                    else:
                        action_list2write.append('')
        elif issue_key == 'ImportIssue' or issue_key == 'UpldFldrIssue':
            if issue_key == 'ImportIssue':
                label_str = 'importation issue'
            else:
                label_str = 'upload folder issue'
            for issue in issue_dict:
                element = issue.get_element()
                if not element:
                    continue
                line_mapping.append({'index': issue_dict.index(issue), 'Element': element,
                                     'IsComment': bool(issue.formatting(comment_type='Comment')),
                                     'IsAction': False})
                if issue_key == 'ImportIssue':
                    issue_list2write.append(issue['description'])
                else:
                    issue_list2write.append('File: ' + issue['fileLoc'] + ' is ' + issue['state'])
                act_str = issue.formatting(comment_type='Action')

                if act_str:
                    action_list2write.append(act_str[0])
                    # you can write act_str[0] because there is only one action per channel
                    line_mapping[-1]['IsAction'] = True
                else:
                    action_list2write.append('')
        else:
            messagebox.showerror('Unknown issue', 'This issue is currently not recognize')
            return

        self.populate_list(dlb_list.elements['list1'], issue_list2write)

        for cnt, mapping in enumerate(line_mapping):
            if mapping['IsComment']:
                dlb_list.elements['list1'].itemconfig(cnt, bg='yellow')
            if mapping['IsAction']:
                dlb_list.elements['list1'].itemconfig(cnt, foreground='green')

        self.populate_list(dlb_list.elements['list2'], action_list2write)
        self.banner_label.set(self.banner_label._default + '\nSelect issue from the ' + label_str + ' list')
        dlb_list.elements['list1'].bind('<Double-Button-1>',
                                        lambda event: what2domenu(issue_key, dlb_list, line_mapping, event))
        dlb_list.elements['list1'].bind('<Return>', lambda event: what2domenu(issue_key, dlb_list, line_mapping, event))

    def import_data(self):
        self.pack_element(self.main_frame['text'])
        self.make_idle('Importing data from ' + self.curr_data2import.dirname)
        try:
            if self.curr_data2import:
                self.curr_bids.import_data(self.curr_data2import)
                # self.update_text(self.curr_bids.curr_log)
            else:
                self.update_text('No upload directory is set.')
        except Exception as err:
            self.update_text(self.curr_bids.curr_log + str(err))
        self.curr_data2import = None
        self.upload_dir = None
        self.change_menu_state(self.uploader_menu, start_idx=1, state=DISABLED)
        self.make_available()

    def close_window(self):
        if self.curr_bids:
            self.curr_bids.access.delete_file()
            # if not os.path.isfile(os.path.join(self.curr_bids.dirname, self.curr_bids.log_path,
            #                                    'bids_' + self.curr_bids.access["access_time"] + '.log')):
            #     self.curr_bids.write_log(self.curr_bids.curr_log)
            self.curr_bids.write_log('Bids Manager was closed')
            self.curr_bids.save_as_json()
        self.quit()
        root.destroy()

    def make_idle(self, str2print=None):
        if str2print is None:
            str2print = ''
        else:
            str2print = '\n' + str2print
        root.config(cursor="wait")
        for key in self.main_frame:
            self.main_frame[key].config(cursor="wait")
        self.banner.configure(bg="red")
        self.banner_label.set(self.banner_label._default + str2print)
        self.update()

    def make_available(self):
        root.config(cursor="")
        for key in self.main_frame:
            self.main_frame[key].config(cursor="")
        self.banner.configure(bg="blue")
        self.banner_label.set(self.banner_label._default)
        self.update()  # may not be necessary if at the end of method but is needed otherwise...

    def run_analysis(self, nameS):
        if not self.curr_bids:
            error_str = 'Bids directory should be selected'
            raise TypeError(error_str)
        soft_analyse = pip.Analysis(nameS, self.curr_bids)
        output_dict = BidsSelectDialog(self, self.curr_bids, soft_analyse)
        #add the parameters
        self.update_text('Subjects selected \n' + '\n'.join(output_dict.results['sub']) + '\nThe analysis is ready to be run')
        soft_analyse.run_analysis()
        self.update_text('The analysis is done')

    @staticmethod
    def make_table(table):
        string_table = ''
        for line in table:
            string_table += '\t'.join(line) + '\n'

        return string_table


class DoubleListbox(object):
    """ DoubleListbox is a class to display two ListBox which share the same scrollbar and are thus synchronous """

    def __init__(self, parent):
        self.elements = dict()
        self.elements['scrollbar'] = Scrollbar(master=parent, orient="vertical", command=self.on_vsb)
        self.elements['list1'] = Listbox(master=parent, font=("Arial", 12),
                                         yscrollcommand=self.elements['scrollbar'].set)
        self.elements['list2'] = Listbox(master=parent, font=("Arial", 12),
                                         yscrollcommand=self.elements['scrollbar'].set)
        self.elements['list1'].bind("<MouseWheel>", self.on_mouse_wheel)
        self.elements['list2'].bind("<MouseWheel>", self.on_mouse_wheel)

    def on_vsb(self, *args):
        self.elements['list1'].yview(*args)
        self.elements['list2'].yview(*args)

    def on_mouse_wheel(self, event):
        self.elements['list1'].yview("scroll", event.delta, "units")
        self.elements['list2'].yview("scroll", event.delta, "units")
        # this prevents default bindings from firing, which
        # would end up scrolling the widget twice
        return "break"

    def pack_elements(self):
        self.elements['scrollbar'].pack(side=RIGHT, fill=Y)
        self.elements['list2'].pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        self.elements['list1'].pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

    def clear_list(self):
        self.elements['list1'].delete(0, END)
        self.elements['list2'].delete(0, END)

    def winfo_ismapped(self):
        return self.elements['list1'].winfo_ismapped()

    def pack_forget(self):
        for key in self.elements.keys():
            self.elements[key].pack_forget()


class IssueList(DoubleListbox):
    """ Based on the DoubleListbox class, the IssueList class adds three buttons to the joint listbox to allow
    validating, saving or deleting the actions chosen by the user related to the issues in the right-hand side list"""
    button_size = [2, 10]

    def __init__(self, master, cmd_apply, cmd_delete):
        super().__init__(master)
        self.user_choice = None
        self.elements['apply'] = Button(master=master, text='Apply', command=cmd_apply,
                                        height=self.button_size[0], width=self.button_size[1])

        self.elements['delete'] = Button(master=master, text='DELETE', command=cmd_delete, height=self.button_size[0],
                                         width=self.button_size[1], default=ACTIVE)

    def pack_elements(self):
        super().pack_elements()
        self.elements['apply'].pack(side=TOP, expand=1, padx=10, pady=5)
        self.elements['delete'].pack(side=TOP, expand=1, padx=10, pady=5)

    def config(self, **kwargs):
        for key in self.elements:
            self.elements[key].config(**kwargs)


class DefaultText(scrolledtext.ScrolledText, object):

    def clear_text(self, start=None, end=None):
        if not start:
            start = 1.0
        if not end:
            end = END
        self.delete(start, end)


class DisplayText(DefaultText):

    def update_text(self, str2show, delete_flag=True, location=None):
        self.config(state=NORMAL)
        if delete_flag:
            self.delete(1.0, END)
        if not location:
            location = END
        self.insert(location, str2show)
        self.config(state=DISABLED)


class TemplateDialog(Toplevel, object):
    button_size = [2, 10]
    default_pad = [2, 2]

    def __init__(self, parent):

        def center(win):
            win.update_idletasks()
            width = win.winfo_width()
            height = win.winfo_height()
            x = (win.winfo_screenwidth() // 2) - (width // 2)
            y = (win.winfo_screenheight() // 2) - (height // 2)
            win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        Toplevel.__init__(self, parent)
        # self.wm_resizable(False, False)
        self.wm_resizable(True, False)
        self.btn_ok = None
        self.btn_cancel = None
        self.withdraw()  # remain invisible for now
        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        self.initial_focus = None
        if parent.winfo_viewable():
            self.transient(parent)

        self.parent = parent
        self.body_widget = Frame(self)
        self.body_widget.pack(padx=self.default_pad[0], pady=self.default_pad[1], fill=BOTH, expand=1)

        self.body(self.body_widget)

        # self.body_widget.geo
        self.results = None
        self.bind("<Escape>", self.cancel)

        # self.list_and_button(parent, input_list=input_list, label_str=label_str, selection_style=selection_style)
        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        if self.parent is not None:
            self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                      parent.winfo_rooty() + 50))

        self.deiconify()  # become visible now

        self.initial_focus.focus_set()
        center(self)
        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def body(self, parent):
        pass

    def ok_cancel_button(self, parent, row=None):
        self.btn_ok = Button(parent, text='OK', command=self.ok, height=self.button_size[0],
                             width=self.button_size[1])

        self.btn_cancel = Button(parent, text='Cancel', command=self.cancel, height=self.button_size[0],
                                 width=self.button_size[1], default=ACTIVE)
        if row:

            self.btn_ok.grid(row=row, column=0, sticky=W+E, padx=self.default_pad[0], pady=self.default_pad[1])
            self.btn_cancel.grid(row=row, column=self.body_widget.grid_size()[0]-1, sticky=W+E,
                                 padx=self.default_pad[0], pady=self.default_pad[1])
        else:
            self.btn_cancel.pack(side=RIGHT, fill=Y, expand=1, padx=10, pady=5)
            self.btn_ok.pack(side=LEFT, fill=Y, expand=1, padx=10, pady=5)

    def ok(self, event=None):
        pass

    def destroy(self):
        """Destroy the window"""
        self.initial_focus = None
        Toplevel.destroy(self)

    def cancel(self, event=None):
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.results = None
        self.destroy()

    def apply(self):
        return self.results


class ListDialog(TemplateDialog):

    def __init__(self, parent, input_list, label_str=None, selection_style=None):

        if not selection_style:
            selection_style = BROWSE
        if not label_str:
            if selection_style in [MULTIPLE, EXTENDED]:
                label_str = 'Select element(s) from the list'
            else:
                label_str = 'Select an element from the list'
        self.label_str = label_str
        self.selection_style = selection_style
        self.input_list = input_list
        self.list = None
        super().__init__(parent)

    def body(self, parent):

        self.title = 'Choose from list'
        Label(parent, text=self.label_str).pack(expand=1, fill=BOTH, side=TOP,
                                                padx=self.default_pad[0], pady=self.default_pad[1])
        self.list = Listbox(parent, selectmode=self.selection_style)
        self.list.pack(expand=1, fill=BOTH,
                       padx=self.default_pad[0], pady=self.default_pad[1])

        for item in self.input_list:
            self.list.insert(END, item)
        # add the default ok and cancel button
        self.ok_cancel_button(parent)

    def ok(self, event=None):
        if self.list.curselection():
            self.results = self.selection_get()
            self.destroy()
        else:
            self.results = None
            self.bell()


class CommentDialog(TemplateDialog):

    def __init__(self, parent, previous_comment=None):
        self.label_str = None
        self.read_comment_area = None
        self.add_comment_area = None
        self.add_comment_btn = None
        if not previous_comment:
            previous_comment = ''
        self.previous_comment = previous_comment
        super().__init__(parent)

    def body(self, parent):
        self.title = 'Choose from list'

        self.read_comment_area = DisplayText(master=parent, height=20, width=100)
        self.read_comment_area.update_text(self.previous_comment)
        self.add_comment_area = DefaultText(master=parent, height=10, width=100)

        Label(parent, text='Previous comment(s)').pack(expand=1, fill=BOTH, side=TOP, padx=self.default_pad[0], pady=self.default_pad[1])

        self.read_comment_area.pack(fill=BOTH, expand=1, padx=5, pady=10, side=TOP)
        Label(parent, text='Add new comment').pack(expand=1, fill=BOTH, side=TOP, padx=self.default_pad[0], pady=self.default_pad[1])
        self.add_comment_area.pack(fill=BOTH, expand=1, padx=5, pady=10, side=TOP)

        # add the default ok and cancel button
        self.ok_cancel_button(parent)

    # def add_new_comment(self):
    #     new_comment = self.add_comment_area.get(1.0, END)
    #     if new_comment:
    #         if not self.results:
    #             self.results = []
    #         self.results.append(new_comment)
    #         self.add_comment_area.clear_text()
    #         self.read_comment_area.update_text(new_comment, delete_flag=False)

    def ok(self, event=None):
        new_comment = self.add_comment_area.get(1.0, END)
        if new_comment:
            self.results = new_comment
        self.destroy()


class BidsTSVDialog(TemplateDialog):

    max_lines = 20
    max_columns = 10
    bln_color = {'True': 'green', 'False': 'red', True: 'green', False: 'red', 'good': 'green', 'bad': 'red'}

    def __init__(self, parent, tsv_table, title=None):
        if not isinstance(tsv_table, bids.BidsTSV) or len(tsv_table) == 1:
            error_str = 'Second input should be a non empty BidsTSV instance'
            messagebox.showerror('Wrong input', error_str)
            return
        self.idx = 0
        self.idx_col = 0
        self.str_title = title
        self.orig_order = [line[0] for line in tsv_table[1:]]
        self.main_brick = type(tsv_table)()  # copy the table  so reordering does not affect BidsTSV
        self.main_brick.copy_values(tsv_table)
        self.n_lines = len(tsv_table) - 1
        self.n_columns = len(tsv_table.header)
        self.key_button = {key: '' for key in tsv_table.header}
        self.next_btn = None
        self.prev_btn = None
        self.next_col_btn = None
        self.prev_col_btn = None
        self.max_lines = min(self.n_lines, self.max_lines)
        self.max_columns = min(self.n_columns, self.max_columns)
        self.key_labels = [[] for k in range(0, self.max_lines)]
        self.n_pages = round(self.n_lines / self.max_lines)
        self.n_pages_columns = round(self.n_columns/self.max_columns)
        self.page_label_var = StringVar()
        self.page_label = None
        self.clmn_width = 0
        self.row_height = 0
        self.table2show = tsv_table[1:self.max_lines + 1]
        super().__init__(parent)

    def body(self, parent):
        if self.n_pages_columns == 1:
            self.make_header(parent)
            self.max_columns = self.n_columns
        self.make_table(parent)
        self.page_label = Label(parent, textvariable=self.page_label_var)
        try:
            self.page_label.grid(row=self.max_lines+1, column=0, columnspan=self.n_columns-2, sticky=W+E)
        except:
            pass
        if not self.n_pages == 1:
            self.prev_btn = Button(parent, text='Previous', state=DISABLED,
                                   command=lambda prnt=parent, stp=-1: self.change_page(prnt, stp))
            self.prev_btn.grid(row=self.max_lines + 1, column=self.n_columns - 2, sticky=W + E)
            self.next_btn = Button(parent, text='Next', command=lambda prnt=parent, stp=1: self.change_page(prnt, stp))
            self.next_btn.grid(row=self.max_lines+1, column=self.n_columns-1, sticky=W+E)
            self.update_page_number()
        if not self.n_pages_columns == 1:
            self.key_button = {key: '' for key in self.main_brick.header[0:self.max_columns]}
            self.make_header(parent)
            self.prev_col_btn = Button(parent, text='Previous Columns', state=DISABLED, command=lambda prnt=parent, stp=-1: self.change_column_page(prnt, stp))
            self.prev_col_btn.grid(row=self.max_lines+1, column=0, sticky=W + E)
            self.next_col_btn = Button(parent, text='Next Columns', command=lambda prnt=parent, stp=1: self.change_column_page(prnt, stp))
            self.next_col_btn.grid(row=self.max_lines+1, column=1, sticky=W + E)
        self.ok_cancel_button(parent, row=self.max_lines+2)
        # for i in range(self.max_lines):
        #     self.body_widget.grid_rowconfigure(i, weight=1, uniform='test')

    def make_header(self, parent):
        for cnt, key in enumerate(self.key_button):
            self.key_button[key] = Button(parent, text=key, command=lambda k=key, prnt=parent: self.reorder(k, prnt))
            self.key_button[key].grid(row=0, column=cnt, sticky=W+E)

    def make_table(self, parent):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, self.n_columns)):
                lbl = self.table2show[line][clmn]
                self.key_labels[line].append(Label(parent, text=lbl, relief=RIDGE))
                self.key_labels[line][-1].grid(row=line+1, column=clmn, sticky=W+E)
                if isinstance(self.main_brick, (bids.ParticipantsTSV, bids.ChannelsTSV)) \
                        and lbl in self.bln_color.keys():
                    self.key_labels[line][-1].config(fg='white', bg=self.bln_color[lbl])
                if isinstance(self.main_brick, bids.ChannelsTSV) and self.main_brick.header[clmn] == 'status':
                    self.key_labels[line][-1].bind('<Double-Button-1>',
                                                   lambda event, l=line, c=clmn: self.switch_chan_status(l, c, event))

    def switch_chan_status(self, lin, col, ev=None):
        lbl_orig = self.key_labels[lin][col]['text']
        if lbl_orig == 'good':
            lbl = 'bad'
        else:
            lbl = 'good'
        self.key_labels[lin][col].config(text=lbl, fg='white', bg=self.bln_color[lbl])
        self.main_brick[1+self.idx*self.max_lines+lin][col] = lbl
        self.results = self.main_brick

    def update_table(self):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, len(self.table2show[0]))):
                lbl = self.table2show[line][clmn]
                self.key_labels[line][clmn]['text'] = lbl
                if isinstance(self.main_brick, (bids.ParticipantsTSV, bids.ChannelsTSV))\
                        and lbl in self.bln_color.keys():
                    self.key_labels[line][clmn].config(fg='white', bg=self.bln_color[lbl])

    def change_page(self, parent, pg_step):
        self.clear_table()
        self.idx += pg_step
        self.update_page_number()
        start_idx = 1+self.idx*self.max_lines
        end_idx = start_idx + self.max_lines
        start_col = self.idx_col * self.max_columns
        end_col = start_col + self.max_columns
        if end_idx > self.n_lines+1:
            end_idx = self.n_lines+1
        if end_col > self.n_columns:
            end_col = self.n_columns
        self.table2show = [line[start_col:end_col] for line in self.main_brick[start_idx:end_idx]]
        self.update_table()

    def change_column_page(self, parent, column_step):
        #Erase header button
        for cnt, key in enumerate(self.key_button):
            self.key_button[key].destroy()
        self.clear_table()
        self.idx_col += column_step
        start_col = self.idx_col*self.max_columns
        end_col = start_col+self.max_columns
        start_idx = 1+self.idx * self.max_lines
        end_idx = start_idx + self.max_lines
        self.next_col_btn.config(state=NORMAL)
        self.prev_col_btn.config(state=NORMAL)
        if end_idx > self.n_lines+1:
            end_idx = self.n_lines+1
        if end_col > self.n_columns:
            end_col = self.n_columns
            self.next_col_btn.config(state=DISABLED)
        if start_col ==0:
            self.prev_col_btn.config(state=DISABLED)
        self.key_button = {key: '' for key in self.main_brick.header[start_col:end_col]}
        self.make_header(parent)
        self.table2show = [line[start_col:end_col] for line in self.main_brick[start_idx:end_idx]]
        self.update_table()

    def ok(self, event=None):
        # first, the table has to be reordered
        new_chan = [line[0] for line in self.main_brick[1:]]
        if not new_chan == self.orig_order:
            idx_list = [new_chan.index(ch) for ch in self.orig_order]
            tmp_brick = [self.main_brick.header]
            tmp_brick += [self.main_brick[idx + 1] for idx in idx_list]
            self.main_brick = type(self.main_brick)()
            self.main_brick.copy_values(tmp_brick)
        self.results = self.main_brick
        self.destroy()

    def update_page_number(self):
        if self.n_pages == 1:
            return
        self.page_label_var.set('Page ' + str(self.idx + 1) + '/' + str(self.n_pages))
        if self.idx == self.n_pages-1:
            self.next_btn.config(state=DISABLED)
        elif self.idx == 0:
            self.next_btn.config(state=NORMAL)
            self.prev_btn.config(state=DISABLED)
        elif self.idx > 0:
            if self.next_btn['state'] == DISABLED:
                self.next_btn.config(state=NORMAL)
            if self.prev_btn['state'] == DISABLED:
                self.prev_btn.config(state=NORMAL)
        else:
            self.prev_btn.config(state=DISABLED)

    def reorder(self, key, parent):
        self.idx = 0
        self.update_page_number()
        self.clear_table()
        key_idx = self.main_brick.header.index(key)
        tmp_list = [line[key_idx] for line in self.main_brick[1:]]
        sorted_idx = sorted(range(len(tmp_list)), key=tmp_list.__getitem__)
        tmp_brick = [self.main_brick.header]
        tmp_brick += [self.main_brick[idx+1] for idx in sorted_idx]
        self.main_brick = type(self.main_brick)()
        self.main_brick.copy_values(tmp_brick)
        self.table2show = [self.main_brick[idx+1] for idx in range(0, self.max_lines)]
        self.update_table()

    def clear_table(self):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, len(self.table2show[0]))):
                # self.key_labels[line][clmn].grid_forget()
                self.key_labels[line][clmn]['text'] = ''
                if self.prev_col_btn:
                    self.key_labels[line][clmn].config(fg='black', bg=self.prev_col_btn.cget("bg"))
            # self.key_labels[line] = []


class FormDialog(TemplateDialog):

    def __init__(self, parent, input_dict, disabled=None, options=None, required_keys=None, title=None):
        def init_dict(keylist, list_attr):
            for att in list_attr:
                setattr(self, att, {key: '' for key in keylist})

        if not isinstance(input_dict, dict):
            error_str = 'Second input should be a dictionary'
            raise TypeError(error_str)
        self.input_dict = input_dict
        self.str_title = title
        init_dict(input_dict.keys(), ['key_labels', 'key_disabled', 'key_entries', 'key_opt_menu', 'options'])
        # [StringVar()]*len(input_dict) duplicate the StringVar(), a change in one will change the other one as well,
        #  not the wanted behaviour. This is the solution
        self.key_opt_var = {key: StringVar() for key in input_dict.keys()}
        self.required_keys = required_keys
        if options:
            for key in options:
                if key in self.options.keys():
                    if options[key]:
                        if not isinstance(options[key], list):
                            self.options[key] = [options[key]]
                        else:
                            self.options[key] = options[key]
        if isinstance(disabled, list):
            for key in disabled:
                    self.key_disabled[key] = DISABLED
        if not required_keys:
            self.required_keys = []
        super().__init__(parent)

    def body(self, parent):
        self.main_form(parent)
        self.ok_cancel_button(parent, row=len(self.input_dict))
        self.results = self.input_dict

    def main_form(self, parent):
        if isinstance(self.str_title, str):
            self.title(self.str_title)
        else:
            self.title('Please fill up the form')
        for cnt, key in enumerate(self.input_dict.keys()):
            if key in self.required_keys:
                color = 'red'
            else:
                color = 'black'
            self.key_labels[key] = Label(parent, text=key, fg=color)
            self.key_labels[key].grid(row=cnt, sticky=W, padx=self.default_pad[0], pady=self.default_pad[1])
            if self.key_disabled[key]:
                self.key_entries[key] = Label(parent, text=self.input_dict[key])
            else:
                self.key_entries[key] = Entry(parent, justify=CENTER)
                self.key_entries[key].insert(END, self.input_dict[key])
            self.key_entries[key].grid(row=cnt, column=1, sticky=W, padx=self.default_pad[0], pady=self.default_pad[1])

            if key in self.options.keys() and self.options[key]:
                self.key_opt_menu[key] = OptionMenu(parent, self.key_opt_var[key], *self.options[key],
                                                    command=lambda opt, k=key: self.update_entry(opt, k))
                self.key_opt_menu[key].config(width=self.key_entries[key]['width'])
                self.key_opt_menu[key].grid(row=cnt, column=2, sticky=W+E, padx=self.default_pad[0],
                                            pady=self.default_pad[1])

    def update_entry(self, idx, key):
        self.key_entries[key].delete(0, END)
        self.key_entries[key].insert(0, idx)

    def ok(self, event=None):
        self.results = {key: self.input_dict[key] for key in self.input_dict.keys()}
        for key in self.input_dict.keys():
            if isinstance(self.key_entries[key], Entry):
                self.results[key] = self.key_entries[key].get()
        self.destroy()


class BidsBrickDialog(FormDialog):
    bidsdataset = None
    meta_brick = None

    def __init__(self, parent, input_dict, disabled=None, options=None, required_keys=None, title=None, flag_process=False):
        if not isinstance(input_dict, (bids.BidsBrick, bids.BidsJSON)):
            raise TypeError('Second input should be a BidsBrick instance.')
        if isinstance(input_dict, (bids.BidsDataset, bids.Data2Import)):
            BidsBrickDialog.meta_brick = input_dict.classname()  # meta_brick is either bids.BidsDataset or bids.Data2Import
            self.attr_dict = input_dict['DatasetDescJSON']
            self.input_dict = dict()
            if not flag_process:
                self.input_dict['Subject'] = input_dict['Subject']
                self.input_dict['Derivatives'] = input_dict['Derivatives']
            else:
                self.input_dict['SubjectProcess'] = input_dict['SubjectProcess']
            title = input_dict.classname() + ': ' + input_dict['DatasetDescJSON']['Name']
            if disabled is None:
                disabled = []
            if isinstance(input_dict, bids.BidsDataset):
                BidsBrickDialog.bidsdataset = input_dict
                self.input_dict['ParticipantsTSV'] = input_dict['ParticipantsTSV']
                disabled = input_dict.keylist
                disabled += self.attr_dict.keylist
        elif isinstance(input_dict, bids.BidsJSON):
            self.attr_dict = input_dict
            self.input_dict = dict()
        else:
            self.attr_dict = input_dict.get_attributes()
            self.input_dict = input_dict
            if isinstance(input_dict, bids.Subject):
                title = 'Subject: ' + input_dict['sub']
            else:
                title = os.path.basename(input_dict['fileLoc'])
        self.main_brick = input_dict
        self.key_button_lbl = {key: '' for key in self.input_dict.keys()
                               if key in bids.BidsBrick.get_list_subclasses_names() +
                               bids.BidsSidecar.get_list_subclasses_names()}
        self.key_listw = {key: '' for key in self.input_dict.keys()
                          if key in bids.BidsBrick.get_list_subclasses_names() +
                          bids.BidsSidecar.get_list_subclasses_names()}
        self.key_button = {key: '' for key in self.input_dict.keys()
                           if key in bids.BidsBrick.get_list_subclasses_names() +
                           bids.BidsSidecar.get_list_subclasses_names()}
        # # [StringVar()]*len(input_dict) duplicate the StringVar(), a change in one will change the other one as well,
        # #  not the wanted behaviour. This is the solution
        # self.key_opt_var = {key: StringVar() for key in input_dict.keys()}
        super().__init__(parent, input_dict=self.attr_dict, options=options,
                         required_keys=input_dict.required_keys, disabled=disabled, title=title)

    def body(self, parent):
        self.main_form(parent)
        cnt_tot = len(self.input_dict)
        # remember input_dict corresponds only to the attributes
        for cnt, key in enumerate(self.key_button_lbl.keys()):
            if key not in bids.BidsSidecar.get_list_subclasses_names() and not self.main_brick[key]:
                # only show none empty BidsBricks but let the JSON and TSV in case you want to add more
                continue

            setting_list = {"row": cnt + cnt_tot, "column": 1, "columnspan": 2, "sticky": W + E,
                            "padx": self.default_pad[0],
                            "pady": self.default_pad[1]}
            setting_label = {"row": cnt + cnt_tot, "sticky": W, "padx": self.default_pad[0],
                             "pady": self.default_pad[1]}
            # if key == 'Subject':
            #     # increase subject list layout length
            #     setting_list['rowspan'] = 6
            #     setting_label['rowspan'] = 6
            #     cnt_tot += setting_list['rowspan'] - 1
            self.key_button_lbl[key] = Label(parent, text=key, fg="black")
            self.key_button_lbl[key].grid(**setting_label)
            if key == 'Subject':
                ht = 8
            elif key in bids.BidsSidecar.get_list_subclasses_names():
                ht = 1
            else:
                ht = 3
            if isinstance(self.main_brick, (bids.ModalityType, bids.GlobalSidecars)):
                setting_list['columnspan'] = 1
            self.key_listw[key] = Listbox(parent, height=ht)
            self.key_listw[key].bind('<Double-Button-1>', lambda event, k=key: self.open_new_window(k, event))
            self.key_listw[key].bind('<Return>', lambda event, k=key: self.open_new_window(k, event))
            self.populate_list(self.key_listw[key], self.main_brick[key])
            self.key_listw[key].grid(**setting_list)

            # if key not in bids.BidsSidecar.get_list_subclasses_names() and \
            #         (key not in self.key_disabled or not self.key_disabled[key] == DISABLED):
            if key not in self.key_disabled or not self.key_disabled[key] == DISABLED:
                if key in bids.BidsSidecar.get_list_subclasses_names():
                    btn_str = 'Modify '
                else:
                    btn_str = 'Add '
                self.key_button[key] = Button(parent, text=btn_str + key, justify=CENTER,
                                              command=lambda k=key: self.add_new_brick(k))
                self.key_button[key].grid(row=cnt+cnt_tot, column=3, sticky=W+E, padx=self.default_pad[0],
                                          pady=self.default_pad[1])
        self.ok_cancel_button(parent, row=cnt_tot+len(self.key_button_lbl))
        if len(self.key_button_lbl):
            for i in range(self.body_widget.grid_size()[0]):
                self.body_widget.grid_columnconfigure(i, weight=1, uniform='test')
        self.results = self.input_dict

    @staticmethod
    def populate_list(list_obj, list_of_bbricks):
        list_obj.delete(0, END)
        if not list_of_bbricks:
            return
        list_of_elmts = []
        if isinstance(list_of_bbricks, (bids.ParticipantsTSV, bids.SrcDataTrack)):
            list_of_elmts.append(list_of_bbricks.filename)
        elif isinstance(list_of_bbricks, bids.BidsSidecar):
            list_of_elmts.append(list_of_bbricks.modality_field + list_of_bbricks.extension)
        elif isinstance(list_of_bbricks[0], (bids.ModalityType, bids.GlobalSidecars)):
            for mod_brick in list_of_bbricks:
                list_of_elmts.append(os.path.basename(mod_brick['fileLoc']))
        elif isinstance(list_of_bbricks[0], bids.Subject):
            for sub in list_of_bbricks:
                list_of_elmts.append(sub['sub'])
        elif isinstance(list_of_bbricks[0], bids.Derivatives):
            for ppln in list_of_bbricks[0]['Pipeline']:
                list_of_elmts.append(ppln['name'])
        elif isinstance(list_of_bbricks[0], bids.Scans):
            for scan in list_of_bbricks:
                list_of_elmts.append(scan['fileLoc'])
        else:
            raise TypeError('not allowed object type')
        BidsManager.populate_list(list_obj, list_of_elmts)

    def open_new_window(self, key, event):
        if not self.key_listw[key].curselection():
            return
        curr_idx = self.key_listw[key].curselection()[0]
        if key == 'Subject' or key == 'SubjectProcess':
            sub = self.main_brick[key][curr_idx]
            if 'Subject' in self.key_disabled:
                disabl = sub.keylist
            else:
                disabl = None
            BidsBrickDialog(self, sub, disabled=disabl,
                            title=sub.classname() + ': ' + sub['sub'])
        elif key == 'Derivatives':
            pip = self.main_brick[key][0]['Pipeline'][curr_idx]
            if 'Derivatives' in self.key_disabled:
                disabl = pip.keylist
            else:
                disabl = None
            BidsBrickDialog(self, pip, disabled=disabl,
                            title=pip.classname() + ': ' + pip['name'], flag_process=True)
        elif key == 'Scans':
            sdcr_file = self.main_brick['Scans'][curr_idx]['ScansTSV']
            title=None
            BidsTSVDialog(self, sdcr_file, title=title).apply()
        elif key in bids.BidsJSON.get_list_subclasses_names():
            sdcr_file = self.main_brick[key]
            # pop_menu = Menu(self.body_widget, tearoff=0)
            # pop_menu.post(event.x_root, event.y_root)
            BidsBrickDialog(self, sdcr_file, disabled=list(sdcr_file.keys()),
                            title=sdcr_file.classname())
        elif key in bids.ModalityType.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
            mod_brick = self.main_brick[key][curr_idx]
            fname = mod_brick['fileLoc']
            pop_menu = Menu(self.body_widget, tearoff=0)
            if not mod_brick['modality'] in ['electrodes', 'coordsystem']:
                pop_menu.add_command(label='Open file',
                                     command=lambda f=fname: self.open_file(f))
            if mod_brick.classname() in self.key_disabled:
                disbl = mod_brick.keylist
            else:
                disbl = [key for key in mod_brick.keylist if key in bids.BidsTSV.get_list_subclasses_names()]
                # pop_menu.add_command(label='Remove',
                #                      command=lambda idx=curr_idx, k=key: self.remove_element(k, idx))
            pop_menu.add_command(label='Show attributes',
                                 command=lambda brick=mod_brick, dsbl=disbl: BidsBrickDialog(self, brick,
                                                                                             disabled=dsbl))
            if BidsBrickDialog.meta_brick == 'BidsDataset':  # allow remove file in bidsdataset
                pop_menu.add_command(label='Remove file',
                                     command=lambda brick=mod_brick, idx=curr_idx, k=key:
                                     self.remove_file(brick, k, idx))
            pop_menu.post(event.x_root, event.y_root)
        elif key in bids.BidsTSV.get_list_subclasses_names():
            sdcr_file = self.main_brick[key]
            title = None
            if isinstance(self.main_brick, bids.ModalityType):
                title = os.path.splitext(os.path.basename(self.main_brick['fileLoc']).replace(
                    self.main_brick['modality'], self.main_brick[key].modality_field))[0]
            sdcr_file_new = BidsTSVDialog(self, sdcr_file, title=title).apply()

            if sdcr_file_new and not sdcr_file_new == sdcr_file:
                sdcr_file.clear()
                sdcr_file.copy_values(sdcr_file_new)
                filename, dirname, ext = self.main_brick.create_filename_from_attributes()
                if sdcr_file_new.modality_field:
                    fname = filename.replace(self.main_brick['modality'],
                                             sdcr_file.modality_field)
                else:
                    fname = filename
                fname2bewritten = os.path.join(bids.BidsDataset.dirname, dirname, fname +
                                               sdcr_file_new.extension)
                sdcr_file.write_file(fname2bewritten)
                self.main_brick.write_log(fname + ' was modified.')
        else:
            print('coucou')

    @staticmethod
    def open_file(fname):
        os.startfile(os.path.normpath(os.path.join(bids.BidsBrick.cwdir, fname)))

    def remove_file(self, mod_brick, key, index):
        if BidsBrickDialog.meta_brick == 'BidsDataset' and \
                messagebox.askyesno('Remove File', 'Are you sure you want to remove ' + mod_brick['fileLoc'] + '?'):
            self.config(cursor="wait")
            BidsBrickDialog.bidsdataset.remove(mod_brick, with_issues=True)
            BidsBrickDialog.bidsdataset.check_requirements(specif_subs=mod_brick['sub'])
            self.populate_list(self.key_listw[key], self.main_brick[key])
            self.config(cursor="")

    # def remove_element(self, key, index):
    #     self.populate_list(self.key_listw[key], self.main_brick[key])

    def add_new_brick(self, key):
        self.update_fields()
        opt = None
        disbld = ['sub', 'fileLoc']
        try:
            if isinstance(self.main_brick, (bids.BidsDataset, bids.Data2Import)):
                messagebox.showerror('Not implemented', "Not implemented for now.")
                return
            elif isinstance(self.main_brick, bids.Subject):

                flag, miss_str = self.main_brick.has_all_req_attributes(nested=False)
                if not flag:
                    messagebox.showerror('Incomplete subject', miss_str)
                    return
                if key in bids.GlobalSidecars.get_list_subclasses_names():
                    fname = filedialog.askopenfilename(title='Please select a file',
                                                       filetypes=[
                                                           ('sidecar', "*.tsv;*.json"),
                                                           ('photo', "*" + ";*".join(bids.Photo.allowed_file_formats))],
                                                       initialdir=bids.BidsBrick.cwdir)
                elif key in bids.Imagery.get_list_subclasses_names():
                    fname = filedialog.askdirectory(title='Please select a file', initialdir=bids.BidsBrick.cwdir)
                else:
                    file_formats = [formt for formt in getattr(bids, key).readable_file_formats
                                    if formt not in getattr(bids, key).allowed_file_formats]
                    fname = filedialog.askopenfilename(title='Please select a file',
                                                       filetypes=[(key, "*" + ";*".join(file_formats))],
                                                       initialdir=bids.BidsBrick.cwdir)

                if not fname:
                    return
                if not os.path.normpath(os.path.dirname(fname)) == os.path.normpath(bids.BidsBrick.cwdir):
                    messagebox.showerror('File not in data2import folder', "File should be in " + bids.BidsBrick.cwdir
                                         + ".")
                    return
                if key in bids.GlobalSidecars.get_list_subclasses_names():
                    new_brick = getattr(bids, key)(fname)
                    disbld.append('modality')
                else:
                    new_brick = getattr(bids, key)()
                    new_brick['fileLoc'] = os.path.basename(fname)
                    if bids.BidsDataset.requirements:
                        # use requirements.json to propose via drop down menu
                        opt = bids.BidsDataset.requirements.make_option_dict(key)
                    else:
                        opt = dict()
                        opt['modalities'] = new_brick.allowed_modalities

                new_brick['sub'] = self.main_brick['sub']
            elif isinstance(self.main_brick, bids.ModalityType) and key in bids.BidsSidecar.get_list_subclasses_names():
                new_brick = getattr(bids, key)()
                if key in bids.BidsJSON.get_list_subclasses_names():
                    new_brick['FileComment'] = bids.BidsJSON.bids_default_unknown
                elif key in bids.BidsTSV.get_list_subclasses_names():
                    raise NotImplementedError('Modification of TSV files has not yet being handled ')
                    # new_brick.append({key: bids.BidsSidecar.bids_default_unknown for key in new_brick.header})
                new_brick.copy_values(self.main_brick[key], simplify_flag=False)
            else:
                new_brick = getattr(bids, key)()
            result_brick = BidsBrickDialog(self, new_brick, disabled=disbld, options=opt,
                                           required_keys=new_brick.required_keys, title=new_brick.classname()).apply()
            if result_brick is not None:
                new_brick.copy_values(result_brick)
                # still issue with JSON since has_all_req_attributes does not return anything... but updates
                # self.is_complete
                flag, miss_str = new_brick.has_all_req_attributes()
                if not isinstance(new_brick, (bids.BidsJSON, bids.BidsTSV)) and not flag:
                    messagebox.showerror('Missing attributes', miss_str)
                    return
                self.main_brick[key] = new_brick
                self.populate_list(self.key_listw[key], self.main_brick[key])
        except Exception as err:
            messagebox.showerror('Error Occurred!', str(err))

    def update_fields(self):
        for key in self.key_entries.keys():
            if isinstance(self.main_brick, (bids.BidsDataset, bids.Data2Import)):
                if isinstance(self.key_entries[key], Entry) and not \
                        self.key_entries[key].get() == self.main_brick['DatasetDescJSON'][key]:
                    self.main_brick['DatasetDescJSON'][key] = self.key_entries[key].get()
            else:
                if isinstance(self.key_entries[key], Entry) and not self.key_entries[key].get() == self.main_brick[key]:
                    self.main_brick[key] = self.key_entries[key].get()


class BidsSelectDialog(TemplateDialog):
    bidsdataset = None
    select_subject = None
    subject_list = {'SubjectToAnalyse': []}

    def __init__(self, parent, input_dict, analysis_dict=None):
        self.vars = {}
        if isinstance(input_dict, bids.BidsDataset):
            BidsSelectDialog.bidsdataset = input_dict
        elif analysis_dict and not isinstance(analysis_dict, pip.Analysis):
            raise TypeError('Third input should be a pipeline analysis')
        else:
            raise TypeError('Second input should be a bids dataset')
        ses_type = []
        task_type = []
        self.subject_dict =dict()
        #self.param_dict =dict()
        for sub in BidsSelectDialog.bidsdataset['Subject']:
            for mod in sub:
                if mod and mod in bids.ModalityType.get_list_subclasses_names():
                    for elt in sub[mod]:
                        try:
                            if elt['ses'] and not elt['ses'] == '':
                                ses_type.append(elt['ses'])
                            if elt['task'] and not elt['task'] == '':
                                task_type.append(elt['task'])
                        except:
                            pass
        ses_type = list(set(ses_type))
        task_type = list(set(task_type))
        self.required_criteria = {'ses': ses_type, 'task': task_type}

        self.participants = BidsSelectDialog.bidsdataset['ParticipantsTSV']
        self.display_dict, self.vars = self.select_criteria(self.participants)

        self.subject_dict['Subject'] = []
        for sub in BidsSelectDialog.bidsdataset['Subject']:
            self.subject_dict['Subject'].append(sub['sub'])
        self.key_label = {key: '' for key in self.display_dict.keys()}
        self.req_label = {key: '' for key in self.required_criteria.keys()}

        #self.vars = [value for key, value in self.display_dict.items()]
        self.vars_req = {'IntVar_'+key: value for key, value in self.required_criteria.items()}

        if analysis_dict:
            self.software = analysis_dict
            self.param_dict, self.param_vars = self.software.select_parameter_analysis()

        super().__init__(parent)

    def select_criteria(self, participant_dict):

        def check_numerical_value(element):
            is_numerical = False
            punctuation = ',.?!:'
            temp = element.translate(str.maketrans('', '', punctuation))
            temp = temp.strip('YymM ')
            if temp.isnumeric():
                is_numerical = True
            return is_numerical

        display_dict = dict()
        req_keys = self.bidsdataset.requirements['Requirements']['Subject']['keys']
        for key, value in req_keys.items():
            if value:
                display_dict[key] = value
            elif 'age' in key:
                display_dict[key] = value
            elif 'duration' in key:
                display_dict[key] = value
        criteria = participant_dict.header
        key_list = display_dict.keys()

        var_dict = dict()
        key_to_remove = []

        for key in key_list:
            idx = criteria.index(key)
            is_string = False
            display_value = []
            for val_part in participant_dict[1::]:
                is_number = check_numerical_value(val_part[idx])
                if is_number and display_dict[key]:
                    display_value.append(val_part[idx])
                elif is_number:
                    display_value.append('min_' + key)
                    display_value.append('max_' + key)
                    is_string = True
                else:
                    l_elt = val_part[idx].split(', ')
                    for l in l_elt:
                        display_value.append(l)
            display_value = list(set(display_value))
            if is_string:
                display_value = sorted(display_value, reverse=True)
                var_dict['StringVar_' + key] = [value for value in display_value]
            elif display_value:
                display_value = list(set(display_value).intersection(set(display_dict[key])))
                if len(display_value) == 1 and not 'n/a' in display_value:
                    var_dict['Label_'+key] = [value for value in display_value]
                elif len(display_value) > 1:
                    var_dict['Variable_' + key] = [value for value in display_value]
                else:
                    key_to_remove.append(key)

        for key in key_to_remove:
            del display_dict[key]

        return display_dict, var_dict

    def body(self, parent):
        def enable(frame, state):
            for child in frame.winfo_children():
                try:
                    child.configure(state=state)
                except:
                    pass

        def enable_frame(frame, button):
            button_value = button.get()
            if button_value == 1:
                enable(frame, 'normal')
            elif button_value == 0:
                enable(frame, 'disabled')

        self.title('Select Subjects and parameters')
        self.All_sub = IntVar()
        self.Id_sub = IntVar()
        self.Crit_sub = IntVar()
        All_sub_butt = Checkbutton(parent, text='All subjects', variable=self.All_sub)
        All_sub_butt.grid(row=0, column=0, sticky=W+E)
        Id_sub_butt = Checkbutton(parent, text='Select subject(s) Id(s)', variable=self.Id_sub, command=lambda: enable_frame(Frame_list, self.Id_sub))
        Id_sub_butt.grid(row=0, column=1, sticky=W+E)
        Crit_sub_butt = Checkbutton(parent, text='Select subjects by criteria', variable=self.Crit_sub, command=lambda: enable_frame(Frame_criteria, self.Crit_sub))
        Crit_sub_butt.grid(row=0, column=2, sticky=W+E)
        Frame_list = Frame(parent, relief=GROOVE, borderwidth=2)
        Frame_req_criteria = Frame(parent, relief=GROOVE, borderwidth=2)
        Label(Frame_req_criteria, text='Select required criteria:').grid(row=0)
        Frame_criteria = Frame(parent, relief=GROOVE, borderwidth=2)
        Label(Frame_criteria, text='Select criteria for multiple subjects analysis:').grid(row=0)

        #Subject list
        self.subject = Label(Frame_list, text='Subject')
        self.subject.grid(row=0, sticky=W)
        list_choice = Variable(Frame_list, self.subject_dict['Subject'])
        self.select_subject = Listbox(Frame_list, listvariable=list_choice, selectmode=MULTIPLE)
        self.select_subject.grid(row=1, column=1, sticky=W + E)

        #Criteria to select subjects
        max_crit, cntC = self.create_button(Frame_criteria, self.key_label,  self.vars)

        #Required criteria for all option
        max_req, cntR = self.create_button(Frame_req_criteria, self.req_label, self.vars_req)

        #place the frame
        Frame_req_criteria.grid(row=1, column=1, rowspan=cntR, columnspan=max_req)
        Frame_list.grid(row=1, column=0, columnspan=1, rowspan=cntR + cntC)
        enable(Frame_list, 'disabled')
        Frame_criteria.grid(row=2, column=1, rowspan=cntC, columnspan=max_crit)
        enable(Frame_criteria, 'disabled')

        if self.param_dict:
            Frame_analysis = Frame(parent, relief=GROOVE, borderwidth=2)
            Label(Frame_analysis, text='Select analysis parameters:').grid(row=0)
            max_param, cntP = self.create_button(Frame_analysis, self.param_dict, self.param_vars)
            col_p = max(max_crit, max_req)
            length = max(cntC, cntP+cntR)
            Frame_analysis.grid(row=0, column=col_p+1, rowspan=length, columnspan=max_param)

        self.ok_cancel_button(parent, row=cntR+cntC+1)

    def ok(self):
        self.results, self.sub_criteria = self.get_the_subject_id()
        self.software.get_analysis_value(self.param_vars, self.results)
        self.destroy()

    def get_the_subject_id(self):

        def get_subject_list_from_criteria(bids_dialog, input_dict, subject_list):
            for elt in bids_dialog.participants[1::]:
                elt_in = []
                for key, value in input_dict.items():
                    idx_key = bids_dialog.participants.header.index(key)
                    if isinstance(value, range):
                        elt[idx_key] = elt[idx_key].replace(',', '.')
                        age_p = round(float(elt[idx_key].rstrip('YyMm ')))
                        if age_p in value:
                            elt_in.append(True)
                    elif isinstance(value, list):
                        for val in value:
                            if val in elt[idx_key]:
                                elt_in.append(True)
                            else:
                                elt_in.append(False)
                    elif isinstance(value, str):
                        if value in elt[idx_key]:
                            elt_in.append(True)
                        else:
                            elt_in.append(False)
                elt_in = list(set(elt_in))
                if len(elt_in) == 1 and elt_in[0] is True:
                    subject_list.append(elt[0])

        subject_list = []
        res_dict = dict()
        if self.All_sub.get():
            subject_list = self.subject_dict['Subject']
        elif self.Id_sub.get():
            for index in self.select_subject.curselection():
                subject_list.append(self.select_subject.get(index))
        elif self.Crit_sub.get():
            for var in self.vars.keys():
                isntype = var.split('_')
                clef_size = len(isntype[0]) + 1
                key = var[clef_size::]
                if isntype[0] == 'Variable':
                    for id_var in self.vars[var]:
                        if id_var.get():
                            try:
                                res_dict[key].append(id_var._name)
                            except:
                                res_dict[key] = []
                                res_dict[key].append(id_var._name)
                elif isntype[0] == 'StringVar':
                    num_value = False
                    for id_var in self.vars[var]:
                        if id_var.get().isalnum():
                            if id_var._name.startswith('min'):
                                minA = int(id_var.get())
                            elif id_var._name.startswith('max'):
                                maxA = int(id_var.get())
                            num_value = True
                    if num_value:
                        res_dict[key] = range(minA, maxA)
                elif isntype[0] == 'IntVar':
                    for id_var in self.vars[var]:
                        if id_var.get():
                            try:
                                res_dict[key].append(id_var._name)
                            except:
                                res_dict[key] = []
                                res_dict[key].append(id_var._name)
            get_subject_list_from_criteria(self, res_dict, subject_list)

        ses_list = []
        task_list = []
        for var in self.vars_req:
            isntype = var.split('_')
            clef_size = len(isntype[0]) + 1
            key = var[clef_size::]
            if isntype[0] == 'IntVar':
                for id_var in self.vars_req[var]:
                    if id_var.get() and key == 'ses':
                        ses_list.append(id_var._name)
                    elif id_var.get() and key == 'task':
                        task_list.append(id_var._name)

        resultats = {'sub': subject_list, 'ses': ses_list, 'task': task_list}

        return resultats, res_dict

    def create_button(self, frame, label_d, var_d):
        max_col = 1
        for cnt, key in enumerate(label_d):
            label_d[key] = Label(frame, text=key)
            label_d[key].grid(row=cnt+1, sticky=W)
            for clef in var_d.keys():
                isn_type = clef.split('_')
                taille = len(isn_type[0]) +1
                if clef[taille::] == key:
                    if isn_type[0] == 'IntVar':
                        if isinstance(var_d[clef], list):
                            idx_var = 0
                            while idx_var < len(var_d[clef]):
                                temp = var_d[clef][idx_var]
                                var_d[clef][idx_var] = IntVar()
                                var_d[clef][idx_var]._name = temp
                                l = Checkbutton(frame, text=temp, variable=var_d[clef][idx_var])
                                l.grid(row=cnt + 1, column=idx_var + 1, sticky=W + E)
                                idx_var += 1
                            max_col = max(max_col, idx_var)
                        elif isinstance(var_d[clef], str):
                            temp = var_d[clef]
                            var_d[clef] = IntVar()
                            var_d[clef]._name = temp
                            l = Checkbutton(frame, text=temp, variable=var_d[clef])
                            l.insert(END, var_d[clef]._name)
                            l.grid(row=cnt + 1, column=max_col, sticky=W + E)
                    elif isn_type[0] == 'StringVar':
                        if isinstance(var_d[clef], list):
                            idx_var = 0
                            while idx_var < len(var_d[clef]):
                                temp = var_d[clef][idx_var]
                                var_d[clef][idx_var] = StringVar()
                                var_d[clef][idx_var]._name = temp
                                l = Entry(frame, textvariable=temp)
                                l.insert(END, temp)
                                l.grid(row=cnt + 1, column=idx_var+1, sticky=W + E)
                                idx_var += 1
                            max_col = max(max_col, idx_var)
                        elif isinstance(var_d[clef], str):
                            temp = var_d[clef]
                            var_d[clef] = StringVar()
                            if len(temp.split('_')) > 1:
                                var_d[clef]._name = temp.split('_')[1]
                            else:
                                var_d[clef]._name = temp
                            l = Entry(frame, textvariable=var_d[clef]._name)
                            l.insert(END, var_d[clef]._name)
                            l.grid(row=cnt + 1, column=max_col, sticky=W + E)
                    elif isn_type[0] == 'Variable':
                        CheckbuttonList(frame, var_d[clef], row_list=cnt+1, col_list=max_col)
                    elif isn_type[0] == 'askopenfile':
                        pass
                    elif isn_type[0] == 'Bool':
                        var_d[clef] = BooleanVar()
                        var_d[clef].set(False)
                        l = Checkbutton(frame, text='True', variable=var_d[clef])
                        l.grid(row=cnt + 1, column=max_col, sticky=W + E)
                    elif isn_type[0] == 'Label':
                        l = Label(frame, text=var_d[clef])
                        l.grid(row=cnt + 1, column=max_col, sticky=W + E)

        return max_col, cnt


class RequirementsDialog(TemplateDialog):

    def __init__(self, parent, bids_dir):
        self.subject_key = ['keys', 'required_keys']
        self.info_key_label = []
        self.info_value_label = []
        self.req_button = []
        self.import_req = IntVar()
        self.create_req = IntVar()
        self.info_button = []
        self.modality_required_key = []
        self.modality_required_value = []
        self.modality_required_name = []
        self.modality_required_amount = []
        self.modality_required_button = []
        self.modality_required_label = []
        self.modality_key = []
        self.modality_value = []
        self.modality_name = []
        self.modality_button = []
        self.modality_label = []
        self.modality_list = bids.Imagery.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names()
        self.req_name=''
        self.elec_name=''
        self.imag_name=''
        self.bids_dir = bids_dir
        self.error_str=''
        super().__init__(parent)

    def ask4path(self, file_type, display=None):
        if file_type == 'req':
            self.req_name = filedialog.askopenfilename(title='Select requirements type',
                                                       filetypes=[('req.', "*.json")],
                                                       initialdir=os.path.join(os.path.dirname(__file__),
                                                                               'requirements_templates'))
            if display:
                display.delete(0,END)
                display.insert(END, self.req_name)
        elif file_type == 'elec':
            self.elec_name = filedialog.askopenfilename(title='Select converter for electrophy. data type (AnyWave)')
            if display:
                display.delete(0, END)
                display.insert(END, self.elec_name)
        elif file_type == 'imag':
            self.imag_name = filedialog.askopenfilename(title='Select converter for imagery data type (dcm2niix)')
            if display:
                display.delete(0, END)
                display.insert(END, self.imag_name)

    def body(self, parent):
        def enable(frame, state):
            for child in frame.winfo_children():
                try:
                    child.configure(state=state)
                except:
                    pass

        def enable_frames(frame, button):
            button_value = button.get()
            if button_value == 1:
                if isinstance(frame, list):
                    for fr in frame:
                        enable(fr, 'normal')
                else:
                    enable(frame, 'normal')
            elif button_value == 0:
                if isinstance(frame, list):
                    for fr in frame:
                        enable(fr, 'disabled')
                else:
                    enable(frame, 'disabled')

        self.geometry('1600x800')
        smallfont = font.Font(family="Segoe UI", size=9)
        self.option_add('*Font', smallfont)
        placement = Frame(parent)
        toolbar = Frame(placement)
        import_req_button = Checkbutton(placement, text='Select your Requirements', variable=self.import_req, command=lambda: enable_frames(toolbar, self.import_req))
        import_req_button.pack(side=LEFT)
        entry_path = Entry(toolbar, state=DISABLED)
        req_path = Button(toolbar, text='Filename path', command=lambda: self.ask4path(file_type='req', display=entry_path), state=DISABLED)
        req_path.pack(side=LEFT)
        entry_path.pack(side=LEFT)
        toolbar.pack(side=LEFT)
        placement.pack(side=TOP)
        create_req_button = Checkbutton(parent, text='Create your Requirements', variable=self.create_req, command=lambda: enable_frames([frame_subject_info.frame, frame_required.frame, frame_modality.frame], self.create_req))
        create_req_button.pack(side=TOP)

        Frame_path = Frame(parent)
        Frame_path .pack(side=LEFT, fill=BOTH)
        Label(Frame_path, text='Indicate the path of the converters').pack(side=TOP, anchor=N)

        #Scrollbar the subject's frame
        frame_subject_info = VerticalScrollbarFrame(parent)
        Label(frame_subject_info.frame, text='Indicate the subjects information you need').grid(row=0)
        Label(frame_subject_info.frame, text='Label').grid(row=1, column=0)
        Label(frame_subject_info.frame, text='Possible Values').grid(row=1, column=1)

        # Scrollbar the frame with canvas
        frame_required = VerticalScrollbarFrame(parent)
        Label(frame_required.frame, text='Indicate the modality required in the dataset').grid(row=0)

        #Scrollbar the modality's frame
        frame_modality = VerticalScrollbarFrame(parent)
        Label(frame_modality.frame, text='Indicate the different values for modality').grid(row=0)
        frame_modality.frame.pack(side=LEFT, fill=BOTH, expand=True)

        #initiate the first button
        self.subject_info_button(frame_subject_info.frame)
        l4 = Button(frame_subject_info.frame, text='+', command=lambda: self.add_lines_command(frame_subject_info.frame, canvas=frame_subject_info.canvas))
        l4.grid(row=1, column=2)
        l5 = Button(frame_subject_info.frame, text='-', command=lambda: self.remove_lines_command())
        l5.grid(row=1, column=3)
        frame_subject_info.update_scrollbar()

        #initiate the modality button
        m1 = ttk.Combobox(frame_required.frame, values=self.modality_list)
        m1.grid(row=1, column=0)
        m2 = Button(frame_required.frame, text='+', command=lambda: self.add_lines_command(frame_required.frame, canvas=frame_required.canvas, mod=self.modality_list[m1.current()], required=True))
        m2.grid(row=1, column=1)
        m5 = Button(frame_required.frame, text='-', command=lambda: self.remove_lines_command(mod=True, required=True))
        m5.grid(row=1, column=2)
        frame_required.update_scrollbar()

        m3 = ttk.Combobox(frame_modality.frame, values=self.modality_list)
        m3.grid(row=1, column=0)
        m4 = Button(frame_modality.frame, text='+', command=lambda: self.add_lines_command(frame_modality.frame, canvas=frame_modality.canvas, mod=self.modality_list[m3.current()]))
        m4.grid(row=1, column=1)
        m6 = Button(frame_modality.frame, text='-', command=lambda: self.remove_lines_command(mod=True))
        m6.grid(row=1, column=2)
        frame_modality.update_scrollbar()

        #path in frame path
        Label(Frame_path, text='Select the Electrophisiology converters').pack(anchor='w')
        entry_elec = Entry(Frame_path)
        Button(Frame_path, text='Electrophysiology converters', command=lambda: self.ask4path(file_type='elec', display=entry_elec)).pack(anchor='center')#grid(row=3)
        entry_elec.pack()
        Label(Frame_path, text='Select the Imagery converters').pack(anchor='w')
        entry_imag = Entry(Frame_path)
        Button(Frame_path, text='Imagery converters', command=lambda: self.ask4path(file_type='imag', display=entry_imag)).pack(anchor='center')#.grid(row=7)
        entry_imag.pack()

        enable(frame_subject_info.frame, 'disabled')
        enable(frame_required.frame, 'disabled')
        enable(frame_modality.frame, 'disabled')

        self.ok_cancel_button(Frame_path)

    def subject_info_button(self, parent):
        self.info_key_label.append(StringVar())
        self.info_value_label.append(StringVar())
        self.req_button.append(IntVar())
        cnt = len(self.info_key_label) + 1
        l1 = Entry(parent, textvariable=self.info_key_label[-1])
        l1.grid(row=cnt, column=0)
        self.info_button.append(l1)
        l2 = Entry(parent, textvariable=self.info_value_label[-1])
        l2.grid(row=cnt, column=1)
        self.info_button.append(l2)
        l3 = Checkbutton(parent, text='required', variable=self.req_button[-1])
        l3.grid(row=cnt, column=2)
        self.info_button.append(l3)

    def ok_cancel_button(self, parent, row=None):
        self.btn_ok = Button(parent, text='OK', command=self.ok, height=self.button_size[0],
                             width=self.button_size[1])

        self.btn_cancel = Button(parent, text='Cancel', command=self.cancel, height=self.button_size[0],
                                 width=self.button_size[1], default=ACTIVE)
        self.btn_ok.pack(side=LEFT, anchor='sw', expand=1, padx=10, pady=5)
        self.btn_cancel.pack(side=RIGHT, anchor='se', expand=1, padx=10, pady=5)

    def remove_lines_command(self, mod=False, required=False):
        if mod:
            if required:
                req = 'required_'
            else:
                req=''
            keys = eval('self.modality_'+req+'key')
            button = eval('self.modality_'+req+'button')
            name = eval('self.modality_'+req+'name')
            value = eval('self.modality_'+req+'value')
            label = eval('self.modality_'+req+'label')
            try:
                number_line = len(keys[-1])
                end_line = len(button) - 1
                idx = end_line - number_line
                while end_line > idx:
                    button[end_line].grid_forget()
                    del button[end_line]
                    end_line = end_line-1
                for key in keys[-1].keys():
                    keys[-1][key].grid_forget()
                label[-1].grid_forget()
                del keys[-1]
                del name[-1]
                del value[-1]
                del label[-1]
            except IndexError:
                messagebox.showerror('Error', 'There are no buttons to delete')
        else:
            end_button = len(self.info_button)-1
            if end_button < 0:
                messagebox.showerror('Error', 'There are no buttons to delete')
            else:
                idx = end_button - 3
                while end_button > idx:
                    self.info_button[end_button].grid_forget()
                    del self.info_button[end_button]
                    end_button = end_button - 1
                del self.info_key_label[-1]
                del self.info_value_label[-1]
                del self.req_button[-1]

    def add_lines_command(self, parent, canvas=None, mod=None, required=False):

        def number_line(list_cnt):
            number = 0
            i=0
            for elt in list_cnt:
                i = list_cnt.index(elt)+1
                number = number + i*len(elt)
            if i == 0:
                autre_num = 2
            else:
                autre_num = i + 3
            return number, autre_num

        if mod:
            key_label = eval('bids.'+mod+'.keylist')
            if required:
                line_num, init_num = number_line(self.modality_required_value)
            else:
                line_num, init_num = number_line(self.modality_value)
            required_key = {}
            required_value = {}
            for elt in key_label:
                if elt not in bids.BidsJSON.get_list_subclasses_names() + bids.BidsTSV.get_list_subclasses_names() + bids.BidsBrick.required_keys + ['fileLoc']:
                    if elt == 'modality':
                        mod_list = eval('bids.'+mod+'.allowed_modalities')
                        if required:
                            required_value[elt] = mod_list
                            required_key[elt] = ''
                    else:
                        required_value[elt] = StringVar()
                        required_key[elt] = ''
            if required:
                required_value['amount'] = StringVar()
                required_key['amount'] = ''

            lab = Label(parent, text=mod+':')
            lab.grid(row=line_num+init_num)
            for cnt, key in enumerate(required_value.keys()):
                required_key[key] = Label(parent, text=key)
                required_key[key].grid(row=line_num + cnt + init_num+1, sticky=W)
                if key == 'modality':
                    l = Listbox(parent, exportselection=0, selectmode=MULTIPLE, height=3)
                    for item in required_value[key]:
                        l.insert(END, item)
                    required_value[key] = l
                else:
                    l = Entry(parent, textvariable=required_value[key])
                l.grid(row=line_num + cnt + init_num+1, column=1)
                if required:
                    self.modality_required_button.append(l)
                else:
                    self.modality_button.append(l)
            if required:
                self.modality_required_value.append(required_value)
                self.modality_required_key.append(required_key)
                self.modality_required_name.append(mod)
                self.modality_required_label.append(lab)
            else:
                self.modality_value.append(required_value)
                self.modality_key.append(required_key)
                self.modality_name.append(mod)
                self.modality_label.append(lab)
        else:
            self.subject_info_button(parent)
        parent.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def ok(self):
        self.error_str = ''
        if not self.elec_name or 'AnyWave' not in os.path.basename(self.elec_name):
            self.error_str += 'Bids Manager requires AnyWave to convert electrophy. data. '
            pass
        if not self.imag_name or 'dcm2niix' not in os.path.basename(self.imag_name):
            self.error_str += 'Bids Manager requires dcm2niix to convert imagery data. '
            pass

        if self.import_req.get():
            if not self.req_name:
                self.error_str = 'Bids Manager requires a requirements.json file to be operational. '
            else:
                req_dict = bids.Requirements(self.req_name)
        elif self.create_req.get():
            req_dict = bids.Requirements()
            keys = {}
            required_keys = []
            for i, elt in enumerate(self.info_key_label):
                value = self.info_value_label[i].get()
                key = elt.get()
                if not key:
                    self.error_str = 'Subject"s information are missing'
                    break
                else:
                    if ' ' in key:
                        key = key.replace(' ', '_')

                if ',' not in value:
                    keys[key] = value
                else:
                    list_val = value.split(', ')
                    keys[key] = [val for val in list_val]
                if self.req_button[i].get():
                    required_keys.append(key)
            else:
                req_dict['Requirements']['Subject']['keys'] = keys
                req_dict['Requirements']['Subject']['required_keys'] = required_keys
            if not self.error_str:
                #to get the required modality for the database
                for i, mod in enumerate(self.modality_required_key):
                    if self.modality_required_name[i] not in req_dict['Requirements']['Subject'].keys():
                        req_dict['Requirements']['Subject'][self.modality_required_name[i]] = []
                    mod_dict = {}
                    type_list = []
                    type_dict = {}
                    for key in mod:
                        if isinstance(self.modality_required_value[i][key], StringVar):
                            value = self.modality_required_value[i][key].get()
                        elif isinstance(self.modality_required_value[i][key], Listbox):
                            value = [self.modality_required_value[i][key].get(ind_sel) for ind_sel in self.modality_required_value[i][key].curselection()]
                        if key == 'amount' and value:
                            mod_dict['amount'] = int(value)
                        elif value and isinstance(value, list):
                            for val in value:
                                type_dict[key] = val
                                type_list.append(deepcopy(type_dict))
                        elif value:
                            type_dict[key] = value
                    if len(type_list) > 1:
                        mod_dict['type'] = type_list
                    else:
                        mod_dict['type'] = type_dict
                    req_dict['Requirements']['Subject'][self.modality_required_name[i]].append(mod_dict)
                #To get the possible keys in modality
                for i, mod in enumerate(self.modality_name):
                    if mod not in req_dict['Requirements'].keys():
                        req_dict['Requirements'][mod] = {}
                        key_dict = {}
                    else:
                        key_dict = req_dict['Requirements'][mod]['keys']
                    for key in self.modality_key[i]:
                        value = self.modality_value[i][key].get()
                        if value:
                            if key not in key_dict.keys():
                                key_dict[key] = []
                            if ',' not in value:
                                key_dict[key].append(value)
                            else:
                                list_val = value.split(', ')
                                for val in list_val:
                                    key_dict[key].append(val)
                            key_dict[key] = list(set(key_dict[key]))
                    req_dict['Requirements'][mod]['keys'] = key_dict
        else:
            self.error_str += 'Bids Manager requires a requirements.json file to be operational. '
            pass

        if self.error_str:
            messagebox.showerror('Error', self.error_str)
        else:
            bids.BidsDataset.converters['Imagery']['path'] = self.imag_name
            req_dict['Converters']['Imagery']['path'] = self.imag_name
            req_dict['Converters']['Imagery']['ext'] = ['.nii']
            bids.BidsDataset.converters['Electrophy']['path'] = self.elec_name
            req_dict['Converters']['Electrophy']['path'] = self.elec_name
            req_dict['Converters']['Electrophy']['ext'] = ['.vhdr', '.vmrk', '.eeg']
            bids.BidsDataset.dirname = self.bids_dir
            req_dict.save_as_json()
            self.destroy()


class VerticalScrollbarFrame(Frame):

    def __init__(self, parent):
        self.Frame_to_scrollbar = Frame(parent, relief=GROOVE, borderwidth=2)
        self.Frame_to_scrollbar.pack(side=LEFT, fill=BOTH, expand=True)
        self.vsb = Scrollbar(self.Frame_to_scrollbar, orient="vertical")
        self.vsb.pack(side=RIGHT, fill=Y)
        self.canvas = Canvas(self.Frame_to_scrollbar, yscrollcommand=self.vsb.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.frame = Frame(self.canvas)#, relief=GROOVE, borderwidth=2)
        self.frame.pack()

    def update_scrollbar(self):
        def myfunction(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.canvas.create_window(0, 0, scrollregion=self.canvas.bbox("all"), window=self.frame, anchor='nw')
        self.canvas.pack()
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.vsb.configure(command=self.canvas.yview)
        self.frame.bind('<Configure>', myfunction(self.canvas))


class CheckbuttonList(Frame):
    variable_list = None

    def __init__(self, parent, variable_list, row_list, col_list):
        self.frame_button = None
        self.hidden = False
        self.test_frame = None
        self.parent = parent
        self.variable_list = variable_list
        self.frame = Frame(parent, width=150, height=25, bg='white')
        self.frame.grid(row=row_list, column=col_list)
        self.combo_entry = Entry(self.frame)
        self.combo_entry.pack(side=LEFT)
        self.create_checkbutton_list()
        self.list_button = Button(parent, text='v', command=lambda: self.call_checkbutton_list())
        self.list_button.grid(row=row_list, column=col_list+1)

    def create_checkbutton_list(self):
        self.combo_entry.toplevel = Toplevel()
        self.combo_entry.toplevel.overrideredirect(1)
        self.combo_entry.toplevel.transient()
        self.return_button = Button(self.combo_entry.toplevel, text='v', command=lambda: self.call_checkbutton_list())
        self.return_button.pack(side=TOP, anchor='ne')
        self.frame_button = VerticalScrollbarFrame(self.combo_entry.toplevel)
        self.frame_button.update_scrollbar()

        idx_var = 0
        while idx_var < len(self.variable_list):
            temp = self.variable_list[idx_var]
            self.variable_list[idx_var] = IntVar()
            self.variable_list[idx_var]._name = temp
            l = Checkbutton(self.frame_button.frame, text=temp, variable=self.variable_list[idx_var])
            l.grid(row=idx_var, sticky=W + E)
            idx_var += 1
        self.frame_button.frame.update_idletasks()
        self.frame_button.canvas.config(scrollregion=self.frame_button.canvas.bbox("all"))
        self.combo_entry.toplevel.withdraw()

    def call_checkbutton_list(self):
        but_width = self.return_button.winfo_reqwidth()
        self.combo_entry.toplevel.geometry("%dx%d+%d+%d" % (self.combo_entry.winfo_reqwidth()+but_width, 125, self.combo_entry.winfo_rootx(),
                             self.combo_entry.winfo_rooty()))
        if not self.hidden:
            self.hidden =True
            self.combo_entry.toplevel.deiconify()
            self.combo_entry.toplevel.grab_set()
        else:
            self.hidden = False
            self.combo_entry.toplevel.withdraw()
            self.parent.master.master.grab_set()


def make_splash():
    if bids.BidsBrick.curr_user == 'Ponz':
        splash = [r" _______  .-./`)  ______        .-'''-.",
                  r"\  ____  \\ .-.')|    _ `''.   / _     \ ",
                  r"| |    \ |/ `-' \| _ | ) _  \ (`' )/`--' ",
                  r"| |____/ / `-'`-`|( ''_'  ) |(_ o _). ",
                  r"|   _ _ '. .---. | . (_) `. | (_,_). '. ",
                  r"|  ( ' )  \|   | |(_    ._) '.---.  \  :",
                  r"| (_{;}_) ||   | |  (_.\.' / \    `-'  |",
                  r"|  (_,_)  /|   | |       .'   \       /",
                  r"/_______.' '---' '-----'`      `-...-'",
                  r",---.    ,---.   ____    ,---.   .--.   ____      .-_'''-.       .-''-.  .-------. ",
                  r"|    \  /    | .'  __ `. |    \  |  | .'  __ `.  '_( )_   \    .'_ _   \ |  _ _   \ ",
                  r"|  ,  \/  ,  |/   '  \  \|  ,  \ |  |/   '  \  \|(_ o _)|  '  / ( ` )   '| ( ' )  |",
                  r"|  |\_   /|  ||___|  /  ||  |\_ \|  ||___|  /  |. (_,_)/___| . (_ o _)  ||(_ o _) /",
                  r"|  _( )_/ |  |   _.-`   ||  _( )_\  |   _.-`   ||  |  .-----.|  (_,_)___|| (_,_).' __",
                  r"| (_ o _) |  |.'   _    || (_ o _)  |.'   _    |'  \  '-   .''  \   .---.|  |\ \  |  | ",
                  r"|  (_,_)  |  ||  _( )_  ||  (_,_)\  ||  _( )_  | \  `-'`   |  \  `-'    /|  | \ `'   /",
                  r"|  |      |  |\ (_ o _) /|  |    |  |\ (_ o _) /  \        /   \       / |  |  \    /",
                  r"'--'      '--' '.(_,_).' '--'    '--' '.(_,_).'    `'-...-'     `'-..-'  ''-'   `'-'"]
    else:
        splash = [r" ____  _     _               _,---._",
                  r"| __ )(_) __| |___         /'  ,`.  `\ ",
                  r"|  _ \| |/ _` / __|       /'`,,'   ;   )",
                  r"| |_) | | (_| \__ \      (_   ;  ,-,---'",
                  r"|____/|_|\__,_|___/       (;;,,;/--'",
                  r"                           \;;;/",
                  r" _    _                      /",
                  r"|  \/  | __ _ _ __   __ _  __ _  ___ _ __",
                  r"| |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|",
                  r"| |  | | (_| | | | | (_| | (_| |  __/ |",
                  r"|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|",
                  r"                          |___/"]

    return splash


if __name__ == '__main__':
    from time import sleep

    splsh = make_splash()
    for line in splsh:
        print(line)
        sleep(0.05)
    sleep(0.2)
    root = Tk()
    root.option_add("*Font", "10")
    my_gui = BidsManager()
    root.protocol("WM_DELETE_WINDOW", my_gui.close_window)
    if platform.system() == 'Windows':
        root.state("zoomed")
    elif platform.system() == 'Linux':
        root.attributes('-zoomed', True)
    # MyDialog(root)
    # The following three commands are needed so the window pops
    # up on top on Windows...
    # root.iconify()
    # root.update()
    # root.deiconify()
    root.mainloop()
