#!/bin/python

# Thank you to chatgpt for writing all this code in 5 minutes

import os
import time
import subprocess
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.config/backup_daemon/config.cfg")
CHECK_INTERVAL = 15  # Time interval to check the config file (in seconds)


def ensure_config_exists(file_path):
    """Ensure the configuration file exists, creating it if necessary."""
    config_dir = os.path.dirname(file_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            file.write("# Add your folders and remote URLs here, one per line:\n")
            file.write("# Example: /path/to/folder https://your-remote-repo.git\n")
        print(f"Config file created at {file_path}.")


def read_config(file_path):
    """Read and parse the configuration file."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    configs = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):  # Skip comments and empty lines
            parts = line.split()
            if len(parts) == 2:
                configs.append((os.path.expanduser(parts[0]), parts[1]))
    return configs


def is_git_repo(folder):
    """Check if a folder is a Git repository."""
    try:
        subprocess.run(["git", "-C", folder, "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def set_remote_url(folder, remote_url):
    """Set the remote URL for the repository."""
    try:
        subprocess.run(["git", "-C", folder, "remote", "remove", "origin"], check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass  # Ignore if the remote doesn't exist yet
    try:
        subprocess.run(["git", "-C", folder, "remote", "add", "origin", remote_url], check=True)
        print(f"Remote URL set to {remote_url} for {folder}.")
    except subprocess.CalledProcessError as e:
        print(f"Error setting remote URL for {folder}: {e}")


def fetch_and_pull(folder):
    """Fetch and pull changes from the remote repository."""
    try:
        subprocess.run(["git", "-C", folder, "fetch", "--all"], check=True)
        subprocess.run(["git", "-C", folder, "pull", "origin", "main"], check=True)
        print(f"Fetched and pulled updates for {folder}.")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching or pulling updates for {folder}: {e}")


def initialize_git_repo(folder, remote_url):
    """Initialize a Git repository and push to the remote URL."""
    try:
        subprocess.run(["git", "-C", folder, "init"], check=True)
        set_remote_url(folder, remote_url)
        subprocess.run(["git", "-C", folder, "add", "."], check=True)
        subprocess.run(
            ["git", "-C", folder, "commit", "-m", f"Initial backup on {datetime.now().isoformat()}"], check=True
        )
        subprocess.run(["git", "-C", folder, "branch", "-M", "main"], check=True)
        subprocess.run(["git", "-C", folder, "push", "--set-upstream", "origin", "main"], check=True)
        print(f"Initialized and pushed repository in {folder} to {remote_url}.")
    except subprocess.CalledProcessError as e:
        print(f"Error initializing repository in {folder}: {e}")


def commit_and_push(folder, remote_url):
    """Commit changes and push to the remote repository."""
    try:
        set_remote_url(folder, remote_url)
        fetch_and_pull(folder)  # Fetch and pull changes first
        subprocess.run(["git", "-C", folder, "add", "."], check=True)
        status_result = subprocess.run(["git", "-C", folder, "status", "--porcelain"], capture_output=True, text=True)
        if status_result.stdout.strip():  # If there are changes to commit
            commit_message = f"Backup on {datetime.now().isoformat()}"
            subprocess.run(["git", "-C", folder, "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "-C", folder, "push", "--set-upstream", "origin", "main"], check=True)
        print(f"Committed and pushed changes in {folder}.")
    except subprocess.CalledProcessError as e:
        print(f"Error committing or pushing changes in {folder}: {e}")


def main():
    """Main function to periodically process the configuration."""
    ensure_config_exists(CONFIG_PATH)

    while True:
        configs = read_config(CONFIG_PATH)
        for folder, remote_url in configs:
            if not os.path.exists(folder):
                print(f"Folder {folder} does not exist. Skipping.")
                continue

            if not is_git_repo(folder):
                initialize_git_repo(folder, remote_url)
            else:
                commit_and_push(folder, remote_url)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
