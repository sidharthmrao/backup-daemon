# Thank you to chatgpt for writing all this code in 5 minutes

import os
import time
import subprocess
from datetime import datetime

# Path to the config file
CONFIG_FILE_PATH = os.path.expanduser("~/.config/backup_daemon/config.cfg")

def read_config_file():
    """
    Read the config file and return a list of (folder, remote_url, branch).
    """
    config_entries = []
    try:
        with open(CONFIG_FILE_PATH, 'r') as config_file:
            for line in config_file:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 3:
                        folder, remote_url, branch = parts
                        config_entries.append((folder, remote_url, branch))
    except FileNotFoundError:
        print(f"Config file not found at {CONFIG_FILE_PATH}. Creating one.")
        create_config_file()
    return config_entries

def create_config_file():
    """
    Create the config file if it doesn't exist.
    """
    default_config = """
    # Example config file format:
    # folder_location remote_url branch
    # /path/to/folder1 git@github.com:user/repo1.git master
    # /path/to/folder2 git@github.com:user/repo2.git main
    """
    with open(CONFIG_FILE_PATH, 'w') as config_file:
        config_file.write(default_config.strip())
    print(f"Config file created at {CONFIG_FILE_PATH}.")

def get_remote_default_branch(repo_path, remote_url):
    """
    Get the default branch from the remote URL if it's not specified in the config.
    """
    result = subprocess.run(
        ["git", "-C", repo_path, "remote", "show", "origin"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "HEAD branch" in line:
                return line.split(":")[1].strip()
    return None

def ensure_correct_branch(repo_path, remote_branch):
    """
    Ensure the local repository is on the specified branch (either main or master).
    """
    # Get the current local branch
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    current_branch = result.stdout.strip()

    if current_branch != remote_branch:
        print(f"Switching to branch '{remote_branch}' in {repo_path}...")
        subprocess.run(["git", "-C", repo_path, "checkout", remote_branch])

def commit_and_push(repo_path, remote_url, branch):
    """
    Commit and push changes to the remote repository.
    """
    try:
        # Ensure we are on the correct branch before pushing
        ensure_correct_branch(repo_path, branch)
        
        # Set the remote URL for the repository
        subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", remote_url])

        # Add all changes
        subprocess.run(["git", "-C", repo_path, "add", "."])

        # Commit the changes
        commit_message = "Backup on {}".format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message])

        # Push the changes
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

        # Set the remote URL
        subprocess.run(["git", "-C", folder, "remote", "add", "origin", remote_url])

        print(f"Initialized and set remote URL for {folder}.")

    # Commit and push changes
    commit_and_push(folder, remote_url, branch)

def main():
    """
    Main function to periodically read config, check folders, and perform backups.
    """
    while True:
        config_entries = read_config_file()
        
        for folder, remote_url, branch in config_entries:
            if os.path.isdir(folder):
                print(f"Processing folder: {folder}")
                process_folder(folder, remote_url, branch)
            else:
                print(f"Folder {folder} does not exist. Skipping...")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
