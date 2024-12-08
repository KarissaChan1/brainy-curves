# Function to check and install required packages
check_and_install <- function(pkg) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg, repos = "http://cran.r-project.org")
    library(pkg, character.only = TRUE)
  }
}

# List of required packages
required_packages <- c("ggplot2", "gamlss", "dplyr", "readr", "data.table")

# Check and install each package
for (pkg in required_packages) {
  check_and_install(pkg)
}

# Print a message to confirm packages are loaded
print("All required R packages are installed and loaded.")

# run script
print("Running R script...")

library(ggplot2)
library(dplyr)
library(readr)


# Check if input_data exists
if (!exists("input_data")) {
  stop("Error: input_data is missing!")
}

# Check for columns specified by user
if (!exists("column_x") || !exists("column_y")) {
  stop("Error: column names (column_x, column_y) are missing!")
}
print(paste("Column of interest (x):", column_x))
print(paste("Column of interest (y):", column_y))

input_data_tissue <- subset(input_data, input_data[[tissue_column]] == tissue)
input_data_tissue <- na.omit(input_data_tissue)
if (nrow(input_data_tissue) == 0) {
  stop("Error: No valid data in input_data_tissue after filtering and removing NAs.")
}

# for y range of disease plots
if (exists("disease_tissue") && !is.null(disease_tissue)) {
    tissue_and_disease_values <- c(tissue, disease_tissue)
    tissue_and_disease <- subset(input_data, input_data[[tissue_column]] %in% tissue_and_disease_values)
}

#GAMLSS MODELS
dynamic_formula <- as.formula(paste(column_y, "~ pb(", column_x, ")"))

# Fit the gamlss models
bct_model <- gamlss(
  formula = dynamic_formula,
  sigma.formula = as.formula(paste("~ pb(", column_x, ")")),
  nu.formula = as.formula(paste("~ pbz(", column_x, ")")),
  tau.formula = as.formula(paste("~ pbz(", column_x, ")")),
  family = BCT,
  data = input_data_tissue,
  control = gamlss.control(n.cyc = 100)
)

bccg_model <- gamlss(
  formula = dynamic_formula,
  sigma.formula = as.formula(paste("~ pb(", column_x, ")")),
  nu.formula = as.formula(paste("~ pbz(", column_x, ")")),
  tau.formula = as.formula(paste("~ pbz(", column_x, ")")),
  family = BCCG,
  data = input_data_tissue,
  control = gamlss.control(n.cyc = 100)
)

bcpe_model <- gamlss(
  formula = dynamic_formula,
  sigma.formula = as.formula(paste("~ pb(", column_x, ")")),
  nu.formula = as.formula(paste("~ pbz(", column_x, ")")),
  tau.formula = as.formula(paste("~ pbz(", column_x, ")")),
  family = BCPE,
  data = input_data_tissue,
  control = gamlss.control(n.cyc = 100)
)

aic_all <- AIC(bct_model,bccg_model,bcpe_model)

# Identify the model with the lowest AIC
best_model <- aic_all[which.min(aic_all$AIC), ]

best_model_name <- rownames(best_model)

# Extract the best model object
best_model_object <- get(best_model_name)

# COMPUTE NORMATIVE CENTILES
output_file <- paste0(save_path, "/centile_plot_", tissue, "_", sex,"_",column_y, ".png")
png(filename = output_file, 
    width = 3000,  # Width in pixels
    height = 2400, # Height in pixels
    res = 300      # Resolution in DPI
)
# Plot the centiles
centile_data <- centiles(
  best_model_object, 
  xvar = input_data_tissue[[column_x]], 
  xlab = column_x, 
  ylab = column_y, 
  main=paste("Centiles of", column_y, "in", tissue, "-", sex),
  cent = c(3, 15, 50, 85, 97), 
  col.centiles = c("grey", "black", "red", "black", "grey"),
  legend = FALSE,
  ylim = range(input_data_tissue[[column_y]]),
  save=TRUE
)
dev.off()
print(paste("Centile plot saved as:", output_file))

# ADD DISEASE DATA
# If disease_tissue is specified, overlay disease-specific points and labels
output_file_disease <- paste0(save_path, "/centile_plot_", tissue, "_", sex,"_",column_y, "_disease.png")
png(filename = output_file_disease, 
    width = 3000,  # Width in pixels
    height = 2400, # Height in pixels
    res = 300      # Resolution in DPI
)
if (exists("disease_tissue") && !is.null(disease_tissue)) {
    # Plot the centiles
    centiles(
    best_model_object, 
    xvar = input_data_tissue[[column_x]], 
    xlab = column_x, 
    ylab = column_y, 
    main=paste("Centiles of", column_y, "in", tissue, "-", sex),
    cent = c(3, 15, 50, 85, 97), 
    col.centiles = c("grey", "black", "red", "black", "grey"),
    legend = FALSE,
    ylim = range(tissue_and_disease[[column_y]])
    )
    input_data_disease <- subset(input_data, input_data[[tissue_column]] %in% disease_tissue)
    for (dt in disease_tissue) {
        dt_data <- subset(input_data_disease, input_data_disease[[tissue_column]] == dt)
        if (nrow(dt_data) == 0) {
        warning(paste("No valid data for disease tissue:", dt, "Skipping this tissue."))
        next
        }
        
        # Add points for the current disease tissue
        points(
        x = dt_data[[column_x]],
        y = dt_data[[column_y]],
        col = "blue",
        pch = 21,
        bg = "blue"
        )
        
        # Add labels for the current disease tissue
        text(
        x = dt_data[[column_x]],
        y = dt_data[[column_y]],
        labels = dt,
        pos = 4,  # Position of the text relative to the points
        cex = 0.8,  # Text size
        col = "blue"
        )
    }
    dev.off()
    print(paste("Disease plot saved as:", output_file_disease))
}

## get results to return
# Convert centiles to a data frame
centile_df <- as.data.frame(centile_data)

# Extract coefficients (always available)
coefficients_values <- coef(best_model_object)

mu_values <- if ("mu" %in% names(best_model_object$parameters)) {
  if (all(is.na(fitted(best_model_object, what = "mu")))) {
    "NA"
  } else {
    as.numeric(fitted(best_model_object, what = "mu"))
  }
} else {
  "Not Applicable"
}

sigma_values <- if ("sigma" %in% names(best_model_object$parameters)) {
  if (all(is.na(fitted(best_model_object, what = "sigma")))) {
    "NA"
  } else {
    as.numeric(fitted(best_model_object, what = "sigma"))
  }
} else {
  "Not Applicable"
}

nu_values <- if ("nu" %in% names(best_model_object$parameters)) {
  if (all(is.na(fitted(best_model_object, what = "nu")))) {
    "NA"
  } else {
    as.numeric(fitted(best_model_object, what = "nu"))
  }
} else {
  "Not Applicable"
}

tau_values <- if ("tau" %in% names(best_model_object$parameters)) {
  if (all(is.na(fitted(best_model_object, what = "tau")))) {
    "NA"
  } else {
    as.numeric(fitted(best_model_object, what = "tau"))
  }
} else {
  "Not Applicable"
}

# Return parameters to Python
result_list <- list(
    mu = mu_values,
    sigma = sigma_values,
    nu = nu_values,
    tau = tau_values,
    coefficients = as.list(coefficients_values),
    centile_data = centile_df
)

result_list