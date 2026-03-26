// Qwikk Assistant - Frontend JS with Voice Support

class QwikkAssistant {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.commandInput = document.getElementById('commandInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.voiceBtn = document.getElementById('voiceBtn');
        this.voiceSelect = document.getElementById('voiceSelect');
        this.quickActions = document.getElementById('quickActions');
        
        this.ws = null;
        this.connected = false;
        
        // Voice features
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.selectedVoice = null;
        this.isListening = false;
        this.voiceInputUsed = false; // Track if last input was voice
        this.isSending = false; // Prevent double-sending
        this.typingTimeout = null; // Timeout for stuck typing
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Voice button
        if (this.voiceBtn) {
            this.voiceBtn.addEventListener('click', () => this.toggleVoice());
        }
        
        // Voice selector
        if (this.voiceSelect) {
            this.voiceSelect.addEventListener('change', () => this.selectVoice());
        }
        
        // Quick action buttons
        this.quickActions.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const cmd = btn.dataset.cmd;
                this.commandInput.value = cmd;
                this.voiceInputUsed = false;
                this.sendMessage();
            });
        });
        
        // Initialize speech recognition
        this.initSpeechRecognition();
        
        // Load voices
        this.loadVoices();
        
        // Connect WebSocket
        this.connectWebSocket();
    }
    
    loadVoices() {
        const loadVoiceList = () => {
            const voices = this.synthesis.getVoices();
            if (!this.voiceSelect || voices.length === 0) return;
            
            // Clear and populate
            this.voiceSelect.innerHTML = '';
            
            // Filter to English voices
            const englishVoices = voices.filter(v => v.lang.startsWith('en'));
            const otherVoices = voices.filter(v => !v.lang.startsWith('en'));
            
            // Add English voices first
            if (englishVoices.length > 0) {
                const engGroup = document.createElement('optgroup');
                engGroup.label = '🇺🇸 English';
                englishVoices.forEach((voice, i) => {
                    const option = document.createElement('option');
                    option.value = i;
                    option.textContent = `${voice.name}`;
                    option.dataset.voiceName = voice.name;
                    if (voice.name.includes('Google') || voice.default) {
                        option.selected = true;
                        this.selectedVoice = voice;
                    }
                    engGroup.appendChild(option);
                });
                this.voiceSelect.appendChild(engGroup);
            }
            
            // Add other voices
            if (otherVoices.length > 0) {
                const otherGroup = document.createElement('optgroup');
                otherGroup.label = '🌍 Other';
                otherVoices.slice(0, 10).forEach((voice, i) => {
                    const option = document.createElement('option');
                    option.value = englishVoices.length + i;
                    option.textContent = `${voice.name}`;
                    option.dataset.voiceName = voice.name;
                    otherGroup.appendChild(option);
                });
                this.voiceSelect.appendChild(otherGroup);
            }
            
            // Set default if none selected
            if (!this.selectedVoice && voices.length > 0) {
                this.selectedVoice = englishVoices[0] || voices[0];
            }
        };
        
        // Load voices (some browsers need event)
        loadVoiceList();
        if (this.synthesis.onvoiceschanged !== undefined) {
            this.synthesis.onvoiceschanged = loadVoiceList;
        }
    }
    
    selectVoice() {
        const voices = this.synthesis.getVoices();
        const selectedName = this.voiceSelect.options[this.voiceSelect.selectedIndex]?.dataset.voiceName;
        
        if (selectedName) {
            this.selectedVoice = voices.find(v => v.name === selectedName);
            // Test the voice
            this.speak("Voice selected!");
        }
    }
    
    initSpeechRecognition() {
        // Check for browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported');
            if (this.voiceBtn) {
                this.voiceBtn.style.opacity = '0.5';
                this.voiceBtn.title = 'Voice not supported in this browser';
            }
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.voiceBtn.classList.add('listening');
            this.commandInput.placeholder = '🎤 Listening...';
        };
        
        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            
            this.commandInput.value = transcript;
            
            // If final result, send the message
            if (event.results[event.results.length - 1].isFinal) {
                this.voiceInputUsed = true;
                this.sendMessage();
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech error:', event.error);
            this.stopListening();
            
            if (event.error === 'not-allowed') {
                this.addMessage('🎤 Microphone access denied. Please allow microphone in browser settings.', 'assistant');
            }
        };
        
        this.recognition.onend = () => {
            this.stopListening();
        };
    }
    
    toggleVoice() {
        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.startListening();
        }
    }
    
    startListening() {
        if (!this.recognition) {
            this.addMessage('🎤 Voice not supported in this browser. Try Chrome or Edge.', 'assistant');
            return;
        }
        
        try {
            this.recognition.start();
        } catch (e) {
            console.error('Failed to start recognition:', e);
        }
    }
    
    stopListening() {
        this.isListening = false;
        if (this.voiceBtn) {
            this.voiceBtn.classList.remove('listening');
        }
        this.commandInput.placeholder = 'type or click 🎤 to speak...';
    }
    
    speak(text) {
        // Only speak if TTS is available
        if (!this.synthesis) return;
        
        // Cancel any ongoing speech
        this.synthesis.cancel();
        
        // Clean text for speech
        const cleanText = this.cleanForSpeech(text);
        if (!cleanText || cleanText.length < 2) return;
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Use selected voice
        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }
        
        this.synthesis.speak(utterance);
    }
    
    cleanForSpeech(text) {
        // Remove emojis, special chars, and formatting
        let clean = text
            .replace(/[╔╗╚╝║═]/g, '')  // Remove box chars
            .replace(/[•●○]/g, '')      // Remove bullets
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')  // Remove emojis
            .replace(/<[^>]*>/g, '')    // Remove HTML tags
            .replace(/\s+/g, ' ')       // Collapse whitespace
            .trim();
        
        // Limit length for long responses (like help)
        if (clean.length > 300) {
            clean = clean.substring(0, 200) + '. And more. Say help for full list.';
        }
        
        return clean;
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
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'welcome') {
                        console.log(data.message);
                    } else if (data.type === 'response') {
                        this.handleResponse(data.message);
                    } else if (data.type === 'error') {
                        this.handleResponse('Error: ' + (data.message || 'Unknown error'));
                    }
                } catch (e) {
                    console.error('Failed to parse message:', e);
                    this.hideTyping();
                }
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                this.updateStatus(false);
                this.hideTyping(); // Clear any stuck typing
                console.log('Disconnected. Reconnecting...');
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.hideTyping(); // Clear any stuck typing
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
        
        // Prevent double-sending
        if (this.isSending) return;
        this.isSending = true;
        
        // Add user message
        this.addMessage(text, 'user');
        this.commandInput.value = '';
        
        // Show typing indicator
        this.showTyping();
        
        // Set timeout to hide typing if no response
        this.typingTimeout = setTimeout(() => {
            this.hideTyping();
            this.addMessage('Taking longer than expected... try again?', 'assistant');
            this.isSending = false;
        }, 15000); // 15 second timeout
        
        // Send via WebSocket or REST
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify({ text }));
            } catch (e) {
                clearTimeout(this.typingTimeout);
                this.hideTyping();
                this.addMessage('Connection error. Trying REST...', 'assistant');
                this.isSending = false;
                await this.sendViaREST(text);
            }
        } else {
            await this.sendViaREST(text);
        }
    }
    
    async sendViaREST(text) {
        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            
            clearTimeout(this.typingTimeout);
            const data = await response.json();
            this.hideTyping();
            this.addMessage(data.response, 'assistant');
            
            // Speak response if input was via voice
            if (this.voiceInputUsed) {
                this.speak(data.response);
                this.voiceInputUsed = false;
            }
        } catch (error) {
            clearTimeout(this.typingTimeout);
            this.hideTyping();
            this.addMessage('oops! something went wrong 😅 check if server is running', 'assistant');
        } finally {
            this.isSending = false;
        }
    }
    
    handleResponse(message) {
        // Clear timeout
        clearTimeout(this.typingTimeout);
        this.hideTyping();
        this.addMessage(message, 'assistant');
        
        // Speak response if input was via voice
        if (this.voiceInputUsed) {
            this.speak(message);
            this.voiceInputUsed = false;
        }
        
        this.isSending = false;
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
            .replace(/📱|🔊|☀️|📸|🔒|📁|💻|🧮|⏰|❓|⚠️|🌐|📶|🔵|📡/g, '<span style="font-size: 1.1em">$&</span>');
        
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
    
    // Load voices (needed for some browsers)
    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
    }
});
