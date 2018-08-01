import ins_bids_class as bids
import os
import platform
from tkinter import Tk, Menu, messagebox, filedialog, Frame, Listbox, scrolledtext, simpledialog, Toplevel, \
    Label, Button, Entry, StringVar, BooleanVar, IntVar, DISABLED, NORMAL, END, W, E, INSERT, BOTH, X, Y, RIGHT, LEFT,\
    TOP, BOTTOM, BROWSE, SINGLE, MULTIPLE, EXTENDED, ACTIVE, RIDGE, Scrollbar


class BidsManager(Frame):
    version = '0.0.1'

    def __init__(self):
        super().__init__()
        self.master.title("BidsManager " + BidsManager.version)
        # self.master.geometry("1000x1000")

        self.curr_bids = None
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
        bids_menu.add_command(label='Set BIDS directory', command=self.ask4bidsdir)
        bids_menu.add_command(label='Show participants.tsv', command=self.print_participants_tsv, state="disabled")
        bids_menu.add_command(label='Show source_data_trace.tsv', command=self.print_srcdata_tsv, state="disabled")
        bids_menu.add_command(label='Solve raised issues', command=self.solve_issues, state="disabled")
        uploader_menu.add_command(label='Set Upload directory', command=self.ask4upload_dir)
        # settings_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label="BIDS", underline=0, menu=bids_menu)
        menu_bar.add_cascade(label="Uploader", underline=0, menu=uploader_menu)

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
        flag = messagebox.askyesno('Are you sure you want to DELETE all chosen actions?')
        if flag:
            for issue in self.curr_bids.issues['ChannelIssue']:
                issue['Action'] = []
            info_str = 'All actions were deleted'
            self.curr_bids.write_log(info_str)
            messagebox.showinfo('Delete actions',info_str)

    @staticmethod
    def populate_list(list_object, input_list):
        for item in input_list:
            list_object.insert(END, item)

    def ask4bidsdir(self):
        bids_dir = filedialog.askdirectory()

        if not bids_dir:
            return
        if self.curr_bids:
            self.curr_bids.clear()
        self.info_label._default = 'Parsing BIDS directory: ' + bids_dir
        self.info_label.set(self.info_label._default)
        self.update()
        self.curr_bids = bids.BidsDataset(bids_dir)
        last = self.bids_menu.index(END)
        for i in range(1, last+1):
            self.bids_menu.entryconfigure(i, state=NORMAL)
        self.info_label.set('Current BIDS directory: ' + bids_dir)
        self.pack_element(self.main_frame['text'])
        self.update_text(str(self.curr_bids.curr_log))

    def ask4upload_dir(self):
        self.pack_element(self.main_frame['text'])
        self.upload_dir = filedialog.askdirectory()

    def print_participants_tsv(self):
        self.pack_element(self.main_frame['text'])
        self.update_text(self.make_table(self.curr_bids['ParticipantsTSV']))

    def print_srcdata_tsv(self):
        self.pack_element(self.main_frame['text'])
        if self.curr_bids['SourceData'] and self.curr_bids['SourceData'][-1]['SrcDataTrack']:
            self.update_text(self.make_table(self.curr_bids['SourceData'][-1]['SrcDataTrack']))
        else:
            self.update_text('Source Data Track does not exist')

    def select_correct_name(self, list_idx, info):

        idx = info['index']
        mismtch_elec = info['MismatchedElectrode']
        curr_dict = self.curr_bids.issues['ChannelIssue'][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        action_list = self.main_frame['double_list'].elements['list2']
        results = ListDialog(self.master, curr_dict['RefElectrodes'], 'Rename ' + mismtch_elec + ' as :').apply()
        if results:
            str_info = mismtch_elec + ' has to be renamed as ' + results + ' in the files related to ' + \
                       os.path.basename(curr_dict['filepath']) + ' (channels.tsv, events.tsv, .vmrk and .vhdr).\n'
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
                       os.path.basename(curr_dict['filepath']) + '.\n'
            # self.pack_element(self.main_frame['text'], side=LEFT, remove_previous=False)
            curr_dict.add_action(mismtch_elec, str_info, 'To be defined')
            # self.populate_list(action_list, self.curr_bids.issues.formatting(specific_issue='ChannelIssue',
            #                                                                  comment_type='action'))
            action_list.delete(list_idx)
            action_list.insert(list_idx, curr_dict['Action'][-1].formatting())
            issue_list.itemconfig(list_idx, foreground='green')

    def get_entry(self, list_idx, info):
        idx = info['index']
        mismtch_elec = info['MismatchedElectrode']
        curr_dict = self.curr_bids.issues['ChannelIssue'][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        list_new_comments = CommentDialog(self.master, '\n'.join(curr_dict.formatting(
            comment_type='Comment', elec_name=mismtch_elec))).apply()
        if list_new_comments:
            for comment in list_new_comments:
                curr_dict.add_comment(mismtch_elec, comment)
            issue_list.itemconfig(list_idx, bg='yellow')

    def solve_issues(self):

        def whatto2menu(dlb_lst, line_map, event):

            if not dlb_lst.elements['list1'].curselection():
                return
            curr_idx = dlb_lst.elements['list1'].curselection()[0]

            pop_menu = Menu(self.master, tearoff=0)
            pop_menu.add_command(label='Rename electrode', command=lambda: self.select_correct_name(curr_idx,
                                                                                                    line_map[curr_idx]))
            pop_menu.add_command(label='Remove group label', command=lambda: self.remove_group_name(curr_idx,
                                                                                                    line_map[curr_idx]))
            pop_menu.add_command(label='Read or add comment', command=lambda: self.get_entry(curr_idx,
                                                                                             line_map[curr_idx]))
            pop_menu.post(event.x_root, event.y_root)

        dlb_list = self.main_frame['double_list']
        # self.update_text(self.curr_bids.issues.formatting(specific_issue='ChannelIssue', comment_type='action'))
        # self.main_frame['list'].delete(0, END)
        dlb_list.clear_list()
        #
        # self.pack_element(self.main_frame['list'], side=TOP, remove_previous=True)
        # self.pack_element(self.main_frame['text'], side=BOTTOM, remove_previous=False)
        self.pack_element(dlb_list)

        issue_dict = self.curr_bids.issues['ChannelIssue']
        issue_list2write = []
        action_list2write = []
        line_mapping = []
        for issue in issue_dict:
            for mismatch_el in issue['MismatchedElectrodes']:
                issue_list2write.append('In file ' + os.path.basename(issue['filepath']) + ' of subject ' + issue['sub'] +
                                        ', ' + mismatch_el + ' does not match electrodes.tsv reference.')
                act_str = issue.formatting(comment_type='Action', elec_name=mismatch_el)

                line_mapping.append({'index': issue_dict.index(issue), 'MismatchedElectrode': mismatch_el,
                                     'IsComment': bool(issue.formatting(comment_type='Comment', elec_name=mismatch_el)),
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
                                        lambda event: whatto2menu(dlb_list, line_mapping, event))
        dlb_list.elements['list1'].bind('<Return>', lambda event: whatto2menu(dlb_list, line_mapping, event))

        # def make_line(issue_dict):
        #     formatted_line = 'File ' + issue_dict['filepath'] + ' of subject ' + issue_dict['sub']\
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

    def __init__(self, master, cmd_apply, cmd_save, cmd_cancel):
        super().__init__(master)
        self.user_choice = None
        self.elements['apply'] = Button(master=master, text='Apply', command=cmd_apply,
                                        height=self.button_size[0], width=self.button_size[1])

        self.elements['save'] = Button(master=master, text='Save', command=cmd_save, height=self.button_size[0],
                                       width=self.button_size[1])

        self.elements['cancel'] = Button(master=master, text='Cancel', command=cmd_cancel, height=self.button_size[0],
                                         width=self.button_size[1], default=ACTIVE)

    def pack_elements(self):
        super().pack_elements()
        self.elements['apply'].pack(side=TOP, expand=1, padx=10, pady=5)
        self.elements['save'].pack(side=TOP, expand=1, padx=10, pady=5)
        self.elements['cancel'].pack(side=TOP, expand=1, padx=10, pady=5)


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

        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def body(self, parent):
        pass

    def ok_cancel_button(self, parent):
        self.btn_ok = Button(parent, text='OK', command=self.ok, height=self.button_size[0],
                             width=self.button_size[1])
        self.btn_ok.pack(side=LEFT, fill=Y, expand=1, padx=10, pady=5)
        self.btn_cancel = Button(parent, text='Cancel', command=self.cancel, height=self.button_size[0],
                                 width=self.button_size[1], default=ACTIVE)
        self.btn_cancel.pack(side=RIGHT, fill=Y, expand=1, padx=10, pady=5)

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
