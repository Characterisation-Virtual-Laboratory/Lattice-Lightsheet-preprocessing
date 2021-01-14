# Lattice-Lightsheet-processing

The Lattice Lightsheet instrument captures data on a Windows based machine. To
take advantage of the processing power in a HPC (High Performance Computing) 
environment the lattice-processing.py script has been created to enable 
processing of raw data.

Mounting a windows file system on Unix has a few challenges. While this can be achieved, 
determining when Windows has finished creating a file, is difficult for Unix. This script
avoids the need to check file locks.

Since file locking can be problematic between Windows and UNIX, the 
lattice-processing.py script has been built with the following assumptions:
 - expects the folder path to end with "emailAddress/YYYYMMDD/experimentID"
 - checks for the existence of the 'processing_file' in the experimentID folder as
   defined in the config.yml, if the file is detected, processing continues.
 - the 'processing_file' is a jinja2 template, each line containing the command to run and the parameters
   for substitution matching those as defined "processing_output_folders" in config.yml

## Installation on the HPC
- create a virtual environment
```
    python3 -m venv ~/virtualenv/lattice-process
```

- activate the virtual environment
```
    source ~/virtualenv/lattice-process/bin/activate
```

- install Python dependencies
```
    pip install python-dateutil pyyml jinja2
```

- Clone the repository
```
    cd ~
    git clone https://github.com/monash-merc/asynchy/lattice-WatchFolder.git
```

### Configuration file  
etc/lattice-config.yml

- massive_input_dir:  Path to local folder containing the files for processing. 
- massive_output_dir: Path to local folder containing the processed folder.

- processing_file: path to the jinaj2 template containing commands for execution
- processing_output_folders: use to create output folders for processed data, but also to substitute values
  in the processing_file

- log-level: Possible values are: logging.DEBUG, logging.INFO, logging.ERROR, logging.WARNING
- log-files:
    watch: Path to the log file. e.g. lattice-WatchFolder/var/log/watchFolder.log

### Configuring the job - sbatch

The file "sbatch-LLSM.sh" is a sample for running the process. The script activates the python virtual
environment and any modules required for processing the data. Then it starts the lattice-Watchfolder process.

## Running the workflow

On your Windows machine, setup a file transfer tool. We suggest using WinSCP as it
can monitor local and remote folders for new files. For details on how to do 
this refer to: https://docs.massive.org.au/M3/transferring-files.html#winscp-windows

1. **PROCESSED files from HPC** 
    Start WinSCP to keep a local folder up to date. This should be linked to the "remote_output_dir"
configured in the lattice-config.yml file and the destination folder on the Windows machine. This step will
return processed data from the HPC to Windows.
2. **UNPROCESSED files to HPC**
    Start WinSCP to 'Keep Remote Directory up to Date'. This should be linked to the "remote_input_dir"
configured in the lattice-config.yml file and the source folder on the Windows machines. e.g. raw files from
the Lattice Lightsheet instrument.  
3. **Submit sbatch-LLSM-deskew.sh**. Submit the sbatch script to the HPC queue. When the script starts, it will
find files from the "remote_input_dir", copy them to "massive_input_dir", use "srun" to process each file individually
with the process writing output to the "massive_output_dir". The script will monitor the "massive_output_dir" 
and copy the processed files to "remote_output_dir"
4. When the HPC starts processing the job, files will be processed, and WinSCP will copy them across to Windows. On the 
Windows machine, you should see a flow of files in and out of the machine.   

## lattice-watchFolder.py command line arguments
- execute: this must be set otherwise the "executable" as defined in the lattice-config.yml file will not run.
- reset:   when set, the contents of the configured folders will be deleted. ("remote_input_dir", "remote_output_dir", 
"massive_input_dir", "massive_output_dir") The file submitted.yml will be removed. This ensures a clean run. No actual
processing takes place, just the cleanup.
