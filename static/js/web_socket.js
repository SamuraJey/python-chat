const socket = io();
const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const currentUsernameSpan = document.getElementById("current-username");
const usernameInput = document.getElementById("username-input");
const updateUsernameButton = document.getElementById("update-username-button");
const toggleUsersButton = document.getElementById('toggle-users');
const membersPanel = document.getElementById('members-panel');
const closeMembersPanel = document.getElementById('close-members-panel');
const membersList = document.getElementById('members-list');

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

// Update your addMessage function to match our new styling
function addMessage(message, type, username = "") {
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
        messageText.className = "message-text";
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

// Функция для загрузки участников чата
function loadChatMembers() {
    membersList.innerHTML = '<div class="loading-spinner">Loading members...</div>';
    
    fetch(`/api/chat/${chatId}/members`)
        .then(response => response.json())
        .then(data => {
            membersList.innerHTML = '';
            
            if (data.error) {
                membersList.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }
            
            if (data.members && data.members.length > 0) {
                data.members.forEach(member => {
                    const memberDiv = document.createElement('div');
                    memberDiv.className = 'chat-member';
                    
                    const usernameSpan = document.createElement('span');
                    usernameSpan.className = 'username';
                    usernameSpan.textContent = member.username;
                    
                    memberDiv.appendChild(usernameSpan);
                    
                    if (member.is_moderator) {
                        const moderatorBadge = document.createElement('span');
                        moderatorBadge.className = 'badge moderator';
                        moderatorBadge.textContent = 'Moderator';
                        memberDiv.appendChild(moderatorBadge);
                    }
                    
                    membersList.appendChild(memberDiv);
                });
            } else {
                membersList.innerHTML = '<div>No members found</div>';
            }
        })
        .catch(error => {
            console.error('Error loading chat members:', error);
            membersList.innerHTML = '<div class="error-message">Failed to load members</div>';
        });
}

// Управление панелью участников
toggleUsersButton.addEventListener('click', (e) => {
    e.stopPropagation(); // Предотвращаем всплытие события
    membersPanel.classList.toggle('active');
    if (membersPanel.classList.contains('active')) {
        loadChatMembers();
    }
});

closeMembersPanel.addEventListener('click', () => {
    membersPanel.classList.remove('active');
});

// Добавляем обработчик клика на документ для закрытия панели при клике вне её
document.addEventListener('click', (e) => {
    // Проверяем, активна ли панель и был ли клик вне панели и вне кнопки переключения
    if (
        membersPanel.classList.contains('active') && 
        !membersPanel.contains(e.target) && 
        e.target !== toggleUsersButton &&
        !toggleUsersButton.contains(e.target)
    ) {
        membersPanel.classList.remove('active');
    }
});

// Предотвращаем закрытие панели при клике внутри неё
membersPanel.addEventListener('click', (e) => {
    e.stopPropagation();
});