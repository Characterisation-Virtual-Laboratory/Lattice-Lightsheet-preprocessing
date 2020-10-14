import argparse
from dateutil.tz import *
import errno
import logging
import os
import shutil
import subprocess
import sys
import time
import yaml


# TODO: persist copied files just like for submitted ??

# TODO: folder paths. Keep using the config.yml as the main output folder definition,
#  but prompt the user for the folder name, this will be used throughout the pipeline.


class WatchFolder:
    def __init__(self, config, execute, reset):
        self.config = config
        self.execute = execute
        self.reset = reset

        # This is the timezone for this script. It actually doesn't matter what value is used here as calls
        # to datetime.datetime.now(self.tz) will convert to whatever timezone you specify and comparisons just need
        # a TZ in both sides of the operator
        self.tz = gettz("Australia/Melbourne")

        self.logger = logging.getLogger("lattice-watchFolder.WatchFolder")
        self.logger.debug("creating an instance of WatchFolder")

        if reset is True:
            # Performing a clean run, delete the submitted.yml
            # Delete the folder contents
            self.logger.info("Clearing submitted.yml")
            try:
                os.remove(self.config["submitted"])
            except OSError as e:
                if e.errno != errno.ENOENT:
                    self.logger.info("Failed to delete {}. Reason: {}".format(self.config["submitted"], e))

            self.logger.info("Deleted contents of: {}".format(self.config["remote_input_dir"]))
            self.delete_path(self.config["remote_input_dir"])

            self.logger.info("Deleted contents of: {}".format(self.config["remote_output_dir"]))
            self.delete_path(self.config["remote_output_dir"])

            self.logger.info("Deleted contents of: {}".format(self.config["massive_input_dir"]))
            self.delete_path(self.config["massive_input_dir"])

            self.logger.info("Deleted contents of: {}".format(self.config["massive_output_dir"]))
            self.delete_path(self.config["massive_output_dir"])

        # From the config, obtain files to ignore. These have been previously processed.
        # Don't process these files again.
        try:
            with open(self.config["submitted"]) as f:
                self.submitted = yaml.safe_load(f.read())
        except FileNotFoundError:
            self.submitted = []

        # Check if output paths exist, if not create them.
        # if not os.path.exists(self.config""):

    def submit_job(self, file):
        # Use this for testing
        # cmd = [
        #     "cp",
        #     file,
        #     self.config["massive_output_dir"],
        # ]

        cmd = [
            self.config["srun_path"],
            self.config["executable"],
            file,
            self.config["massive_output_dir"],
        ]

        if self.execute is True:
            p = subprocess.Popen(
                args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            for stdout_line in iter(p.stdout.readline, b""):
                self.logger.info("Stdout: {}".format(stdout_line.decode("utf-8")))
            for stderr_line in iter(p.stderr.readline, b""):
                self.logger.warning("Stderr: {}".format(stderr_line.decode("utf-8")))
        else:
            self.logger.info("Job: {}".format(cmd))

    def delete_path(self, folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                self.logger.info("Failed to delete {}. Reason: {}".format(file_path, e))

    def main(self):
        copied_output = []

        last_file_process_delay = 0
        process = True

        self.logger.info("Watching folder: {}".format(self.config["remote_input_dir"]))

        while process:
            # Monitor remote input directory
            input_path, input_directory, input_files = next(
                os.walk(self.config["remote_input_dir"])
            )
            input_file_count = len(input_files)
            self.logger.debug("Input file count: {}".format(input_file_count))
            input_file = ""

            input_files.sort()

            submitted_flag = False

            if input_file_count > 1:
                for input_file in input_files:
                    if (
                            input_file not in self.submitted
                            and input_file != input_files[input_file_count - 1]
                    ):
                        # Copy the file from the input path to Massive input storage.
                        shutil.copy2(
                            os.path.join(input_path, input_file),
                            self.config["massive_input_dir"],
                        )
                        self.logger.debug("Submitting file: {}".format(input_file))
                        self.submit_job(self.config["massive_input_dir"] + input_file)
                        # Append the file to submitted, sort it, then write to disk.
                        self.submitted.append(input_file)
                        self.submitted.sort()
                        try:
                            with open(self.config["submitted"], "w") as f:
                                yaml.dump(self.submitted, f)
                        except EnvironmentError:
                            self.logger.error(
                                "Unable to update {}".format(self.config["submitted"])
                            )
                        self.logger.debug(os.stat(os.path.join(input_path, input_file)))
                        submitted_flag = True

            # Monitor Massive output directory
            output_path, output_directory, output_files = next(
                os.walk(self.config["massive_output_dir"])
            )
            output_file_count = len(output_files)
            self.logger.debug("Output file count: {}".format(output_file_count))

            output_files.sort()

            if output_file_count > 1:
                for output_file in output_files:
                    if (
                            output_file not in copied_output
                            and output_file != output_files[output_file_count - 1]
                    ):
                        shutil.copy2(
                            os.path.join(output_path, output_file),
                            self.config["remote_output_dir"],
                        )
                        copied_output.append(output_file)

            if submitted_flag:
                last_file_process_delay = 0
            else:
                last_file_process_delay += 1

            self.logger.debug(
                "last_file_process_delay: {}".format(last_file_process_delay)
            )
            # Delay is met, submit last file for processing.
            if (last_file_process_delay == self.config["delay"]) \
                    and input_file_count > 1:
                shutil.copy2(
                    os.path.join(input_path, input_files[input_file_count - 1]),
                    self.config["massive_input_dir"],
                )
                self.logger.info(
                    "Submitted last file: {}{}".format(
                        self.config["massive_input_dir"],
                        input_files[input_file_count - 1],
                    )
                )
                self.submit_job(
                    self.config["massive_input_dir"] + input_files[input_file_count - 1]
                )
                self.submitted.append(input_file)
                try:
                    with open(self.config["submitted"], "w") as f:
                        yaml.dump(self.submitted, f)
                except EnvironmentError:
                    self.logger.error(
                        "Unable to update {}".format(self.config["submitted"])
                    )
            # Delay is met, last file processed has been written, copy and end processing.
            elif (last_file_process_delay >= self.config["delay"]) \
                    and (input_file_count == output_file_count) \
                    and input_file_count > 1:
                shutil.copy2(
                    os.path.join(output_path, output_files[output_file_count - 1]),
                    self.config["remote_output_dir"],
                )
                process = False
                self.logger.info(
                    "Copied last file to: {}{}".format(
                        self.config["remote_output_dir"],
                        output_files[output_file_count - 1],
                    )
                )
            # Delay is met, but no files were processed, end processing.
            elif (last_file_process_delay >= self.config["delay"]) \
                    and input_file_count == 0:
                process = False
                self.logger.info("No files processed, as none were found")
            else:
                time.sleep(self.config["timeout"])


def main():
    parser = argparse.ArgumentParser(
        description="lattice-watchFolder: monitor a folder for new files and submit for processing."
    )
    parser.add_argument("-c", "--config", type=str, help="path to config.yml")
    parser.add_argument(
        "-e", "--execute", help="If not set, --dryrun executes", action="store_true"
    )
    parser.add_argument(
        "-r", "--reset",
        help="If set submitted.yml will be cleared and the contents of the input and output folders will be deleted.",
        action="store_true"
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

    fh = logging.FileHandler(config["log-files"]["watch"])
    fh.setLevel(logging_dict[config["log-level"]])
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s:%(process)s: %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    watch = WatchFolder(config, args.execute, args.reset)
    if not args.reset:
        watch.main()


if __name__ == "__main__":
    main()
