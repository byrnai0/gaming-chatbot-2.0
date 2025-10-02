async function sendMessage() {
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");

  const message = userInput.value.trim();
  if (!message) return;

  // Show user message
  chatBox.innerHTML += `<p class="user"><b>You:</b> ${message}</p>`;
  userInput.value = "";

  try {
    // Send to backend
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: [] })
    });

    const data = await response.json();

    // Show bot response
    chatBox.innerHTML += `<p class="bot"><b>Bot:</b> ${data.response}</p>`;
    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (error) {
    chatBox.innerHTML += `<p class="bot"><b>Error:</b> ${error.message}</p>`;
  }
}
