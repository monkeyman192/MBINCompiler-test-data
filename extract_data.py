import json
import os
import os.path as op
import struct
import subprocess
import sys
import time

from hgpaktool import HGPAKFile

try:
    from tkinter import Tk, filedialog

    has_tkinter = True
except ModuleNotFoundError:
    has_tkinter = False


CFG_FOLDER = op.join(os.environ.get("APPDATA", op.expanduser("~")), "MBINCompiler-test-data")
OUTPUT_FOLDER = "data"


def update_index(fpath, new_data: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    # Get the old data
    with open(fpath, "r") as f:
        existing_data = json.load(f)

    # Loop over the new data, and merge it into the existing data.
    for pakname, new_pak_contents in new_data.items():
        # If the pak name already exists in the current data, update the dict.
        if (existing_pak_data := existing_data.get(pakname)) is not None:
            existing_pak_data.update(new_pak_contents)
            existing_data[pakname] = existing_pak_data
        # Otherwise add to the existing data.
        else:
            existing_data[pakname] = new_pak_contents

    # Write the new data
    with open(fpath, "w") as f:
        json.dump(existing_data, f, indent=1)

    return existing_data


def parse_index(fpath) -> set[int]:
    # Read the index file and get the list of currently used namehashes.
    namehashes = set()
    with open(fpath, "r") as f:
        data = json.load(f)
        for pak_contents in data.values():
            for namehash in pak_contents.values():
                namehashes.add(int(namehash))
    return namehashes


def extract_data(data: dict[str, dict[str, int]], pcbanks_dir: str) -> int:
    count = 0
    for pakname, pak_contents in data.items():
        with HGPAKFile(op.join(pcbanks_dir, pakname)) as pak:
            count += pak.unpack(OUTPUT_FOLDER, list(pak_contents.keys()), upper=True)
    return count


if __name__ == "__main__":
    if not op.exists(CFG_FOLDER):
        os.makedirs(CFG_FOLDER, exist_ok=True)

    # Check to see if we have the PCBANKS folder configured
    do_configure = False
    pcbanks_dir = None

    settings_fpath = op.join(CFG_FOLDER, "settings.json")

    if not op.exists(settings_fpath):
        do_configure = True

    if not do_configure:
        with open(settings_fpath, "r") as f:
            settings = json.load(f)
            if isinstance(settings, dict):
                if not (pcbanks_dir := settings.get("PCBANKS_dir")):
                    do_configure = True
            else:
                do_configure = True

    if do_configure:
        if has_tkinter:
            root = Tk()
            root.withdraw()
            pcbanks_dir = filedialog.askdirectory(title="PCBANKS directory")
            with open(settings_fpath, "w") as f:
                json.dump({"PCBANKS_dir": pcbanks_dir}, f)
        else:
            with open(settings_fpath, "w") as f:
                json.dump({"PCBANKS_dir": ""}, f)
            print(
                f"Tkinter not installed! Opening {CFG_FOLDER!r} and exiting. Please write fill in the "
                "settings file manually."
            )
            subprocess.call(f'explorer "{CFG_FOLDER}"')
            sys.exit(1)

    if not pcbanks_dir:
        print(
            "There was an issue resolving your PCBANKS directory, please set it manually in the "
            "settings.json file."
        )
        subprocess.call(f'explorer "{CFG_FOLDER}"')
        sys.exit(1)

    t0 = time.perf_counter()

    filename_pak_map: dict[str, str] = {}  # Map filenames to the pak they are in.
    file_namehash_map: dict[str, int] = {}  # Map filename to the namehash contained.
    found_namehashes = set()  # Set of found namehashes so we can determine if there are new ones.

    # Extract a tonne of info from the pak files.
    for pak_fname in os.listdir(pcbanks_dir):
        if pak_fname.endswith(".pak"):
            with HGPAKFile(op.join(pcbanks_dir, pak_fname)) as pak:
                for _fname in pak.filenames:
                    if _fname.lower().endswith(".mbin"):
                        filename_pak_map[_fname] = pak_fname
                        # Only read the first 0x20 bytes of the mbin file since we only need the header.
                        for fname, _data in pak.extract(_fname, max_bytes=0x20):
                            namehash, guid = struct.unpack("<12xIQ8x", _data)
                            if namehash == 0x2E:
                                # Skip a broken file...
                                continue
                            file_namehash_map[fname] = namehash
                            found_namehashes.add(namehash)

    # Parse the existing index.json file to see what we currently track in this repo.
    current_namehashes = parse_index("index.json")
    new_namehashes = found_namehashes - current_namehashes

    # List of newly taken namehashes so that we only add each new one once.
    taken_new_namehashes = set()

    new_data: dict[str, dict[str, int]] = {}

    # For each file in the namehash map, check to see if it's in the new set of found namehashes.
    # If it is, then add the info to the new data and update.
    if new_namehashes:
        for fname, namehash in file_namehash_map.items():
            if namehash in new_namehashes and namehash not in taken_new_namehashes:
                # Get the pak the file is in and write the data to the dict.
                pak_name = filename_pak_map[fname]
                if pak_name in new_data:
                    new_data[pak_name][fname] = namehash
                else:
                    new_data[pak_name] = {fname: namehash}
                taken_new_namehashes.add(namehash)

    # Update the index.
    updated_data = update_index("index.json", new_data)
    # Extract all the files in the index. Git will handle whether they are new or not.
    num_extracted = extract_data(updated_data, pcbanks_dir)

    print(f"Process complete in {time.perf_counter() - t0:.6f}s")
    print("Summary:")
    print(f" - Updated the index with {len(new_namehashes)} new namehashes")
    print(f" - Extracted {num_extracted} files")
