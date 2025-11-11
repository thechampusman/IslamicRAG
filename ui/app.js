// Use the same origin as the backend to avoid port mismatches
const API_BASE = window.location.origin;

// DOM Elements
const newChatBtn = document.getElementById('newChatBtn');
const chatHistory = document.getElementById('chatHistory');
const welcomeScreen = document.querySelector('.welcome-screen');
const messagesContainer = document.getElementById('messagesContainer');
const chatForm = document.getElementById('chatForm');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const examplePrompts = document.querySelectorAll('.example-prompt');
const themeToggle = document.getElementById('themeToggle');
const mobileMenuToggle = document.getElementById('mobileMenuToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

// State
let currentChatId = null;
let chats = [];
let currentRequestController = null; // For cancelling ongoing requests

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  autoResizeTextarea();
  loadThemePreference();
  loadChatHistory();
  
  // Cancel request when user leaves page
  window.addEventListener('beforeunload', cancelCurrentRequest);
});

function setupEventListeners() {
  // New Chat Button
  newChatBtn.addEventListener('click', startNewChat);
  
  // Theme Toggle
  themeToggle.addEventListener('click', toggleTheme);
  
  // Mobile Menu
  mobileMenuToggle.addEventListener('click', toggleMobileMenu);
  sidebarOverlay.addEventListener('click', closeMobileMenu);
  
  // Example Prompts
  examplePrompts.forEach(prompt => {
    prompt.addEventListener('click', () => {
      const text = prompt.querySelector('.prompt-text').textContent;
      questionInput.value = text;
      questionInput.focus();
      closeMobileMenu();
    });
  });
  
  // Form Submit
  chatForm.addEventListener('submit', handleSubmit);
  
  // Input auto-resize
  questionInput.addEventListener('input', autoResizeTextarea);
  
  // Send button state
  questionInput.addEventListener('input', () => {
    sendBtn.disabled = !questionInput.value.trim();
  });
}

function toggleTheme() {
  const currentTheme = document.body.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  document.body.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  
  // Update icon
  const icon = themeToggle.querySelector('.theme-icon');
  icon.textContent = newTheme === 'light' ? '☀️' : '🌙';
}

function loadThemePreference() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.body.setAttribute('data-theme', savedTheme);
  
  const icon = themeToggle.querySelector('.theme-icon');
  icon.textContent = savedTheme === 'light' ? '☀️' : '🌙';
}

function toggleMobileMenu() {
  sidebar.classList.toggle('open');
  sidebarOverlay.classList.toggle('active');
}

function closeMobileMenu() {
  sidebar.classList.remove('open');
  sidebarOverlay.classList.remove('active');
}

function startNewChat() {
  currentChatId = Date.now().toString();
  
  // Create chat on server
  fetch(`${API_BASE}/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: currentChatId, title: 'New Chat' })
  }).catch(err => console.error('Error creating chat:', err));
  
  // Add to local array
  chats.push({ id: currentChatId, messages: [], title: 'New Chat' });
  
  // Hide welcome, show messages
  welcomeScreen.style.display = 'none';
  messagesContainer.classList.add('active');
  messagesContainer.innerHTML = '';
  
  closeMobileMenu();
  questionInput.focus();
}

function autoResizeTextarea() {
  questionInput.style.height = 'auto';
  questionInput.style.height = Math.min(questionInput.scrollHeight, 200) + 'px';
}

async function handleSubmit(e) {
  e.preventDefault();
  
  const question = questionInput.value.trim();
  if (!question) return;
  
  // Cancel any ongoing request
  cancelCurrentRequest();
  
  // Start new chat if needed
  if (!currentChatId) {
    startNewChat();
  }
  
  // Add user message
  addMessage('user', question);
  
  // Clear input
  questionInput.value = '';
  autoResizeTextarea();
  sendBtn.disabled = true;
  
  // Show loading
  const loadingId = addLoadingMessage();
  
  // Create new AbortController for this request
  currentRequestController = new AbortController();
  
  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, chat_id: currentChatId }),
      signal: currentRequestController.signal
    });
    
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    
    const data = await res.json();
    
    // Remove loading
    removeLoadingMessage(loadingId);
    
    // Add assistant message
    addMessage('assistant', data.answer, data.citations, data.mode === 'fallback');
    
    // Update chat title if first message
    const chat = chats.find(c => c.id === currentChatId);
    if (chat && chat.messages.length === 2) {
      chat.title = question.substring(0, 40) + (question.length > 40 ? '...' : '');
      updateChatHistory();
    }
    
  } catch (err) {
    removeLoadingMessage(loadingId);
    
    // Don't show error if request was cancelled
    if (err.name === 'AbortError') {
      console.log('Request cancelled by user');
    } else {
      addMessage('assistant', `Error: ${err.message}`);
    }
  } finally {
    currentRequestController = null;
  }
}

async function loadChatHistory() {
  try {
    const res = await fetch(`${API_BASE}/chats`);
    if (!res.ok) return;
    
    const serverChats = await res.json();
    
    // Convert server chats to local format
    chats = serverChats.map(chat => ({
      id: chat.id,
      title: chat.title,
      messages: [], // Messages loaded on demand
      created_at: chat.created_at,
      updated_at: chat.updated_at
    }));
    
    updateChatHistory();
  } catch (err) {
    console.error('Error loading chat history:', err);
  }
}

function addMessage(role, text, citations = null, isFallback = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  
  // Avatar
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'user' ? '👤' : '🤖';
  messageDiv.appendChild(avatar);
  
  // Content
  const content = document.createElement('div');
  content.className = 'message-content';
  
  const textDiv = document.createElement('div');
  textDiv.className = 'message-text';
  textDiv.innerHTML = formatMessageText(text);
  content.appendChild(textDiv);
  
  // Citations
  if (citations && citations.length > 0) {
    const citationsDiv = document.createElement('div');
    citationsDiv.className = 'citations';
    
    const header = document.createElement('div');
    header.className = 'citations-header';
    header.innerHTML = '📚 Sources';
    citationsDiv.appendChild(header);
    
    citations.forEach((c, i) => {
      const citationItem = document.createElement('div');
      citationItem.className = 'citation-item';
      
      const source = document.createElement('div');
      source.className = 'citation-source';
      source.textContent = `${i + 1}. ${c.source}`;
      citationItem.appendChild(source);
      
      const snippet = document.createElement('div');
      snippet.className = 'citation-text';
      snippet.textContent = c.snippet;
      citationItem.appendChild(snippet);
      
      citationsDiv.appendChild(citationItem);
    });
    
    content.appendChild(citationsDiv);
  }
  
  // Fallback notice
  if (isFallback) {
    const fallbackDiv = document.createElement('div');
    fallbackDiv.className = 'fallback-notice';
    fallbackDiv.innerHTML = '<span>⚠️</span><div>No documents found in database. Answer based on general Islamic knowledge. Add more texts to improve accuracy!</div>';
    content.appendChild(fallbackDiv);
  }
  
  messageDiv.appendChild(content);
  messagesContainer.appendChild(messageDiv);
  
  // Scroll to bottom
  messagesContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
  
  // Save to chat history
  if (currentChatId) {
    const chat = chats.find(c => c.id === currentChatId);
    if (chat) {
      chat.messages.push({ role, text, citations, isFallback });
    }
  }
}

function addLoadingMessage() {
  const loadingId = 'loading-' + Date.now();
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';
  messageDiv.id = loadingId;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = '🤖';
  messageDiv.appendChild(avatar);
  
  const content = document.createElement('div');
  content.className = 'message-content';
  
  const loading = document.createElement('div');
  loading.className = 'loading';
  loading.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
  content.appendChild(loading);
  
  messageDiv.appendChild(content);
  messagesContainer.appendChild(messageDiv);
  
  messagesContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
  
  return loadingId;
}

function removeLoadingMessage(loadingId) {
  const loadingEl = document.getElementById(loadingId);
  if (loadingEl) loadingEl.remove();
}

function updateChatHistory() {
  chatHistory.innerHTML = '';
  
  chats.slice().reverse().forEach(chat => {
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-history-item';
    chatItem.style.cssText = 'padding:0.75rem;cursor:pointer;border-radius:0.375rem;font-size:0.875rem;color:var(--text-secondary);transition:all 0.2s;display:flex;justify-content:space-between;align-items:center;';
    
    const titleSpan = document.createElement('span');
    titleSpan.textContent = chat.title;
    titleSpan.style.flex = '1';
    titleSpan.style.overflow = 'hidden';
    titleSpan.style.textOverflow = 'ellipsis';
    titleSpan.style.whiteSpace = 'nowrap';
    
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '🗑️';
    deleteBtn.style.cssText = 'background:none;border:none;cursor:pointer;font-size:1rem;opacity:0.6;padding:0.25rem;';
    deleteBtn.onclick = (e) => {
      e.stopPropagation();
      deleteChat(chat.id);
    };
    
    chatItem.appendChild(titleSpan);
    chatItem.appendChild(deleteBtn);
    
    chatItem.addEventListener('mouseenter', () => {
      chatItem.style.background = 'var(--bg-tertiary)';
      titleSpan.style.color = 'var(--text-primary)';
    });
    
    chatItem.addEventListener('mouseleave', () => {
      chatItem.style.background = 'transparent';
      titleSpan.style.color = 'var(--text-secondary)';
    });
    
    titleSpan.addEventListener('click', () => loadChat(chat.id));
    
    chatHistory.appendChild(chatItem);
  });
}

async function deleteChat(chatId) {
  try {
    const res = await fetch(`${API_BASE}/chats/${chatId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete chat');
    
    // Remove from local array
    chats = chats.filter(c => c.id !== chatId);
    updateChatHistory();
    
    // If current chat was deleted, show welcome screen
    if (currentChatId === chatId) {
      currentChatId = null;
      welcomeScreen.style.display = 'flex';
      messagesContainer.classList.remove('active');
      messagesContainer.innerHTML = '';
    }
  } catch (err) {
    console.error('Error deleting chat:', err);
    alert('Failed to delete chat');
  }
}

async function loadChat(chatId) {
  try {
    // Fetch messages from server
    const res = await fetch(`${API_BASE}/chats/${chatId}/messages`);
    if (!res.ok) throw new Error('Failed to load chat');
    
    const messages = await res.json();
    
    currentChatId = chatId;
    welcomeScreen.style.display = 'none';
    messagesContainer.classList.add('active');
    messagesContainer.innerHTML = '';
    
    // Display messages
    messages.forEach(msg => {
      addMessage(msg.role, msg.content, msg.citations, msg.is_fallback);
    });
    
    closeMobileMenu();
  } catch (err) {
    console.error('Error loading chat:', err);
    alert('Failed to load chat');
  }
}

function formatMessageText(text) {
  // Convert plain text paragraphs into structured HTML
  
  // Split by double newlines for paragraphs
  let formatted = text.split(/\n\n+/).map(para => {
    para = para.trim();
    if (!para) return '';
    
    // Check if it's a numbered list
    if (/^\d+\./.test(para)) {
      const items = para.split(/\n(?=\d+\.)/).map(item => {
        const match = item.match(/^\d+\.\s*(.+)$/s);
        return match ? `<li>${escapeHtml(match[1].trim())}</li>` : '';
      }).join('');
      return `<ol>${items}</ol>`;
    }
    
    // Check if it's a bullet list
    if (/^[-•*]/.test(para)) {
      const items = para.split(/\n(?=[-•*])/).map(item => {
        const match = item.match(/^[-•*]\s*(.+)$/s);
        return match ? `<li>${escapeHtml(match[1].trim())}</li>` : '';
      }).join('');
      return `<ul>${items}</ul>`;
    }
    
    // Check if it's a heading (all caps or ends with colon)
    if (para.length < 100 && (para === para.toUpperCase() || para.endsWith(':'))) {
      return `<h4>${escapeHtml(para)}</h4>`;
    }
    
    // Regular paragraph
    return `<p>${escapeHtml(para)}</p>`;
  }).join('');
  
  // Handle inline formatting
  formatted = formatted
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') // Bold
    .replace(/\*(.+?)\*/g, '<em>$1</em>') // Italic
    .replace(/`(.+?)`/g, '<code>$1</code>'); // Code
  
  return formatted;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function cancelCurrentRequest() {
  if (currentRequestController) {
    currentRequestController.abort();
    currentRequestController = null;
  }
}
