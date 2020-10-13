# Lattice-Lightsheet-preprocessing

The Lattice Lightsheet instrument captures data on a Windows based machine. To
take advantage of the processing power in a HPC (High Performance Computing) 
environment the lattice-watchFolder.py script has been created to enable live 
processing of raw data.

Mounting a windows file system on Unix has a few challenges. While this can be achieved, 
determining when Windows has finished creating a file, is difficult for Unix. This 
script avoids the need to check file locks.

Since file locking can be problematic between Windows and UNIX, the 
lattice-Watchfolder.py script has been built with the following assumptions:
 - files are written sequentially from the instrument.
 - the first file is not processed, (how do we know it is complete? )
 - when a second file is written, the first file is processed by the script, and so on.
 - a configurable time delay is used by the script, to determine when to 
 process the last file.

## Installation on the HPC
- create a virtual environment
```
    python3 -m venv ~/virtualenv/lattice-watchFolder
```

- activate the virtual environment
```
    source ~/virtualenv/lattice-watchFolder/bin/activate
```

- install Python dependencies
```
    pip install python-dateutil pyyml
```

- Clone the repository
```
    cd ~
    git clone https://github.com/monash-merc/asynchy/lattice-WatchFolder.git
```

### Configuration file  
etc/lattice-config.yml

- remote_input_dir:   Path to local folder that is receiving files from Windows.
- remote_output_dir:  Path to local folder with files that have completed processing. e.g. SCP back to Windows.
- massive_input_dir:  Path to local folder containing the files for processing. 
- massive_output_dir: Path to local folder containing the processed folder.

- submitted:  Path to submitted.yml. This file is used to track files submitted for processing. If the process is 
            restarted, the files listed in submitted.yml are not reprocessed. This file will be created if it does
            not exist.
- srun_path:  Path to 'srun' for submitting the file for processing
- executable: Path to the executable that will process the file. The executable is expected to write output to 
            the "massive_output_dir"

- timeout:    Controls the main loop. e.g. 5. pause the main loop for 5 seconds before searching for more files.
- delay: 3    Used to determine, when to process the last file. When "delay X timeout" in seconds is reached, the
            last file will be submitted for processing. This value will require adjusting depending on the
            speed of your connection to upload files to the HPC. 

- log-level: Possible values are: logging.DEBUG, logging.INFO, logging.ERROR, logging.WARNING
- log-files:
    watch: Path to the log file. e.g. lattice-WatchFolder/var/log/watchFolder.log

### Configuring the job - sbatch

The file "sbatch-LLSM-deskew.sh" is a sample for running the process. The script activates the python virtual
environment and any modules required for processing the data. Then it starts the lattice-Watchfolder process.

## Running the workflow

On your Windows machine, setup a file transfer tool. We suggest using WinSCP as it
can monitor local and remote folders for new files. For details on how to do 
this refer to: add link to doco on docs.massive (need to write it up)

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
