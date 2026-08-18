const API_URL = const API_URL = "https://ragforge-ai-production.up.railway.app";;
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const documentList = document.getElementById("documentList");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const messagesContainer = document.getElementById("messagesContainer");

uploadBtn.addEventListener("click", uploadFile);
sendBtn.addEventListener("click", sendMessage);
questionInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter") sendMessage();
});

async function uploadFile() {
    const files = fileInput.files;
    if (files.length === 0) {
        alert("Select a PDF");
        return;
    }
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";
    
    const file = files[0];
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch(API_URL + "/upload", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        alert("Uploaded: " + data.filename + " with " + data.chunk_count + " chunks");
        refreshDocumentList();
    } catch (error) {
        alert("Upload failed: " + error.message);
    }
    
    fileInput.value = "";
    uploadBtn.disabled = false;
    uploadBtn.textContent = "Upload PDF";
}

function refreshDocumentList() {
    fetch(API_URL + "/documents")
        .then(r => r.json())
        .then(data => {
            documentList.innerHTML = "";
            if (data.count > 0) {
                data.documents.forEach(doc => {
                    const div = document.createElement("div");
                    div.className = "document-item";
                    
                    const info = document.createElement("div");
                    info.className = "doc-info";
                    
                    const name = document.createElement("div");
                    name.className = "doc-name";
                    name.textContent = "📄 " + doc.filename;
                    
                    const chunks = document.createElement("div");
                    chunks.className = "doc-chunks";
                    chunks.textContent = doc.chunks + " chunks • " + doc.stored + " stored";
                    
                    info.appendChild(name);
                    info.appendChild(chunks);
                    div.appendChild(info);
                    
                    const btn = document.createElement("button");
                    btn.className = "delete-doc";
                    btn.textContent = "Delete";
                    btn.onclick = function() {
                        deleteDocument(doc.doc_id);
                    };
                    
                    div.appendChild(btn);
                    documentList.appendChild(div);
                });
            } else {
                documentList.innerHTML = '<p class="empty-state">No documents uploaded yet</p>';
            }
        });
}

function deleteDocument(docId) {
    if (!confirm("Delete this document?")) return;
    
    fetch(API_URL + "/documents/" + docId, {method: "DELETE"})
        .then(r => r.json())
        .then(data => {
            displayMessage("Document deleted successfully", "bot");
            refreshDocumentList();
        });
}

async function sendMessage() {
    const question = questionInput.value.trim();
    if (!question) return;
    
    displayMessage(question, "user");
    questionInput.value = "";
    sendBtn.disabled = true;
    sendBtn.textContent = "Thinking...";
    
    try {
        const response = await fetch(API_URL + "/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({question: question})
        });
        const data = await response.json();
        
        // Display answer and sources
        displayMessage(data.answer, "bot", data.sources);
        
    } catch (error) {
        displayMessage("Error: " + error.message, "bot");
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = "Send";
        questionInput.focus();
    }
}

function displayMessage(text, sender, sources = null) {
    const div = document.createElement("div");
    div.className = "message " + sender + "-message";
    
    // Display answer text
    const answerDiv = document.createElement("div");
    answerDiv.textContent = text;
    div.appendChild(answerDiv);
    
    // Display sources if provided (bot message only)
    if (sender === "bot" && sources && sources.length > 0) {
        const sourcesDiv = document.createElement("div");
        sourcesDiv.className = "message-sources";
        
        const sourceTitle = document.createElement("div");
        sourceTitle.style.fontWeight = "700";
        sourceTitle.style.marginBottom = "8px";
        sourceTitle.textContent = "📚 Sources";
        sourcesDiv.appendChild(sourceTitle);
        
        sources.forEach(source => {
            const sourceItem = document.createElement("div");
            sourceItem.className = "source-item";
            sourceItem.innerHTML = "<strong>" + source.filename + "</strong><br><span style=\"font-size: 11px; opacity: 0.8;\">Chunk " + source.chunk_index + " • Similarity: " + (source.similarity * 100).toFixed(1) + "%</span>";
            sourcesDiv.appendChild(sourceItem);
        });
        
        div.appendChild(sourcesDiv);
    }
    
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

refreshDocumentList();