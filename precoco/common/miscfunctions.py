import configparser
import os
import sys
import subprocess
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError
from tkinter import filedialog, messagebox
from dateutil import parser
import re
import pickle
from precoco.common.globalflags import root_dir

Config = configparser.ConfigParser()


def edit_user_config(key, option, value):
    """
    edits user_config.ini when provided with key, option, value
    creates new section/option if none is found
    :param key: string in CAPS
    :param option: string
    :param value: string
    :return: None
    """
    path_config = root_dir + '/data/user_config.ini'
    if os.path.exists(path_config):
        Config.read(path_config)
        if not Config.has_section(key):
            Config[key] = {}
        Config[key][option] = value
        with open(path_config, 'w') as configfile:
            Config.write(configfile)


def read_user_config():
    """
    This function checks whether a user config .ini-file is already present which contains:
        - the path to the work folder
        - the current version of PreCoCo
    if none is found it the user can specify the work folder and current version number is pulled from github
    :return: tuple (work folder path, version number)
    """
    path_config = root_dir + '/data/user_config.ini'
    if os.path.exists(path_config):
        Config.read(path_config)
        path_folder_user = Config['PATHS']['opening_dir']
        _local_version_ = Config['VERSION']['precoco_version']
    else:
        messagebox.showinfo('Info', 'Choose your folder to be opened at startup now!')
        Config['PATHS'] = {}
        Config['PATHS']['opening_dir'] = filedialog.askdirectory(title='Choose the directory to open when using PreCoco!')
        path_folder_user = Config['PATHS']['opening_dir']
        Config['VERSION'] = {}
        Config['VERSION']['precoco_version'], _local_version_ = '0.0', '0.0'
        with open(path_config, 'w') as configfile:
            Config.write(configfile)
    return path_folder_user, _local_version_


def is_up_to_date(_local_version_):
    """
    compares the passed local version to the global version on github
    :param _local_version_: string
    :return: bool if up to date
    """
    try:
        _global_version_ = urlopen('https://raw.githubusercontent.com/Trollert/precoco/master/__version__.txt').read().decode('utf-8')
    except URLError:
        messagebox.showwarning('No network connection',
                               "Couldn't check the current PreCoCo version. \n Check your internet connection! \n Proceed with current version!")
        return True

    if _global_version_ != _local_version_:
        return False
    else:
        return True


def install_update():
    """
    pulls the new updater from github to the passed working directory
    :param path: directory of update.py
    :return: None
    """
    # cwed = os.getcwd()
    # print(cwed)
    subprocess.Popen(['python', os.getcwd()+'/install_precoco.py'])
    sys.exit()
    # urlretrieve('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py', filename=path)
    # urlretrieve('https://github.com/Trollert/precoco/archive/master.zip', filename=path)


# configure german for dateutil parser
class GermanParserInfo(parser.parserinfo):
    WEEKDAYS = [("Mo.", "Montag"),
                ("Di.", "Dienstag"),
                ("Mi.", "Mittwoch"),
                ("Do.", "Donnerstag"),
                ("Fr.", "Freitag"),
                ("Sa.", "Samstag"),
                ("So.", "Sonntag")]
    MONTHS = [("Jan.", "Januar"),
              ("Feb.", "Februar"),
              ("März", "März"),
              ("Apr.", "April"),
              ("Mai", "Mai"),
              ("Jun.", "Juni"),
              ("Jul.", "Juli"),
              ("Aug.", "August"),
              ("Sept.", "September"),
              ("Okt.", "Oktober"),
              ("Nov.", "November"),
              ("Dez.", "Dezember")]


def is_date(date_input, ignore_whitespace=False):
    """
    accepts a string which is evaluated whether it represents a date
    :param date_input: str
    :param ignore_whitespace: bool
    :return: bool
    """
    try:
        if not ignore_whitespace:
            parser.parse(date_input, parserinfo=GermanParserInfo())
        else:
            date_input = re.sub('\s', '', date_input)
            parser.parse(date_input, parserinfo=GermanParserInfo())
        return True
    # TODO: catch exceptions properly
    except:
        return False


# save repl_dict to report folder with name
def save_replacements(repl_dict, name, path_report):
    if os.path.exists(path_report + name):
        save_file = open(path_report + name, 'rb')
        old_dict = pickle.load(save_file)
        repl_dict = {**old_dict, **repl_dict}
        save_file.close()
    save_file = open(path_report + name, 'wb')
    pickle.dump(repl_dict, save_file)
    save_file.close()


# this is to split a list in sublists with chunks of consecutive data from the inserted list
def split_non_consecutive(data):
    consec_list = []
    inner_list = []
    for i in range(len(data)):
        if i == 0:
            inner_list = [data[i]]
        elif data[i] == data[i-1] + 1:
            inner_list.append(data[i])
        else:
            consec_list.append(inner_list.copy())
            inner_list.clear()
            inner_list = [data[i]]
    else:
        consec_list.append(inner_list.copy())
    return consec_list


def pre_parsing(filename):
    with open(filename, 'r', encoding='UTF-8') as file_input:
        htm_text = file_input.read()
        htm_text = htm_text.replace('CO2', 'CO<sub>2</sub>')
        htm_text = htm_text.replace('–', '-')
        htm_text = htm_text.replace('—', '-')  # replaces en dash with normal dash
        htm_text = htm_text.replace('&nbsp;', ' ')  # replaces non breaking spaces
    with open(filename, 'w', encoding='UTF-8') as file_input:
        file_input.write(htm_text)


