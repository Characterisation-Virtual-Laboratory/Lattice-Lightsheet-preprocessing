#!/bin/bash
#SBATCH --job-name=LLSM-processing
#SBATCH --account=ACCOUNT_ID
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:K80:1
#SBATCH --partition=m3e
#SBATCH --mem=20GB
# To receive an email when job completes or fails
#SBATCH --mail-user=firstname.lastname@monash.edu
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

# Set the file for output (stdout)
#SBATCH --output=/projects/PROJECT/scripts/var/job-output/MyJob-%j.out

# Set the file for error log (stderr)
#SBATCH --error=/projects/PROJECT/scripts/var/job-output/MyJob-%j.err

#Load the required modules for processing the instrument data
module load arrayfire
module load cuda/10.1
module load qt/5.7.1-gcc5

INPUT_FOLDER=$1

#Activate the virtual environment
source /projects/PROJECT_ID/virtualenv/watchFolder/bin/activate

cd /projects/PROJECT_ID/scripts/
python lattice-watchFolder.py --config etc/lattice-config.yml --execute --input $INPUT_FOLDER
