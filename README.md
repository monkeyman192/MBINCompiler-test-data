# MBINCompiler test data

This repo contains the test data for MBINCompiler.

This is just a small subset of all the games' MBIN files to try and get a good idea whether or not MBINCompiler is correctly (de)serializing the files correctly.

## Updating

First, ensure you have [hgpaktool](https://pypi.org/project/hgpaktool/) installed:

`python -m pip install hgpaktool`

You can also use [uv](https://github.com/astral-sh/uv) and run `uv sync` if you are more comfortable using python virtual environments.

Then run

`python extract_data.py`

The first time you run this it will prompt you to specify the location of your PCBANKS directory. This will be stored in a file in your user directory (`C:\Users\<username>\AppData\Roaming\MBINCompiler-test-data`) in a json file.
If you need to move this directory, you can change the path in this file, or just delete the file and re-run the script and it will prompt you to choose the directory again.

Once the files have been updated, if there are actually any file changes, the `data/.version` file MUST be updated to have the latest steam build ID.
