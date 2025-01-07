#!/bin/bash

# Installation script for Backup Daemon Service

# Fetch current directory where the script is run from
SCRIPT_PATH="$(pwd)/backup.py"
WORKING_DIR="$(pwd)"

# Fetch the current user and group
USER=$(whoami)
GROUP=$(id -gn)

SERVICE_NAME="backup_daemon"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Function to create a systemd service file
create_service_file() {
    echo "Creating systemd service file at $SERVICE_FILE..."

    # Create the systemd service file
    sudo bash -c "cat > $SERVICE_FILE <<EOF
[Unit]
Description=Backup Daemon Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 $SCRIPT_PATH
WorkingDirectory=$WORKING_DIR
Restart=always
User=$USER
Group=$GROUP
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

    echo "Service file created."
}

# Function to reload systemd, enable, and start the service
setup_service() {
    echo "Reloading systemd and enabling the service..."
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME.service
    sudo systemctl start $SERVICE_NAME.service

    echo "Service $SERVICE_NAME is now running."
}

# Main function
main() {
    echo "Backup Daemon Installer Script"
    
    # Create systemd service file
    create_service_file
    
    # Set up and start the service
    setup_service
    
    echo "Installation complete!"
    echo "Use 'sudo systemctl status $SERVICE_NAME.service' to check the service status."
    echo "Use 'journalctl -u $SERVICE_NAME.service -f' to view logs."
}

# Run the main function
main
