import { useState } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const formatResponse = (data) => {
    // Extract only non-empty fields that matter
    const parts = []
    
    if (data.summary) parts.push(data.summary)
    if (data.no_spoilers) parts.push(data.no_spoilers)
    if (data.game_length) parts.push(`⏱️ ${data.game_length}`)
    if (data.lore) parts.push(data.lore)
    if (data.game_tips) parts.push(data.game_tips)
    if (data.rawg_data) parts.push(data.rawg_data)
    
    if (data.warning) parts.push(`⚠️ ${data.warning}`)
    if (data.spoilers) parts.push(data.spoilers)
    
    return parts.length > 0 ? parts.join('\n\n') : 'No information found.'
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input })
      })
      
      const data = await response.json()
      const botMessage = { 
        role: 'assistant', 
        content: formatResponse(data)
      }
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      const errorMessage = { 
        role: 'assistant', 
        content: 'Error: Could not connect to server' 
      }
      setMessages(prev => [...prev, errorMessage])
    }
    
    setLoading(false)
  }

  return (
    <div className="app">
      <div className="chat-container">
        <h1>Gaming Assistant</h1>
        
        <div className="messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {loading && <div className="message assistant">Thinking...</div>}
        </div>

        <div className="input-box">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about a game..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  )
}

export default App
