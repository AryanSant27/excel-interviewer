import json
import random
from .questions import fetch_questions

class Interview:
    def __init__(self, candidate_name, difficulty="easy", num_questions=None):
        self.candidate_name = candidate_name
        self.difficulty = difficulty
        
        all_questions_of_difficulty = fetch_questions(difficulty)
        self._available_main_questions = list(all_questions_of_difficulty)
        random.shuffle(self._available_main_questions)
        
        self.num_questions_to_ask = num_questions if num_questions is not None else len(self._available_main_questions)
        self.questions_asked_count = 0

        self.current_main_question_data = None # Stores the data of the current MAIN question being addressed
        self.last_question_sent_data = None # Stores the data of the last question (main or follow-up) sent to the user
        self.chat_history = []
        self.pending_follow_ups = []

    def get_next_question(self):
        if self.pending_follow_ups:
            question_to_send = self.pending_follow_ups.pop(0)
            self.last_question_sent_data = question_to_send
            self.add_to_history("interviewer", question_to_send["question"])
            return question_to_send
        
        # If no pending follow-ups, try to get a new main question
        if self.questions_asked_count < self.num_questions_to_ask and self._available_main_questions:
            question_to_send = self._available_main_questions.pop()
            self.current_main_question_data = question_to_send
            self.last_question_sent_data = question_to_send
            self.questions_asked_count += 1
            self.add_to_history("interviewer", question_to_send["question"])
            return question_to_send
        else:
            # No more questions or follow-ups
            return None

    def add_to_history(self, role, content):
        self.chat_history.append({"role": role, "content": content})

    def add_follow_up(self, follow_up):
        self.pending_follow_ups.append(follow_up)
