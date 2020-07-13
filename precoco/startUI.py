#!/usr/bin/env python3
import sys
import os
from tkinter import filedialog
from lxml import html
import zipfile

# custom imports
# try:
from precoco.common.elementfunctions import pre_cleanup
from precoco.common.UI import create_ui
from precoco.common.miscfunctions import read_user_config, is_up_to_date, get_update
# except ImportError:
#     urlretrieve('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py', filename=os.getcwd() + '/update_script.py')
#     messagebox.showerror('Warning', 'Some modules could not be found! \n\nUpdate manually by clicking update.py!')
#     sys.exit()


def run():
    """
    This is the main function to call to start the UI and process the inserted .htm-file.
    It only provides the control sequence, not the underlying logic. Refer to the submodules for that
    """
    # first check the local version of PreCoCo and read the config file if present
    path_directory_reports, _local_version_ = read_user_config()
    # check version and get new updater if out of date
    flag_up_to_date = is_up_to_date(_local_version_)
    if not flag_up_to_date:
        get_update()

    # ask user for file
    filename = filedialog.askopenfilename(initialdir=path_directory_reports, title="Select file", filetypes=(("HTML files", "*.htm"), ("all files", "*.*")))
    path_report = os.path.dirname(filename)
    # close script if no file was selected
    if not filename: sys.exit()

    # prepare htm file for parsing
    # todo: find a more elegant solution for preparation
    with open(filename, 'r', encoding='UTF-8') as file_input:
        htm_text = file_input.read()
        htm_text = htm_text.replace('CO2', 'CO<sub>2</sub>')
        htm_text = htm_text.replace('–', '-')
        htm_text = htm_text.replace('—', '-')  # replaces en dash with normal dash
        htm_text = htm_text.replace('&nbsp;', ' ')  # replaces non breaking spaces
    with open(filename, 'w', encoding='UTF-8') as file_input:
        file_input.write(htm_text)

    with open(filename, 'r', encoding='UTF-8') as file_input:
        tree = html.parse(file_input)
        tree = pre_cleanup(tree)

        create_ui(tree, _local_version_, filename, flag_up_to_date)


if __name__ == '__main__':
    run()
