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
  
//   // Call this after connection is established
//   socket.on('connect', function() {
//     console.log('Joining chat room:', chatId);
//     socket.emit('join', { chat_id: chatId });
//     loadPreviousMessages(chatId);
//   });

let currentUsername = "";

let connectionEstablished = false;

socket.on('connect', function() {
    console.log('Socket connected successfully');
    connectionEstablished = true;
    joinChatRoom();
});

function joinChatRoom() {
    console.log('Joining chat room:', chatId);
    socket.emit('join', { chat_id: chatId });
    
    // Wait a short time to ensure the join happens before loading messages
    setTimeout(() => {
        loadPreviousMessages(chatId);
    }, 300);
}

// Make sure messages are displayed correctly
function addMessage(message, type, username = "", avatar = "") {
    console.log(`Adding message: "${message}" from ${username}, type: ${type}`);
    
    // Create message element
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

// socket.on("set_username", (data) => {
//     currentUsername = data.username;
//     currentUsernameSpan.textContent = `Your username: ${currentUsername}`;
// });

socket.on("user_joined", (data) => {
    addMessage(`${data.username} joined the chat`, "system");
});

socket.on("user_left", (data) => {
    addMessage(`${data.username} left the chat`, "system");
});

socket.on("receive_message", (data) => {
    addMessage(data.message, "user", data.username, data.avatar);
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

updateUsernameButton.addEventListener("click", updateUsername);

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

function addMessage(message, type, username = "", avatar = "") {
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