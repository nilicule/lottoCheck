import csv
import re
import pdfplumber
import argparse
from collections import defaultdict

def parse_pdf_lottery_data(pdf_path):
    participants = []
    last_name = None
    name_count = defaultdict(int)

    # Open the PDF file
    with pdfplumber.open(pdf_path) as pdf:
        # Process each page
        for page in pdf.pages:
            # Extract text from the page
            text = page.extract_text()

            # Split into lines and process each line
            lines = text.split('\n')

            for line in lines:
                # Skip header lines and empty lines
                if not line.strip() or line.startswith('DEELNEMER') or 'TREKKING' in line or \
                        'BEDRAG' in line or 'POT' in line or '€' in line or \
                        'DEELNEMERS:' in line or 'INLEG' in line:
                    continue

                # Try to extract participant data
                match = re.match(r'^\d{1,3}\s+(.+?)\s+(\d+(?:\s+\d+){9,})', line)

                if match:
                    name = match.group(1)
                    # Extract all numbers from the second group
                    numbers = re.findall(r'\d+', match.group(2))[:10]  # Take only first 10 numbers

                    # Clean up the name
                    name = re.sub(r'\s+\d+\s*$', '', name)  # Remove trailing numbers
                    name = re.sub(r'\s+X_GOED\s*$', '', name)  # Remove X_GOED

                    # Only add if we have exactly 10 numbers
                    if len(numbers) == 10:
                        name_count[name] += 1
                        unique_name = f"{name} ({name_count[name]})" if name_count[name] > 1 else name
                        participants.append({
                            'name': unique_name.strip(),
                            'numbers': [int(num) for num in numbers]
                        })
                        last_name = name.strip()
                else:
                    # If no match, assume it's a continuation of the last name
                    if last_name:
                        last_name += ' ' + line.strip()
                        participants[-1]['name'] = last_name

    return participants


def save_to_csv(participants, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['Name', 'Number1', 'Number2', 'Number3', 'Number4', 'Number5',
                         'Number6', 'Number7', 'Number8', 'Number9', 'Number10'])

        # Write data
        for p in participants:
            writer.writerow([p['name']] + p['numbers'])


def process_lottery_pdf(pdf_path):
    output_csv = 'data/lottery_participants.csv'
    try:
        # Parse the PDF data
        participants = parse_pdf_lottery_data(pdf_path)

        # Save to CSV
        save_to_csv(participants, output_csv)

        # Print statistics
        print(f"Successfully processed {len(participants)} participants")
        print(f"Data saved to {output_csv}")

        # Print first few entries as verification
        for p in participants[:10]:
            print(f"{p['name']}: {p['numbers']}")

        return True

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a lottery PDF file.')
    parser.add_argument('pdf_path', help='Path to the PDF file to process')

    args = parser.parse_args()

    process_lottery_pdf(args.pdf_path)