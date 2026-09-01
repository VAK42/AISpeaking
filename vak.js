const appState = {
  activeLanguage: "English",
  conversationHistory: [],
  mediaRecorder: null,
  audioChunks: [],
  isRecording: false
};
const domElements = {
  languageSelect: document.getElementById("languageSelect"),
  statusValue: document.getElementById("statusValue"),
  waveVisualizer: document.getElementById("waveVisualizer"),
  chatStream: document.getElementById("chatStream"),
  voiceButton: document.getElementById("voiceButton"),
  sendButton: document.getElementById("sendButton"),
  clearChatButton: document.getElementById("clearChatButton"),
  textInput: document.getElementById("textInput"),
  audioPlayer: document.getElementById("tutorAudioPlayer")
};
function syncActiveLanguage() {
  if (domElements.languageSelect && domElements.languageSelect.value) {
    appState.activeLanguage = domElements.languageSelect.value;
  }
}
function setWaveActive(isActive) {
  if (isActive) {
    domElements.waveVisualizer.classList.remove("waveHidden");
  } else {
    domElements.waveVisualizer.classList.add("waveHidden");
  }
}
function updateStatus(statusText, isAnimating = false) {
  domElements.statusValue.textContent = statusText;
  setWaveActive(isAnimating);
}
function appendUserMessage(messageText) {
  const rowDiv = document.createElement("div");
  rowDiv.className = "messageRow userRow";
  const bubbleDiv = document.createElement("div");
  bubbleDiv.className = "userBubble";
  const headerDiv = document.createElement("div");
  headerDiv.className = "bubbleHeader";
  const titleSpan = document.createElement("span");
  titleSpan.textContent = "You";
  const timeSpan = document.createElement("span");
  timeSpan.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  headerDiv.appendChild(titleSpan);
  headerDiv.appendChild(timeSpan);
  const contentDiv = document.createElement("div");
  contentDiv.className = "bubbleContent";
  contentDiv.textContent = messageText;
  bubbleDiv.appendChild(headerDiv);
  bubbleDiv.appendChild(contentDiv);
  rowDiv.appendChild(bubbleDiv);
  domElements.chatStream.appendChild(rowDiv);
  domElements.chatStream.scrollTop = domElements.chatStream.scrollHeight;
}
function appendTutorMessage(messageText) {
  const rowDiv = document.createElement("div");
  rowDiv.className = "messageRow tutorRow";
  const bubbleDiv = document.createElement("div");
  bubbleDiv.className = "tutorBubble";
  const headerDiv = document.createElement("div");
  headerDiv.className = "bubbleHeader";
  const titleSpan = document.createElement("span");
  titleSpan.textContent = "Nobunaga";
  const replayBtn = document.createElement("button");
  replayBtn.className = "replayBtn";
  replayBtn.textContent = "Again";
  replayBtn.addEventListener("click", () => playSpeech(messageText, appState.activeLanguage));
  headerDiv.appendChild(titleSpan);
  headerDiv.appendChild(replayBtn);
  const contentDiv = document.createElement("div");
  contentDiv.className = "bubbleContent";
  contentDiv.textContent = messageText;
  bubbleDiv.appendChild(headerDiv);
  bubbleDiv.appendChild(contentDiv);
  rowDiv.appendChild(bubbleDiv);
  domElements.chatStream.appendChild(rowDiv);
  domElements.chatStream.scrollTop = domElements.chatStream.scrollHeight;
}
async function sendUserMessage(textContent) {
  syncActiveLanguage();
  if (!textContent || textContent.trim() === "") {
    return;
  }
  const trimmedText = textContent.trim();
  appendUserMessage(trimmedText);
  appState.conversationHistory.push({ role: "User", content: trimmedText });
  domElements.textInput.value = "";
  updateStatus("Nobunaga Is Thinking", true);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: trimmedText,
        tutorLanguage: appState.activeLanguage,
        history: appState.conversationHistory
      })
    });
    const data = await response.json();
    const tutorReply = data.response || "I Understood! Let Us Continue Practicing";
    appendTutorMessage(tutorReply);
    appState.conversationHistory.push({ role: "Nobunaga", content: tutorReply });
    playSpeech(tutorReply, appState.activeLanguage);
  } catch (errorObject) {
    updateStatus("Connection Error", false);
    const fallbackText = "Sorry, I Encountered A Network Issue! Please Try Again";
    appendTutorMessage(fallbackText);
  }
}
async function playSpeech(textToSpeak, languageName) {
  updateStatus("Speaking Out Loud", true);
  const languageCode = languageName === "Japanese" ? "ja" : "en";
  try {
    const response = await fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: textToSpeak, language: languageCode })
    });
    if (response.ok) {
      const audioBlob = await response.blob();
      if (audioBlob.size > 0) {
        const audioUrl = URL.createObjectURL(audioBlob);
        domElements.audioPlayer.src = audioUrl;
        domElements.audioPlayer.onplay = () => updateStatus("Speaking Out Loud", true);
        domElements.audioPlayer.onended = () => updateStatus("Ready For Speaking", false);
        domElements.audioPlayer.onerror = () => updateStatus("Audio Playback Error", false);
        domElements.audioPlayer.play().catch(() => updateStatus("Click Again To Play Audio", false));
      } else {
        updateStatus("Ready For Speaking", false);
      }
    } else {
      updateStatus("Speech Synthesis Error", false);
    }
  } catch (errorObject) {
    updateStatus("Speech Synthesis Error", false);
  }
}
async function toggleVoiceRecording() {
  if (appState.isRecording) {
    stopAudioRecording();
  } else {
    await startAudioRecording();
  }
}
async function startAudioRecording() {
  syncActiveLanguage();
  try {
    const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    appState.audioChunks = [];
    appState.mediaRecorder = new MediaRecorder(audioStream);
    appState.mediaRecorder.ondataavailable = eventObject => {
      if (eventObject.data.size > 0) {
        appState.audioChunks.push(eventObject.data);
      }
    };
    appState.mediaRecorder.onstop = async () => {
      syncActiveLanguage();
      updateStatus("Transcribing Speech Input", true);
      const audioBlob = new Blob(appState.audioChunks, { type: "audio/wav" });
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(
        new Uint8Array(arrayBuffer).reduce((dataString, byteValue) => dataString + String.fromCharCode(byteValue), "")
      );
      const languageCode = appState.activeLanguage === "Japanese" ? "ja" : "en";
      try {
        const response = await fetch("/api/transcribe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ audio: base64Audio, language: languageCode })
        });
        const data = await response.json();
        if (data.transcript && data.transcript.trim() !== "") {
          sendUserMessage(data.transcript);
        } else {
          updateStatus("No Speech Detected", false);
        }
      } catch (errorObject) {
        updateStatus("Transcription Failed", false);
      }
    };
    appState.mediaRecorder.start();
    appState.isRecording = true;
    domElements.voiceButton.classList.add("recordingActive");
    updateStatus("Listening To Your Voice", true);
  } catch (errorObject) {
    updateStatus("Microphone Permission Denied", false);
  }
}
function stopAudioRecording() {
  if (appState.mediaRecorder && appState.isRecording) {
    appState.mediaRecorder.stop();
    appState.isRecording = false;
    domElements.voiceButton.classList.remove("recordingActive");
    appState.mediaRecorder.stream.getTracks().forEach(trackItem => trackItem.stop());
  }
}
function resetConversation() {
  syncActiveLanguage();
  appState.conversationHistory = [];
  domElements.chatStream.innerHTML = "";
  const welcomeText = appState.activeLanguage === "Japanese"
    ? "こんにちは！ノブナガです。日本語の準備ができました。挨拶や好きな話題を話してください"
    : "Hi! I Am Nobunaga, Your English Tutor. Please Greet Or Speak Any Topic To Begin";
  appendTutorMessage(welcomeText);
  updateStatus("Ready For Speaking", false);
}
function attachEventListeners() {
  domElements.languageSelect.addEventListener("change", () => {
    syncActiveLanguage();
    resetConversation();
  });
  domElements.voiceButton.addEventListener("click", toggleVoiceRecording);
  domElements.sendButton.addEventListener("click", () => {
    sendUserMessage(domElements.textInput.value);
  });
  domElements.textInput.addEventListener("keydown", eventObject => {
    if (eventObject.key === "Enter") {
      sendUserMessage(domElements.textInput.value);
    }
  });
  domElements.clearChatButton.addEventListener("click", resetConversation);
}
document.addEventListener("DOMContentLoaded", () => {
  attachEventListeners();
  syncActiveLanguage();
  resetConversation();
});