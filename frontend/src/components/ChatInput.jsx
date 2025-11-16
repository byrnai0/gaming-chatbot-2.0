import { useState } from 'react';

export default function ChatInput({ onSend, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-slate-700 p-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about any game..."
          disabled={disabled}
          className="flex-1 bg-slate-800 text-slate-100 rounded-xl px-4 py-3 
                     focus:outline-none focus:ring-2 focus:ring-primary 
                     disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="bg-gradient-to-r from-primary to-secondary text-white 
                     px-6 py-3 rounded-xl font-medium
                     hover:opacity-90 transition-opacity
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </form>
  );
}
