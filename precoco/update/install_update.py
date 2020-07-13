import zipfile
from distutils.dir_util import copy_tree, remove_tree

with zipfile.ZipFile('update.zip', 'r') as zip_ref:
    zip_ref.extractall('../..')

zip_path = '../../precoco-master'
copy_tree(zip_path, '../..')
remove_tree(zip_path)