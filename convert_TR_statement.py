# #####################################################################################
# This script reads a TradeRepublic PDF export and converts it to a Pandas dataframe ##
# #####################################################################################

import pandas as pd
import pdfplumber
import re
import os

# Input file
file_path = '/my/path/to/Account statement.pdf'

# Check if file exists
if not os.path.exists(file_path):
    raise FileNotFoundError(f"The file {file_path} does not exist.")

# Patterns
type_pattern = re.compile(r'(Kartentransaktion|Erträge|Prämie|Zinszahlung|Überweisung|Handel|Steuern|Gebühren)')
transaction_pattern = re.compile(f"{type_pattern.pattern}+.*")
date_pattern = re.compile(r'^\d{2}\s+(Jan\.|Feb\.|März|Apr\.|Mai|Juni|Juli|Aug\.|Sep\.|Okt\.|Nov\.|Dez\.)')
year_pattern = re.compile(r'^\b\d{4}\b')
combined_pattern = re.compile(f'({transaction_pattern.pattern})|({date_pattern.pattern})|({year_pattern.pattern})')

try:
    # Extract and clean text from PDF
    with pdfplumber.open(file_path) as pdf:
        extracted_text = [line['text'].strip() for page in pdf.pages for line in
                          page.extract_text_lines(keep_blank_chars=False)]

    if not extracted_text:
        raise ValueError("No text could be extracted from the PDF.")

    # Filter and process lines based on patterns
    filtered_text = [
        combined_pattern.match(line).group()
        for line in extracted_text
        if combined_pattern.search(line)
        ]

    if len(filtered_text) < 3:
        raise ValueError("Filtered text does not contain enough lines to process.")

    # Concatenate every 3 lines, put a semicolon in front of values, remove all €s and append a semicolon to transaction
    result = [
        type_pattern.sub(r'\g<0>;', re.sub(r" €", '', re.sub(r"\s*(\d*\.?\d+,\d{2})", r';\1',
                                                             f"{filtered_text[i]} {filtered_text[i + 2]};{filtered_text[i + 1]}")))
        for i in range(0, len(filtered_text) - 2, 3)
    ]

    if not result:
        raise ValueError("No valid data to add to DataFrame.")

    # Fill the DataFrame
    try:
        df = pd.DataFrame([line.split(';') for line in result], columns=['Datum', 'Typ', 'Text', 'Betrag', 'Saldo'])
    except Exception as e:
        raise ValueError(f"Error creating DataFrame: {e}")

    # Looking at the dataframe
    # print(df.to_string())

    # Write the DataFrame to a CSV file
    output_file = file_path + '.csv'
    try:
        df.to_csv(output_file, index=False, sep=';')
        print(f"Data successfully written to {output_file}")
    except Exception as e:
        raise IOError(f"Error writing DataFrame to CSV: {e}")

except FileNotFoundError as fnf_error:
    print(fnf_error)
except ValueError as ve:
    print(ve)
except IOError as io_error:
    print(io_error)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
