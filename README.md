# Lattice-Lightsheet-processing - one-way

The Lattice Lightsheet instrument captures data on a Windows based machine. To
take advantage of the processing power in a HPC (High Performance Computing) 
environment the lattice-processing.py script has been created to enable 
processing of raw data.

This version of the processing has been designed to run one-way: Instrument machine to HPC.

Mounting a windows file system on Unix has a few challenges. While this can be achieved, 
determining when Windows has finished creating a file, is difficult for Unix. This script
avoids the need to check file locks.

Since file locking can be problematic between Windows and UNIX, the 
lattice-processing.py script has been built with the following assumptions:
 - expects the folder path to end with "emailAddress/YYYYMMDD/experimentID"
 - checks for the existence of the 'processing_file' in the experimentID folder as
   defined in the config.yml, if the file is detected, processing continues.
 - the 'processing_file' is a jinja2 template, each line containing the command to run, and the parameters
   for substitution, matching those as defined as "processing_output_folders" in the config.yml
 - the first line of the 'processing_file' may contain 'wait_for_files' followed by a total number
   of files (inclusive of subdir files) to be processed. This will cause the program to check that the actual number
   of files matches. If they don't, it will sleep for 30 secs and check again. This additional check was added to ensure 
   all files were in place before processing starts.

## Processing 
The following scripts are used to process the raw data files from the Lattice Lightsheet instrument:
- Deskew.py - perform deskew processing - requires an NVIDIA GPU (CUDA)
- Decon.py  - perform deconvolution processing
- PhotoBleachCorrect_Multiprocessing.py - perform photo bleach correction.

The sample 'processing.j2' file is configured to call these scripts.

## Installation - HPC specific instructions.
- install MiniConda3
```
    cd /projects/ProjectName/processing/
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh   
    ## Review the licence
    ## set the install directory to /projects/ProjectName/processing/miniconda3
    ## DO NOT run conda init when asked. This causes problems on the MASSIVE HPC.
    source miniconda3/bin/activate.
```
- create conda environment, installing pycudadecon
```
    conda config --add channels conda-forge
    conda config --add channels talley
 
    conda create -n decon_env pycudadecon

    conda activate decon_env    
```

- install Python dependencies
```
    #Ensure cuda is loaded 
    module load cuda/11.0
    pip install python-dateutil pyyml jinja2 cupy-cuda110
```

- Clone the repository
```
    git clone -b one-way https://github.com/Characterisation-Virtual-Laboratory/Lattice-Lightsheet-preprocessing
```

### Configuration file  
etc/lattice-config.yml

- massive_input_dir:  Path to local folder containing the files for processing. 
- massive_output_dir: Path to local folder containing the processed folder.

- processing_file: path to the jinja2 template containing commands for execution
- processing_output_folders: used to create output folders for processed data, but also to substitute values
  in the processing_file

- log-level: Possible values are: logging.DEBUG, logging.INFO, logging.ERROR, logging.WARNING
- log-files:
    watch: Path to the log file. e.g. Lattice-Lightsheet-preprocessing/var/log/watchFolder.log

## lattice-processing.py command line arguments
- config:  path to the "lattic-config.yml" file
- execute: this must be set otherwise a "dry-run" will take place.
- input:   path to data for processing. /YourPath/emailAddress/YYYYMMDD/experimentID

### Configuring the job - sbatch

The file "sbatch-LLSM.sh" is a sample for running the process. The sbatch script activates conda, and then
activates the conda environment. This process is required in the HPC environment. 
The script expects as input, the folder to be processed. e.g. /YourPath/emailAddress/YYYYMMDD/experimentID

## Running the workflow

On your Windows machine, setup a file transfer tool. We suggest using WinSCP as it
can monitor local and remote folders for new files. For details on how to do 
this refer to: https://docs.massive.org.au/M3/transferring-files.html#winscp-windows

1. **UNPROCESSED files to HPC**
    Start WinSCP to 'Keep Remote Directory up to Date'. This should be linked to the "remote_input_dir"
configured in the lattice-config.yml file and the source folder on the Windows machines. e.g. raw files from
the Lattice Lightsheet instrument.  
2. **Submit sbatch-LLSM.sh**. 

```sbatch --user-email=EmailAddress sbatch-LLSM-sh /YourPath/emailAddress/YYYYMMDD/experimentID```

Submit the sbatch script to the HPC queue. When the script starts, it will
check for the existence of the 'processing.j2' file. If not found, it will exit. If found, processing.j2 will 
be parsed. If 'wait_for_files' is the first line in 'processing.j2' the number of files will be checked. If the 
number of files does not match, it will sleep for 30 secs and then check again. When the number of files matches
the output directory structure will be created, and the files copied across. Then the remaining lines in 'processing.j2'
will be used to process the files.
