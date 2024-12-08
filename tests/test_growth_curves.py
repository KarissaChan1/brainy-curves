import os
import shutil
import subprocess
from pathlib import Path
from growth_curves.main import main

def test_growth_curves_main():
    tests_dir = Path(__file__).parent
    data_dir = tests_dir / "data/"
    save_path = tests_dir / 'test_output/'
    
    if save_path.exists():
        shutil.rmtree(save_path)

    # Construct the CLI command
    command = [
        "growth_curves",
        "-i", os.path.join(data_dir, "HSC_Normals_Biomarkers_FINAL.xlsx"),
        "-a", "Age_yrs_",
        "-b", "Intensity", "Damage_Micro",
        "-d", "NAWM",
        "-s", save_path.as_posix()
    ]

    # Run the command and capture the result
    result = subprocess.run(command, capture_output=True, text=True)

    # Print command output for debugging
    print(result.stdout)
    print(result.stderr)

    # Assert the command ran successfully
    assert result.returncode == 0
    assert save_path.exists()  # Ensure the output directory is created

