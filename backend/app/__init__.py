from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://excel-interviewer.vercel.app"}})

from app import routes
