const API_URL = "https://ragforge-ai-production.up.railway.app";

const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const documentList = document.getElementById("documentList");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const messagesContainer = document.getElementById("messagesContainer");


// ============================================================
// TEMPORARY CLIENT ID
// ============================================================

// This is NOT authentication.
// It simply gives each browser a unique ID.
//
// Later, when we add Supabase Auth + JWT,
// this will be replaced by the real authenticated user ID.

let clientId = localStorage.getItem("inside_client_id");

if (!clientId) {
    clientId = crypto.randomUUID();
    localStorage.setItem("inside_client_id", clientId);
}

console.log("INSIDE Client ID:", clientId);


// ============================================================
// EVENT LISTENERS
// ============================================================

uploadBtn.addEventListener("click", uploadFile);

sendBtn.addEventListener("click", sendMessage);

questionInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});


// ============================================================
// COMMON HEADERS
// ============================================================

function getClientHeaders() {
    return {
        "X-Client-ID": clientId
    };
}


// ============================================================
// UPLOAD PDF
// ============================================================

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

        const response = await fetch(
            API_URL + "/upload",
            {
                method: "POST",

                headers: getClientHeaders(),

                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Upload failed"
            );
        }

        alert(
            "Uploaded: " +
            data.filename +
            " with " +
            data.chunk_count +
            " chunks"
        );

        refreshDocumentList();

    } catch (error) {

        alert(
            "Upload failed: " +
            error.message
        );

    } finally {

        fileInput.value = "";

        uploadBtn.disabled = false;

        uploadBtn.textContent = "Upload PDF";
    }
}


// ============================================================
// GET DOCUMENTS
// ============================================================

async function refreshDocumentList() {

    try {

        const response = await fetch(
            API_URL + "/documents",
            {
                method: "GET",

                headers: getClientHeaders()
            }
        );

        const data = await response.json();

        documentList.innerHTML = "";

        if (data.count > 0) {

            data.documents.forEach(doc => {

                const div =
                    document.createElement("div");

                div.className =
                    "document-item";


                // --------------------------------------------
                // DOCUMENT INFO
                // --------------------------------------------

                const info =
                    document.createElement("div");

                info.className =
                    "doc-info";


                const name =
                    document.createElement("div");

                name.className =
                    "doc-name";

                name.textContent =
                    "📄 " + doc.filename;


                const chunks =
                    document.createElement("div");

                chunks.className =
                    "doc-chunks";

                chunks.textContent =
                    doc.chunks +
                    " chunks • " +
                    doc.stored +
                    " stored";


                info.appendChild(name);

                info.appendChild(chunks);

                div.appendChild(info);


                // --------------------------------------------
                // DELETE BUTTON
                // --------------------------------------------

                const btn =
                    document.createElement("button");

                btn.className =
                    "delete-doc";

                btn.textContent =
                    "Delete";


                btn.onclick = function() {

                    deleteDocument(
                        doc.doc_id
                    );

                };


                div.appendChild(btn);

                documentList.appendChild(div);

            });

        } else {

            documentList.innerHTML =
                '<p class="empty-state">' +
                'No documents uploaded yet' +
                '</p>';
        }

    } catch (error) {

        console.error(
            "Failed to load documents:",
            error
        );

    }
}


// ============================================================
// DELETE DOCUMENT
// ============================================================

async function deleteDocument(docId) {

    if (
        !confirm(
            "Delete this document?"
        )
    ) {
        return;
    }


    try {

        const response = await fetch(

            API_URL +
            "/documents/" +
            encodeURIComponent(docId),

            {
                method: "DELETE",

                headers: getClientHeaders()
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Delete failed"
            );
        }


        displayMessage(
            "Document deleted successfully",
            "bot"
        );


        refreshDocumentList();


    } catch (error) {

        displayMessage(
            "Delete error: " +
            error.message,
            "bot"
        );
    }
}


// ============================================================
// SEND CHAT MESSAGE
// ============================================================

async function sendMessage() {

    const question =
        questionInput.value.trim();


    if (!question) {
        return;
    }


    // Show user's question

    displayMessage(
        question,
        "user"
    );


    questionInput.value = "";


    sendBtn.disabled = true;

    sendBtn.textContent =
        "Thinking...";


    try {

        const response =
            await fetch(
                API_URL + "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "X-Client-ID":
                            clientId
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Chat request failed"
            );
        }


        // Display answer + sources

        displayMessage(
            data.answer,
            "bot",
            data.sources
        );


    } catch (error) {

        displayMessage(
            "Error: " +
            error.message,
            "bot"
        );

    } finally {

        sendBtn.disabled = false;

        sendBtn.textContent =
            "Send";

        questionInput.focus();
    }
}


// ============================================================
// DISPLAY MESSAGE
// ============================================================

function displayMessage(
    text,
    sender,
    sources = null
) {

    const div =
        document.createElement("div");


    div.className =
        "message " +
        sender +
        "-message";


    // --------------------------------------------
    // ANSWER TEXT
    // --------------------------------------------

    const answerDiv =
        document.createElement("div");


    answerDiv.textContent =
        text;


    div.appendChild(
        answerDiv
    );


    // --------------------------------------------
    // SOURCES
    // --------------------------------------------

    if (
        sender === "bot" &&
        sources &&
        sources.length > 0
    ) {

        const sourcesDiv =
            document.createElement("div");


        sourcesDiv.className =
            "message-sources";


        const sourceTitle =
            document.createElement("div");


        sourceTitle.style.fontWeight =
            "700";


        sourceTitle.style.marginBottom =
            "8px";


        sourceTitle.textContent =
            "📚 Relevant Documents";


        sourcesDiv.appendChild(
            sourceTitle
        );


        sources.forEach(source => {

            const sourceItem =
                document.createElement("div");


            sourceItem.className =
                "source-item";


            // ----------------------------------------
            // Create elements safely instead of
            // inserting raw HTML.
            // ----------------------------------------

            const filename =
                document.createElement("strong");

            filename.textContent =
                "📄 " +
                source.filename;


            const details =
                document.createElement("span");


            details.style.fontSize =
                "11px";


            details.style.opacity =
                "0.8";


            details.style.display =
                "block";


            details.textContent =
                "Chunk " +
                source.chunk_index +
                " • Similarity: " +
                (
                    source.similarity * 100
                ).toFixed(1) +
                "%";


            sourceItem.appendChild(
                filename
            );


            sourceItem.appendChild(
                details
            );


            sourcesDiv.appendChild(
                sourceItem
            );

        });


        div.appendChild(
            sourcesDiv
        );
    }


    // --------------------------------------------
    // ADD MESSAGE TO CHAT
    // --------------------------------------------

    messagesContainer.appendChild(
        div
    );


    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}


// ============================================================
// INITIAL LOAD
// ============================================================

refreshDocumentList();