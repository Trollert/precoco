import zipfile
from distutils.dir_util import copy_tree, remove_tree
import os
from urllib.request import urlopen, urlretrieve
from tkinter import messagebox
from urllib.error import URLError

if not os.path.exists('update.zip'):
    try:
        urlretrieve('https://github.com/Trollert/precoco/archive/master.zip', filename='update.zip')
    except URLError:
        messagebox.showerror('Network error', 'Could not fetch installation file. Check your network connection!')
        exit()

with zipfile.ZipFile('update.zip', 'r') as zip_ref:
    zip_ref.extractall()

zip_path = '/precoco-master'
copy_tree(zip_path, '.')
remove_tree(zip_path)