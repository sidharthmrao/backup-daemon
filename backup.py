import os
import time
import json
import shutil
import subprocess
from datetime import datetime

# Default config file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.expanduser("~/.config/backup_daemon/config.json")
EXAMPLE_CONFIG_PATH = os.path.join(SCRIPT_DIR, "example_config.json")

class Config:
    """
    Manages loading and validating the configuration file.
    """
    def __init__(self, config_path, example_config_path):
        self.config_path = config_path
        self.example_config_path = example_config_path
        self.global_options = {"enabled": True, "check_interval": 300}
        self.backup_locations = []
        self.load_config()

    def load_config(self):
        """
        Load the configuration file or copy an example config if missing.
        """
        if not os.path.exists(self.config_path):
            print(f"Config file not found at {self.config_path}. Copying example config.")
            self.copy_example_config()
        else:
            with open(self.config_path, 'r') as file:
                config_data = json.load(file)
                self.global_options = config_data.get("global_options", self.global_options)
                self.backup_locations = config_data.get("backup_locations", [])
                self.validate_config()

    def validate_config(self):
        """
        Validate the loaded configuration.
        """
        if not isinstance(self.global_options.get("enabled"), bool):
            self.global_options["enabled"] = True
        if not isinstance(self.global_options.get("check_interval"), int):
            self.global_options["check_interval"] = 300

        for location in self.backup_locations:
            if "folder" not in location or "remote_url" not in location or "branch" not in location:
                raise ValueError(f"Invalid configuration for backup location: {location}")
            location["enabled"] = location.get("enabled", True)

    def copy_example_config(self):
        """
        Copy the example config file to the user's config directory.
        """
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        shutil.copy(self.example_config_path, self.config_path)
        print(f"Example config file copied to {self.config_path}. Please update it before running the script again.")
        exit()

def ensure_correct_branch(repo_path, branch):
    """
    Ensure the local repository is on the specified branch.
    """
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    current_branch = result.stdout.strip()
    if current_branch != branch:
        print(f"Switching to branch '{branch}' in {repo_path}...")
        subprocess.run(["git", "-C", repo_path, "checkout", branch])

def commit_and_push(repo_path, remote_url, branch):
    """
    Commit and push changes to the remote repository.
    """
    try:
        ensure_correct_branch(repo_path, branch)
        subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", remote_url])
        subprocess.run(["git", "-C", repo_path, "add", "."])
        commit_message = f"Backup on {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}"
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message])
        subprocess.run(["git", "-C", repo_path, "push", "origin", branch])
        print(f"Changes committed and pushed to {branch} on {remote_url}.")
    except subprocess.CalledProcessError as e:
        print(f"Error committing or pushing changes: {e}")

def process_folder(folder, remote_url, branch):
    """
    Check if the folder is a Git repository, initialize if not, and push changes.
    """
    if not os.path.isdir(os.path.join(folder, ".git")):
        print(f"Initializing Git repository in {folder}...")
        subprocess.run(["git", "-C", folder, "init"])
        subprocess.run(["git", "-C", folder, "remote", "add", "origin", remote_url])
        print(f"Initialized and set remote URL for {folder}.")
    commit_and_push(folder, remote_url, branch)

def main():
    """
    Main function to periodically process backups based on the configuration.
    """

    while True:
        config = Config(CONFIG_FILE_PATH, EXAMPLE_CONFIG_PATH)
        if not config.global_options["enabled"]:
            print("Backup service disabled.")
            time.sleep(config.global_options["check_interval"])

        for location in config.backup_locations:
            if location["enabled"] and os.path.isdir(location["folder"]):
                print(f"Processing folder: {location['folder']}")
                process_folder(location["folder"], location["remote_url"], location["branch"])
            elif not os.path.isdir(location["folder"]):
                print(f"Folder {location['folder']} does not exist. Skipping...")
        time.sleep(config.global_options["check_interval"])

if __name__ == "__main__":
    main()
