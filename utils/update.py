# Check if any file in the index has been updated based on the files found
# under the specified file path.

# USAGE: Run this file with python. It will prompt you to select the folder
# that has all your files extracted to.
# This script will overwrite the files in the data folder with the ones from
# the PCBANKS folder specified.
# NOTE: Ensure that these files are up to date, otherwise this analysis will be
# inaccurate.

__author__ = "monkeyman192"
__version__ = "1.0"

from hashlib import sha256
import os.path as op
import shutil
from tkinter import Tk, filedialog
import xml.etree.ElementTree as ET


# A flag to indicate that we don't want to actually replace any files and to
# just analyse the files.
DRYRUN = False
DATA_FOLDER = op.join(op.dirname(__file__), '../data')
index = op.join(DATA_FOLDER, 'index.xml')

if __name__ == "__main__":
    window = Tk()
    pcbanks_folder = filedialog.askdirectory(title="Select PCBANKS folder")
    tree = ET.parse(index)
    root = tree.getroot()
    files = {}
    different_files = 0

    for child in root:
        if child.tag == 'folder':
            # In this case the child is a folder containing files
            for file in child:
                files[op.join(child.attrib['name'],
                              file.attrib['name'])] = file.attrib['path']
        else:
            # These are just globals.
            files[child.attrib['name']] = child.attrib['path']
    for test_file, vanilla_file in files.items():
        full_vanilla_path = op.join(pcbanks_folder, vanilla_file)
        full_test_path = op.join(DATA_FOLDER, test_file)
        if not op.exists(full_vanilla_path):
            print(f'Cannot find {full_vanilla_path} in PCBANKS folder...')
            continue
        with open(full_vanilla_path, 'rb') as fv:
            vanilla_hash = sha256(fv.read()).hexdigest()
        with open(full_test_path, 'rb') as ft:
            test_hash = sha256(ft.read()).hexdigest()
        if vanilla_hash != test_hash:
            print(f'{full_test_path} and {full_vanilla_path} are different!')
            if not DRYRUN:
                shutil.copy(full_vanilla_path, op.dirname(full_test_path))
            different_files += 1
    print(f'Updated: {different_files}/{len(files)} have changed!')
