import ins_bids_class as bids
import os
from tkinter import Tk, Menu, filedialog, Frame, scrolledtext, \
    Label, Button, Entry, StringVar, BooleanVar, DISABLED, NORMAL, END, W, E, INSERT, BOTH, X, Y, RIGHT, LEFT, TOP, \
    BOTTOM


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

    def update_text(self, str2show, delete_flag=True):
        self.log_area.config(state=NORMAL)
        if delete_flag:
            self.log_area.delete(1.0, END)
        self.log_area.insert(END, str2show)
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
        print('upload')

    def print_participants_tsv(self):
        self.update_text(self.make_table(self.curr_bids['ParticipantsTSV']))

    def print_srcdata_tsv(self):
        self.update_text(self.make_table(self.curr_bids['SourceData'][-1]['SrcDataTrack']))

    def solve_issues(self):

        def make_line(issue_dict):
            formatted_line = 'Modality ' + issue_dict['modality'] + ' of subject ' + issue_dict['sub']\
                             + ' has following mismatched electrodes: ' + str(issue_dict['mismatched_electrodes'])\
                             + '.\n'
            return formatted_line

        self.update_text('')
        for line in self.curr_bids.keep_channel_issues:
            self.update_text(make_line(line), delete_flag=False)
            button1 = Button(self.log_area, text="Modify ...")
            button2 = Button(self.log_area, text="Add comment")
            flag = BooleanVar()
            button3 = Button(self.log_area, text="Next issue", command=lambda: flag.set(True))
            self.log_area.window_create(END, window=button1)
            self.log_area.window_create(END, window=button2)
            self.log_area.window_create(END, window=button3)
            self.update_text('\n\n', delete_flag=False)
            self.update()
            button3.wait_variable(flag)
            button1.configure(state=DISABLED)
            button2.configure(state=DISABLED)
            button3.configure(state=DISABLED)
            self.update()


    def onExit(self):
        self.quit()

    @staticmethod
    def make_table(table):
        string_table = ''
        for line in table:
            string_table += '\t'.join(line) + '\n'

        return string_table

root = Tk()
my_gui = BidsManager()
root.mainloop()