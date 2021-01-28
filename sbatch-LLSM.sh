#!/bin/bash
#SBATCH --job-name=LLSM-processing
#SBATCH --account=ACCOUNT_ID
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=10
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:K80:1
#SBATCH --partition=m3e
#SBATCH --mem=40GB
# To receive an email when job completes or fails
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

# Set the file for output (stdout)
#SBATCH --output=/projects/PROJECT/scripts/var/job-output/MyJob-%j.out

# Set the file for error log (stderr)
#SBATCH --error=/projects/PROJECT/scripts/var/job-output/MyJob-%j.out

INPUT_FOLDER=$@

#Load the required modules for processing the instrument data
module load cuda/11.0

#Activate the virtual environment - miniconda3
source /projects/PROJECT_ID/processing/miniconda3/bin/activate ""

#Activate the conda environment
conda activate decon_env

cd /projects/PROJECT_ID/processing/lightsheet-processing/
python lattice-watchFolder.py --config etc/lattice-config.yml --execute --input "$INPUT_FOLDER"
