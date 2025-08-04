# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup
```bash
pip install -r requirements.txt
```

### Main workflow commands
```bash
# Start new lottery run from PDF
python lottery.py PosthoornLotto.pdf

# Show current standings and add new draw (interactive)
python lottery.py
```

### Optional filter configuration
Create a `.env` file with `FILTER_FAMILY=FamilyName` to automatically show future winner analysis for that family.

## Architecture Overview

This is a unified lottery analysis system that tracks participants' numbers against weekly draws and maintains persistent progress data.

### Core Component

**lottery.py**: Unified lottery management system that combines all functionality:
- PDF parsing using pdfplumber to extract participant data (names and 10 chosen numbers)
- Persistent progress tracking via `LotteryTracker` class with JSON state storage
- Interactive draw processing with colored output (intense green for new matches, regular green for previous)
- Future winner analysis for filtered families (configurable via .env)
- Automatic date suggestion and validation

### Data Flow

1. PDF → `lottery.py` → `data/lottery_participants.csv` (participant numbers)
2. Weekly draws → `lottery.py` → `data/trekking.csv` (draw history) 
3. Progress tracking → `data/lottery_progress.json` (cumulative correct numbers per player)
4. Optional filter → `.env` file → automatic future winner analysis

### Key Features

- **Unified Interface**: Single script handles all lottery operations
- **Persistent Progress**: Maintains cumulative correct numbers across all draws
- **Colored Output**: Uses termcolor to highlight newly correct numbers (intense green) vs previously correct (regular green)
- **Interactive Mode**: Prompts for draw date and numbers with validation
- **Family Analysis**: Automatic future winner analysis when filter is configured
- **Data Integrity**: Automatic CSV creation and JSON progress file management

### Data Directory Structure
```
data/
├── lottery_participants.csv    # Participant names and chosen numbers
├── trekking.csv               # Weekly draw results
└── lottery_progress.json      # Cumulative progress tracking
```