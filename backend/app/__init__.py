from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(
    app,
    origins=["https://excel-interviewer.vercel.app"],
    methods=["GET", "POST", "OPTIONS"],
    supports_credentials=True,
    allow_headers=["Content-Type"]
)

from app import routes
