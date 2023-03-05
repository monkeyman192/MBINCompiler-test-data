# Check if any file in the index has been updated based on the files found
# under the specified file path.

# USAGE: Run this file with python. It will prompt you to select the folder
# that has all your files extracted to.
# This script will overwrite the files in the data folder with the ones from
# the unpacked-PCBANKS folder specified.
# NOTE: Ensure that these files are up to date, otherwise this analysis will be
# inaccurate.

__author__ = "monkeyman192"
__version__ = "1.2"

from hashlib import sha256
import sys
import os
import os.path as op
import re
import shutil
from tkinter import Tk, filedialog
import xml.etree.ElementTree as ET


# A flag to indicate that we don't want to actually replace any files and to
# just analyse the files.
DRYRUN = False
# If True then we will go over the entire unpacked-PCBANKS folder to look for new
# classes.
DISCOVER_NEW = True
# Regex expression to find and classes in .mbin files
CLASS_PATT = re.compile(b'(c(?:(?:Tk)|(?:Gc))\\w*)')
DATA_FOLDER = op.join(op.dirname(__file__), '../data')
INDEX = op.join(DATA_FOLDER, 'index.xml')
FOLDERS = ('METADATA', 'MODELS', 'SCENES', 'TEXTURES', 'UI')
XML_FMT = '\t\t<file name="{0}" path="{1}"/>\n'

class_mapping = dict()
wanted_files = {x: set() for x in FOLDERS}
tree = ET.parse(INDEX)
root_ = tree.getroot()


if __name__ == "__main__":
    window = Tk()
    unpacked_PCBANKS_folder = sys.argv[1] if len(sys.argv) >= 2 else filedialog.askdirectory(title="Select unpacked-PCBANKS folder")
    files = {}
    different_files = 0

    for child in root_:
        if child.tag == 'folder':
            # In this case the child is a folder containing files
            for file in child:
                files[op.join(child.attrib['name'],
                              file.attrib['name'])] = file.attrib['path']
        else:
            # These are just globals.
            files[child.attrib['name']] = child.attrib['path']
    for test_file, vanilla_file in files.items():
        full_vanilla_path = op.join(unpacked_PCBANKS_folder, vanilla_file)
        full_test_path = op.join(DATA_FOLDER, test_file)
        # If the file in the index cannot be found in the unpacked folder print
        # an error then continue.
        if not op.exists(full_vanilla_path):
            print(f'Cannot find {full_vanilla_path} in unpacked-PCBANKS folder...')
            continue
        # If the file doesn't exist in the test data but is in the index, then
        # just copy it over.
        if not op.exists(full_test_path):
            os.makedirs(op.dirname(full_test_path), exist_ok=True)
            print(f'Adding {full_vanilla_path} to the test data')
            if not DRYRUN:
                shutil.copy(full_vanilla_path, op.dirname(full_test_path))
            different_files += 1
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

    if DISCOVER_NEW:
        # Iterate over the whole unpacked-PCBANKS folder
        for folder_name in FOLDERS:
            count = 0
            print(f'Considering {folder_name}...')
            for root, dirs, files in os.walk(
                    op.join(unpacked_PCBANKS_folder, folder_name)):
                for file in files:
                    filepath = op.join(root, file)
                    rel_path = op.relpath(filepath, unpacked_PCBANKS_folder)
                    if (op.splitext(filepath)[1] != '.MBIN' or
                            filepath.endswith('MATERIAL.MBIN') or
                            filepath.endswith('DESCRIPTOR.MBIN') or
                            filepath.endswith('SCENE.MBIN') or
                            filepath.endswith('MATERIAL.MBIN')):
                        continue
                    count += 1
                    with open(filepath, 'rb') as f:
                        data = f.read()
                        size = f.tell()
                    for m in re.findall(CLASS_PATT, data):
                        if m in class_mapping:
                            if size > class_mapping[m][0]:
                                class_mapping[m] = (size, folder_name,
                                                    filepath)
                        else:
                            class_mapping[m] = (size, folder_name, filepath)
                    del data
                    if count % 100 == 0:
                        print(count)
            print(f'Considered {folder_name} ({count})')
        for k, v in class_mapping.items():
            wanted_files[v[1]].add(v[2])
        for k, v in wanted_files.items():
            if not op.exists(op.join(DATA_FOLDER, k)):
                os.makedirs(op.join(DATA_FOLDER, k), exist_ok=True)
            # Get a list of all the attribs in the folder for comparison.
            node = root_.find(f".//folder[@name='{k}']")
            # Get all the attribs
            attribs = [x.attrib for x in node.iter('file')]
            for full_path in v:
                fname = op.basename(full_path)
                dst_path = op.join(DATA_FOLDER, k, fname)
                if not op.exists(dst_path):
                    shutil.copy(full_path, op.dirname(dst_path))
                att = {'name': fname,
                       'path': op.relpath(full_path, unpacked_PCBANKS_folder)}
                if att not in attribs:
                    node.append(ET.Element('file', att))
        print(f'{len(class_mapping)} classes found')
        tree.write(INDEX)
