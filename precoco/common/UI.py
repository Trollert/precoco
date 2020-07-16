import sys
import os
from tkinter import Label, Frame, Button, Checkbutton, filedialog
from functools import partial
from lxml import html

import precoco.common.globalflags as gf
from precoco.common.UIfunctions import display_changelog, VerticalScrolledFrame, ListboxEditable, create_tool_tip
from precoco.common.elementfunctions import get_false_numbers, get_false_words, generate_final_tree, pre_cleanup
from precoco.common.miscfunctions import install_update, pre_parsing, read_user_config, is_up_to_date


class UserInterface(Frame):
    def __init__(self, master, up_to_date, version, open_dir):
        Frame.__init__(self, master)
        self.root = master
        self.root.geometry('700x800')
        self.root.title('CoCo PreProcessor UI v. ' + version)
        self.rootFrame = Frame(self.root)
        self.rootFrame.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        # misc elements
        self.up_to_date = up_to_date
        self.path_work_folder = open_dir
        self.arg_list = None
        self.filename = None
        self.dir_file = None
        self.tree = None
        self.false_numbers = None
        self.false_words = None
        self.version = version

        # layout elements
        self.FrameTopMaster = None
        self.MasterLabel = None
        self.ButtonUpdate = None
        self.ChangelogButton = None
        self.FrameNumbers = None
        self.ListboxNumbers = None
        self.FrameWords = None
        self.ListboxWords = None
        self.FrameChecks = None
        self.CheckboxBreakFondsTable = None
        self.CheckboxEmptyRows = None
        self.CheckboxFalseTextBreaks = None
        self.CheckboxFootnotes = None
        self.CheckboxHeaders = None
        self.CheckboxIndentUnorderedLists = None
        self.CheckboxRenamePics = None
        self.CheckboxSplitRowspan = None
        self.CheckboxSetUnorderedLists = None
        self.CheckboxTsdFix = None
        self.CheckboxVerticalMerge = None
        self.CheckboxSpanHeaders = None
        self.LabelFondsReport = None
        self.LabelFormatted = None
        self.FrameButtons = None
        self.FrameOptions = None
        self.ButtonGenerate = None
        self.ButtonOpen = None
        self.create_layout()

    def create_layout(self):
        ################
        # TOP Elements #
        ################
        self.FrameTopMaster = Frame(self.rootFrame, height=3)
        self.FrameTopMaster.pack(side='top', fill='x')
        self.MasterLabel = Label(self.FrameTopMaster,
                                 text='Double Click on list entry to change entry OR\n'
                                      'Navigate with ↑↓ between entries, open with ENTER',
                                 width=55, font=('Arial', 10, 'bold'))
        self.MasterLabel.pack(side='left')
        # Version control Buttons
        if not self.up_to_date:
            self.ButtonUpdate = Button(self.FrameTopMaster,
                                       text='Click here to update!',
                                       width=30,
                                       font=('Arial', 9, 'bold'),
                                       fg='red',
                                       command=install_update)
            self.ButtonUpdate.pack(side='right')
        else:
            self.ChangelogButton = Button(self.FrameTopMaster,
                                          text='Display Changelog',
                                          width=30,
                                          font=('Arial', 9),
                                          command=display_changelog)
            self.ChangelogButton.pack(side='left')

        #################
        # LIST Elements #
        #################
        # FRAME 1
        # this is not a common frame, it enables scrolling within a frame
        self.FrameNumbers = VerticalScrolledFrame(self.rootFrame,
                                                  width=150,
                                                  height=50,
                                                  borderwidth=2,
                                                  relief="groove")
        self.FrameNumbers.pack(fill='y', side='left')
        # LISTBOX 2
        # this is not a real listbox, its a frame with sublabels to enable inline editing
        self.ListboxNumbers = ListboxEditable(self.FrameNumbers, width=25)

        # FRAME 2
        # this is not a common frame, it enables scrolling within a frame
        self.FrameWords = VerticalScrolledFrame(self.rootFrame,
                                                width=250,
                                                height=50,
                                                borderwidth=2,
                                                relief="groove")
        self.FrameWords.pack(fill='y', side='left', expand=True)
        # LISTBOX 2
        # this is not a real listbox, its a frame with sublabels to enable inline editing
        self.ListboxWords = ListboxEditable(self.FrameWords, popup_menu=True, width=45)

        #####################
        # OPTIONS / BUTTONS #
        #####################

        self.FrameOptions = Frame(self.rootFrame, width=25)
        self.FrameOptions.pack(side='left', fill='y')

        #####################
        # CHECKBOX ELEMENTS #
        #####################

        self.FrameChecks = Frame(self.FrameOptions, width=25)
        self.FrameChecks.pack(fill='y', side='top')

        ####################
        #   BUTTON FRAME   #
        ####################

        self.FrameButtons = Frame(self.FrameOptions, width=25)
        self.FrameButtons.pack(side='bottom')

        ###################
        # GENERATE BUTTON #
        ###################
        arg_list = []
        self.ButtonGenerate = Button(self.FrameButtons, height=3, width=20, bd=2, fg='white', font=('Arial', 15),
                                     text='UNABLE TO\nGENERATE', command=None,
                                     bg='dark red')
        self.ButtonGenerate.pack(side='bottom')

        ###############
        # OPEN BUTTON #
        ###############
        self.ButtonOpen = Button(self.FrameButtons, height=1, width=20, bd=2, fg='white', font=('Arial', 15),
                                 text='OPEN FILE', command=self.open_file,
                                 bg='dark turquoise')
        self.ButtonOpen.pack(side='bottom')

    def change_work_path(self, path):
        self.path_work_folder = path

    def open_file(self):
        self.filename = filedialog.askopenfilename(initialdir=self.path_work_folder, title="Select file",
                                                   filetypes=(("HTML files", "*.htm"), ("all files", "*.*")))
        self.dir_file = os.path.dirname(self.filename)
        self.root.title('CoCo PreProcessor UI v. ' + self.version + ' - ' + self.filename)
        gf.error_log.clear()
        if not self.filename: sys.exit()
        pre_parsing(self.filename)
        self.preprocess_file(self.filename)

    def preprocess_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as file_input:
            self.tree = html.parse(file_input)
        self.tree = pre_cleanup(self.tree)
        self.false_words = get_false_words(self.tree, self.dir_file)
        self.false_numbers = get_false_numbers(self.tree, self.dir_file)
        self.generate_checkboxes()
        self.update_lists()
        self.enable_generate_button()

    def generate_checkboxes(self):
        self.FrameChecks.destroy()
        self.FrameChecks = Frame(self.FrameOptions, width=25)
        self.FrameChecks.pack(fill='y', side='top')

        self.CheckboxHeaders = Checkbutton(self.FrameChecks, anchor='w', text='detect headers',
                                           variable=gf.b_set_headers)
        self.CheckboxFootnotes = Checkbutton(self.FrameChecks, anchor='w', text='detect footnotes',
                                             variable=gf.b_set_footnotes)
        self.CheckboxEmptyRows = Checkbutton(self.FrameChecks, anchor='w', text='remove empty rows',
                                             variable=gf.b_remove_empty_rows)
        self.CheckboxFalseTextBreaks = Checkbutton(self.FrameChecks, anchor='w', text='remove false text breaks',
                                                   variable=gf.b_remove_false_text_breaks)
        self.CheckboxVerticalMerge = Checkbutton(self.FrameChecks, anchor='w', text='vertically merge tables',
                                                 variable=gf.b_merge_tables_vertically)
        self.CheckboxRenamePics = Checkbutton(self.FrameChecks, anchor='w', text='rename .png to .jpg',
                                              variable=gf.b_rename_pics)
        self.CheckboxSplitRowspan = Checkbutton(self.FrameChecks, anchor='w', text='split row span',
                                                variable=gf.b_split_rowspan)
        self.CheckboxSetUnorderedLists = Checkbutton(self.FrameChecks, anchor='w', text='detect unordered lists',
                                                     variable=gf.b_set_unordered_lists)
        self.CheckboxIndentUnorderedLists = Checkbutton(self.FrameChecks, anchor='w', text='indent unordered lists?',
                                                        variable=gf.b_indent_unordered_list)

        self.CheckboxHeaders.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxHeaders, 'detect table headers and set them accordingly')
        self.CheckboxFootnotes.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxFootnotes, 'detect footnote tables and set anchors')
        self.CheckboxEmptyRows.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxEmptyRows, 'remove all empty table rows')
        self.CheckboxFalseTextBreaks.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxFalseTextBreaks, 'remove mid-sentence text breaks (e.g. when a sentence spans 2 pdf pages)')
        self.CheckboxVerticalMerge.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxVerticalMerge, 'merges tables vertically if §§ markers are set properly and column numbers are identical ')
        self.CheckboxRenamePics.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxRenamePics, 'renames saved pictures from .png to .jpg and changes the parts in the html-file')
        self.CheckboxSplitRowspan.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxSplitRowspan, 'splits vertically merged cells and moves content to top cell. works properly with colspan etc.')
        self.CheckboxSetUnorderedLists.pack(side='top', anchor='w')
        create_tool_tip(self.CheckboxSetUnorderedLists, 'detect lists and sets them to unordered lists')
        self.CheckboxIndentUnorderedLists.pack(side='top')
        create_tool_tip(self.CheckboxIndentUnorderedLists, 'detects eventually indented elements in above lists and indents them')
        if gf.flag_is_formatted:
            self.LabelFormatted = Label(self.FrameChecks, text='Formatted report detected', font=('Arial', 9, 'bold'),
                                        fg='red')
            self.LabelFormatted.pack(side='top')
            self.CheckboxSpanHeaders = Checkbutton(self.FrameChecks, anchor='w', text='analyze heading (BETA)',
                                                   variable=gf.b_span_headings)
            self.CheckboxSpanHeaders.pack(side='top', anchor='w')
            create_tool_tip(self.CheckboxSpanHeaders,
                            'analyzes headings depending on fontsize and occurrence. ONLY FOR FORMATTED HTML files')

        if gf.b_fonds_report.get():
            self.LabelFondsReport = Label(self.FrameChecks, text='Fonds report detected', font=('Arial', 9, 'bold'),
                                          fg='red')
            self.LabelFondsReport.pack(side='top')
            self.CheckboxTsdFix = Checkbutton(self.FrameChecks, anchor='w', text='fix tsd separators',
                                              variable=gf.b_fix_tsd_separators)
            self.CheckboxBreakFondsTable = Checkbutton(self.FrameChecks, anchor='w', text='break Vermögensaufstellung',
                                                       variable=gf.b_break_fonds_table)
            self.CheckboxTsdFix.pack(side='top', anchor='w')
            create_tool_tip(self.CheckboxTsdFix,
                            'fixes falsely separated numbers in cell, which follow this pattern: 1 234 123.124241')
            self.CheckboxBreakFondsTable.pack(side='top', anchor='w')
            create_tool_tip(self.CheckboxBreakFondsTable,
                            'only for fonds-reports that need you to insert "shift+enter" breaks in the first column and header of the "Vermögensaufstellungs"-table')

    def update_lists(self):
        self.ListboxNumbers.clear_list()
        self.ListboxNumbers.update_list(self.false_numbers)
        self.ListboxNumbers.placeListBoxEditable()
        self.ListboxWords.clear_list()
        self.ListboxWords.update_list(self.false_words)
        self.ListboxWords.placeListBoxEditable()

    def enable_generate_button(self):
        self.arg_list = [self.tree, self.false_numbers, self.false_words, self.ListboxNumbers, self.ListboxWords,
                         self.filename]
        self.ButtonGenerate['text'] = 'GENERATE FILE \n AND QUIT'
        self.ButtonGenerate['bg'] = 'dark green'
        self.ButtonGenerate['command'] = partial(generate_final_tree, self.arg_list)


def create_ui(up_to_date, version, open_dir):
    tk = gf.tk
    app = UserInterface(tk, up_to_date, version, open_dir)
    tk.mainloop()


def run():
    """
    This is the main function to call to start the UI and process the inserted .htm-file.
    It only provides the control sequence, not the underlying logic. Refer to the submodules for that
    """
    # first check the local version of PreCoCo and read the config file if present
    path_directory_reports, _local_version_ = read_user_config()
    # check version and get new updater if out of date
    flag_up_to_date = is_up_to_date(_local_version_)

    create_ui(flag_up_to_date, _local_version_, path_directory_reports)


if __name__ == '__main__':
    run()
