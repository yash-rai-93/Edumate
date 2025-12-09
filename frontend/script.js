const API_URL = "http://127.0.0.1:8000/ask";

// 1. Generate a random Session ID when the page loads
const sessionId = "session_" + Math.random().toString(36).substr(2, 9);
console.log("Your Session ID:", sessionId);

function appendMessage(text, sender) {
    const box = document.getElementById("chat-box");
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerHTML = text.replace(/\n/g, "<br>");
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
            // 2. Send session_id along with the question
            body: JSON.stringify({ 
                question: message,
                session_id: sessionId 
            })
        });

        const data = await res.json();
        removeTyping();
        appendMessage(data.answer, "bot");

    } catch (error) {
        console.error(error);
        removeTyping();
        appendMessage("⚠️ Error contacting server.", "bot");
    }
}