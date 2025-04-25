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
const bannedUsersTab = document.createElement('div');
const bannedUsersList = document.createElement('div');
let isModerator = false; // Will be set when loading members

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

// Handle errors, including ban notifications
socket.on("error", (data) => {
    console.error("Socket error:", data);
    if (data.message === "You are banned from this chat") {
        chatMessages.innerHTML = '';
        const banMessage = document.createElement('div');
        banMessage.className = 'ban-message';
        banMessage.innerHTML = `
            <div class="ban-icon">⛔</div>
            <h2>You have been banned from this chat</h2>
            <p>You can no longer send or receive messages in this chat.</p>
        `;
        chatMessages.appendChild(banMessage);
        
        // Disable message input
        messageInput.disabled = true;
        sendButton.disabled = true;
        messageInput.placeholder = "You cannot send messages in this chat";
    }
});

socket.on("banned_from_chat", (data) => {
    console.log("Banned from chat:", data);
    if (parseInt(data.chat_id) === chatId) {
        chatMessages.innerHTML = '';
        const banMessage = document.createElement('div');
        banMessage.className = 'ban-message';
        banMessage.innerHTML = `
            <div class="ban-icon">⛔</div>
            <h2>You have been banned from ${data.chat_name}</h2>
            <p>A moderator has banned you from this chat.</p>
            <p>You can no longer send or receive messages in this chat.</p>
        `;
        chatMessages.appendChild(banMessage);
        
        // Disable message input
        messageInput.disabled = true;
        sendButton.disabled = true;
        messageInput.placeholder = "You cannot send messages in this chat";
    }
});


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

socket.on("set_username", (data) => {
    if (data.username) {
        currentUsername = data.username;
    }
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

// Setup tabs for members panel
function setupMembersPanel() {
    // Проверяем, была ли уже создана структура вкладок
    if (membersPanel.querySelector('.tabs-container')) {
        return; // Если структура уже существует, не создаем ее повторно
    }
    
    // Сохраняем ссылку на оригинальный список участников
    const originalMembersList = membersList.cloneNode(true);
    
    // Create tab headers
    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'tabs-container';
    
    const membersTab = document.createElement('div');
    membersTab.className = 'tab active';
    membersTab.textContent = 'Members';
    
    bannedUsersTab.className = 'tab';
    bannedUsersTab.textContent = 'Banned Users';
    bannedUsersTab.style.display = 'none'; // Hide by default, only show for moderators
    
    tabsContainer.appendChild(membersTab);
    tabsContainer.appendChild(bannedUsersTab);
    
    // Create content containers
    const tabContents = document.createElement('div');
    tabContents.className = 'tab-contents';
    
    const membersContent = document.createElement('div');
    membersContent.className = 'tab-content active';
    membersContent.id = 'members-list-container';
    membersContent.appendChild(originalMembersList);
    
    bannedUsersList.className = 'tab-content';
    bannedUsersList.id = 'banned-users-list';
    
    tabContents.appendChild(membersContent);
    tabContents.appendChild(bannedUsersList);
    
    // Очищаем текущее содержимое панели
    while (membersPanel.firstChild) {
        membersPanel.removeChild(membersPanel.firstChild);
    }
    
    // Создаем заново заголовок
    const header = document.createElement('div');
    header.className = 'chat-members-header';
    
    const headerTitle = document.createElement('h3');
    headerTitle.textContent = 'Chat Members';
    
    const closeButton = document.createElement('button');
    closeButton.id = 'close-members-panel';
    closeButton.textContent = '×';
    closeButton.addEventListener('click', () => {
        membersPanel.classList.remove('active');
    });
    
    header.appendChild(headerTitle);
    header.appendChild(closeButton);
    
    // Добавляем элементы в панель
    membersPanel.appendChild(header);
    membersPanel.appendChild(tabsContainer);
    membersPanel.appendChild(tabContents);
    
    // Add event listeners for tabs
    membersTab.addEventListener('click', () => {
        membersTab.classList.add('active');
        bannedUsersTab.classList.remove('active');
        membersContent.classList.add('active');
        bannedUsersList.classList.remove('active');
    });
    
    bannedUsersTab.addEventListener('click', () => {
        bannedUsersTab.classList.add('active');
        membersTab.classList.remove('active');
        bannedUsersList.classList.add('active');
        membersContent.classList.remove('active');
        if (isModerator) {
            loadBannedUsers();
        }
    });
}

// Функция для загрузки участников чата
function loadChatMembers() {
    // После перестройки DOM нужно заново найти элемент списка участников
    const currentMembersList = document.getElementById('members-list');
    
    if (!currentMembersList) {
        console.error('Members list element not found');
        return;
    }
    
    currentMembersList.innerHTML = '<div class="loading-spinner">Loading members...</div>';
    
    fetch(`/api/chat/${chatId}/members`)
        .then(response => response.json())
        .then(data => {
            currentMembersList.innerHTML = '';
            
            if (data.error) {
                currentMembersList.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }
            
            if (data.members && data.members.length > 0) {
                // Check if current user is a moderator
                const currentUser = data.members.find(member => member.username === currentUsername);
                isModerator = currentUser && currentUser.is_moderator;
                
                // Show banned users tab if user is moderator
                if (isModerator) {
                    const tabsContainer = membersPanel.querySelector('.tabs-container');
                    if (tabsContainer && bannedUsersTab) {
                        bannedUsersTab.style.display = 'block';
                    }
                }
                
                data.members.forEach(member => {
                    const memberDiv = document.createElement('div');
                    memberDiv.className = 'chat-member';
                    memberDiv.dataset.userId = member.id;
                    
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
                    
                    // Add ban button if current user is moderator and target is not
                    if (isModerator && !member.is_moderator && member.username !== currentUsername) {
                        const banButton = document.createElement('button');
                        banButton.className = 'action-button ban-button';
                        banButton.textContent = 'Ban';
                        banButton.onclick = () => banUser(member.id, member.username);
                        memberDiv.appendChild(banButton);
                    }
                    
                    currentMembersList.appendChild(memberDiv);
                });
            } else {
                currentMembersList.innerHTML = '<div>No members found</div>';
            }
        })
        .catch(error => {
            console.error('Error loading chat members:', error);
            currentMembersList.innerHTML = '<div class="error-message">Failed to load members</div>';
        });
}

// Load banned users
function loadBannedUsers() {
    bannedUsersList.innerHTML = '<div class="loading-spinner">Loading banned users...</div>';
    
    fetch(`/api/chat/${chatId}/banned`)
        .then(response => response.json())
        .then(data => {
            bannedUsersList.innerHTML = '';
            
            if (data.error) {
                bannedUsersList.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }
            
            if (data.banned_users && data.banned_users.length > 0) {
                data.banned_users.forEach(user => {
                    const userDiv = document.createElement('div');
                    userDiv.className = 'banned-user';
                    
                    const usernameDiv = document.createElement('div');
                    usernameDiv.className = 'banned-username';
                    usernameDiv.textContent = user.username;
                    
                    const bannedInfo = document.createElement('div');
                    bannedInfo.className = 'banned-info';
                    
                    // Format the date
                    const banDate = user.banned_at ? new Date(user.banned_at) : null;
                    const formattedDate = banDate ? banDate.toLocaleDateString() + ' ' + banDate.toLocaleTimeString() : 'Unknown';
                    
                    bannedInfo.innerHTML = `
                        <div>Banned on: ${formattedDate}</div>
                        <div>Reason: ${user.reason || 'No reason provided'}</div>
                    `;
                    
                    const unbanButton = document.createElement('button');
                    unbanButton.className = 'action-button unban-button';
                    unbanButton.textContent = 'Unban';
                    unbanButton.onclick = () => unbanUser(user.id, user.username);
                    
                    userDiv.appendChild(usernameDiv);
                    userDiv.appendChild(bannedInfo);
                    userDiv.appendChild(unbanButton);
                    
                    bannedUsersList.appendChild(userDiv);
                });
            } else {
                bannedUsersList.innerHTML = '<div class="no-banned-users">No banned users</div>';
            }
        })
        .catch(error => {
            console.error('Error loading banned users:', error);
            bannedUsersList.innerHTML = '<div class="error-message">Failed to load banned users</div>';
        });
}

// Ban a user
function banUser(userId, username) {
    if (!confirm(`Are you sure you want to ban ${username} from this chat?`)) {
        return;
    }
    
    const reason = prompt(`Please provide a reason for banning ${username}:`);
    
    fetch(`/api/chat/${chatId}/ban`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            user_id: userId, 
            reason: reason || 'No reason provided' 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add system message
            addMessage(`${username} has been banned from the chat`, "system");
            
            // Refresh member list and banned list
            loadChatMembers();
            if (isModerator) {
                loadBannedUsers();
            }
        } else {
            alert(`Failed to ban user: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error banning user:', error);
        alert('Failed to ban user due to a network error');
    });
}

// Unban a user
function unbanUser(userId, username) {
    if (!confirm(`Are you sure you want to unban ${username}?`)) {
        return;
    }
    
    fetch(`/api/chat/${chatId}/unban`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add system message
            addMessage(`${username} has been unbanned from the chat`, "system");
            
            // Refresh banned list
            loadBannedUsers();
        } else {
            alert(`Failed to unban user: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error unbanning user:', error);
        alert('Failed to unban user due to a network error');
    });
}

// Управление панелью участников
toggleUsersButton.addEventListener('click', (e) => {
    e.stopPropagation(); // Предотвращаем всплытие события
    membersPanel.classList.toggle('active');
    if (membersPanel.classList.contains('active')) {
        setupMembersPanel(); // Initialize panel structure
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

// После других обработчиков событий socket.on
socket.on("user_banned", (data) => {
    // Добавляем системное сообщение о бане пользователя
    addMessage(`${data.username} has been banned from the chat by ${data.banned_by}`, "system");
    
    // Обновляем список участников, если панель открыта
    if (membersPanel.classList.contains('active')) {
        loadChatMembers();
    }
});