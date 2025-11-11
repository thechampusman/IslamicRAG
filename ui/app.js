// Use the same origin as the backend to avoid port mismatches
const API_BASE = window.location.origin;

const messagesEl = document.getElementById('messages');
const citationsEl = document.getElementById('citations');
const form = document.getElementById('chat-form');
const input = document.getElementById('question');

function appendMessage(role, text){
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = `${role === 'user' ? 'You' : 'Assistant'}: ${text}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if(!q) return;
  appendMessage('user', q);
  input.value='';
  citationsEl.innerHTML = '';

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: q})
    });
    if(!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    appendMessage('assistant', data.answer);
    
    if(data.citations && data.citations.length > 0){
      citationsEl.innerHTML = '<h3>Sources:</h3>';
      data.citations.forEach((c, i) => {
        const div = document.createElement('div');
        div.className = 'citation';
        div.innerHTML = `<strong>${i+1}. ${c.source}</strong><br>${c.snippet}`;
        citationsEl.appendChild(div);
      });
    } else if(data.mode === 'fallback') {
      citationsEl.innerHTML = '<div style="color:#f90;padding:10px;background:#fff3cd;border-radius:6px;"><strong>ℹ️ Fallback Mode:</strong> No documents found in database. Answer based on general Islamic knowledge. Add more texts to improve accuracy!</div>';
    }
  } catch(err){
    appendMessage('assistant', 'Error: ' + err.message);
  }
});
