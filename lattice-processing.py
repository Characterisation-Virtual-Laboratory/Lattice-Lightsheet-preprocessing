import argparse
from dateutil.tz import *
from jinja2 import Environment, FileSystemLoader
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import yaml


class WatchFolder:
    def __init__(self, config, input_path, execute):
        self.config = config
        self.input = input_path
        self.execute = execute

        # This is the timezone for this script. It actually doesn't matter what value is used here as calls
        # to datetime.datetime.now(self.tz) will convert to whatever timezone you specify and comparisons just need
        # a TZ in both sides of the operator
        self.tz = gettz("Australia/Melbourne")

        self.logger = logging.getLogger("lattice-watchFolder.WatchFolder")
        self.logger.debug("creating an instance of WatchFolder")

    def submit_job(self, path):

        # prepare environment to read Jinja templates
        env = Environment(loader=FileSystemLoader(path + "/" + self.config["processing_output_folders"]["rawdata"]))
        # obtain the text and html template
        template_text = env.get_template(self.config["processing_file"])

        full_paths = {}
        for folder in self.config["processing_output_folders"]:
            full_paths[folder] = path + "/" + self.config["processing_output_folders"][folder]

        text = template_text.render(**full_paths)

        for line in text.splitlines():
            if self.execute is True:
                p = subprocess.Popen(
                    args=line, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                for stdout_line in iter(p.stdout.readline, b""):
                    self.logger.info("Stdout: {}".format(stdout_line.decode("utf-8")))
                for stderr_line in iter(p.stderr.readline, b""):
                    self.logger.warning("Stderr: {}".format(stderr_line.decode("utf-8")))
            else:
                self.logger.info("Job: {}".format(line))

    def main(self):
        self.logger.info("Processing folder: {}".format(self.input))

        # Check if the processing file exists
        # Existence confirms, no more data for this experiment_id, run processing
        processing_file_exists = False

        if os.path.exists(self.input + '/' + self.config["processing_file"]):
            processing_file_exists = True
        else:
            self.logger.error("The processing file: {} does not exist. This is required to indicate data collection is complete.".format(self.config["processing_file"]))

        if processing_file_exists:
            # Obtaining the emailAddress, Date, dataset from the folder structure
            # e.g. /project/ProjectID/massive_input/emailAddress/YYYYMMDD/experimentID
            folders = self.input.rsplit("/", 3)
            email_address = folders[1]
            date_folder = folders[2]
            experiment_id = folders[3]

            sub_structure = email_address + "/" + date_folder + "/" + experiment_id

            # Create output folders
            for folder in self.config["processing_output_folders"]:
                # Don't create the rawdata folder, as created by move below.
                if not folder == "rawdata":
                    new_folder = self.config["massive_output_dir"] + 'rawdata/' + sub_structure + '/' + \
                                 self.config["processing_output_folders"][folder]
                    self.logger.debug("Creating output folder: {}".format(new_folder))
                    try:
                        os.makedirs(new_folder, exist_ok=True)
                    except FileExistsError:
                        self.logger.debug("Output folder exists: {}".format(self.config["processing_output_folders"][folder]))

            # Moving input files to new location
            self.logger.debug("Moving rawdata to permanent location")
            try:
                shutil.move(self.config["massive_input_dir"] + sub_structure + '/',
                            self.config["massive_output_dir"] + 'rawdata/'+ sub_structure + "/" +
                            self.config["processing_output_folders"]['rawdata'])
            except shutil.Error as error:
                self.logger.error("Error moving files: ", error)

            # Process the data
            self.submit_job(self.config["massive_output_dir"] + 'rawdata/'+ sub_structure)

def main():
    parser = argparse.ArgumentParser(
        description="lattice-watchFolder: monitor a folder for new files and submit for processing."
    )
    parser.add_argument("-c", "--config", type=str, help="path to config.yml")
    parser.add_argument("-i", "--input", type=str, help="Input folder for processing")
    parser.add_argument(
        "-e", "--execute", help="If not set, --dryrun executes", action="store_true"
    )
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    with open(args.config) as f:
        config = yaml.safe_load(f.read())

    # setup logging
    logging_dict = {
        "logging.ERROR": logging.ERROR,
        "logging.WARNING": logging.WARNING,
        "logging.INFO": logging.INFO,
        "logging.DEBUG": logging.DEBUG,
    }

    logger = logging.getLogger("lattice-watchFolder")
    logger.setLevel(logging_dict[config["log-level"]])

    fh = logging.handlers.RotatingFileHandler(config["log-files"]["watch"], maxBytes=10*1024*1024, backupCount=5)
    fh.setLevel(logging_dict[config["log-level"]])
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s:%(process)s: %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    watch = WatchFolder(config, args.input, args.execute)
    watch.main()


if __name__ == "__main__":
    main()
