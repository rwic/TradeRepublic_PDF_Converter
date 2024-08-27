import re
import pdfplumber
import pandas as pd
import os


# Input file
file_path = '/path/to/your/Statement of securities account.pdf'

# Check if file exists
if not os.path.exists(file_path):
    raise FileNotFoundError(f"The file {file_path} does not exist.")

# Function to process and extract data from grouped lines
def process_group(lines):
    combined_text = " ".join(line.strip() for line in lines)

    # Compile the regex pattern
    pattern = re.compile(r'(?P<shares>\d*\.*\d*,\d{2,})\s+Stk\.\s+'
                         r'(?P<name>.+?)\s+'
                         r'(?P<price>\d*\.*\d*,\d{2,})\s+'
                         r'(?P<total>\d*\.*\d*,\d{2,})\s+(?P<type>.+?)\s+'
                         r'(?P<date>\d{2}\.\d{2}\.\d{4})\s+ISIN:\s+(?P<isin>[A-Z0-9]+)')
    match = pattern.search(combined_text)

    if match:
        return [
            match.group('shares'),
            match.group('name'),
            match.group('price'),
            match.group('total'),
            match.group('type'),
            match.group('date'),
            match.group('isin'),
        ]
    return None


# Extract text from PDF and process it
def extract_and_process_pdf(file_path):
    data = []
    entry_lines = []
    # entry_start_pattern = re.compile(r'^\d{1,3}(?:,\d+)\s+Stk\.')
    entry_start_pattern = re.compile(r'^\d*\.*\d*,\d{2,}\s+Stk\.\s+')

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                lines = page_text.splitlines()

                for line in lines:
                    if entry_start_pattern.match(line):
                        # If we're already collecting lines for an entry, process the previous group
                        if entry_lines:
                            result = process_group(entry_lines)
                            if result:
                                data.append(result)
                            entry_lines = []  # Reset for the new entry

                        # Start a new entry
                        entry_lines.append(line)
                    else:
                        # Add to the current entry group
                        entry_lines.append(line)

        # Don't forget to process the last group after the loop ends
        if entry_lines:
            result = process_group(entry_lines)
            if result:
                data.append(result)

    # Convert the extracted data to a DataFrame
    df = pd.DataFrame(data, columns=['Shares', 'Stock Name', 'Price per Share', 'Total Value', 'Type', 'Date', 'ISIN'])

    return df

try:
    # Process the PDF and get the DataFrame
    df = extract_and_process_pdf(file_path)

    # Display the DataFrame
    print(df.to_string())

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