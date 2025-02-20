# MBINCompiler test data

This repo contains the test data for MBINCompiler.

This is just a small subset of all the games' MBIN files to try and get a good idea whether or not MBINCompiler is correctly (de)serializing the files correctly.

## Updating

Currently updating this repo is slightly convoluded, but it can be done in the following way:

```
python .\HGPAKTool\hgpaktool.py -U --json "{json_path}" --upper -O "{data_path}" "{PCBANKS_path}"
```

Where the following substitutions should be made:
Note: All paths MUST be absolute paths.

- `json_path`: The path to index.json within this repo.
- `data_path`: The path to the `data` directory within this repo.
- `PCBANKS_path`: The path to the PCBANKS directory in the games' files.

The command is then ran from within the `HGPAKTool` folder.
This command will extract all the files in the `index.json` file into the data directory of this repo.

Once the files have been updated, if there are actually any file changes, the `data/.version` file MUST be updated to have the latest steam build ID.

**NOTE:** Currently the `utils/update.py` file is not working. More work needs to be done in both this repo as well as the HGPAKTool repo to make this easier to do. For now, if new files are added we need to add them manually to the `index.json` file.
