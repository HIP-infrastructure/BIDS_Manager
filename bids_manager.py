#!/usr/bin/python3

import ins_bids_class as bids
import os
import platform
from tkinter import Tk, Menu, messagebox, filedialog, Frame, Listbox, scrolledtext, simpledialog, Toplevel, \
    Label, Button, Entry, StringVar, BooleanVar, IntVar, DISABLED, NORMAL, END, W, E, INSERT, BOTH, X, Y, RIGHT, LEFT,\
    TOP, BOTTOM, BROWSE, SINGLE, MULTIPLE, EXTENDED, ACTIVE, RIDGE, Scrollbar, CENTER, OptionMenu


class BidsManager(Frame):
    version = '0.1.1'
    bids_startfile = 'D:\\roehri\\BIDs\\small_2048_test'
    import_startfile = 'D:\\roehri\\BIDs\\Temp_2048'

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
        # settings_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label="BIDS", underline=0, menu=bids_menu)
        menu_bar.add_cascade(label="Uploader", underline=0, menu=uploader_menu)
        menu_bar.add_cascade(label="Issues", underline=0, menu=issue_menu)

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
        if not str2show.endswith('\n'):
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
        results = BidsBrickDialog(root, self.curr_data2import, disabled=None,
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
        self.make_idle('Parsing BIDS directory.')
        self.curr_bids._assign_bids_dir(self.curr_bids.dirname)
        try:
            if self.curr_bids:
                self.curr_bids.parse_bids()
                self.update_text(self.curr_bids.curr_log)
                self.pack_element(self.main_frame['text'])
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

    @staticmethod
    def show_bids_desc(input_dict):

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
                if not output_dict == temp_dict and \
                        messagebox.askyesno('Change ' + input_dict.__class__.filename + '?',
                                            'You are about to modify ' + input_dict.__class__.filename +
                                            '.\nAre you sure?'):
                    input_dict.copy_values(output_dict)
                    input_dict.write_file()

    @staticmethod
    def change_menu_state(menu, start_idx=0, end_idx=None, state=None):
        if state is None or state not in [NORMAL, DISABLED]:
            state = NORMAL
        if end_idx is None:
            end_idx = menu.index(END)
        if end_idx > menu.index(END):
            raise IndexError('End index is out of range (' + str(end_idx) + '>' + str(menu.index(END)) + ').')
        if start_idx > end_idx:
            raise IndexError('Start index greater than the end index (' + str(start_idx) + '>' + str(end_idx) + ').')
        for i in range(start_idx, end_idx+1):
            menu.entryconfigure(i, state=state)

    def ask4bidsdir(self, isnew_dir=False):
        """Either set (isnew_dir = False) or create Bids directory (isnew_dir=True)"""

        def create_new_bidsdataset(bids_dir):
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
            req_fname = filedialog.askopenfilename(title='Select requirements type',
                                                   filetypes=[('req.', "*.json")],
                                                   initialdir=os.path.join(os.path.dirname(__file__),
                                                                           'requirements_templates'))
            if not req_fname:
                error_str += 'Bids Manager requires a requirements.json file to be operational.'
                return error_str
            req_dict = bids.Requirements(req_fname)
            # set the converter paths (read path should be handled in a future release)
            fname = filedialog.askopenfilename(title='Select converter for imagery data type (dcm2niix)')
            if not fname or 'dcm2niix' not in os.path.basename(fname):
                error_str += 'Bids Manager requires dcm2niix to convert imagery data.'
                return error_str
            bids.BidsDataset.converters['Imagery']['path'] = fname
            req_dict['Converters']['Imagery']['path'] = fname
            fname = filedialog.askopenfilename(title='Select converter for electrophy. data type (AnyWave)')
            if not fname or 'AnyWave' not in os.path.basename(fname):
                error_str += 'Bids Manager requires AnyWave to convert electrophy. data.'
                return error_str
            bids.BidsDataset.converters['Electrophy']['path'] = fname
            req_dict['Converters']['Electrophy']['path'] = fname
            bids.BidsDataset.dirname = bids_dir
            datasetdesc.write_file()
            req_dict.save_as_json()

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
        self.pack_element(self.main_frame['text'])
        self.upload_dir = None
        self.curr_data2import = None
        if self.curr_bids:
            self.curr_bids.access.delete_file()
            self.curr_bids = None
        if isnew_dir:
            # if new bids directory than create dataset_desc.json and but the requirements in code
            error_str = create_new_bidsdataset(bids_dir)
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
        self.bids_menu.entryconfigure(5, command=lambda: self.show_bids_desc(self.curr_bids['DatasetDescJSON']))
        self.bids_menu.entryconfigure(6, command=self.explore_bids_dataset)
        # enable selection of upload directory
        self.change_menu_state(self.uploader_menu, end_idx=0)
        # enable all issue sub-menu
        self.change_menu_state(self.issue_menu)
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
            os.startfile(os.path.join(self.curr_bids.dirname, curr_iss['fileLoc']))
        else:
            os.startfile(os.path.join(curr_iss['path'], info['Element']['fileLoc']))

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

    @staticmethod
    def make_table(table):
        string_table = ''
        for line in table:
            string_table += '\t'.join(line) + '\n'

        return string_table


class DoubleListbox:
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


class DefaultText(scrolledtext.ScrolledText):

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


class TemplateDialog(Toplevel):
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
        self.wm_resizable(False, False)
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
    bln_color = {'True': 'green', 'False': 'red', True: 'green', False: 'red', 'good': 'green', 'bad': 'red'}

    def __init__(self, parent, tsv_table, title=None):
        if not isinstance(tsv_table, bids.BidsTSV) or len(tsv_table) == 1:
            error_str = 'Second input should be a non empty BidsTSV instance'
            messagebox.showerror('Wrong input', error_str)
            return
        self.idx = 0
        self.str_title = title
        self.orig_order = [line[0] for line in tsv_table[1:]]
        self.main_brick = type(tsv_table)()  # copy the table  so reordering does not affect BidsTSV
        self.main_brick.copy_values(tsv_table)
        self.n_lines = len(tsv_table) - 1
        self.n_columns = len(tsv_table.header)
        self.key_button = {key: '' for key in tsv_table.header}
        self.next_btn = None
        self.prev_btn = None
        self.max_lines = min(self.n_lines, self.max_lines)
        self.key_labels = [[] for k in range(0, self.max_lines)]
        self.n_pages = round(self.n_lines / self.max_lines)
        self.page_label_var = StringVar()
        self.page_label = None
        self.clmn_width = 0
        self.row_height = 0
        self.table2show = tsv_table[1:self.max_lines + 1]
        super().__init__(parent)

    def body(self, parent):
        self.make_header(parent)
        self.make_table(parent)
        self.page_label = Label(parent, textvariable=self.page_label_var)
        self.page_label.grid(row=self.max_lines+1, column=0, columnspan=self.n_columns-2, sticky=W+E)
        if not self.n_pages == 1:
            self.prev_btn = Button(parent, text='Previous', state=DISABLED,
                                   command=lambda prnt=parent, stp=-1: self.change_page(prnt, stp))
            self.prev_btn.grid(row=self.max_lines + 1, column=self.n_columns - 2, sticky=W + E)
            self.next_btn = Button(parent, text='Next', command=lambda prnt=parent, stp=1: self.change_page(prnt, stp))
            self.next_btn.grid(row=self.max_lines+1, column=self.n_columns-1, sticky=W+E)
            self.update_page_number()
        self.ok_cancel_button(parent, row=self.max_lines+2)
        # for i in range(self.max_lines):
        #     self.body_widget.grid_rowconfigure(i, weight=1, uniform='test')

    def make_header(self, parent):
        for cnt, key in enumerate(self.key_button):
            self.key_button[key] = Button(parent, text=key, command=lambda k=key, prnt=parent: self.reorder(k, prnt))
            self.key_button[key].grid(row=0, column=cnt, sticky=W+E)

    def make_table(self, parent):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, self.n_columns):
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
            for clmn in range(0, self.n_columns):
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
        if end_idx > self.n_lines+1:
            end_idx = self.n_lines+1
        self.table2show = [line for line in self.main_brick[start_idx:end_idx]]
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
            for clmn in range(0, self.n_columns):
                # self.key_labels[line][clmn].grid_forget()
                self.key_labels[line][clmn]['text'] = ''
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

    def __init__(self, parent, input_dict, disabled=None, options=None, required_keys=None, title=None):
        if not isinstance(input_dict, (bids.BidsBrick, bids.BidsJSON)):
            raise TypeError('Second input should be a BidsBrick instance.')
        if isinstance(input_dict, (bids.BidsDataset, bids.Data2Import)):
            if isinstance(input_dict, bids.BidsDataset):
                BidsBrickDialog.bidsdataset = input_dict
            self.attr_dict = input_dict['DatasetDescJSON']
            self.input_dict = dict()
            self.input_dict['Subject'] = input_dict['Subject']
            title = input_dict.classname() + ': ' + input_dict['DatasetDescJSON']['Name']
            if disabled is None:
                disabled = []
            if isinstance(input_dict, bids.BidsDataset):
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
        for cnt, key in enumerate(self.key_button_lbl.keys()):
            self.key_button_lbl[key] = Label(parent, text=key, fg="black")
            self.key_button_lbl[key].grid(row=cnt+cnt_tot, sticky=W, padx=self.default_pad[0], pady=self.default_pad[1])
            self.key_listw[key] = Listbox(parent, height=3)
            self.key_listw[key].bind('<Double-Button-1>', lambda event, k=key: self.open_new_window(k, event))
            self.key_listw[key].bind('<Return>', lambda event, k=key: self.open_new_window(k, event))
            self.populate_list(self.key_listw[key], self.main_brick[key])
            self.key_listw[key].grid(row=cnt + cnt_tot, column=1, columnspan=2, sticky=W+E, padx=self.default_pad[0],
                                     pady=self.default_pad[1])
            if key not in bids.BidsSidecar.get_list_subclasses_names() and \
                    (key not in self.key_disabled or not self.key_disabled[key] == DISABLED):
                self.key_button[key] = Button(parent, text='Add ' + key, justify=CENTER,
                                              command=lambda k=key: self.add_new_brick(k))
                self.key_button[key].grid(row=cnt+cnt_tot, column=3, sticky=W+E, padx=self.default_pad[0],
                                          pady=self.default_pad[1])
            # self.key_button[key] = Button(parent, text='Add ' + key, justify=CENTER,
            #                               command=lambda: print('coucou'))
            # self.key_button[key].grid(row=cnt + cnt_tot, column=3, sticky=W+E, padx=5, pady=5)
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
        else:
            raise TypeError('not allowed object type')
        BidsManager.populate_list(list_obj, list_of_elmts)

    def open_new_window(self, key, event):
        if not self.key_listw[key].curselection():
            return
        curr_idx = self.key_listw[key].curselection()[0]
        if key == 'Subject':
            sub = self.main_brick[key][curr_idx]
            if 'Subject' in self.key_disabled:
                disabl = sub.keylist
            else:
                disabl = None
            BidsBrickDialog(self, sub, disabled=disabl,
                            title=sub.classname() + ': ' + sub['sub'])
        elif key in bids.BidsJSON.get_list_subclasses_names():
            sdcr_file = self.main_brick[key]
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
                disbl = None
                # pop_menu.add_command(label='Remove',
                #                      command=lambda idx=curr_idx, k=key: self.remove_element(k, idx))
            pop_menu.add_command(label='Show attributes',
                                 command=lambda brick=mod_brick, dsbl=disbl: BidsBrickDialog(self, brick,
                                                                                             disabled=dsbl))
            if isinstance(BidsBrickDialog.bidsdataset, bids.BidsDataset):  # allow remove file in bidsdataset
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
        os.startfile(os.path.join(bids.BidsBrick.cwdir, fname))

    def remove_file(self, mod_brick, key, index):
        if isinstance(BidsBrickDialog.bidsdataset, bids.BidsDataset) and \
                messagebox.askyesno('Remove File', 'Are you sure you want to remove ' + mod_brick['fileLoc'] + '?'):
            BidsBrickDialog.bidsdataset.remove(mod_brick, with_issues=True)
            self.populate_list(self.key_listw[key], self.main_brick[key])

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
                    opt = dict()
                    if bids.BidsDataset.requirements:
                        req = bids.BidsDataset.requirements['Requirements']
                        if 'Subject' in req and key in req['Subject']:
                            for k in new_brick.keylist:
                                if k not in bids.BidsBrick.get_list_subclasses_names() and \
                                        k not in ['sub', 'modality']:
                                    opt[k] = set()
                                    for elmt in req['Subject'][key]:
                                        if isinstance(elmt['type'], list):
                                            [opt[k].add(l[k]) for l in elmt['type'] if k in l and not l[k] == '_']
                                        elif k in elmt['type'] and not elmt['type'][k] == '_':
                                            opt[k].add(elmt['type'][k])
                                    opt[k] = list(opt[k])
                    opt['modality'] = new_brick.allowed_modalities

                new_brick['sub'] = self.main_brick['sub']

            else:
                new_brick = getattr(bids, key)()
            result_brick = BidsBrickDialog(self, new_brick, disabled=disbld, options=opt,
                                           required_keys=new_brick.required_keys, title=new_brick.classname()).apply()
            if result_brick is not None:
                new_brick.copy_values(result_brick)
                flag, miss_str = new_brick.has_all_req_attributes()
                if not flag:
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


def make_splash():
    if bids.BidsBrick.curr_user == 'ponz':
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
