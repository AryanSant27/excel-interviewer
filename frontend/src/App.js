import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import TextInput from './components/TextInput';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { sender: 'interviewer', text: `Welcome to the Excel mock interview! To begin, type 'start' or 'start N' where N is the number of questions (e.g., 'start 5').` }
  ]);
  const [interviewId, setInterviewId] = useState(null);
  const [interviewFinished, setInterviewFinished] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const handleSendMessage = async (text) => {
    const newMessages = [...messages, { sender: 'user', text }];
    setMessages(newMessages);

    const startCommandMatch = text.toLowerCase().match(/^start\s*(\d*)$/);

    if (startCommandMatch && !interviewId) {
      let numQuestions = null;
      if (startCommandMatch[1]) {
        numQuestions = parseInt(startCommandMatch[1], 10);
      }

      try {
        const response = await fetch('http://127.0.0.1:5000/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ candidate_name: 'Candidate', difficulty: 'easy', num_questions: numQuestions }),
        });
        const data = await response.json();
        setInterviewId(data.interview_id);
        if (data.question) {
          setMessages(prev => [...prev, { sender: 'interviewer', text: data.question.question }]);
        } else {
          setMessages(prev => [...prev, { sender: 'interviewer', text: data.message }]);
        }
      } catch (error) {
        console.error("Error starting interview:", error);
        setMessages(prev => [...prev, { sender: 'interviewer', text: 'Sorry, something went wrong. Please try again later.' }]);
      }
    } else if (interviewId && !interviewFinished) {
      try {
        const response = await fetch('http://127.0.0.1:5000/answer', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ interview_id: interviewId, answer: text }),
        });
        const data = await response.json();

        if (data.question) {
          setMessages(prev => [...prev, { sender: 'interviewer', text: data.question }]);
        } else {
          setMessages(prev => [...prev, { sender: 'interviewer', text: data.message }]);
          if(data.report) {
            let report_text = `\n--- Final Interview Report ---\n`;
            report_text += `Overall Score: ${data.report.final_score}/100\n`;
            report_text += `Summary: ${data.report.summary}\n\n`;
            if (data.report.strengths && data.report.strengths.length > 0) {
              report_text += `Strengths:\n- ${data.report.strengths.join('\n- ')}\n\n`;
            }
            if (data.report.weaknesses && data.report.weaknesses.length > 0) {
              report_text += `Weaknesses:\n- ${data.report.weaknesses.join('\n- ')}\n\n`;
            }
            if (data.report.suggestions && data.report.suggestions.length > 0) {
              report_text += `Suggestions for Improvement:\n- ${data.report.suggestions.join('\n- ')}\n`;
            }
            setMessages(prev => [...prev, { sender: 'interviewer', text: report_text }]);
            setInterviewFinished(true); // Set interview as finished
          }
        }
      } catch (error) {
        console.error("Error submitting answer:", error);
        setMessages(prev => [...prev, { sender: 'interviewer', text: 'Sorry, something went wrong. Please try again later.' }]);
      }
    }
  };

  const handleDownloadTranscript = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/download-transcript');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'transcript.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error("Error downloading transcript:", error);
      // Optionally, show an error message to the user
    }
  };

  return (
    <div className={`app ${darkMode ? 'dark' : 'light'}`}>
      <div className="app-header">
        <div className="header-content">
          <h1 className="app-title">Excel Mock Interviewer</h1>
          <div className="header-actions">
            {interviewFinished && (
              <button onClick={handleDownloadTranscript} className="download-transcript-button">
                📄 Transcript
              </button>
            )}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="theme-toggle"
              aria-label="Toggle dark mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </div>
      <main className="chat-container">
        <ChatWindow messages={messages} />
        <TextInput onSendMessage={handleSendMessage} disabled={interviewFinished} />
      </main>
    </div>
  );
}

export default App;
