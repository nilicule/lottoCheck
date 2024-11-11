import pandas as pd
from collections import defaultdict
import json
import sys


def get_texts(language):
    texts = {
        'en': {
            'title': "Future Winners Analysis",
            'current_correct': "Current correct numbers",
            'missing_numbers': "Missing numbers",
            'winners': "Winners if all numbers drawn ({} winners): {}",
            'no_winners': "No other players would win if all missing numbers are drawn"
        },
        'nl': {
            'title': "Toekomstige Winnaars Analyse",
            'current_correct': "Huidig aantal juiste nummers",
            'missing_numbers': "Ontbrekende nummers",
            'winners': "Winnaars als alle nummers getrokken worden ({} winnaars): {}",
            'no_winners': "Geen andere spelers zouden winnen als alle ontbrekende nummers getrokken worden"
        }
    }
    return texts.get(language, texts['en'])


def analyze_future_winners(language='en'):
    texts = get_texts(language)

    # Read participant data
    participants_df = pd.read_csv('data/lottery_participants.csv')

    # Load current progress
    with open('data/lottery_progress.json', 'r') as f:
        progress = json.load(f)

    # Get all family members' data
    family_members = participants_df[participants_df['Name'].str.startswith(family_name)]

    # Dictionary to store results per Brink member
    member_results = {}

    for _, family_member in family_members.iterrows():
        name = family_member['Name']
        current_numbers = set(progress['players'].get(name, {}).get('correct_numbers', []))
        chosen_numbers = set(family_member[f'Number{i}'] for i in range(1, 11))
        missing_numbers = chosen_numbers - current_numbers

        # Track potential winners
        potential_winners = set()

        # Check each participant against all missing numbers
        for _, participant in participants_df.iterrows():
            participant_name = participant['Name']
            if participant_name == name:
                continue

            # Get their current correct numbers
            participant_correct = set(progress['players'].get(participant_name, {}).get('correct_numbers', []))
            participant_total = len(participant_correct)

            # Count how many of their missing numbers match
            participant_numbers = set(participant[f'Number{i}'] for i in range(1, 11))
            matching_numbers = missing_numbers.intersection(participant_numbers)

            # If they would reach 10 with these numbers, add them to potential winners
            if participant_total + len(matching_numbers) >= 10:
                potential_winners.add(participant_name)

        member_results[name] = {
            'current_correct': len(current_numbers),
            'missing_numbers': sorted(list(missing_numbers)),
            'potential_winners': sorted(list(potential_winners))
        }

    # Display results
    print(f"\n{texts['title']}")
    print("=" * 70)

    for member_name in sorted(member_results.keys()):
        result = member_results[member_name]
        print(f"\n{member_name}")
        print(f"{texts['current_correct']}: {result['current_correct']}")
        print(f"{texts['missing_numbers']}: {result['missing_numbers']}")
        print("-" * 70)

        if result['potential_winners']:
            winners_str = ", ".join(result['potential_winners'])
            print(texts['winners'].format(len(result['potential_winners']), winners_str))
        else:
            print(texts['no_winners'])
        print()


if __name__ == "__main__":
    # Default to English if no argument provided
    language = 'en'

    # Check command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-nl', '-en']:
            language = arg[1:]  # Remove the hyphen

    # Default family name
    family_name = 'Brink'

    # Check for family name argument
    if len(sys.argv) > 2:
        family_name = sys.argv[2]

    analyze_future_winners(language)