const socket = io();
const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const currentUsernameSpan = document.getElementById("current-username");
const usernameInput = document.getElementById("username-input");
const updateUsernameButton = document.getElementById("update-username-button");

const pathParts = window.location.pathname.split('/');
console.log(pathParts);
const chatId = parseInt(pathParts[pathParts.length - 1], 10); // Ensure it's a number
console.log(chatId);
function loadPreviousMessages(chatId) {
    fetch(`/api/messages/${chatId}`)
        .then(response => response.json())
        .then(data => {
            data.messages.forEach(msg => {
                addMessage(msg.content, "user", msg.username);
            });
        })
        .catch(error => console.error('Error loading messages:', error));
}


let currentUsername = "";
const displayedMessages = new Set();

let connectionEstablished = false;

socket.on('connect', function () {
    console.log('Socket connected successfully');
    connectionEstablished = true;
    joinChatRoom();
});

function joinChatRoom() {
    console.log('Joining chat room:', chatId);
    // Join needs to happen before any messages can be received
    socket.emit('join', { chat_id: chatId });

    // Add this debug line to confirm joining worked
    socket.on('joined_chat', (data) => {
        console.log('Successfully joined chat room:', data.chat_id);
        loadPreviousMessages(chatId);
    });
}


socket.on("user_joined", (data) => {
    addMessage(`${data.username} joined the chat`, "system");
});

socket.on("user_left", (data) => {
    addMessage(`${data.username} left the chat`, "system");
});

socket.on("receive_message", (data) => {
    console.log("Received message:", data);

    // Create a unique identifier for this message
    const messageId = data.message_id || `${data.timestamp}-${data.username}-${data.message.substring(0, 10)}`;

    // Check if we've already displayed this message
    if (!displayedMessages.has(messageId)) {
        displayedMessages.add(messageId);
        addMessage(data.message, "user", data.username);
    } else {
        console.log("Skipping duplicate message:", messageId);
    }
});

socket.on("username_updated", (data) => {
    addMessage(`${data.old_username} changed their name to ${data.new_username}`, "system");
    if (data.old_username === currentUsername) {
        currentUsername = data.new_username;
        currentUsernameSpan.textContent = `Your username: ${currentUsername}`;
    }
});

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});



function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        socket.emit("send_message", { message: message, chat_id: chatId });
        messageInput.value = "";
    }
}

function updateUsername() {
    const newUsername = usernameInput.value.trim();
    if (newUsername && newUsername !== currentUsername) {
        socket.emit("update_username", { username: newUsername });
        usernameInput.value = "";
    }
}

function addMessage(message, type, username = "",) {
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    if (type === "user") {
        const isSentMessage = username === currentUsername;
        if (isSentMessage) {
            messageElement.classList.add("sent");
        }

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";

        const usernameDiv = document.createElement("div");
        usernameDiv.className = "message-username";
        usernameDiv.textContent = username;
        contentDiv.appendChild(usernameDiv);

        const messageText = document.createElement("div");
        messageText.textContent = message;
        contentDiv.appendChild(messageText);

        messageElement.appendChild(contentDiv);
    } else {
        messageElement.className = "system-message";
        messageElement.textContent = message;
    }
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}