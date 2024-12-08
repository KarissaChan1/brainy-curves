import subprocess
import platform
import os

def install_r():
    """Install R based on the operating system."""
    system = platform.system()
    try:
        if system == "Linux":
            # Install R for Debian/Ubuntu
            print("Detected Linux OS. Installing R...")
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "r-base"], check=True)
        elif system == "Darwin":
            # Install R for macOS using Homebrew
            print("Detected macOS. Installing R via Homebrew...")
            subprocess.run(["brew", "install", "r"], check=True)
        elif system == "Windows":
            # Install R for Windows
            print("Detected Windows OS. Downloading and Installing R...")
            r_installer_url = "https://cran.r-project.org/bin/windows/base/R-4.3.0-win.exe"
            installer_path = "R_installer.exe"
            # Download the installer
            subprocess.run(["curl", "-o", installer_path, r_installer_url], check=True)
            # Run the installer silently
            subprocess.run([installer_path, "/SILENT"], check=True)
        else:
            raise RuntimeError("Unsupported Operating System")
    except subprocess.CalledProcessError as e:
        print(f"Error during R installation: {e}")
        raise

def check_r_installed():
    """Check if R is installed."""
    try:
        result = subprocess.run(["R", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        print("R is installed.")
        print(result.stdout)
        return True
    except FileNotFoundError:
        print("R is not installed.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking R installation: {e}")
        return False

def set_environment_variables():
    """Set environment variables for R."""
    try:
        r_home = subprocess.check_output(["R", "RHOME"], text=True).strip()
        os.environ["R_HOME"] = r_home
        print(f"R_HOME set to: {r_home}")
    except subprocess.CalledProcessError as e:
        print(f"Error setting R_HOME: {e}")
        raise

def install_r_packages(packages):
    """Install required R packages."""
    for package in packages:
        print(f"Installing R package: {package}")
        subprocess.run(
            ["R", "-e", f"if (!require('{package}', quietly = TRUE)) install.packages('{package}', repos='http://cran.r-project.org')"],
            check=True
        )

# Main logic
if __name__ == "__main__":
    # Check if R is installed
    if not check_r_installed():
        install_r()
        if not check_r_installed():
            raise RuntimeError("Failed to install R.")

    # Set R environment variables
    set_environment_variables()

    # Install required R packages
    required_packages = ["ggplot2", "gamlss", "tidyverse", "openxlsx", "dplyr", "data.table", "writexl"]
    install_r_packages(required_packages)