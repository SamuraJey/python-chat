document.addEventListener('DOMContentLoaded', function() {
    // Загрузка обзорных данных
    fetch('/api/analytics/overview')
        .then(response => response.json())
        .then(data => {
            document.querySelector('#total-users .analytics-value').textContent = data.total_users;
            document.querySelector('#total-chats .analytics-value').textContent = data.total_chats;
            document.querySelector('#active-users .analytics-value').textContent = data.active_users;
            document.querySelector('#messages-today .analytics-value').textContent = data.messages_today;
        });
    
    // Загрузка данных для графика активности чатов
    fetch('/api/analytics/chat-activity')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('chatActivityChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Количество сообщений',
                        data: data.datasets[0].data,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true
                }
            });
        });
    
    // Загрузка данных для графика активности пользователей
    fetch('/api/analytics/user-activity')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('userActivityChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Количество сообщений',
                        data: data.datasets[0].data,
                        fill: false,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    responsive: true
                }
            });
        });
});