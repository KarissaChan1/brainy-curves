import os
import subprocess
import rpy2.robjects as ro
import pandas as pd
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import ListVector
import argparse
import pickle

# Activate pandas-to-R conversion
pandas2ri.activate()

def check_r_installed():
    """Check if R is installed and accessible."""
    try:
        subprocess.run(["R", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("R is installed.")
    except FileNotFoundError:
        raise RuntimeError("R is not installed. Run setup/install_r.py first.")

def run_r_script_from_file(script_path, **kwargs):
    """
    Runs an external R script using rpy2.

    Parameters:
    - script_path (str): Path to the R script file.
    - kwargs: Key-value arguments to pass into the R script as variables.

    Returns:
    - result: The result of the last evaluated R expression in the script.
    """
    try:
        # Pass Python variables to R environment
        for key, value in kwargs.items():
            ro.globalenv[key] = value

        # Load and run the R script
        with open(script_path, "r") as r_file:
            r_code = r_file.read()
        result = ro.r(r_code)
        return result
    except Exception as e:
        print(f"Error while running R script:\n{str(e)}")
        raise

def convert_r_object(r_obj):
    """
    Recursively converts R objects to Python-friendly formats.
    """
    if isinstance(r_obj, ro.vectors.ListVector):
        # Convert ListVector recursively
        return {k: convert_r_object(v) for k, v in r_obj.items()}
    elif isinstance(r_obj, ro.vectors.BoolVector):
        # Convert BoolVector (logical in R)
        return [None if x is ro.NA_Logical else bool(x) for x in r_obj]
    elif isinstance(r_obj, ro.vectors.FloatVector) or isinstance(r_obj, ro.vectors.IntVector):
        # Convert numeric/int vectors
        return [None if x is ro.NA_Real else x for x in r_obj]
    elif isinstance(r_obj, ro.rinterface.NULLType):
        # Convert R NULL to Python None
        return None
    elif hasattr(r_obj, "names"):  # Handle named vectors or data frames
        return {k: convert_r_object(v) for k, v in zip(r_obj.names, list(r_obj))}
    return r_obj

def compute_growth_curves(input_data, save_path, biomarkers, tissue_column, tissue_types, sex_column, sex_labels, age_column, disease_tissue):
    # Path to the R script
    r_script_path = "./growth_curves/growth_curves.R"

    results = {}
    for s in sex_labels:
        plot_disease = False
        filtered_input_data = input_data[input_data[sex_column] == s]
        if disease_tissue:
            available_disease_tissues = set(filtered_input_data[tissue_column].unique())
            if all(label in available_disease_tissues for label in disease_tissue):
                plot_disease = True
            else:
                plot_disease = False
        for t in tissue_types:
            for biomarker in biomarkers:
                model_params = {}
                r_input_data = ro.conversion.py2rpy(filtered_input_data)

                try:
                    if plot_disease==True:

                        result = run_r_script_from_file(
                            r_script_path,
                            input_data=r_input_data,
                            column_x= age_column,
                            column_y=biomarker,
                            tissue_column=tissue_column,
                            tissue =t,
                            sex =s,
                            disease_tissue = disease_tissue,
                            save_path = save_path
                        )
                    else:
                        result = run_r_script_from_file(
                            r_script_path,
                            input_data=r_input_data,
                            column_x= age_column,
                            column_y=biomarker,
                            tissue_column=tissue_column,
                            tissue =t,
                            sex =s,
                            save_path = save_path
                        )
                    
                    # Structure the result in the results dictionary
                    if t not in results:
                        results[t] = {}
                    if s not in results[t]:
                        results[t][s] = {}
                    
                    model_params = {
                        "mu": convert_r_object(result.rx2("mu")),
                        "sigma": convert_r_object(result.rx2("sigma")),
                        "nu": convert_r_object(result.rx2("nu")),
                        "tau": convert_r_object(result.rx2("tau")),
                        "coefs": convert_r_object(result.rx2("coefficients")),
                    }
                    # Store the result for the current biomarker
                    results[t][s][biomarker] = {
                        "model_parameters": model_params,
                        "centiles": pandas2ri.rpy2py(result.rx2("centile_data"))
                    }

                except Exception as e:
                    print(f"Error: {str(e)}")
    
    pickle_file = os.path.join(save_path, "results.pkl")
    with open(pickle_file, "wb") as pkl_file:  # Open in binary write mode
        pickle.dump(results, pkl_file)

    print(f"Results saved to {pickle_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_path', required=True, dest='input_path',
                        help='Input spreadsheet path and filename')
    parser.add_argument('-a', '--age_col', required=True, dest='age_col',
                        help='Age column name')
    parser.add_argument('-t', '--tissue_types',nargs='+', required=False, dest='tissue_types',
                        help='Tissue types to plot. If none, default is GM and WM')
    parser.add_argument('-d', '--disease_tissue',nargs='+', required=False, dest='disease_tissue',
                        help='Disease tissue data points to plot on top of growth curves')
    parser.add_argument('-b', '--biomarker_columns', nargs='+',required=True, dest='biomarker_columns',
                        help='List of biomarkers to plot')
    parser.add_argument('-s', '--save_path', required=True, dest='save_path',
                        help='Path to save directory')

    args = parser.parse_args()
    input_path = args.input_path
    tissue_types = args.tissue_types
    disease = args.disease_tissue
    age_col = args.age_col
    biomarkers = args.biomarker_columns
    save_path = args.save_path
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    if not tissue_types:
        tissue_types = ['GM','WM']

    # Input data from Python
    input_data = pd.read_excel(input_path)

    # Preprocess input data (ensure columns are there)
    sex_column = next((col for col in input_data.columns if col.lower() == "sex"), None)
    tissue_column = next((col for col in input_data.columns if "tissue" in col.lower()), None)

    if not sex_column:
        raise ValueError("No column found for sex - check column name")
    if not tissue_column:
        raise ValueError("No column found for tissue - check column name")
    
    input_data = input_data.dropna(subset=[sex_column, tissue_column])
    unique_sex_labels = input_data[sex_column].unique()

    # check R installation before starting
    check_r_installed()

    # compute 
    compute_growth_curves(input_data, save_path, biomarkers, tissue_column, tissue_types, sex_column, unique_sex_labels, age_col, disease)

# Example Usage
if __name__ == "__main__":

    main()