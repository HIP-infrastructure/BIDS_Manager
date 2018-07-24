import ins_bids_class as bids
import os
from tkinter import Tk, Menu, messagebox, filedialog, Frame, Listbox, scrolledtext, simpledialog, Toplevel, \
    Label, Button, Entry, StringVar, BooleanVar, IntVar, DISABLED, NORMAL, END, W, E, INSERT, BOTH, X, Y, RIGHT, LEFT,\
    TOP, BOTTOM, BROWSE, SINGLE, MULTIPLE, EXTENDED, ACTIVE


class BidsManager(Frame):
    version = '0.0.1'

    def __init__(self):
        super().__init__()
        self.master.title("BidsManager " + BidsManager.version)
        self.master.geometry("1000x1000")
        menu_bar = Menu(self.master)
        self.curr_bids = None
        self.curr_import_folder = None
        self.bids_dir = None
        self.upload_dir = None
        root['menu'] = menu_bar
        # area to print logs
        self.log_area = scrolledtext.ScrolledText(master=self.master)
        self.log_area.pack(fill=BOTH, expand=1)
        self.log_area.pack(fill=BOTH, expand=1)
        # little band to print small infos
        self.info_label = StringVar()
        self.info_band = Label(self.master, textvariable=self.info_label, bg="blue", fg="white", font=("Arial", 15))
        self.info_band.pack(fill=X, side=BOTTOM)
        # settings menu
        bids_menu = Menu(menu_bar, tearoff=0)
        self.bids_menu = bids_menu
        uploader_menu = Menu(menu_bar, tearoff=0)
        self.uploader_menu = uploader_menu
        bids_menu = Menu(menu_bar, tearoff=0)
        self.bids_menu = bids_menu
        bids_menu.add_command(label='Set BIDS directory', command=self.askdir4bids)
        bids_menu.add_command(label='Show participants.tsv', command=self.print_participants_tsv, state="disabled")
        bids_menu.add_command(label='Show source_data_trace.tsv', command=self.print_srcdata_tsv, state="disabled")
        bids_menu.add_command(label='Solve raised issues', command=self.solve_issues, state="disabled")
        uploader_menu.add_command(label='Set Upload directory', command=self.askdir4upload_dir)
        # settings_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label="BIDS", underline=0, menu=bids_menu)
        menu_bar.add_cascade(label="Uploader", underline=0, menu=uploader_menu)

    def update_text(self, str2show, delete_flag=True, location=None):
        self.log_area.config(state=NORMAL)
        if delete_flag:
            self.log_area.delete(1.0, END)
        if not location:
            location = END
        self.log_area.insert(location, str2show)
        self.log_area.config(state=DISABLED)

    def askdir4bids(self):
        bids_dir = filedialog.askdirectory()

        if not bids_dir:
            return
        if self.curr_bids:
            self.curr_bids.clear()
        self.info_label.set('Parsing BIDS directory: ' + bids_dir)
        self.update()
        self.curr_bids = bids.BidsDataset(bids_dir)
        last = self.bids_menu.index(END)
        for i in range(1, last+1):
            self.bids_menu.entryconfigure(i, state=NORMAL)
        self.info_label.set('Current BIDS directory: ' + bids_dir)
        self.update_text(str(self.curr_bids.curr_log))

    def askdir4upload_dir(self):
        self.upload_dir = filedialog.askdirectory()


    def print_participants_tsv(self):
        self.update_text(self.make_table(self.curr_bids['ParticipantsTSV']))

    def print_srcdata_tsv(self):
        self.update_text(self.make_table(self.curr_bids['SourceData'][-1]['SrcDataTrack']))

    def select_correct_name(self, idx, location):

        curr_dict = self.curr_bids.keep_channel_issues[idx]
        if 'info' not in curr_dict.keys():
            curr_dict['info'] = []
        for mismtch_elec in curr_dict['mismatched_electrodes']:
            results = ListDialog(self.master, curr_dict['ref_electrodes'], 'Modify ' + mismtch_elec + ' in :').apply()
            if results:
                str_info = mismtch_elec + ' has to be renamed as ' + results + ' in the channels.tsv, events.tsv' \
                                                                               ' and in the .vhdr.\n'
                self.update_text(str_info, delete_flag=False, location=location)
                curr_dict['info'].append(str_info)

    def remove_group_name(self, idx, location):
        curr_dict = self.curr_bids.keep_channel_issues[idx]
        if 'info' not in curr_dict.keys():
            curr_dict['info'] = []
        for mismtch_elec in curr_dict['mismatched_electrodes']:
            flag = messagebox.askyesno('Remove group name', 'Do you want to remove the group label from ' +
                                       mismtch_elec + '?')
            str_info = 'Remove group label for ' + mismtch_elec + ': ' + str(flag) + '.\n'
            self.update_text(str_info, delete_flag=False, location=location)
            curr_dict['info'].append(str_info)


    def solve_issues(self):

        def make_line(issue_dict):
            formatted_line = 'File ' + issue_dict['filepath'] + ' of subject ' + issue_dict['sub']\
                             + ' has following mismatched electrodes: ' + str(issue_dict['mismatched_electrodes'])\
                             + '.\n'
            return formatted_line

        def make_button_line(frame, idx):
            btn_list = list()
            btn_list.append(Button(frame.log_area, text="Modify name",
                                   command=lambda: frame.select_correct_name(idx, "here")))
            btn_list.append(Button(frame.log_area, text="Remove contact from group list",
                                   command=lambda: frame.remove_group_name(idx, "here")))
            btn_list.append(Button(frame.log_area, text="Add comment"))

            flg = BooleanVar()
            btn_list.append(Button(self.log_area, text="Next issue", command=lambda: flg.set(True)))
            for btn in btn_list:
                frame.log_area.window_create(END, window=btn)
            return btn_list, flg

        self.update_text('')  # empty previous page
        for line in self.curr_bids.keep_channel_issues:
            self.update_text(make_line(line), delete_flag=False)
            self.log_area.mark_set("here", END)
            self.log_area.mark_gravity("here", direction=LEFT)
            button_list, flag = make_button_line(self, self.curr_bids.keep_channel_issues.index(line))
            self.update_text('\n\n', delete_flag=False)
            self.update()
            button_list[-1].wait_variable(flag)
            for button in button_list:
                button.configure(state=DISABLED)
            self.update()

    def onExit(self):
        self.quit()

    @staticmethod
    def make_table(table):
        string_table = ''
        for line in table:
            string_table += '\t'.join(line) + '\n'

        return string_table


class ListDialog(Toplevel):
    button_size = [2, 10]

    def __init__(self, parent, input_list, label_str=None, selection_style=None):
        if not selection_style:
            selection_style = BROWSE
        if not label_str:
            if selection_style in [MULTIPLE, EXTENDED]:
                label_str = 'Select element(s) from the list'
            else:
                label_str = 'Select an element from the list'
        Toplevel.__init__(self, parent)

        self.list = None
        self.btn_ok = None
        self.btn_cancel = None
        self.results = None

        self.withdraw()  # remain invisible for now
        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        self.initial_focus = None
        if parent.winfo_viewable():
            self.transient(parent)

        self.parent = parent
        body = Frame(self)
        self.list_and_button(body, input_list=input_list, label_str=label_str, selection_style=selection_style)
        body.pack(padx=5, pady=5)
        self.result = None

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

    def list_and_button(self, parent, input_list=None, label_str=None, selection_style=None):

        self.title = 'Choose from list'
        Label(parent, text=label_str).pack(expand=1, fill=BOTH, side=TOP, padx=5, pady=5)
        self.list = Listbox(parent, selectmode=selection_style)
        self.list.pack(expand=1, fill=BOTH, padx=5, pady=5)
        self.btn_ok = Button(parent, text='OK', command=self.ok, height=self.button_size[0],
                             width=self.button_size[1])
        self.btn_ok.pack(side=LEFT, expand=1, padx=10, pady=5)
        self.btn_cancel = Button(parent, text='Cancel', command=self.cancel, height=self.button_size[0],
                                 width=self.button_size[1], default=ACTIVE)
        self.btn_cancel.pack(side=RIGHT, expand=1, padx=10, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        # self.protocol("WM_DELETE_WINDOW", self.cancel)

        for item in input_list:
            self.list.insert(END, item)

        return

    def ok(self, event=None):
        if self.list.curselection():
            self.results = self.selection_get()
            self.destroy()
        else:
            self.results = None
            self.bell()

    def destroy(self):
        """Destroy the window"""
        self.initial_focus = None
        Toplevel.destroy(self)

    def cancel(self, event=None):
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

    def apply(self):
        return self.results



root = Tk()
my_gui = BidsManager()

# MyDialog(root)
# The following three commands are needed so the window pops
# up on top on Windows...
# root.iconify()
# root.update()
# root.deiconify()
root.mainloop()
