# Tool for Generating GAMLSS Growth Curves
This tool replicates the GAMLSS growth curve construction in the following publication: [Developmental Curves of the Paediatric Brain Using FLAIR MRI Texture Biomarkers](https://journals.sagepub.com/doi/10.1177/08465371241262175) 

It is implemented using Python to run on command line, and uses rpy2 to run an R script for the gamlss package.
Normative growth curves (centiles 3, 15, 50, 85, 97) are plotted by sex, tissue, and biomarker, with an option to overlay diseased tissue data points onto the centile curves.

### Setup Instructions (do this before moving on to Usage step)
**Install R (versioni 4.4.2) and Required Packages**:
   Run the following command:
   ```
   cd tiny-curvy-brains
   python setup/install_r.py
   ```
This checks for any existing R versions and installs R version 4.4.2 based on your operating system, along with required packages:
- ggplot2
- gamlss
- dplyr

### Usage
1. Install poetry: Visit the official poetry website (https://python-poetry.org/docs/) and follow the installation instructions for your operating system.
2. Clone the repo at: KarissaChan1/tiny-curvy-brains
3. run cd tiny-curvy-brains, enter the project directory.
4. Run poetry install, to set up all project dependencies within a dedicated virtual environment. Note: This project uses Poetry version 1.8.3.
5. Run poetry shell, activate the virtual environment.
6. View the help for usage:
```
usage: growth_curves [-h] -i INPUT_PATH -a AGE_COL
                     [-t TISSUE_TYPES [TISSUE_TYPES ...]]
                     [-d DISEASE_TISSUE [DISEASE_TISSUE ...]] -b
                     BIOMARKER_COLUMNS [BIOMARKER_COLUMNS ...] -s SAVE_PATH

options:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input_path INPUT_PATH
                        Input spreadsheet path and filename
  -a AGE_COL, --age_col AGE_COL
                        Age column name
  -t TISSUE_TYPES [TISSUE_TYPES ...], --tissue_types TISSUE_TYPES [TISSUE_TYPES ...]
                        Tissue types to plot. If none, default is GM and WM
  -d DISEASE_TISSUE [DISEASE_TISSUE ...], --disease_tissue DISEASE_TISSUE [DISEASE_TISSUE ...]
                        Disease tissue data points to plot on top of growth
                        curves
  -b BIOMARKER_COLUMNS [BIOMARKER_COLUMNS ...], --biomarker_columns BIOMARKER_COLUMNS [BIOMARKER_COLUMNS ...]
                        List of biomarkers to plot
  -s SAVE_PATH, --save_path SAVE_PATH
                        Path to save directory
```

Example command:

To plot normative growth curves for Intensity, with disease tissue (NAWM and ED) data points overlaid:
```
growth_curves -i ./tests/data/HSC_Normals_Biomarkers_FINAL.xlsx -a Age_yrs_ -b Intensity -s ./tests/test_output/ -d NAWM
```

Example output plot:
![Female WM Intensity growth curve with NAWM overlaid](https://github.com/KarissaChan1/tiny-curvy-brains/blob/main/readme_pics/centile_plot_WM_F_Intensity_disease%20copy.png?raw=true)
