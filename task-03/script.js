const BACKEND_URL = "/chat";
let controller, typingInterval;
let isNewSession = true;
let pendingPrompt = "";
let pendingChatName = "";
let currentRenameId = null;
let currentDeleteId = null;

const parseMarkdown = (text) => {
  if (typeof marked === 'undefined') return text;
  const rawHtml = marked.parse(text);
  return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml;
};

function showToast(message, type = 'error') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-msg ${type === 'error' ? 'error' : ''}`;
  const icon = type === 'error' ? '<i class="fas fa-exclamation-circle text-red-500"></i>' : '<i class="fas fa-check-circle text-primary"></i>';
  toast.innerHTML = `${icon} <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('fade-out');
    toast.addEventListener('animationend', () => toast.remove());
  }, 3500);
}

async function createNewSession() {
  try {
    const token = localStorage.getItem("access_token");
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch("/session/new", { method: "POST", headers });
    const data = await res.json();
    localStorage.setItem("chat_session_id", data.session_id);
    isNewSession = true;
    return data.session_id;
  } catch (err) {
    const fallbackId = "sess_" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("chat_session_id", fallbackId);
    isNewSession = true;
    return fallbackId;
  }
}

async function getSessionId() {
  let sId = localStorage.getItem("chat_session_id");
  if (!sId) sId = await createNewSession();
  return sId;
}

let savedChats = JSON.parse(localStorage.getItem("saved_chats") || "[]");

function renderSidebar() {
  const historyList = document.getElementById('historyList');
  historyList.innerHTML = "";
  savedChats.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));

  savedChats.forEach(chat => {
    const isPinned = chat.pinned ? '<i class="fas fa-thumbtack text-xs text-primary"></i>' : '<i class="fas fa-comment-dots text-xs"></i>';
    const html = `
      <div class="history-item flex items-center justify-between px-3 py-2.5 rounded-lg mb-1 cursor-pointer" data-id="${chat.id}">
        <span class="flex items-center gap-3 truncate w-4/5" onclick="selectChat('${chat.id}')">
          ${isPinned}
          <span class="text-sm truncate">${chat.name}</span>
        </span>
        <div class="chat-actions">
          <button class="chat-actions-btn" onclick="toggleChatMenu(event, '${chat.id}')">
            <i class="fas fa-ellipsis-h text-xs"></i>
          </button>
          <div class="chat-dropdown" id="menu-${chat.id}">
            <div class="chat-dropdown-item" onclick="pinChat(event, '${chat.id}')">
              <i class="fas fa-thumbtack"></i> ${chat.pinned ? 'Unpin' : 'Pin'}
            </div>
            <div class="chat-dropdown-item" onclick="openRenameModal(event, '${chat.id}')">
              <i class="fas fa-edit"></i> Rename
            </div>
            <div class="chat-dropdown-item delete" onclick="openDeleteModal(event, '${chat.id}')">
              <i class="fas fa-trash"></i> Delete
            </div>
          </div>
        </div>
      </div>`;
    historyList.insertAdjacentHTML('beforeend', html);
  });
}

async function addChatToSidebar(title, autoSelect = false) {
  const currentId = await getSessionId();
  savedChats.push({ id: currentId, name: title, pinned: false });
  localStorage.setItem("saved_chats", JSON.stringify(savedChats));
  renderSidebar();

  if (autoSelect) {
    selectChat(currentId);
  } else {
    document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
    const item = document.querySelector(`.history-item[data-id="${currentId}"]`);
    if (item) item.classList.add('active');
  }
}

function toggleChatMenu(e, id) {
  e.stopPropagation();
  document.querySelectorAll('.chat-dropdown').forEach(m => {
    if (m.id !== `menu-${id}`) m.classList.remove('show');
  });
  document.getElementById(`menu-${id}`).classList.toggle('show');
}

function pinChat(e, id) {
  e.stopPropagation();
  const chat = savedChats.find(c => c.id === id);
  if (chat) chat.pinned = !chat.pinned;
  localStorage.setItem("saved_chats", JSON.stringify(savedChats));
  renderSidebar();
}

const renameModal = document.getElementById('renameModal');
const renameInput = document.getElementById('renameInput');
const renameForm = document.getElementById('renameForm');

function openRenameModal(e, id) {
  e.stopPropagation();
  currentRenameId = id;
  const chat = savedChats.find(c => c.id === id);
  if (chat) {
    renameInput.value = chat.name;
    renameModal.classList.remove('hidden');
    renameInput.focus();
  }
}

document.getElementById('cancelRenameBtn').addEventListener('click', () => {
  renameModal.classList.add('hidden');
  currentRenameId = null;
});

renameForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const newName = renameInput.value.trim();
  if (newName && currentRenameId) {
    const chat = savedChats.find(c => c.id === currentRenameId);
    if (chat) {
      chat.name = newName;
      localStorage.setItem("saved_chats", JSON.stringify(savedChats));
      renderSidebar();
    }
  }
  renameModal.classList.add('hidden');
  currentRenameId = null;
});

const deleteModal = document.getElementById('deleteModal');

function openDeleteModal(e, id) {
  e.stopPropagation();
  currentDeleteId = id;
  deleteModal.classList.remove('hidden');
}

document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
  deleteModal.classList.add('hidden');
  currentDeleteId = null;
});

document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
  if (!currentDeleteId) return;
  const id = currentDeleteId;
  deleteModal.classList.add('hidden');
  currentDeleteId = null;

  const token = localStorage.getItem("access_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    await fetch(`/chat/${id}`, { method: 'DELETE', headers });
  } catch (err) { console.error(err); }

  savedChats = savedChats.filter(c => c.id !== id);
  localStorage.setItem("saved_chats", JSON.stringify(savedChats));
  renderSidebar();

  if (localStorage.getItem("chat_session_id") === id) {
    document.getElementById('newChatBtn').click();
  }
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('.chat-actions')) {
    document.querySelectorAll('.chat-dropdown').forEach(m => m.classList.remove('show'));
  }
});

async function syncUserChats() {
  const token = localStorage.getItem("access_token");
  if (!token) return;
  try {
    const res = await fetch("/user/chats", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();

    let localChats = JSON.parse(localStorage.getItem("saved_chats") || "[]");
    data.chats.forEach(serverChat => {
      if (!localChats.find(c => c.id === serverChat.id)) {
        localChats.push(serverChat);
      }
    });
    localStorage.setItem("saved_chats", JSON.stringify(localChats));
    savedChats = localChats;
    renderSidebar();
  } catch (err) { console.error(err); }
}

document.addEventListener("DOMContentLoaded", () => {
  const storedName = localStorage.getItem("user_name");
  if (storedName) document.getElementById('profileName').textContent = storedName;
  renderSidebar();
  syncUserChats();
});

const authModal = document.getElementById('authModal');
const openModalBtn = document.getElementById('openModalBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const tabLoginBtn = document.getElementById('tabLoginBtn');
const tabSignupBtn = document.getElementById('tabSignupBtn');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const modalTitle = document.getElementById('modalTitle');
const modalSubtitle = document.getElementById('modalSubtitle');
const profileName = document.getElementById('profileName');

const openModal = () => authModal.classList.remove('hidden');
const closeModal = () => authModal.classList.add('hidden');

const showLogin = () => {
  tabLoginBtn.classList.add('active'); tabSignupBtn.classList.remove('active');
  loginForm.classList.remove('hidden'); signupForm.classList.add('hidden');
  modalTitle.textContent = 'Welcome back';
  modalSubtitle.textContent = 'Login to continue your conversations';
};

const showSignup = () => {
  tabSignupBtn.classList.add('active'); tabLoginBtn.classList.remove('active');
  signupForm.classList.remove('hidden'); loginForm.classList.add('hidden');
  modalTitle.textContent = 'Create an account';
  modalSubtitle.textContent = 'Sign up to start saving your chats';
};

openModalBtn.addEventListener('click', openModal);
closeModalBtn.addEventListener('click', closeModal);
tabLoginBtn.addEventListener('click', showLogin);
tabSignupBtn.addEventListener('click', showSignup);

function handleAuthSuccess(name, userId, token) {
  localStorage.setItem("user_id", userId);
  localStorage.setItem("user_name", name);
  localStorage.setItem("access_token", token);
  profileName.textContent = name;
  closeModal();
  showToast("Successfully authenticated!", "success");
  syncUserChats();
  if (pendingPrompt) {
    const textToSend = pendingPrompt;
    pendingPrompt = "";
    executeSend(textToSend, true);
  }
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;
  try {
    const res = await fetch("/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const contentType = res.headers.get("content-type");
    let data;
    if (contentType && contentType.includes("application/json")) {
      data = await res.json();
    } else {
      const errText = await res.text();
      throw new Error(errText || "Internal Server Error");
    }
    if (!res.ok) throw new Error(data.detail || "Login failed");
    handleAuthSuccess(data.name, data.user_id, data.access_token);
  } catch (err) { showToast(err.message, "error"); }
});

signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("signupFirstName").value + " " + document.getElementById("signupLastName").value;
  const email = document.getElementById("signupEmail").value;
  const password = document.getElementById("signupPassword").value;
  try {
    const res = await fetch("/register", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });

    const contentType = res.headers.get("content-type");
    let data;
    if (contentType && contentType.includes("application/json")) {
      data = await res.json();
    } else {
      const errText = await res.text();
      throw new Error(errText || "Internal Server Error");
    }
    if (!res.ok) throw new Error(data.detail || "Registration failed");
    handleAuthSuccess(data.name, data.user_id, data.access_token);
  } catch (err) { showToast(err.message, "error"); }
});

const welcomeScreen = document.getElementById('welcomeScreen');
const chatScreen = document.getElementById('chatScreen');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const chatInputActive = document.getElementById('chatInputActive');
const sendBtnActive = document.getElementById('sendBtnActive');
const stopBtnActive = document.getElementById('stopBtnActive');
const newChatBtn = document.getElementById('newChatBtn');
const chatNameModal = document.getElementById('chatNameModal');
const chatNameForm = document.getElementById('chatNameForm');
const chatNameInput = document.getElementById('chatNameInput');
const closeChatNameModalBtn = document.getElementById('closeChatNameModalBtn');

function toggleInputState(input, send) {
  send.disabled = !(input.value.trim().length > 0);
}

function handleInputResize(textarea, sendButton) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  toggleInputState(textarea, sendButton);
}

function handleKeyDown(e, textarea) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (textarea.value.trim().length > 0) {
      handleSend();
    }
  }
}

function cancelChatName() {
  chatNameModal.classList.add('hidden');
  pendingPrompt = "";
  chatInput.value = "";
  chatInputActive.value = "";
  chatInput.style.height = 'auto';
  chatInputActive.style.height = 'auto';
  sendBtn.disabled = true;
  sendBtnActive.disabled = true;
  if (!welcomeScreen.classList.contains('hidden')) {
    chatInput.focus();
  } else {
    chatInputActive.focus();
  }
}

closeChatNameModalBtn.addEventListener('click', cancelChatName);

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (!authModal.classList.contains('hidden')) closeModal();
    if (!chatNameModal.classList.contains('hidden')) cancelChatName();
    if (!renameModal.classList.contains('hidden')) {
      renameModal.classList.add('hidden');
      currentRenameId = null;
    }
    if (!deleteModal.classList.contains('hidden')) {
      deleteModal.classList.add('hidden');
      currentDeleteId = null;
    }
  }
});

const typingEffect = (text, textElement) => {
  textElement.innerHTML = "";
  const words = text.split(" ");
  let wordIndex = 0;
  const messageArea = document.getElementById('messageArea');
  typingInterval = setInterval(() => {
    if (wordIndex < words.length) {
      wordIndex++;
      const currentText = words.slice(0, wordIndex).join(" ");
      textElement.innerHTML = parseMarkdown(currentText);
      if (messageArea) messageArea.scrollTop = messageArea.scrollHeight;
    } else {
      clearInterval(typingInterval);
      stopBtnActive.classList.add("hidden");
    }
  }, 35);
};

function handleSend() {
  const activeInput = !welcomeScreen.classList.contains('hidden') ? chatInput : chatInputActive;
  const text = activeInput.value.trim();
  if (!text) return;

  if (isNewSession) {
    pendingPrompt = text;
    chatNameInput.value = text.substring(0, 25) + (text.length > 25 ? "..." : "");
    chatNameModal.classList.remove('hidden');
    chatNameInput.focus();
    return;
  }

  executeSend(text);
}

chatNameForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const chatName = chatNameInput.value.trim();
  if (chatName) {
    pendingChatName = chatName;
  }
  chatNameModal.classList.add('hidden');

  if (pendingPrompt) {
    const textToSend = pendingPrompt;
    pendingPrompt = "";
    executeSend(textToSend);
  }
});

async function executeSend(text, isRetry = false) {
  if (!welcomeScreen.classList.contains('hidden')) {
    welcomeScreen.classList.add('hidden');
    chatScreen.classList.remove('hidden');
  }

  if (!isRetry) {
    appendMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    chatInputActive.value = '';
    chatInputActive.style.height = 'auto';
    sendBtn.disabled = true;
    sendBtnActive.disabled = true;
    chatInput.disabled = true;
    chatInputActive.disabled = true;
  }

  const aiMsgDiv = appendMessage('ai', 'Thinking...');
  stopBtnActive.classList.remove("hidden");
  controller = new AbortController();

  const token = localStorage.getItem("access_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const sessionId = await getSessionId();
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ prompt: text, session_id: sessionId }),
      signal: controller.signal
    });

    const contentType = response.headers.get("content-type");
    let data;
    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
    } else {
      const errText = await response.text();
      throw new Error(errText || "Internal Server Error");
    }

    if (response.status === 403 && data.detail === "LOGIN_REQUIRED") {
      aiMsgDiv.remove();
      const container = document.getElementById('messageArea').querySelector('.message-container');
      if (container && container.lastElementChild) {
        container.lastElementChild.remove();
      }
      pendingPrompt = text;
      openModal();
      return;
    }

    if (!response.ok) throw new Error(data.detail || "Server error occurred");

    if (pendingChatName) {
      await addChatToSidebar(pendingChatName, false);
      isNewSession = false;
      pendingChatName = "";
    }

    typingEffect(data.response.trim(), aiMsgDiv);
  } catch (error) {
    aiMsgDiv.textContent = error.name === "AbortError" ? "Stopped." : error.message;
    aiMsgDiv.style.color = "#d62939";
    stopBtnActive.classList.add("hidden");
  } finally {
    chatInput.disabled = false;
    chatInputActive.disabled = false;
    chatInputActive.focus();
  }
}

function appendMessage(sender, text) {
  const container = document.getElementById('messageArea').querySelector('.message-container');
  if (!container) return null;

  const roleClass = (sender === 'assistant' || sender === 'ai') ? 'ai' : 'user';
  const div = document.createElement('div');
  div.className = `message ${roleClass}`;
  
  if (roleClass === 'ai') {
    div.innerHTML = parseMarkdown(text);
  } else {
    div.innerText = text;
  }
  
  container.appendChild(div);
  const messageArea = document.getElementById('messageArea');
  if (messageArea) messageArea.scrollTop = messageArea.scrollHeight;
  return div;
}

chatInput.addEventListener('input', function() { handleInputResize(this, sendBtn); });
chatInput.addEventListener('keydown', function(e) { handleKeyDown(e, this); });
sendBtn.addEventListener('click', handleSend);

chatInputActive.addEventListener('input', function() { handleInputResize(this, sendBtnActive); });
chatInputActive.addEventListener('keydown', function(e) { handleKeyDown(e, this); });
sendBtnActive.addEventListener('click', handleSend);

stopBtnActive.addEventListener('click', () => {
  controller?.abort();
  clearInterval(typingInterval);
  stopBtnActive.classList.add("hidden");
  chatInput.disabled = false;
  chatInputActive.disabled = false;
});

newChatBtn.addEventListener('click', async () => {
  await createNewSession();
  welcomeScreen.classList.remove('hidden');
  chatScreen.classList.add('hidden');
  
  const container = document.getElementById('messageArea').querySelector('.message-container');
  if (container) container.innerHTML = '';
  
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;
  chatInput.focus();
  document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
});

async function selectChat(sid) {
  document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
  const item = document.querySelector(`.history-item[data-id="${sid}"]`);
  if (item) item.classList.add('active');

  localStorage.setItem("chat_session_id", sid);
  isNewSession = false;

  const token = localStorage.getItem("access_token");
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`/history/${sid}`, { headers });
    const contentType = res.headers.get("content-type");
    let data;
    if (contentType && contentType.includes("application/json")) {
      data = await res.json();
    } else {
      const errText = await res.text();
      throw new Error(errText || "Internal Server Error");
    }

    const container = document.getElementById('messageArea').querySelector('.message-container');
    if (container) container.innerHTML = '';
    
    welcomeScreen.classList.add('hidden');
    chatScreen.classList.remove('hidden');

    if (data.history) {
      data.history.forEach(msg => appendMessage(msg.role, msg.content));
    }
  } catch (err) { console.error(err); }
}

window.addEventListener('load', () => chatInput.focus());
window.addEventListener('click', (e) => {
  if (e.target === authModal) closeModal();
  if (e.target === chatNameModal) cancelChatName();
  if (e.target === renameModal) { renameModal.classList.add('hidden'); currentRenameId = null; }
  if (e.target === deleteModal) { deleteModal.classList.add('hidden'); currentDeleteId = null; }
});