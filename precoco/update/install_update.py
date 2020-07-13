import zipfile

with zipfile.ZipFile('update.zip', 'r') as zip_ref:
    zip_ref.extractall('../..')