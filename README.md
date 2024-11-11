# Lottery Analysis Project

## Overview

This project is designed to manage and analyze lottery participants and their chances of winning. It consists of several scripts that handle different aspects of the lottery process.

## Usage

### 1. Import Participants

When a new lottery run starts, participants are imported by running `pdf_parser.py`. This script parses a PDF file containing participant data and saves it to a CSV file.

```bash
python pdf_parser.py path/to/lottery_participants.pdf
```

### 2. Update Lottery Standings

Every week, `drawing.py` is run to update the dataset with the numbers drawn that week. This script will output the current lottery standings.

```bash
python drawing.py
```

### 3. Analyze Future Winners

To see how much chance of a prize a certain group of people have, run `future_winners.py` with the name of the group you're looking for as an argument.

```bash
python future_winners.py -en GroupName
```

## Setup

### Requirements

The project dependencies are listed in `requirements.txt`. To set up the project, install the required packages using pip:

```bash
pip install -r requirements.txt
```

This will ensure that all necessary libraries are installed for the scripts to run correctly.

## Files

- `pdf_parser.py`: Parses participant data from a PDF file.
- `drawing.py`: Updates the dataset with the numbers drawn each week.
- `future_winners.py`: Analyzes the chances of a certain group of people winning the lottery.
- `requirements.txt`: Lists the dependencies required for the project.

## License

This project is licensed under the MIT License.