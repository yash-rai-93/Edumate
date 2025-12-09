const API_URL = "http://127.0.0.1:8000/ask";

// 1. Generate a random Session ID when the page loads
const sessionId = "session_" + Math.random().toString(36).substr(2, 9);
console.log("Your Session ID:", sessionId);

// --- VOICE SETUP ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'en-US'; // Set to English
recognition.interimResults = false;

// Flag to check if we should speak the response
let isVoiceActive = false;

// 1. Start Listening
function startVoice() {
    const micBtn = document.getElementById("mic-btn");
    
    if (isVoiceActive) {
        // Stop if already listening
        recognition.stop();
        return;
    }

    try {
        recognition.start();
        micBtn.classList.add("listening"); // Turn red
        isVoiceActive = true;
    } catch (error) {
        console.error("Speech recognition error:", error);
        isVoiceActive = false;
    }
}

// 2. Handle Result (When user stops speaking)
recognition.onend = () => {
    const micBtn = document.getElementById("mic-btn");
    micBtn.classList.remove("listening");
    // We don't reset isVoiceActive immediately so we know to speak the reply
};

recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("user-input").value = transcript;
    
    // Auto-send after speaking
    sendMessage();
};

// 3. Text-to-Speech Function (EduMate Speaks)
function speakText(text) {
    // Stop any current speech
    window.speechSynthesis.cancel();

    // Clean text (remove bold markers like ** or <b> for smoother speech)
    const cleanText = text.replace(/\*/g, "").replace(/<[^>]*>/g, "");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'en-US';
    utterance.rate = 1; // Normal speed
    utterance.pitch = 1;

    window.speechSynthesis.speak(utterance);
}

function appendMessage(text, sender) {
    const box = document.getElementById("chat-box");

    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    
    // 1. Convert newlines (\n) to <br>
    // 2. Convert bold markers (**text**) to <b>text</b>
    let formattedText = text.replace(/\n/g, "<br>");
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");

    msg.innerHTML = formattedText;

    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
}
function showTyping() {
    const box = document.getElementById("chat-box");
    const typing = document.createElement("div");
    typing.classList.add("message", "bot");
    typing.id = "typing";
    typing.innerHTML = `
        <div class="typing">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    box.appendChild(typing);
    box.scrollTop = box.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById("typing");
    if (el) el.remove();
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    input.value = "";
    showTyping();

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                question: message,
                session_id: sessionId 
            })
        });

        const data = await res.json();
        removeTyping();
        appendMessage(data.answer, "bot");

        // IF request came from Voice, speak the answer
        if (isVoiceActive) {
            speakText(data.answer);
            isVoiceActive = false; // Reset flag after speaking
        }

    } catch (error) {
        console.error(error);
        removeTyping();
        appendMessage("⚠️ Error contacting server.", "bot");
        isVoiceActive = false;
    }
}

// ... existing code ...

async function requestFeature(type) {
    let topic = "";
    let endpoint = "";
    
    // 1. Determine action based on button click
    if (type === 'quiz') {
        topic = prompt("Enter the topic for the quiz (e.g., Acids and Bases):");
        if (!topic) return;
        appendMessage(`📝 Generating quiz for: ${topic}...`, "user");
        endpoint = "/quiz";
    } 
    else if (type === 'summary') {
        topic = prompt("Enter the chapter/topic to summarize:");
        if (!topic) return;
        appendMessage(`📄 Summarizing: ${topic}...`, "user");
        endpoint = "/summary";
    } 
    else if (type === 'countdown') {
        appendMessage("⏳ Checking exam schedule...", "user");
        endpoint = "/countdown";
    }

    showTyping();

    try {
        let body = {};
        let method = "POST";
        
        // Prepare request data
        if (type === 'countdown') {
            method = "GET"; 
        } else {
            body = JSON.stringify({ topic: topic });
        }

        const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: method === "POST" ? body : null
        });

        const data = await res.json();
        removeTyping();
        
        // Show result
        appendMessage(data.answer, "bot");

    } catch (error) {
        removeTyping();
        appendMessage("⚠️ Error fetching data.", "bot");
    }
}