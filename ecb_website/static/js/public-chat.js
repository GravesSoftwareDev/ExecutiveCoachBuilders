(function () {
  const root = document.getElementById('ecb-chat-widget');
  if (!root) return;

  const launcher = document.getElementById('ecb-chat-launcher');
  const panel = document.getElementById('ecb-chat-panel');
  const closeBtn = document.getElementById('ecb-chat-close');
  const messagesEl = document.getElementById('ecb-chat-messages');
  const form = document.getElementById('ecb-chat-form');
  const input = document.getElementById('ecb-chat-input');
  const sendBtn = document.getElementById('ecb-chat-send');
  const chips = document.getElementById('ecb-chat-chips');
  const chatUrl = root.dataset.chatUrl;
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  const history = [];

  function setOpen(open) {
    panel.classList.toggle('is-open', open);
    launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) input.focus();
  }

  function addMessage(role, text, record = true) {
    const node = document.createElement('div');
    node.className = `ecb-msg ecb-msg-${role}`;
    node.textContent = text;
    messagesEl.appendChild(node);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    if (record && (role === 'user' || role === 'bot')) {
      history.push({ role: role === 'bot' ? 'assistant' : 'user', content: text });
      if (history.length > 12) history.shift();
    }
    return node;
  }

  async function ask(text) {
    const message = text.trim();
    if (!message) return;
    const priorHistory = history.slice();
    input.value = '';
    addMessage('user', message);
    const pending = addMessage('bot', 'Thinking...', false);
    sendBtn.disabled = true;

    try {
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf,
        },
        body: JSON.stringify({ message, history: priorHistory }),
      });
      const data = await response.json();
      const reply = data.reply || 'I could not answer that right now. Please use the contact form.';
      pending.textContent = reply;
      history.push({ role: 'assistant', content: reply });
    } catch (error) {
      pending.textContent = 'Chat is unavailable right now. Please use the contact form.';
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  launcher.addEventListener('click', () => setOpen(!panel.classList.contains('is-open')));
  closeBtn.addEventListener('click', () => setOpen(false));
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    ask(input.value);
  });
  chips.addEventListener('click', (event) => {
    if (event.target.tagName === 'BUTTON') ask(event.target.textContent || '');
  });
})();
