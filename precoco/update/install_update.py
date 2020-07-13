import zipfile
import shutil

with zipfile.ZipFile('update.zip', 'r') as zip_ref:
    zip_ref.extractall('../..')

zip_path = '../../precoco-master'
for file in zip_path.glob('*.*'):
    shutil.copy(zip_path, '../..')

shutil.rmtree('../../precoco-master')