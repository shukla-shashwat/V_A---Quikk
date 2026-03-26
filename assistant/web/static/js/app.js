// Qwikk Assistant - Frontend JS

class QwikkAssistant {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.commandInput = document.getElementById('commandInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.quickActions = document.getElementById('quickActions');
        
        this.ws = null;
        this.connected = false;
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Quick action buttons
        this.quickActions.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const cmd = btn.dataset.cmd;
                this.commandInput.value = cmd;
                this.sendMessage();
            });
        });
        
        // Connect WebSocket
        this.connectWebSocket();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.connected = true;
                this.updateStatus(true);
                console.log('⚡ Connected to Qwikk');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'welcome') {
                    console.log(data.message);
                } else if (data.type === 'response') {
                    this.hideTyping();
                    this.addMessage(data.message, 'assistant');
                }
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                this.updateStatus(false);
                console.log('Disconnected. Reconnecting...');
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.fallbackToREST();
            };
        } catch (e) {
            this.fallbackToREST();
        }
    }
    
    fallbackToREST() {
        // If WebSocket fails, use REST API
        this.ws = null;
        this.updateStatus(true); // Still show online since REST works
    }
    
    async sendMessage() {
        const text = this.commandInput.value.trim();
        if (!text) return;
        
        // Add user message
        this.addMessage(text, 'user');
        this.commandInput.value = '';
        
        // Show typing indicator
        this.showTyping();
        
        // Send via WebSocket or REST
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ text }));
        } else {
            // Fallback to REST API
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                
                const data = await response.json();
                this.hideTyping();
                this.addMessage(data.response, 'assistant');
            } catch (error) {
                this.hideTyping();
                this.addMessage('oops! something went wrong 😅', 'assistant');
            }
        }
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = sender === 'assistant' ? '⚡' : '👤';
        
        // Format the text (handle newlines and lists)
        const formattedText = this.formatMessage(text);
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-bubble">${formattedText}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(text) {
        // Convert newlines to <br> and handle lists
        let formatted = text
            .replace(/\n/g, '<br>')
            .replace(/•/g, '<span style="color: var(--accent-cyan)">•</span>')
            .replace(/📱|🔊|☀️|📸|🔒|📁|💻|🧮|⏰|❓|⚠️|🌐/g, '<span style="font-size: 1.1em">$&</span>');
        
        // Wrap in paragraph if no HTML
        if (!formatted.includes('<br>') && !formatted.includes('<p>')) {
            formatted = `<p>${formatted}</p>`;
        }
        
        return formatted;
    }
    
    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">⚡</div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) typing.remove();
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    updateStatus(online) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (online) {
            statusDot.style.background = 'var(--accent-green)';
            statusText.textContent = 'Online';
        } else {
            statusDot.style.background = 'var(--accent-pink)';
            statusText.textContent = 'Reconnecting...';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.qwikk = new QwikkAssistant();
});
