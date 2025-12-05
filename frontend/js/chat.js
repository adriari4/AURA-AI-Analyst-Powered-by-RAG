const API_URL = "http://localhost:8000";

// --- Search Logic ---
const queryInput = document.getElementById('queryInput');
const askBtn = document.getElementById('askBtn');
const resultCard = document.getElementById('resultCard');
const answerText = document.getElementById('answerText');
const sourceLink = document.getElementById('sourceLink');
const loader = document.getElementById('loader');
let currentAudio = null;

async function askText() {
    const query = queryInput.value.trim();
    if (!query) return;

    showLoading(true);

    try {
        const response = await fetch(`${API_URL}/ask-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await response.json();
        displayResult(data);
    } catch (error) {
        displayResult({ answer: "Error: " + error.message });
    } finally {
        showLoading(false);
    }
}
function displayResult(data) {
    const text = data.answer || "";
    const audioBase64 = data.audio_base64;

    // Regex for markdown links
    const linkRegex = /\[(.*?)\]\((.*?)\)/;
    const match = text.match(linkRegex);

    let cleanText = text;
    let citationHtml = "INVERTIR DESDE CERO YOUTUBE CHANNEL"; // Default requested by user

    if (match) {
        cleanText = text.replace(match[0], "").trim();
        citationHtml = `<a href="${match[2]}" target="_blank">${match[1]}</a>`;
    } else if (text.includes("Source: Invertir Desde Cero (Pinecone)")) {
        // Clean up the backend's text citation so it doesn't appear twice
        cleanText = text.replace("Source: Invertir Desde Cero (Pinecone)", "").trim();
        citationHtml = "INVERTIR DESDE CERO YOUTUBE CHANNEL";
    }

    // Typewriter effect for text? Or just simple fade in.
    answerText.innerText = cleanText;
    sourceLink.innerHTML = citationHtml;

    resultCard.classList.add('visible');

    // Auto Play Audio
    if (audioBase64) {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        currentAudio = new Audio("data:audio/mp3;base64," + audioBase64);
        currentAudio.play().catch(e => console.error("Auto-play failed:", e));
    }
}

function showLoading(isLoading) {
    if (isLoading) {
        loader.style.display = 'flex';
        resultCard.classList.remove('visible');
    } else {
        loader.style.display = 'none';
    }
}

if (askBtn) {
    askBtn.addEventListener('click', askText);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') askText();
    });
}

// --- Audio Logic ---
const micBtn = document.getElementById('micBtn');
let mediaRecorder;
let audioChunks = [];

if (micBtn) {
    micBtn.addEventListener('click', async () => {
        if (!mediaRecorder || mediaRecorder.state === "inactive") {
            startRecording();
        } else {
            stopRecording();
        }
    });
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            // Browsers (Chrome/Firefox) record in WebM/Ogg by default.
            // Using 'audio/mp3' here was incorrect and caused corrupt files.
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudio(audioBlob);

            // Stop all tracks to release microphone
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        micBtn.classList.add('recording');
    } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Could not access microphone. Please allow permissions.");
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        micBtn.classList.remove('recording');
    }
}

async function sendAudio(blob) {
    showLoading(true);
    const formData = new FormData();
    // Send as .webm
    formData.append("file", blob, "recording.webm");

    try {
        const response = await fetch(`${API_URL}/ask-audio`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        // If transcription exists, update input box to show what was heard
        if (data.transcription) {
            queryInput.value = data.transcription;
        }

        displayResult(data);
    } catch (error) {
        displayResult({ answer: "Error: " + error.message });
    } finally {
        showLoading(false);
    }
}

// --- Dashboard Logic ---
async function fetchStats() {
    const videoCountEl = document.getElementById('videoCount');
    const vectorCountEl = document.getElementById('vectorCount');

    if (!videoCountEl) return;

    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();

        vectorCountEl.innerText = data.total_vectors || 0;
        videoCountEl.innerText = "30+";
    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}

if (document.getElementById('videoCount')) {
    fetchStats();
}
