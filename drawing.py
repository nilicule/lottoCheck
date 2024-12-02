import pandas as pd
from termcolor import colored
import sys
import json
from pathlib import Path
import os


def colored_intense(text, color):
    """Create an intense colored version of the text"""
    return f"\033[1m{colored(text, color)}\033[0m"


class LotteryTracker:
    def __init__(self):
        self.progress_file = 'data/lottery_progress.json'
        self.progress = {
            'players': {},
            'processed_draws': []
        }
        self.load_progress()

    def load_progress(self):
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
            self.save_progress()

    def save_progress(self):
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except IOError as e:
            print(f"Error saving progress file: {e}")

    def update_progress(self, player_results, draw_date):
        for name, correct_numbers in player_results:
            if name not in self.progress['players']:
                self.progress['players'][name] = {
                    'total_correct': 0,
                    'correct_numbers': []
                }

            # Add newly correct numbers
            current_correct = set(self.progress['players'][name]['correct_numbers'])
            new_correct = set(correct_numbers)
            all_correct = current_correct.union(new_correct)

            self.progress['players'][name]['correct_numbers'] = sorted(list(all_correct))
            self.progress['players'][name]['total_correct'] = len(all_correct)

        if draw_date not in self.progress['processed_draws']:
            self.progress['processed_draws'].append(draw_date)
        self.save_progress()

    def get_unprocessed_draws(self):
        try:
            trekking = read_trekking()
            unprocessed = []
            for _, row in trekking.iterrows():
                draw_date = row['date']
                if draw_date not in self.progress['processed_draws']:
                    numbers = [row[f'number{i}'] for i in range(1, 7)]
                    unprocessed.append((sorted(numbers), draw_date))
            return unprocessed
        except Exception as e:
            print(f"Error reading trekking.csv: {e}")
            return []


def read_trekking():
    """Read trekking.csv, creating it if it doesn't exist"""
    os.makedirs('data', exist_ok=True)
    file_path = 'data/trekking.csv'

    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['date'] + [f'number{i}' for i in range(1, 7)])
        df.to_csv(file_path, index=False)
        return df

    return pd.read_csv(file_path)


def parse_input():
    print("Enter 6 numbers (comma or space separated), or press Enter to show current standings:")
    user_input = input().strip()

    if not user_input:
        return None

    try:
        numbers = user_input.replace(',', ' ').split()
        numbers = [int(n) for n in numbers]
        if len(numbers) != 6:
            print("Please enter exactly 6 numbers")
            return parse_input()
        if not all(1 <= n <= 45 for n in numbers):
            print("Numbers must be between 1 and 45")
            return parse_input()
        if len(set(numbers)) != 6:
            print("Numbers must be unique")
            return parse_input()
        return sorted(numbers)
    except ValueError:
        print("Please enter valid numbers")
        return parse_input()


def add_to_trekking(numbers):
    trekking = read_trekking()

    if trekking.empty:
        next_date = pd.Timestamp.now().strftime('%d-%b-%y')
    else:
        last_date = pd.to_datetime(trekking['date'].iloc[-1], format='%d-%b-%y')
        next_date = (last_date + pd.Timedelta(days=7)).strftime('%d-%b-%y')

    new_row = {
        'date': next_date,
        'number1': numbers[0],
        'number2': numbers[1],
        'number3': numbers[2],
        'number4': numbers[3],
        'number5': numbers[4],
        'number6': numbers[5]
    }
    trekking = pd.concat([trekking, pd.DataFrame([new_row])], ignore_index=True)
    trekking.to_csv('data/trekking.csv', index=False)
    return new_row['date']


def check_participants(winning_numbers, draw_date, tracker, is_latest_draw=False):
    participants = pd.read_csv('data/lottery_participants.csv')

    print(f"\nResults for draw date: {draw_date}")
    print("=" * 70)
    print("Winning numbers:", " ".join(f"{n:2d}" for n in sorted(winning_numbers)))
    print("-" * 70)

    results = []
    player_results = []

    for idx, row in participants.iterrows():
        name = row['Name']
        numbers = sorted([row[f'Number{i}'] for i in range(1, 11)])

        # Get previously correct numbers
        previous_correct = set(tracker.progress['players'].get(name, {}).get('correct_numbers', []))

        # Find correct numbers in this draw
        correct_in_draw = set(n for n in numbers if n in winning_numbers)

        # Identify truly new correct numbers (never seen before)
        truly_new_correct = correct_in_draw - previous_correct if is_latest_draw else set()

        # Create output string
        number_str = "["
        for n in numbers:
            if n in truly_new_correct:
                # Truly new correct numbers in latest draw - intense green
                number_str += colored_intense(f"{n:2d}", 'green') + " "
            elif n in previous_correct or n in correct_in_draw:
                # Previously correct numbers - regular green
                number_str += colored(f"{n:2d}", 'green') + " "
            else:
                number_str += f"{n:2d} "
        number_str = number_str.rstrip() + "]"

        total_correct = len(previous_correct.union(correct_in_draw))
        new_correct = len(truly_new_correct) if is_latest_draw else 0

        results.append((total_correct, new_correct, name, number_str))
        player_results.append((name, [n for n in numbers if n in winning_numbers]))

    # Sort by total correct (descending) and then by new correct (descending)
    results.sort(reverse=True)

    # Get highest total and find all players with that total
    if results:
        highest_total = results[0][0]  # Get the highest total

        # Separate results into highest scorers and Brink family
        highest_scorers = []
        brink_family = []

        for total_correct, new_correct, name, number_str in results:
            if total_correct == highest_total:
                highest_scorers.append((total_correct, new_correct, name, number_str))
            if name.startswith('Brink'):
                brink_family.append((total_correct, new_correct, name, number_str))

        # Print highest scorers
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

        # Print Brink family results
        if brink_family:
            print("\nBrink Family Results:")
            print("-" * 70)
            for total_correct, new_correct, name, number_str in brink_family:
                if new_correct > 0:
                    print(f"{name:<25} {number_str} - {total_correct} total (+{new_correct} new)")
                else:
                    print(f"{name:<25} {number_str} - {total_correct} total")
                if total_correct >= 10:
                    print(f"\n🎉 WINNER! {name} has reached 10 correct numbers! 🎉")

        if not highest_scorers and not brink_family:
            print("No results to display")
    else:
        print("No results to display")

    # Update progress
    tracker.update_progress(player_results, draw_date)


def process_all_unprocessed_draws(tracker):
    unprocessed = tracker.get_unprocessed_draws()
    if unprocessed:
        print(f"\nProcessing {len(unprocessed)} unprocessed draws...")
        for i, (numbers, draw_date) in enumerate(unprocessed):
            is_latest = (i == len(unprocessed) - 1)  # True only for the last unprocessed draw
            check_participants(numbers, draw_date, tracker, is_latest)
    return bool(unprocessed)


def get_latest_results(tracker):
    trekking = read_trekking()
    if not trekking.empty:
        latest = trekking.iloc[-1]
        numbers = sorted([latest[f'number{i}'] for i in range(1, 7)])
        return numbers, latest['date']
    return None, None


def main():
    try:
        from termcolor import colored
    except ImportError:
        print("Please install termcolor: pip install termcolor")
        sys.exit(1)

    tracker = LotteryTracker()

    # First process any unprocessed draws from trekking.csv
    found_unprocessed = process_all_unprocessed_draws(tracker)

    # Then handle new input if needed
    numbers = parse_input()

    if numbers is not None:
        draw_date = add_to_trekking(numbers)
        check_participants(numbers, draw_date, tracker, True)  # True for latest draw
    elif not found_unprocessed:
        # Only show latest if we didn't just process any unprocessed draws
        numbers, draw_date = get_latest_results(tracker)
        if numbers and draw_date:
            check_participants(numbers, draw_date, tracker, True)  # True for latest draw
        else:
            print("No draws found in trekking.csv")


if __name__ == "__main__":
    main()