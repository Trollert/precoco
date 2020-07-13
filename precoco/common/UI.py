from tkinter import Label, Frame, Button, Checkbutton
import os

import precoco.common.globalflags as gf
from precoco.common.UIfunctions import display_changelog, VerticalScrolledFrame, ListboxEditable
from precoco.common.elementfunctions import get_false_numbers, get_false_words, generate_final_tree
from functools import partial

tk = gf.tk


# MASTER WINDOW
def create_ui(tree, version, file_path, up_to_date):
    folder_path = os.path.dirname(file_path)
    tk.title('CoCo PreProcessor UI v. ' + version + ' --  ' + os.path.splitext(folder_path)[0])
    tk.geometry('700x800')
    FrameTopMaster = Frame(tk, height=3)
    FrameTopMaster.pack(side='top', fill='x')
    MasterLabel = Label(FrameTopMaster,
                        text='Double Click on list entry to change entry OR\n'
                             'Navigate with ↑↓ between entries, open with ENTER',
                        width=55, font=('Arial', 10, 'bold'))
    MasterLabel.pack(side='left')
    if not up_to_date:
        VersionLabel = Label(FrameTopMaster,
                             text='New Version available!\n'
                                  'Please update with update_script!',
                             width=30, font=('Arial', 9, 'bold'), fg='red')
        VersionLabel.pack(side='right')
    else:
        ChangelogButton = Button(FrameTopMaster, text='Display Changelog', width=30, font=('Arial', 9), command=display_changelog)
        ChangelogButton.pack(side='left')

    # FRAME 1
    # this is not a common frame, it enables scrolling within a frame
    FrameNumbers = VerticalScrolledFrame(tk, width=150, height=50, borderwidth=2, relief="groove")
    FrameNumbers.pack(fill='y', side='left')
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    false_number = get_false_numbers(tree, folder_path)
    ListboxNumbers = ListboxEditable(FrameNumbers, false_number, width=25)
    ListboxNumbers.placeListBoxEditable()

    # FRAME 2
    # this is not a common frame, it enables scrolling within a frame
    FrameWords = VerticalScrolledFrame(tk, width=250, height=50, borderwidth=2, relief="groove")
    FrameWords.pack(fill='y', side='left', expand=True)
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    false_words = get_false_words(tree, folder_path)
    ListboxWords = ListboxEditable(FrameWords, false_words, popup_menu=True, width=45)
    ListboxWords.placeListBoxEditable()

    # FRAME 3
    FrameChecks = Frame(tk, width=25, height=50)
    FrameChecks.pack(fill='y', side='left')
    CheckboxHeaders = Checkbutton(FrameChecks, anchor='w', text='convert headers', variable=gf.b_set_headers)
    CheckboxFootnotes = Checkbutton(FrameChecks, anchor='w', text='convert footnotes', variable=gf.b_set_footnotes)
    CheckboxEmptyRows = Checkbutton(FrameChecks, anchor='w', text='remove empty rows', variable=gf.b_remove_empty_rows)
    CheckboxFalseTextBreaks = Checkbutton(FrameChecks, anchor='w', text='remove false text breaks', variable=gf.b_remove_false_text_breaks)
    CheckboxVerticalMerge = Checkbutton(FrameChecks, anchor='w', text='vertically merge tables (§§)',
                                        variable=gf.b_merge_tables_vertically)
    if gf.flag_is_formatted:
        CheckboxSpanHeaders = Checkbutton(FrameChecks, anchor='w', text='analyze heading (BETA)', variable=gf.b_span_headings)
    CheckboxRenamePics = Checkbutton(FrameChecks, anchor='w', text='rename .png to .jpg', variable=gf.b_rename_pics)
    CheckboxSplitRowspan = Checkbutton(FrameChecks, anchor='w', text='split row span', variable=gf.b_split_rowspan)
    CheckboxSetUnorderedLists = Checkbutton(FrameChecks, anchor='w', text='set unordered lists', variable=gf.b_set_unordered_lists)
    CheckboxIndentUnorderedLists = Checkbutton(FrameChecks, anchor='w', text='Indent unordered lists?', variable=gf.b_indent_unordered_list)

    CheckboxHeaders.pack(side='top', anchor='w')
    CheckboxFootnotes.pack(side='top', anchor='w')
    CheckboxEmptyRows.pack(side='top', anchor='w')
    CheckboxFalseTextBreaks.pack(side='top', anchor='w')
    CheckboxVerticalMerge.pack(side='top', anchor='w')
    if gf.flag_is_formatted:
        CheckboxSpanHeaders.pack(side='top', anchor='w')
    CheckboxRenamePics.pack(side='top', anchor='w')
    CheckboxSplitRowspan.pack(side='top', anchor='w')
    CheckboxSetUnorderedLists.pack(side='top', anchor='w')
    CheckboxIndentUnorderedLists.pack(side='top')

    # Sup check button
    # LabelSupCheckbox = Label(FrameChecks, text='\nSuperscript elements')
    # LabelSupCheckbox.pack(side='top', anchor='w')
    # FrameSupCheckbox = Frame(FrameChecks, width=25, height=5)
    # FrameSupCheckbox.pack(side='top')
    # CheckboxSup = Checkbutton(FrameSupCheckbox, anchor='w', variable=gf.b_sup_elements)
    # CheckboxSup.pack(side='left', anchor='w')
    # EntrySup = Entry(FrameSupCheckbox, width=23, )
    # EntrySup.insert(0, ', '.join(lSupElements))
    # EntrySup.pack(side='left')

    if gf.b_fonds_report.get():
        LabelFondsReport = Label(FrameChecks, text='Fonds report detected', font=('Arial', 9, 'bold'), fg='red')
        LabelFondsReport.pack(side='top')
        CheckboxTsdFix = Checkbutton(FrameChecks, anchor='w', text='fix tsd separators', variable=gf.b_fix_tsd_separators)
        CheckboxBreakFondsTable = Checkbutton(FrameChecks, anchor='w', text='break Vermögensaufstellung', variable=gf.b_break_fonds_table)
        CheckboxTsdFix.pack(side='top', anchor='w')
        CheckboxBreakFondsTable.pack(side='top', anchor='w')

    arg_list = [tree, false_number, false_words, ListboxNumbers.return_list(), ListboxWords.return_list(), file_path, tk]
    ButtonGenerate = Button(FrameChecks, height=3, width=20, bd=2, fg='white', font=('Arial', 15),
                            text='GENERATE FILE \n AND QUIT', command=partial(generate_final_tree, arg_list),
                            bg='dark green')
    ButtonGenerate.pack(side='bottom')
    tk.mainloop()

