import ReactMarkdown from 'react-markdown';

export default function ChatMessage({ message, isUser }) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser 
          ? 'bg-gradient-to-r from-primary to-secondary text-white' 
          : 'bg-slate-800 text-slate-100'
      }`}>
        {isUser ? (
          <p className="text-sm">{message}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{message}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
