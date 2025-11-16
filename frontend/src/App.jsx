import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import LoadingDots from './components/LoadingDots';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (userMessage) => {
    setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
    setLoading(true);

    try {
      const response = await axios.post('/chat', {
        query: userMessage
      });

      setMessages(prev => [...prev, { 
        text: response.data.response || response.data.message, 
        isUser: false 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        text: 'Sorry, something went wrong. Please try again.', 
        isUser: false 
      }]);
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-darker">
      {/* Header */}
      <header className="bg-dark border-b border-slate-700 p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-transparent bg-clip-text 
                         bg-gradient-to-r from-primary to-secondary">
            Gaming Chatbot 2.0
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Ask me anything about video games
          </p>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto chat-scroll">
        <div className="max-w-4xl mx-auto p-4">
          {messages.length === 0 && (
            <div className="text-center mt-20">
              <div className="text-6xl mb-4">🎮</div>
              <h2 className="text-xl text-slate-300 mb-2">Welcome to Gaming Chatbot</h2>
              <p className="text-slate-500">Ask about game details, playtime, plot summaries, and more</p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg.text} isUser={msg.isUser} />
          ))}
          
          {loading && <LoadingDots />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="max-w-4xl mx-auto w-full">
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
}

export default App;
