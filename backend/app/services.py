import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

from .models import Interview
from .questions import fetch_questions

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("GEMINI_API_KEY not found in .env file. Gemini API will not be used.")

def start_interview(candidate_name, difficulty, num_questions=None):
    return Interview(candidate_name, difficulty, num_questions)

def get_interview_questions(difficulty="all"):
    return fetch_questions(difficulty)

def evaluate_answer(question, answer, reference_answer=None):
    if not API_KEY:
        print("Using placeholder evaluation as GEMINI_API_KEY is not set.")
        return {"score": 8, "feedback": "This is a placeholder evaluation."}

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""You are an Excel expert evaluating a candidate's response.\n\nQuestion: {question}\nCandidate Answer: {answer}\n"""
        if reference_answer:
            prompt += f"Reference Answer: {reference_answer}\n"
        
        prompt += """\nEvaluate the candidate's answer. Provide a score from 1 to 10. Return your response as a JSON object with the following key: \"score\" (integer).\nExample:\n{{\n  \"score\": 9\n}}\n"""
        prompt += "You MUST return ONLY the JSON object, and no other text or explanation."
        response = model.generate_content(prompt)
        print(f"Raw LLM response for evaluation: {response.text}") # Debugging line
        # Extract JSON from markdown code block
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1).strip()
        else:
            json_string = response.text.strip() # Fallback if no markdown block
        evaluation_result = json.loads(json_string)
        return evaluation_result
    except Exception as e:
        print(f"Error calling Gemini API for answer evaluation: {e}")
        return {"score": 8, "feedback": "Error during evaluation. Using placeholder feedback."}

def generate_final_report(interview):
    if not API_KEY:
        print("Using placeholder final report as GEMINI_API_KEY is not set.")
        return {
            "final_score": "N/A",
            "summary": "This is a placeholder final report. The interview is complete!",
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Construct the transcript for the LLM
        transcript = ""
        for entry in interview.chat_history:
            if entry["role"] == "interviewer":
                transcript += f"Interviewer: {entry['content']}\n"
            elif entry["role"] == "user":
                transcript += f"Candidate: {entry['content']}\n"
                if "evaluation" in entry:
                    transcript += f"  (Evaluation: Score {entry['evaluation']['score']})\n"

        prompt = f"""You are an AI interviewer providing a final report for a candidate's Excel mock interview.\n\nHere is the full transcript of the interview, including questions, candidate answers, and individual question evaluations:\n\n{transcript}\n\nBased on this transcript, generate a comprehensive final report. The report should include:\n1.  An overall final score for the candidate (out of 100).\n2.  A summary of the candidate's overall performance.\n3.  Key strengths demonstrated by the candidate.\n4.  Key weaknesses or areas for improvement.\n5.  Specific, actionable suggestions for how the candidate can improve their Excel skills.\n\nReturn your response as a JSON object with the following keys:\n\"final_score\": (integer, overall score out of 100),\n\"summary\": (string, overall summary),\n\"strengths\": (array of strings),\n\"weaknesses\": (array of strings),\n\"suggestions\": (array of strings)\n\nExample:\n{{\n  \"final_score\": 75,\n  \"summary\": \"The candidate demonstrated a good understanding of basic Excel functions and formulas, but struggled with advanced concepts.\",\n  \"strengths\": [\"Strong grasp of basic formulas\", \"Clear communication on simple topics\"],\n  \"weaknesses\": [\"Limited knowledge of advanced functions like INDEX/MATCH\", \"Difficulty explaining complex scenarios\"],\n  \"suggestions\": [\"Practice advanced lookup functions\", \"Work on explaining problem-solving approaches verbally\"]\n}}\n"""
        prompt += "You MUST return ONLY the JSON object, and no other text or explanation."
        response = model.generate_content(prompt)
        print(f"Raw LLM response for final report: {response.text}") # Debugging line
        # Extract JSON from markdown code block
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1).strip()
        else:
            json_string = response.text.strip() # Fallback if no markdown block
        report_result = json.loads(json_string)
        return report_result
    except Exception as e:
        print(f"Error calling Gemini API for final report: {e}")
        return {
            "final_score": "N/A",
            "summary": "Error generating report. Using placeholder report.",
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }

def save_transcript(interview, report):
    transcript_data = {
        "interview_summary": [],
        "final_report": report
    }

    # Assuming chat_history stores pairs of questions and answers
    # This logic needs to be robust to handle the sequence of messages
    question_data = None
    answer_data = None

    for entry in interview.chat_history:
        if entry['role'] == 'interviewer':
            # This is a question
            question_data = {
                "question": entry['content'],
                "sub_question": "NA", # Default value
                "user_answer": "",
                "reference_answer": "",
                "score": None
            }
        elif entry['role'] == 'user' and question_data:
            # This is an answer to the previous question
            question_data['user_answer'] = entry['content']
            if 'evaluation' in entry:
                question_data['score'] = entry['evaluation'].get('score')
            
            # Find the corresponding question in the question bank to get the reference answer
            # This is a simplified approach; a more robust solution would be to store the question object itself
            all_questions = fetch_questions('all')
            for q in all_questions:
                if q['question'] == question_data['question']:
                    question_data['reference_answer'] = q.get('reference_answer', 'Not available')
                    # Check for sub-questions
                    if 'follow_ups' in q:
                        # This is a simplistic check. A better approach would be to track which follow-up is being asked.
                        # For now, we just take the first one as an example.
                        if len(q['follow_ups']) > 0:
                            question_data['sub_question'] = q['follow_ups'][0].get('question', 'NA')
                    break
            
            transcript_data["interview_summary"].append(question_data)
            question_data = None # Reset for the next question

    with open('transcript.json', 'w') as f:
        json.dump(transcript_data, f, indent=4)

def submit_answer(interview, answer):
    interview.add_to_history("user", answer)
    
    question_just_answered_data = interview.last_question_sent_data
    if not question_just_answered_data:
        return {"error": "No question data available for evaluation."}

    # Determine the reference answer based on whether it's a main question or follow-up
    reference_answer = question_just_answered_data.get("reference_answer")

    evaluation = evaluate_answer(question_just_answered_data["question"], answer, reference_answer)
    interview.chat_history[-1]["evaluation"] = evaluation

    # Only check for and add follow-up questions if the question just answered was a main question
    # and it has follow-ups defined.
    if interview.current_main_question_data and "follow_ups" in interview.current_main_question_data and interview.current_main_question_data == question_just_answered_data: # Ensure it's the main question that was just answered
        if evaluation["score"] >= 7: # Using 7 as example threshold
            for follow_up in interview.current_main_question_data["follow_ups"]:
                if evaluation["score"] >= follow_up["trigger_score_threshold"]:
                    interview.add_follow_up(follow_up)

    next_question = interview.get_next_question()

    if next_question:
        return {"question": next_question["question"], "evaluation": evaluation}
    else:
        report = generate_final_report(interview)
        save_transcript(interview, report) # Save the transcript
        return {"message": "Interview complete!", "evaluation": evaluation, "report": report}

def generate_questions_from_transcript():
    if not API_KEY:
        return {"error": "GEMINI_API_KEY not found."}

    try:
        with open('transcript.json', 'r') as f:
            transcript_data = json.load(f)
    except FileNotFoundError:
        return {"error": "transcript.json not found."}

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""Based on the following interview transcript, generate 5 new interview questions. The questions should be relevant to the topics discussed in the interview and should be of a similar difficulty level.

Transcript:
{json.dumps(transcript_data, indent=4)}

Return your response as a JSON object with a single key "generated_questions" which is an array of strings.
Example:
{{
  "generated_questions": [
    "What is the difference between a VLOOKUP and an HLOOKUP?",
    "How would you create a pivot table to summarize sales data?",
    "Explain the use of the IFERROR function.",
    "How do you use conditional formatting to highlight duplicate values?",
    "What is the purpose of the CONCATENATE function?"
  ]
}}
"""
        prompt += "You MUST return ONLY the JSON object, and no other text or explanation."
        response = model.generate_content(prompt)
        
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1).strip()
        else:
            json_string = response.text.strip()
            
        generated_questions = json.loads(json_string)

        with open('generated_questions.json', 'w') as f:
            json.dump(generated_questions, f, indent=4)

        return generated_questions
    except Exception as e:
        print(f"Error calling Gemini API for question generation: {e}")
        return {"error": "Error during question generation."}

def run_test_interview(difficulty, num_questions):
    candidate_name = "Test Candidate"
    interview = start_interview(candidate_name, difficulty, num_questions)

    # Loop through the interview, answering each question
    while True:
        question_data = interview.get_next_question()
        if not question_data:
            break # Exit loop when no more questions

        # Use the reference answer if available, otherwise use a placeholder
        answer = question_data.get("reference_answer", "This is a default test answer.")
        # Submit the answer, which also evaluates it and adds to history
        submit_answer(interview, answer)

    # After the loop, explicitly generate the final report and save the transcript
    final_report = generate_final_report(interview)
    save_transcript(interview, final_report)

    return {
        "message": "Test interview completed successfully. Transcript and final report have been generated.",
        "final_report": final_report
    }
