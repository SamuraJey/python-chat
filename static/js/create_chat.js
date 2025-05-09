document.addEventListener('DOMContentLoaded', function () {
    // Элементы модального окна
    const modal = document.getElementById('create-chat-modal');
    const createChatBtn = document.getElementById('create-chat-btn');
    const createFirstChatBtn = document.getElementById('create-first-chat-btn');
    const closeBtn = modal.querySelector('.close');
    const privateChatBtn = document.getElementById('private-chat-btn');
    const groupChatBtn = document.getElementById('group-chat-btn');
    const userSearchInput = document.getElementById('user-search');
    const searchResults = document.getElementById('search-results');
    const selectedUsersContainer = document.getElementById('selected-users-container');
    const chatNameInput = document.getElementById('chat-name');
    const createChatSubmit = document.getElementById('create-chat-submit');

    // Состояние
    let isGroupChat = false;
    let selectedUsers = [];
    let searchTimeout = null;

    // Открытие модального окна
    function openModal() {
        modal.style.display = 'block';
        resetModal();
    }

    // Закрытие модального окна
    function closeModal() {
        modal.style.display = 'none';
        resetModal();
    }

    // Сброс состояния модального окна
    function resetModal() {
        isGroupChat = false;
        selectedUsers = [];
        userSearchInput.value = '';
        chatNameInput.value = '';
        searchResults.innerHTML = '';
        searchResults.classList.remove('active');
        selectedUsersContainer.innerHTML = '';
        privateChatBtn.classList.add('active');
        groupChatBtn.classList.remove('active');
    }

    // Переключение типа чата
    function toggleChatType(isGroup) {
        isGroupChat = isGroup;
        if (isGroup) {
            privateChatBtn.classList.remove('active');
            groupChatBtn.classList.add('active');
        } else {
            privateChatBtn.classList.add('active');
            groupChatBtn.classList.remove('active');
            // Если это личный чат, оставляем только одного выбранного пользователя
            if (selectedUsers.length > 1) {
                selectedUsers = [selectedUsers[0]];
                renderSelectedUsers();
            }
        }
    }

    // Поиск пользователей
    function searchUsers(query) {
        if (query.length < 2) {
            searchResults.innerHTML = '';
            searchResults.classList.remove('active');
            return;
        }

        fetch(`/api/search-users?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                searchResults.innerHTML = '';

                if (data.users && data.users.length > 0) {
                    data.users.forEach(user => {
                        // Пропускаем уже выбранных пользователей
                        if (selectedUsers.some(selectedUser => selectedUser.id === user.id)) {
                            return;
                        }

                        const searchItem = document.createElement('div');
                        searchItem.classList.add('search-item');
                        searchItem.textContent = user.username;
                        searchItem.addEventListener('click', () => addUserToSelection(user));
                        searchResults.appendChild(searchItem);
                    });

                    searchResults.classList.add('active');
                } else {
                    searchResults.innerHTML = '<div class="search-item">Пользователи не найдены</div>';
                    searchResults.classList.add('active');
                }
            })
            .catch(error => {
                console.error('Ошибка при поиске пользователей:', error);
            });
    }

    // Добавление пользователя в выбранные
    function addUserToSelection(user) {
        // Если это не групповой чат и уже есть выбранный пользователь, заменяем его
        if (!isGroupChat && selectedUsers.length > 0) {
            selectedUsers = [user];
        } else {
            selectedUsers.push(user);
        }

        renderSelectedUsers();
        userSearchInput.value = '';
        searchResults.innerHTML = '';
        searchResults.classList.remove('active');

        // Автоматически устанавливаем имя чата для личного чата
        if (!isGroupChat) {
            chatNameInput.value = user.username;
        }
    }

    // Удаление пользователя из выбранных
    function removeUserFromSelection(userId) {
        selectedUsers = selectedUsers.filter(user => user.id !== userId);
        renderSelectedUsers();
    }

    // Отображение выбранных пользователей
    function renderSelectedUsers() {
        selectedUsersContainer.innerHTML = '';

        selectedUsers.forEach(user => {
            const userTag = document.createElement('div');
            userTag.classList.add('selected-user-tag');
            userTag.innerHTML = `
                ${user.username}
                <span class="remove-user" data-user-id="${user.id}">&times;</span>
            `;
            selectedUsersContainer.appendChild(userTag);
        });

        // Добавляем обработчики для удаления пользователей
        document.querySelectorAll('.remove-user').forEach(removeBtn => {
            removeBtn.addEventListener('click', function () {
                const userId = parseInt(this.getAttribute('data-user-id'));
                removeUserFromSelection(userId);
            });
        });
    }

    // Создание нового чата
    function createNewChat() {
        // Валидация
        if (selectedUsers.length === 0) {
            alert('Выберите хотя бы одного пользователя');
            return;
        }

        if (!chatNameInput.value.trim()) {
            alert('Введите название чата');
            return;
        }

        const chatData = {
            name: chatNameInput.value.trim(),
            is_group: isGroupChat,
            user_ids: selectedUsers.map(user => user.id)
        };

        fetch('/api/chats/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(chatData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Перенаправляем на страницу нового чата
                    window.location.href = `/chat/${data.chat.id}`;
                } else {
                    alert(data.error || 'Ошибка при создании чата');
                }
            })
            .catch(error => {
                console.error('Ошибка при создании чата:', error);
                alert('Произошла ошибка при создании чата');
            });
    }

    // Обработчики событий
    if (createChatBtn) {
        createChatBtn.addEventListener('click', openModal);
    }

    if (createFirstChatBtn) {
        createFirstChatBtn.addEventListener('click', openModal);
    }

    closeBtn.addEventListener('click', closeModal);

    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    privateChatBtn.addEventListener('click', () => toggleChatType(false));
    groupChatBtn.addEventListener('click', () => toggleChatType(true));

    userSearchInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchUsers(this.value);
        }, 300);
    });

    createChatSubmit.addEventListener('click', createNewChat);
});
