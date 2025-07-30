import json
import os

def fetch_questions(difficulty="all"):
    # In a real app, this would load from a database or a more robust source
    # For this example, we'll load from a JSON file.
    
    # Correctly locate the questions.json file relative to the current file.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'questions.json')

    try:
        with open(file_path, 'r') as f:
            all_questions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle cases where the file doesn't exist or is invalid
        return []

    if difficulty == "all":
        return all_questions
    else:
        return [q for q in all_questions if q.get('difficulty') == difficulty]
