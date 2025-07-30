from app import app
from flask import request, jsonify, send_file
from .services import start_interview, get_interview_questions, submit_answer, save_transcript, generate_questions_from_transcript, run_test_interview
import os

interviews = {}

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json()
    candidate_name = data.get('candidate_name', 'Candidate')
    difficulty = data.get('difficulty', 'easy')
    interview = start_interview(candidate_name, difficulty)
    interviews[interview.candidate_name] = interview
    return jsonify({
        "message": "Interview started.",
        "interview_id": interview.candidate_name, 
        "question": interview.get_next_question()
    })

@app.route('/answer', methods=['POST'])
def answer():
    print("Received request at /answer")
    data = request.get_json()
    interview_id = data.get('interview_id')
    answer_text = data.get('answer')
    interview = interviews.get(interview_id)

    if not interview:
        return jsonify({"error": "Interview not found"}), 404

    response = submit_answer(interview, answer_text)
    return jsonify(response)

@app.route('/questions', methods=['GET'])
def get_questions():
    difficulty = request.args.get('difficulty', 'all')
    questions = get_interview_questions(difficulty)
    return jsonify(questions)

@app.route('/generate-questions', methods=['POST'])
def generate_questions():
    result = generate_questions_from_transcript()
    return jsonify(result)

@app.route('/test-interview', methods=['POST'])
def test_interview():
    data = request.get_json()
    difficulty = data.get('difficulty', 'easy')
    num_questions = data.get('num_questions', 5) # Default to 5 questions
    result = run_test_interview(difficulty, num_questions)
    return jsonify(result)

@app.route('/download-transcript', methods=['GET'])
def download_transcript():
    try:
        # The transcript.json is in the root directory, which is one level above the 'backend' directory.
        # A simpler, more robust way to get the project root is often needed.
        # For now, let's assume the script is run from the project root.
        transcript_path = os.path.join(os.getcwd(), 'transcript.json')
        if not os.path.exists(transcript_path):
            # If not found, try a relative path from the app's location
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            transcript_path = os.path.join(base_dir, 'transcript.json')

        if not os.path.exists(transcript_path):
            return jsonify({"error": "Transcript file not found."}), 404
            
        return send_file(transcript_path, as_attachment=True)
    except Exception as e:
        print(f"Error during transcript download: {e}")
        return jsonify({"error": "An error occurred while downloading the transcript."}), 500
