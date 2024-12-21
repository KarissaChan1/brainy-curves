import os
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import pickle

def generate_output_report(results_folder, disease_tissue, run_time):
    '''
    working_path: output path
    results_folder: folder containing results pickle file
    run_time: run time of the model fitting
    '''
    print('Generating output report...')

    # Load results from pickle file
    with open(os.path.join(results_folder, 'results.pkl'), 'rb') as f:
        results = pickle.load(f)

    # Get Run time
    hours, remainder = divmod(run_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the run time as X h X min X s
    formatted_run_time = f"{int(hours)} h {int(minutes)} min {int(seconds)} s"

    # Create a PDF using SimpleDocTemplate
    pdf = SimpleDocTemplate(os.path.join(results_folder, 'growth_curves_output_report.pdf'), pagesize=letter)
    
    styles = getSampleStyleSheet()
    figure_caption_style = ParagraphStyle(
    'CenteredStyle', 
    parent=styles['Italic'],
    alignment=TA_CENTER
    )
    content = []

    title = Paragraph("GAMLSS Growth Curves Report", styles['Title'])
    content.append(title)

    description = Paragraph(
        f"This is the output report for fitted GAMLSS models ran on: {datetime.now()} <br/><br/>"
        f"Run time: {formatted_run_time}  <br/>", styles['BodyText'])
    content.append(description)
    
    # Add Model Parameters section
    heading = Paragraph("Optimized model parameters", styles['Heading2'])
    content.append(heading)
    content.append(Spacer(1, 12))

    # Get all unique biomarkers
    biomarkers = set()
    for tissue in results:
        for gender in results[tissue]:
            biomarkers.update(results[tissue][gender].keys())

    # Loop through biomarkers first, then tissues
    for biomarker in biomarkers:
        biomarker_heading = Paragraph(f"Biomarker: {biomarker}", styles['Heading3'])
        content.append(biomarker_heading)
        content.append(Spacer(1, 12))

        for tissue in results.keys():
            # Skip if biomarker not present for this tissue in either gender
            if not any(biomarker in results[tissue][gender] for gender in results[tissue]):
                continue

            # First add parameter table (existing code)
            table_caption = Paragraph(
                f"{tissue} Model Parameters for Male and Female",
                figure_caption_style
            )
            content.append(table_caption)
            content.append(Spacer(1, 6))
            
            # Create table data with three columns
            data = [['Parameter', 'Value (M)', 'Value (F)']]  # Header row
            
            # Get parameters for both genders
            params_m = results[tissue]['M'][biomarker]['model_parameters'] if biomarker in results[tissue]['M'] else None
            params_f = results[tissue]['F'][biomarker]['model_parameters'] if biomarker in results[tissue]['F'] else None

            # Get all unique parameter names
            param_names = set()
            if params_m:
                param_names.update(params_m['coefs'].keys())
            if params_f:
                param_names.update(params_f['coefs'].keys())

            # Add coefficients
            for param_name in sorted(param_names):
                row = [str(param_name)]
                # Add male value
                if params_m and param_name in params_m['coefs']:
                    row.append(f"{float(params_m['coefs'][param_name][0]):.6f}")
                else:
                    row.append("N/A")
                # Add female value
                if params_f and param_name in params_f['coefs']:
                    row.append(f"{float(params_f['coefs'][param_name][0]):.6f}")
                else:
                    row.append("N/A")
                data.append(row)

            # Add distribution parameters if applicable
            for param in ['mu', 'sigma', 'nu', 'tau']:
                row = [param]
                # Add male value
                if params_m and param in params_m:
                    row.append(str(params_m[param][0]))
                else:
                    row.append("N/A")
                # Add female value
                if params_f and param in params_f:
                    row.append(str(params_f[param][0]))
                else:
                    row.append("N/A")
                data.append(row)

            # Create and style table
            param_table = Table(data)
            param_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
                
            content.append(param_table)
            content.append(Spacer(1, 12))

            # Check for existence of growth curves for each gender
            figure_images = []
            has_figures = False
            for gender in ['M', 'F']:
                # Try disease plot first if disease_tissue is not None
                if disease_tissue is not None:
                    img_path = os.path.join(results_folder, f"centile_plot_{tissue}_{gender}_{biomarker}_disease.png")
                    if not os.path.exists(img_path):
                        # If disease plot doesn't exist, try regular plot
                        img_path = os.path.join(results_folder, f"centile_plot_{tissue}_{gender}_{biomarker}.png")
                else:
                    img_path = os.path.join(results_folder, f"centile_plot_{tissue}_{gender}_{biomarker}.png")

                if os.path.exists(img_path):
                    img = Image(img_path, width=3*inch, height=3*inch)
                    figure_images.append(img)
                    has_figures = True
                else:
                    figure_images.append(Paragraph(f"No growth curve available for {gender}", styles['Normal']))

            # Only add figure table and caption if at least one figure exists
            if has_figures:
                figure_table = Table([[figure_images[0], figure_images[1]]])
                figure_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))

                # Modify caption based on whether it's a disease tissue
                caption_text = f"Growth curves of males and females in {tissue}"
                if disease_tissue is not None:
                    caption_text += " (Disease Tissue)"
                
                figure_caption = Paragraph(caption_text, figure_caption_style)
                
                content.append(figure_table)
                content.append(Spacer(1, 6))
                content.append(figure_caption)
                content.append(Spacer(1, 12))

            # Add page break after each tissue
            content.append(PageBreak())

    # Build the PDF document
    pdf.build(content)