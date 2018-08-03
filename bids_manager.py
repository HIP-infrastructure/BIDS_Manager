#!/usr/bin/python3

import ins_bids_class as bids
import os
import platform
from tkinter import Tk, Menu, messagebox, filedialog, Frame, Listbox, scrolledtext, simpledialog, Toplevel, \
    Label, Button, Entry, StringVar, BooleanVar, IntVar, DISABLED, NORMAL, END, W, E, INSERT, BOTH, X, Y, RIGHT, LEFT,\
    TOP, BOTTOM, BROWSE, SINGLE, MULTIPLE, EXTENDED, ACTIVE, RIDGE, Scrollbar, CENTER, OptionMenu


class BidsManager(Frame):
    version = '0.0.1'

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
        bids_menu.add_command(label='Show dataset_description.json', state=DISABLED)
        bids_menu.add_command(label='Show participants.tsv', state=DISABLED)
        bids_menu.add_command(label='Show source_data_trace.tsv', state=DISABLED)
        # fill up the upload/import menu
        uploader_menu.add_command(label='Set Upload directory', command=self.ask4upload_dir)
        uploader_menu.add_command(label='Import', command=self.import_data, state=DISABLED)
        # fill up the issue menu
        issue_menu.add_command(label='Solve importation issues',
                               command=lambda: self.solve_issues(bids.Issue.keylist[0]))
        issue_menu.add_command(label='Solve channel issues', command=lambda: self.solve_issues(bids.Issue.keylist[1]))
        # settings_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label="BIDS", underline=0, menu=bids_menu)
        menu_bar.add_cascade(label="Uploader", underline=0, menu=uploader_menu)
        menu_bar.add_cascade(label="Issues", underline=0, menu=issue_menu)

        # area to print logs
        self.main_frame['text'] = DisplayText(master=self.master)

        # area to print lists
        self.main_frame['list'] = Listbox(master=self.master, font=("Arial", 12))

        # area to print double linked list
        self.main_frame['double_list'] = IssueList(self.master, self.apply_actions, self.save_actions,
                                                   self.delete_actions)

        # little band to print small infos
        self.info_label = StringVar()
        self.info_band = Label(self.master, textvariable=self.info_label, bg="blue", fg="white", font=("Arial", 15))
        self.info_band.pack(fill=X, side=TOP)

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
        self.main_frame['text'].update_text(str2show, delete_flag=delete_flag, location=location)

    def save_actions(self):
        self.curr_bids.issues.save_as_json()
        info_str = 'Actions were save for another session in the log folder of the current BIDS directory'
        self.curr_bids.write_log(info_str)
        messagebox.showinfo('Save actions', info_str)

    def apply_actions(self):
        print('actions applied (To be implemented!)')

    def delete_actions(self):
        flag = messagebox.askyesno('DELETE All Actions', 'Are you sure you want to DELETE all chosen actions?')
        if flag:
            for issue in self.curr_bids.issues['ChannelIssue']:
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
    def enable_menu(menu, start_idx=0, end_idx=None):
        if not end_idx:
            end_idx = menu.index(END)
        if end_idx > menu.index(END):
            raise IndexError('End index is out of range (' + str(end_idx) + '>' + str(menu.index(END)) + ').')
        if start_idx > end_idx:
            raise IndexError('Start index greater than the end index (' + str(start_idx) + '>' + str(end_idx) + ').')
        for i in range(start_idx, end_idx+1):
            menu.entryconfigure(i, state=NORMAL)

    def ask4bidsdir(self, isnew_dir=False):
        bids_dir = filedialog.askdirectory()

        if not bids_dir:
            return
        if self.curr_bids:
            self.curr_bids.clear()
        if isnew_dir:
            error_str = ''
            if os.listdir(bids_dir):
                error_str = 'The folder is not empty!'
            else:
                self.curr_bids = bids.BidsDataset(bids_dir)
                output_dict = FormDialog(root, self.curr_bids['DatasetDescJSON'],
                                         required_keys=bids.DatasetDescJSON.required_keys,
                                         title='Fill up the ' + bids.DatasetDescJSON.filename).apply()
                if output_dict:
                    self.curr_bids['DatasetDescJSON'].copy_values(output_dict)
                if not self.curr_bids['DatasetDescJSON'].is_complete and \
                        self.curr_bids['DatasetDescJSON']['Name'] == bids.DatasetDescJSON.bids_default_unknown:
                    error_str = bids.DatasetDescJSON.filename + ' needs at least these elements: ' +\
                                str(bids.DatasetDescJSON.required_keys) + 'to be filled.'
            if not error_str:
                self.curr_bids['DatasetDescJSON'].write_file()
            else:
                messagebox.showerror('Error', error_str)
                return
        else:
            self.info_label._default = 'Parsing BIDS directory: ' + bids_dir
            self.info_label.set(self.info_label._default)
            self.update()
            self.curr_bids = bids.BidsDataset(bids_dir)

        # enable all bids sub-menu
        self.enable_menu(self.bids_menu)
        self.bids_menu.entryconfigure(2, command=lambda: self.show_bids_desc(self.curr_bids['DatasetDescJSON']))
        self.bids_menu.entryconfigure(3, command=lambda: self.show_bids_desc(self.curr_bids['ParticipantsTSV']))
        if self.curr_bids['SourceData'] and self.curr_bids['SourceData'][-1]['SrcDataTrack']:
            self.bids_menu.entryconfigure(4, command=lambda: self.show_bids_desc(
                self.curr_bids['SourceData'][-1]['SrcDataTrack']), state=NORMAL)
        # enable all issue sub-menu
        self.enable_menu(self.issue_menu)
        self.info_label.set('Current BIDS directory: ' + bids_dir)
        self.pack_element(self.main_frame['text'])
        self.update_text(self.curr_bids.curr_log)

    def ask4upload_dir(self):
        self.pack_element(self.main_frame['text'])
        self.upload_dir = filedialog.askdirectory()
        if not self.upload_dir:
            return
        try:
            self.curr_data2import = bids.Data2Import(self.upload_dir)
            self.enable_menu(self.uploader_menu)
            self.update_text(self.curr_data2import.curr_log)

        except Exception as err:
            self.update_text(str(err))

    def print_participants_tsv(self):
        self.pack_element(self.main_frame['text'])
        self.update_text(self.make_table(self.curr_bids['ParticipantsTSV']))

    def print_srcdata_tsv(self):
        self.pack_element(self.main_frame['text'])
        if self.curr_bids['SourceData'] and self.curr_bids['SourceData'][-1]['SrcDataTrack']:
            self.update_text(self.make_table(self.curr_bids['SourceData'][-1]['SrcDataTrack']))
        else:
            self.update_text('Source Data Track does not exist')

    def do_not_import(self, list_idx, info):
        pass

    def modify_attributes(self, list_idx, info):
        pass
        # temp_dict = input_dict.__class__()
        # temp_dict.copy_values(input_dict, simplify_flag=False)
        # output_dict = FormDialog(root, temp_dict,
        #                          required_keys=input_dict.required_keys,
        #                          title='Fill up the ' + input_dict.__class__.filename).apply()

    def select_correct_name(self, list_idx, info):

        idx = info['index']
        mismtch_elec = info['MismatchedElectrode']
        curr_dict = self.curr_bids.issues['ChannelIssue'][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        action_list = self.main_frame['double_list'].elements['list2']
        results = ListDialog(self.master, curr_dict['RefElectrodes'], 'Rename ' + mismtch_elec + ' as :').apply()
        if results:
            str_info = mismtch_elec + ' has to be renamed as ' + results + ' in the files related to ' + \
                       os.path.basename(curr_dict['fileLoc']) + ' (channels.tsv, events.tsv, .vmrk and .vhdr).\n'
            curr_dict.add_action(mismtch_elec, str_info, 'To be defined')
            # self.update_text(self.curr_bids.issues.formatting(specific_issue='ChannelIssue', comment_type='action'))
            # self.populate_list(action_list, self.curr_bids.issues.formatting(specific_issue='ChannelIssue',
            #                                                                  comment_type='action'))
            action_list.delete(list_idx)
            action_list.insert(list_idx, curr_dict['Action'][-1].formatting())
            issue_list.itemconfig(list_idx, foreground='green')

    def remove_group_name(self, list_idx, info):
        idx = info['index']
        mismtch_elec = info['MismatchedElectrode']
        curr_dict = self.curr_bids.issues['ChannelIssue'][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        action_list = self.main_frame['double_list'].elements['list2']
        flag = messagebox.askyesno('Remove group name', 'Do you want to remove the group label from ' +
                                   mismtch_elec + '?')
        if flag:
            str_info = 'Remove group label for ' + mismtch_elec + ' in the channel file related to ' + \
                       os.path.basename(curr_dict['fileLoc']) + '.\n'
            # self.pack_element(self.main_frame['text'], side=LEFT, remove_previous=False)
            curr_dict.add_action(mismtch_elec, str_info, 'To be defined')
            # self.populate_list(action_list, self.curr_bids.issues.formatting(specific_issue='ChannelIssue',
            #                                                                  comment_type='action'))
            action_list.delete(list_idx)
            action_list.insert(list_idx, curr_dict['Action'][-1].formatting())
            issue_list.itemconfig(list_idx, foreground='green')

    def get_entry(self, issue_key, list_idx, info):
        idx = info['index']
        mismtch_elec = info['MismatchedElectrode']
        curr_dict = self.curr_bids.issues[issue_key][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        list_new_comments = CommentDialog(self.master, '\n'.join(curr_dict.formatting(
            comment_type='Comment', elec_name=mismtch_elec))).apply()
        if list_new_comments:
            for comment in list_new_comments:
                curr_dict.add_comment(mismtch_elec, comment)
            issue_list.itemconfig(list_idx, bg='yellow')

    def cancel_action(self, issue_key, list_idx, info):
        idx = info['index']
        mismtch_elec = info['MismatchedElectrode']
        curr_dict = self.curr_bids.issues[issue_key][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        action_list = self.main_frame['double_list'].elements['list2']
        for action in curr_dict['Action']:
            if action['label'] == mismtch_elec:
                curr_dict['Action'].pop(curr_dict['Action'].index(action))
                action_list.delete(list_idx)
                action_list.insert(list_idx, '')
                issue_list.itemconfig(list_idx, foreground='black')

    def solve_issues(self, issue_key):

        def whatto2menu(iss_key, dlb_lst, line_map, event):

            if not dlb_lst.elements['list1'].curselection():
                return
            curr_idx = dlb_lst.elements['list1'].curselection()[0]

            pop_menu = Menu(self.master, tearoff=0)
            if iss_key == 'ChannelIssue':
                pop_menu.add_command(label='Rename electrode',
                                     command=lambda: self.select_correct_name(curr_idx, line_map[curr_idx]))
                pop_menu.add_command(label='Remove group label',
                                     command=lambda: self.remove_group_name(curr_idx, line_map[curr_idx]))
            else:
                pass
            pop_menu.add_command(label='Read or add comment',
                                 command=lambda: self.get_entry(issue_key, curr_idx, line_map[curr_idx]))
            pop_menu.add_command(label='Cancel action',
                                 command=lambda: self.cancel_action(issue_key, curr_idx, line_map[curr_idx]))
            pop_menu.post(event.x_root, event.y_root)

        dlb_list = self.main_frame['double_list']
        # self.update_text(self.curr_bids.issues.formatting(specific_issue='ChannelIssue', comment_type='action'))
        # self.main_frame['list'].delete(0, END)
        dlb_list.clear_list()
        #
        # self.pack_element(self.main_frame['list'], side=TOP, remove_previous=True)
        # self.pack_element(self.main_frame['text'], side=BOTTOM, remove_previous=False)
        self.pack_element(dlb_list)

        issue_dict = self.curr_bids.issues[issue_key]
        issue_list2write = []
        action_list2write = []
        line_mapping = []
        if issue_key == bids.Issue.keylist[1]:
            for issue in issue_dict:
                for mismatch_el in issue['MismatchedElectrodes']:
                    issue_list2write.append('In file ' + os.path.basename(issue['fileLoc']) + ' of subject ' +
                                            issue['sub'] + ', ' + mismatch_el +
                                            ' does not match electrodes.tsv reference.')
                    act_str = issue.formatting(comment_type='Action', elec_name=mismatch_el)

                    line_mapping.append({'index': issue_dict.index(issue), 'MismatchedElectrode': mismatch_el,
                                         'IsComment': bool(issue.formatting(comment_type='Comment',
                                                                            elec_name=mismatch_el)),
                                         'IsAction': False})
                    if act_str:
                        action_list2write.append(act_str[0])
                        # you can write act_str[0] because there is only one action per channel
                        line_mapping[-1]['IsAction'] = True
                    else:
                        action_list2write.append('')
        elif issue_key == bids.Issue.keylist[0]:
            for issue in issue_dict:
                issue_list2write.append(issue['description'])
                act_str = issue.formatting(comment_type='Action')

                line_mapping.append({'index': issue_dict.index(issue), 'MismatchedElectrode': '',
                                     'IsComment': bool(issue.formatting(comment_type='Comment')),
                                     'IsAction': False})
                if act_str:
                    action_list2write.append(act_str[0])
                    # you can write act_str[0] because there is only one action per channel
                    line_mapping[-1]['IsAction'] = True
                else:
                    action_list2write.append('')

        self.populate_list(dlb_list.elements['list1'], issue_list2write)

        for cnt, mapping in enumerate(line_mapping):
            if mapping['IsComment']:
                dlb_list.elements['list1'].itemconfig(cnt, bg='yellow')
            if mapping['IsAction']:
                dlb_list.elements['list1'].itemconfig(cnt, foreground='green')

        self.populate_list(dlb_list.elements['list2'], action_list2write)

        self.info_label.set(self.info_label._default + '\nSelect issue from list')
        # self.main_frame['list'].bind('<Double-Button-1>', lambda event: whatto2menu(line_mapping, event))
        # self.main_frame['list'].bind('<Return>', lambda event: whatto2menu(line_mapping, event))
        dlb_list.elements['list1'].bind('<Double-Button-1>',
                                        lambda event: whatto2menu(issue_key, dlb_list, line_mapping, event))
        dlb_list.elements['list1'].bind('<Return>', lambda event: whatto2menu(issue_key, dlb_list, line_mapping, event))

        # def make_line(issue_dict):
        #     formatted_line = 'File ' + issue_dict['fileLoc'] + ' of subject ' + issue_dict['sub']\
        #                      + ' has following mismatched electrodes: ' + str(issue_dict['MismatchedElectrodes'])\
        #                      + '.\n'
        #     return formatted_line
        #
        # def make_button_line(frame, idx):
        #     btn_list = list()
        #     btn_list.append(Button(frame.log_area, text="Modify name",
        #                            command=lambda: frame.select_correct_name(idx, "here")))
        #     btn_list.append(Button(frame.log_area, text="Remove contact from group list",
        #                            command=lambda: frame.remove_group_name(idx, "here")))
        #     btn_list.append(Button(frame.log_area, text="Add comment"))
        #
        #     flg = BooleanVar()
        #     btn_list.append(Button(self.main_frame['text'], text="Next issue", command=lambda: flg.set(True)))
        #     for btn in btn_list:
        #         frame.log_area.window_create(END, window=btn)
        #     return btn_list, flg
        #
        # self.update_text('')  # empty previous page
        # for line in self.curr_bids.issues:
        #     self.update_text(make_line(line), delete_flag=False)
        #     self.main_frame['text'].mark_set("here", END)
        #     self.main_frame['text'].mark_gravity("here", direction=LEFT)
        #     button_list, flag = make_button_line(self, self.curr_bids.issues.index(line))
        #     self.update_text('\n\n', delete_flag=False)
        #     self.update()
        #     button_list[-1].wait_variable(flag)
        #     for button in button_list:
        #         button.configure(state=DISABLED)
        #     self.update()

    def import_data(self):
        try:
            self.curr_bids.import_data(self.curr_data2import)
            self.update_text(self.curr_bids.curr_log)
        except Exception as err:
            self.update_text(self.curr_bids.curr_log + str(err))

    def onExit(self):
        self.quit()

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

    def __init__(self, master, cmd_apply, cmd_save, cmd_delete):
        super().__init__(master)
        self.user_choice = None
        self.elements['apply'] = Button(master=master, text='Apply', command=cmd_apply,
                                        height=self.button_size[0], width=self.button_size[1])

        self.elements['save'] = Button(master=master, text='Save', command=cmd_save, height=self.button_size[0],
                                       width=self.button_size[1])

        self.elements['delete'] = Button(master=master, text='DELETE', command=cmd_delete, height=self.button_size[0],
                                         width=self.button_size[1], default=ACTIVE)

    def pack_elements(self):
        super().pack_elements()
        self.elements['apply'].pack(side=TOP, expand=1, padx=10, pady=5)
        self.elements['save'].pack(side=TOP, expand=1, padx=10, pady=5)
        self.elements['delete'].pack(side=TOP, expand=1, padx=10, pady=5)


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
    default_pad = [5, 5]

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
            self.btn_ok.grid(row=row, column=0, sticky=W+E, padx=10, pady=5)
            self.btn_cancel.grid(row=row, column=1, sticky=W+E, padx=10, pady=5)
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
        Label(parent, text=self.label_str).pack(expand=1, fill=BOTH, side=TOP, padx=5, pady=5)
        self.list = Listbox(parent, selectmode=self.selection_style)
        self.list.pack(expand=1, fill=BOTH, padx=5, pady=5)

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
        self.add_comment_btn = Button(parent, text='Add comment', command=self.add_new_comment,
                                      height=self.button_size[0], width=self.button_size[1])

        Label(parent, text='Previous comment(s)').pack(expand=1, fill=BOTH, side=TOP, padx=5, pady=5)

        self.read_comment_area.pack(fill=BOTH, expand=1, padx=5, pady=10, side=TOP,)
        Label(parent, text='Add new comment').pack(expand=1, fill=BOTH, side=TOP, padx=5, pady=5)
        self.add_comment_area.pack(fill=BOTH, expand=1, padx=5, pady=10, side=TOP,)

        self.add_comment_btn.pack(side=TOP, fill=X, expand=1, padx=10, pady=5)
        # add the default ok and cancel button
        self.ok_cancel_button(parent)

    def add_new_comment(self):
        new_comment = self.add_comment_area.get(1.0, END)
        if new_comment:
            if not self.results:
                self.results = []
            self.results.append(new_comment)
            self.add_comment_area.clear_text()
            self.read_comment_area.update_text(new_comment, delete_flag=False)

    def ok(self, event=None):
        self.destroy()


class FormDialog(TemplateDialog):

    def __init__(self, parent, input_dict, options=None, required_keys=None, title=None):
        if not isinstance(input_dict, dict):
            error_str = 'Second input should be a dictionary'
            raise TypeError(error_str)
        self.input_dict = input_dict
        self.str_title = title
        self.key_labels = {key: '' for key in input_dict.keys()}
        self.key_entries = {key: '' for key in input_dict.keys()}
        self.key_opt_menu = {key: '' for key in input_dict.keys()}
        # [StringVar()]*len(input_dict) duplicate the StringVar(), a change in one will change the other one as well,
        #  not the wanted behaviour. This is the solution
        self.key_opt_var = {key: StringVar() for key in input_dict.keys()}
        self.required_keys = required_keys
        self.options = options
        if not self.options:
            self.options = {key: '' for key in input_dict.keys()}
        if not required_keys:
            self.required_keys = []
        super().__init__(parent)

    def body(self, parent):
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
            self.key_labels[key].grid(row=cnt, sticky=W+E, padx=5, pady=5)
            self.key_entries[key] = Entry(parent, justify=CENTER)
            self.key_entries[key].insert(END, self.input_dict[key])
            self.key_entries[key].grid(row=cnt, column=1, sticky=W+E, padx=5, pady=5)
            if self.options[key]:
                self.key_opt_menu[key] = OptionMenu(parent, self.key_opt_var[key], *self.options[key],
                                                    command=lambda opt, k=key: self.update_entry(opt, k))
                self.key_opt_menu[key].grid(row=cnt, column=2, sticky=W+E, padx=5, pady=5)
        self.ok_cancel_button(parent, row=len(self.input_dict))
        self.results = self.input_dict

    def update_entry(self, idx, key):
        print(key)
        self.key_entries[key].delete(0, END)
        self.key_entries[key].insert(0, idx)

    def ok(self, event=None):
        self.results = {key: self.input_dict[key] for key in self.input_dict.keys()}
        for key in self.input_dict.keys():
            self.results[key] = self.key_entries[key].get()
        self.destroy()


if __name__ == '__main__':
    root = Tk()
    if platform.system() == 'Windows':
        root.state("zoomed")
    elif platform.system() == 'Linux':
        root.attributes('-zoomed', True)
    my_gui = BidsManager()
    # MyDialog(root)
    # The following three commands are needed so the window pops
    # up on top on Windows...
    # root.iconify()
    # root.update()
    # root.deiconify()
    root.mainloop()
