import React, { useState } from 'react';

const TextInput = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="text-input-form">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your answer here..."
        className="text-input-field"
      />
      <button type="submit" className="send-button">Send</button>
    </form>
  );
};

export default TextInput;
