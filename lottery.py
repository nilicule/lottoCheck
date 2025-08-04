#!/usr/bin/env python3
"""
Unified Lottery Management System

Usage:
    python lottery.py <pdf_file>     # Start new lottery run from PDF
    python lottery.py               # Show current standings and add new draw
"""

import csv
import re
import pdfplumber
import argparse
import os
import pandas as pd
from termcolor import colored
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def colored_intense(text, color):
    """Create an intense colored version of the text"""
    return f"\033[1m{colored(text, color)}\033[0m"


class LotteryManager:
    def __init__(self):
        self.progress_file = 'data/lottery_progress.json'
        self.participants_file = 'data/lottery_participants.csv'
        self.trekking_file = 'data/trekking.csv'
        self.progress = {
            'players': {},
            'processed_draws': []
        }
        self.load_progress()
        
    def load_progress(self):
        """Load existing progress data"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    self.progress['players'].update(saved_progress.get('players', {}))
                    self.progress['processed_draws'] = saved_progress.get('processed_draws', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading progress file: {e}")
                print("Starting with fresh progress file")
        else:
            print("No existing progress file found. Starting fresh.")
            
    def save_progress(self):
        """Save progress data"""
        os.makedirs('data', exist_ok=True)
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except IOError as e:
            print(f"Error saving progress file: {e}")

    def parse_pdf_lottery_data(self, pdf_path):
        """Parse participant data from PDF file"""
        participants = []
        last_name = None
        name_count = defaultdict(int)

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                for line in lines:
                    if not line.strip() or line.startswith('DEELNEMER') or 'TREKKING' in line or \
                            'BEDRAG' in line or 'POT' in line or '€' in line or \
                            'DEELNEMERS:' in line or 'INLEG' in line:
                        continue

                    match = re.match(r'^\d{1,3}\s+(.+?)\s+(\d+(?:\s+\d+){9,})', line)

                    if match:
                        name = match.group(1)
                        numbers = re.findall(r'\d+', match.group(2))[:10]

                        name = re.sub(r'\s+\d+\s*$', '', name)
                        name = re.sub(r'\s+X_GOED\s*$', '', name)

                        if len(numbers) == 10:
                            name_count[name] += 1
                            unique_name = f"{name} ({name_count[name]})" if name_count[name] > 1 else name
                            participants.append({
                                'name': unique_name.strip(),
                                'numbers': [int(num) for num in numbers]
                            })
                            last_name = name.strip()
                    else:
                        if last_name:
                            last_name += ' ' + line.strip()
                            participants[-1]['name'] = last_name

        return participants

    def save_participants_to_csv(self, participants):
        """Save participants to CSV file"""
        os.makedirs('data', exist_ok=True)
        with open(self.participants_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Number1', 'Number2', 'Number3', 'Number4', 'Number5',
                           'Number6', 'Number7', 'Number8', 'Number9', 'Number10'])
            for p in participants:
                writer.writerow([p['name']] + p['numbers'])

    def start_new_lottery(self, pdf_path):
        """Start a new lottery run from PDF"""
        if not os.path.isfile(pdf_path):
            print(f"Error: The file {pdf_path} does not exist.")
            return False

        try:
            participants = self.parse_pdf_lottery_data(pdf_path)
            self.save_participants_to_csv(participants)
            
            # Reset progress for new lottery
            self.progress = {'players': {}, 'processed_draws': []}
            self.save_progress()
            
            # Clear trekking data
            if os.path.exists(self.trekking_file):
                os.remove(self.trekking_file)

            print(f"Successfully processed {len(participants)} participants")
            print(f"Data saved to {self.participants_file}")
            print(f"\nFirst 10 participants:")
            for p in participants[:10]:
                print(f"  {p['name']}: {p['numbers']}")
                
            return True

        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return False

    def read_trekking(self):
        """Read trekking.csv, creating it if it doesn't exist"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.trekking_file):
            df = pd.DataFrame(columns=['date'] + [f'number{i}' for i in range(1, 7)])
            df.to_csv(self.trekking_file, index=False)
            return df
        
        return pd.read_csv(self.trekking_file)

    def parse_input(self):
        """Get lottery numbers from user input"""
        print("\nEnter 6 numbers (comma or space separated), or press Enter to quit:")
        user_input = input("Numbers: ").strip()

        if not user_input:
            return None

        try:
            numbers = user_input.replace(',', ' ').split()
            numbers = [int(n) for n in numbers]
            if len(numbers) != 6:
                print("Please enter exactly 6 numbers")
                return self.parse_input()
            if not all(1 <= n <= 45 for n in numbers):
                print("Numbers must be between 1 and 45")
                return self.parse_input()
            if len(set(numbers)) != 6:
                print("Numbers must be unique")
                return self.parse_input()
            return sorted(numbers)
        except ValueError:
            print("Please enter valid numbers")
            return self.parse_input()

    def get_draw_date(self):
        """Get draw date from user input"""
        trekking = self.read_trekking()
        
        if trekking.empty:
            suggested_date = datetime.now().strftime('%d-%b-%y')
        else:
            last_date = pd.to_datetime(trekking['date'].iloc[-1], format='%d-%b-%y')
            suggested_date = (last_date + pd.Timedelta(days=7)).strftime('%d-%b-%y')
        
        print(f"\nEnter draw date (suggested: {suggested_date}):")
        date_input = input("Date (DD-MMM-YY): ").strip()
        
        if not date_input:
            return suggested_date
        
        try:
            # Validate date format
            pd.to_datetime(date_input, format='%d-%b-%y')
            return date_input
        except:
            print("Invalid date format. Please use DD-MMM-YY (e.g., 04-Aug-25)")
            return self.get_draw_date()

    def add_to_trekking(self, numbers, draw_date):
        """Add new draw to trekking data"""
        trekking = self.read_trekking()
        
        new_row = {
            'date': draw_date,
            'number1': numbers[0],
            'number2': numbers[1],
            'number3': numbers[2],
            'number4': numbers[3],
            'number5': numbers[4],
            'number6': numbers[5]
        }
        trekking = pd.concat([trekking, pd.DataFrame([new_row])], ignore_index=True)
        trekking.to_csv(self.trekking_file, index=False)
        return draw_date

    def update_progress(self, player_results, draw_date):
        """Update player progress"""
        for name, correct_numbers in player_results:
            if name not in self.progress['players']:
                self.progress['players'][name] = {
                    'total_correct': 0,
                    'correct_numbers': []
                }

            current_correct = set(self.progress['players'][name]['correct_numbers'])
            new_correct = set(correct_numbers)
            all_correct = current_correct.union(new_correct)

            self.progress['players'][name]['correct_numbers'] = sorted(list(all_correct))
            self.progress['players'][name]['total_correct'] = len(all_correct)

        if draw_date not in self.progress['processed_draws']:
            self.progress['processed_draws'].append(draw_date)
        self.save_progress()

    def check_participants(self, winning_numbers, draw_date, is_latest_draw=False):
        """Check participants against winning numbers"""
        if not os.path.exists(self.participants_file):
            print("No participants file found. Please start a new lottery run first.")
            return

        participants = pd.read_csv(self.participants_file)

        print(f"\nResults for draw date: {draw_date}")
        print("=" * 70)
        print("Winning numbers:", " ".join(f"{n:2d}" for n in sorted(winning_numbers)))
        print("-" * 70)

        results = []
        player_results = []

        for idx, row in participants.iterrows():
            name = row['Name']
            numbers = sorted([row[f'Number{i}'] for i in range(1, 11)])

            previous_correct = set(self.progress['players'].get(name, {}).get('correct_numbers', []))
            correct_in_draw = set(n for n in numbers if n in winning_numbers)
            truly_new_correct = correct_in_draw - previous_correct if is_latest_draw else set()

            number_str = "["
            for n in numbers:
                if n in truly_new_correct:
                    number_str += colored_intense(f"{n:2d}", 'green') + " "
                elif n in previous_correct or n in correct_in_draw:
                    number_str += colored(f"{n:2d}", 'green') + " "
                else:
                    number_str += f"{n:2d} "
            number_str = number_str.rstrip() + "]"

            total_correct = len(previous_correct.union(correct_in_draw))
            new_correct = len(truly_new_correct) if is_latest_draw else 0

            results.append((total_correct, new_correct, name, number_str))
            player_results.append((name, [n for n in numbers if n in winning_numbers]))

        results.sort(reverse=True)

        if results:
            highest_total = results[0][0]
            highest_scorers = []
            filter_family = self.get_filter_family()
            filter_results = []

            for total_correct, new_correct, name, number_str in results:
                if total_correct == highest_total:
                    highest_scorers.append((total_correct, new_correct, name, number_str))
                if filter_family and name.startswith(filter_family):
                    filter_results.append((total_correct, new_correct, name, number_str))

            if highest_scorers:
                print("\nHighest Scorers:")
                print("-" * 70)
                for total_correct, new_correct, name, number_str in highest_scorers:
                    if new_correct > 0:
                        print(f"{name:<25} {number_str} - {total_correct} total (+{new_correct} new)")
                    else:
                        print(f"{name:<25} {number_str} - {total_correct} total")
                    if total_correct >= 10:
                        print(f"\n🎉 WINNER! {name} has reached 10 correct numbers! 🎉")

            if filter_results:
                print(f"\n{filter_family} Family Results:")
                print("-" * 70)
                for total_correct, new_correct, name, number_str in filter_results:
                    if new_correct > 0:
                        print(f"{name:<25} {number_str} - {total_correct} total (+{new_correct} new)")
                    else:
                        print(f"{name:<25} {number_str} - {total_correct} total")
                    
                    # Add condensed future winner analysis
                    missing_info = self.get_missing_numbers_info(name, winning_numbers)
                    if missing_info:
                        missing_nums, winner_count = missing_info
                        print(f"    missing: {missing_nums}, {winner_count} other winners")
                    
                    if total_correct >= 10:
                        print(f"\n🎉 WINNER! {name} has reached 10 correct numbers! 🎉")

        self.update_progress(player_results, draw_date)

    def get_filter_family(self):
        """Get family filter from .env file if it exists"""
        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('FILTER_FAMILY='):
                            return line.split('=', 1)[1].strip().strip('"\'')
            except Exception as e:
                print(f"Error reading .env file: {e}")
        return None

    def get_missing_numbers_info(self, player_name, winning_numbers):
        """Get missing numbers and potential winner count for a player"""
        if not os.path.exists(self.participants_file) or not os.path.exists(self.progress_file):
            return None

        try:
            participants_df = pd.read_csv(self.participants_file)
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)

            # Find the player
            player_row = participants_df[participants_df['Name'] == player_name]
            if player_row.empty:
                return None

            player_row = player_row.iloc[0]
            current_numbers = set(progress['players'].get(player_name, {}).get('correct_numbers', []))
            chosen_numbers = set(int(player_row[f'Number{i}']) for i in range(1, 11))
            missing_numbers = chosen_numbers - current_numbers

            # Count potential winners
            potential_winners = 0
            for _, participant in participants_df.iterrows():
                participant_name = participant['Name']
                if participant_name == player_name:
                    continue

                participant_correct = set(progress['players'].get(participant_name, {}).get('correct_numbers', []))
                participant_total = len(participant_correct)
                participant_numbers = set(int(participant[f'Number{i}']) for i in range(1, 11))
                matching_numbers = missing_numbers.intersection(participant_numbers)

                if participant_total + len(matching_numbers) >= 10:
                    potential_winners += 1

            return sorted(list(missing_numbers)), potential_winners

        except Exception as e:
            print(f"Error analyzing missing numbers: {e}")
            return None

    def analyze_future_winners(self, family_name):
        """Analyze future winners for a specific family"""
        if not os.path.exists(self.participants_file) or not os.path.exists(self.progress_file):
            print("Missing required data files. Please ensure lottery data exists.")
            return

        participants_df = pd.read_csv(self.participants_file)
        with open(self.progress_file, 'r') as f:
            progress = json.load(f)

        family_members = participants_df[participants_df['Name'].str.startswith(family_name)]
        
        if family_members.empty:
            print(f"No family members found starting with '{family_name}'")
            return

        print(f"\nFuture Winners Analysis for {family_name} Family")
        print("=" * 70)

        for _, family_member in family_members.iterrows():
            name = family_member['Name']
            current_numbers = set(progress['players'].get(name, {}).get('correct_numbers', []))
            chosen_numbers = set(family_member[f'Number{i}'] for i in range(1, 11))
            missing_numbers = chosen_numbers - current_numbers

            potential_winners = set()

            for _, participant in participants_df.iterrows():
                participant_name = participant['Name']
                if participant_name == name:
                    continue

                participant_correct = set(progress['players'].get(participant_name, {}).get('correct_numbers', []))
                participant_total = len(participant_correct)
                participant_numbers = set(participant[f'Number{i}'] for i in range(1, 11))
                matching_numbers = missing_numbers.intersection(participant_numbers)

                if participant_total + len(matching_numbers) >= 10:
                    potential_winners.add(participant_name)

            print(f"\n{name}")
            print(f"Current correct numbers: {len(current_numbers)}")
            print(f"Missing numbers: {sorted(list(missing_numbers))}")
            print("-" * 70)

            if potential_winners:
                winners_str = ", ".join(sorted(potential_winners))
                print(f"Winners if all numbers drawn ({len(potential_winners)} winners): {winners_str}")
            else:
                print("No other players would win if all missing numbers are drawn")

    def show_current_standings(self):
        """Show current standings from latest draw"""
        trekking = self.read_trekking()
        if not trekking.empty:
            latest = trekking.iloc[-1]
            numbers = sorted([latest[f'number{i}'] for i in range(1, 7)])
            self.check_participants(numbers, latest['date'], True)
        else:
            print("No draws found. Please add a draw first.")

    def run_interactive_mode(self):
        """Run interactive mode for current standings and new draws"""
        if not os.path.exists(self.participants_file):
            print("No participants file found. Please start a new lottery run first.")
            print("Usage: python lottery.py <pdf_file>")
            return

        print("Current Lottery Standings")
        print("=" * 50)
        self.show_current_standings()
        
        print("\n" + "=" * 50)
        print("Add New Draw")
        print("=" * 50)
        
        numbers = self.parse_input()
        if numbers is None:
            print("Goodbye!")
            return
            
        draw_date = self.get_draw_date()
        self.add_to_trekking(numbers, draw_date)
        self.check_participants(numbers, draw_date, True)


def main():
    try:
        from termcolor import colored
    except ImportError:
        print("Please install termcolor: pip install termcolor")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Unified Lottery Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lottery.py PosthoornLotto.pdf    # Start new lottery from PDF
  python lottery.py                       # Show standings and add new draw
        """
    )
    parser.add_argument('pdf_file', nargs='?', help='PDF file to start new lottery run')
    
    args = parser.parse_args()
    
    manager = LotteryManager()
    
    if args.pdf_file:
        # Start new lottery from PDF
        if manager.start_new_lottery(args.pdf_file):
            print("\nNew lottery run started successfully!")
        else:
            sys.exit(1)
    else:
        # Interactive mode
        manager.run_interactive_mode()


if __name__ == "__main__":
    main()