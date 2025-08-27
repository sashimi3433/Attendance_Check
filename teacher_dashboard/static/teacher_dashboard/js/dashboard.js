// 講師ダッシュボード JavaScript

// DOM読み込み完了時の初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// ダッシュボード初期化
function initializeDashboard() {
    initializeSidebar();
    initializeAutoRefresh();
    initializeFilters();
    initializeCharts();
    initializeTableSorting();
    initializeSearchFunctionality();
    initializeNotifications();
}

// サイドバー制御
function initializeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            if (overlay) {
                overlay.classList.toggle('active');
            }
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
    
    // 現在のページをアクティブにする
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// 自動更新機能
function initializeAutoRefresh() {
    const autoRefreshCheckbox = document.querySelector('#auto-refresh');
    const refreshInterval = 10 * 60 * 1000; // 10分
    let refreshTimer;
    
    function startAutoRefresh() {
        refreshTimer = setInterval(() => {
            refreshDashboardData();
        }, refreshInterval);
    }
    
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
    }
    
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
                showNotification('自動更新が有効になりました', 'success');
            } else {
                stopAutoRefresh();
                showNotification('自動更新が無効になりました', 'info');
            }
        });
        
        // 初期状態で自動更新を開始
        if (autoRefreshCheckbox.checked) {
            startAutoRefresh();
        }
    }
}

// ダッシュボードデータ更新
function refreshDashboardData() {
    const currentPage = document.body.dataset.page;
    
    switch (currentPage) {
        case 'dashboard-home':
            refreshHomeData();
            break;
        case 'attendance-history':
            refreshAttendanceData();
            break;
        case 'statistics':
            refreshStatisticsData();
            break;
    }
}

// ホームページデータ更新
function refreshHomeData() {
    fetch('/teacher-dashboard/api/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            updateStatCards(data.stats);
            updateRecentAttendance(data.recent_attendance);
        })
        .catch(error => {
            console.error('データ更新エラー:', error);
            showNotification('データの更新に失敗しました', 'error');
        });
}

// 最近の出席記録更新
function updateRecentAttendance(recentAttendance) {
    const tableBody = document.querySelector('.recent-attendance tbody');
    if (!tableBody) return;
    
    // テーブルの内容をクリア
    tableBody.innerHTML = '';
    
    if (recentAttendance.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="4" style="text-align: center; color: var(--text-secondary); padding: 20px;">
                <i class="fas fa-info-circle" style="margin-right: 8px;"></i>
                最近の出席記録がありません
            </td>
        `;
        tableBody.appendChild(row);
        return;
    }
    
    // 新しいデータでテーブルを更新
    recentAttendance.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.timestamp}</td>
            <td>${record.user_name}</td>
            <td>${record.kiosk_name}</td>
            <td>
                <span class="badge badge-success">
                    <i class="fas fa-check"></i>
                    出席
                </span>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// 統計カード更新
function updateStatCards(stats) {
    const statElements = {
        'today-attendance': stats.today_attendance,
        'total-kiosks': stats.total_kiosks,
        'active-tokens': stats.active_tokens,
        'weekly-attendance': stats.weekly_attendance
    };
    
    Object.entries(statElements).forEach(([id, value]) => {
        const element = document.querySelector(`#${id} .stat-value`);
        if (element) {
            animateNumber(element, parseInt(element.textContent), value);
        }
    });
}

// 数値アニメーション
function animateNumber(element, start, end) {
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// フィルター機能
function initializeFilters() {
    const filterForm = document.querySelector('.filters form');
    const resetBtn = document.querySelector('.filter-reset');
    
    if (filterForm) {
        // フィルター変更時の自動送信
        const filterInputs = filterForm.querySelectorAll('select, input[type="date"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                filterForm.submit();
            });
        });
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const form = this.closest('form');
            form.reset();
            form.submit();
        });
    }
}

// チャート初期化
function initializeCharts() {
    // Chart.jsが読み込まれている場合のみ実行
    if (typeof Chart !== 'undefined') {
        initializeDailyChart();
        initializeHourlyChart();
        initializeKioskChart();
    }
}

// 日別出席チャート
function initializeDailyChart() {
    const canvas = document.getElementById('dailyChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const data = JSON.parse(canvas.dataset.chartData || '{}');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: '出席者数',
                data: data.values || [],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// 時間帯別チャート
function initializeHourlyChart() {
    const canvas = document.getElementById('hourlyChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const data = JSON.parse(canvas.dataset.chartData || '{}');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: '出席者数',
                data: data.values || [],
                backgroundColor: '#16a34a',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// キオスク別チャート
function initializeKioskChart() {
    const canvas = document.getElementById('kioskChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const data = JSON.parse(canvas.dataset.chartData || '{}');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: [
                    '#2563eb',
                    '#16a34a',
                    '#d97706',
                    '#9333ea',
                    '#dc2626'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// テーブルソート機能
function initializeTableSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const column = this.dataset.column;
            const currentSort = this.dataset.sort || 'asc';
            const newSort = currentSort === 'asc' ? 'desc' : 'asc';
            
            // ソート状態をリセット
            sortableHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                h.dataset.sort = '';
            });
            
            // 新しいソート状態を設定
            this.dataset.sort = newSort;
            this.classList.add(`sort-${newSort}`);
            
            // テーブルをソート
            sortTable(table, column, newSort);
        });
    });
}

// テーブルソート実行
function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.querySelector(`[data-column="${column}"]`)?.textContent.trim() || '';
        const bValue = b.querySelector(`[data-column="${column}"]`)?.textContent.trim() || '';
        
        // 数値の場合
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return direction === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        // 文字列の場合
        return direction === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // ソート結果を反映
    rows.forEach(row => tbody.appendChild(row));
}

// 検索機能
function initializeSearchFunctionality() {
    const searchInput = document.querySelector('#search-input');
    const searchBtn = document.querySelector('#search-btn');
    const clearBtn = document.querySelector('#clear-search');
    
    if (searchInput) {
        // リアルタイム検索
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
        
        // Enterキーで検索
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(this.value);
            }
        });
    }
    
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const query = searchInput.value;
            performSearch(query);
        });
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            searchInput.value = '';
            performSearch('');
        });
    }
}

// 検索実行
function performSearch(query) {
    const table = document.querySelector('.data-table tbody');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const matches = text.includes(query.toLowerCase());
        row.style.display = matches ? '' : 'none';
    });
    
    // 検索結果数を表示
    const visibleRows = table.querySelectorAll('tr:not([style*="display: none"])');
    const resultCount = document.querySelector('.search-results');
    if (resultCount) {
        resultCount.textContent = `${visibleRows.length}件の結果`;
    }
}

// 通知システム
function initializeNotifications() {
    // 通知コンテナを作成
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
}

// 通知表示
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = `
        margin-bottom: 10px;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease;
        cursor: pointer;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>${message}</span>
            <button style="background: none; border: none; font-size: 18px; cursor: pointer; margin-left: 10px;">&times;</button>
        </div>
    `;
    
    // 閉じるボタンのイベント
    notification.querySelector('button').addEventListener('click', () => {
        removeNotification(notification);
    });
    
    // クリックで閉じる
    notification.addEventListener('click', () => {
        removeNotification(notification);
    });
    
    container.appendChild(notification);
    
    // 自動削除
    if (duration > 0) {
        setTimeout(() => {
            removeNotification(notification);
        }, duration);
    }
}

// 通知削除
function removeNotification(notification) {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// CSS アニメーション追加
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .sortable {
        cursor: pointer;
        user-select: none;
        position: relative;
    }
    
    .sortable:hover {
        background-color: #f3f4f6;
    }
    
    .sortable::after {
        content: '↕';
        position: absolute;
        right: 8px;
        opacity: 0.5;
    }
    
    .sortable.sort-asc::after {
        content: '↑';
        opacity: 1;
    }
    
    .sortable.sort-desc::after {
        content: '↓';
        opacity: 1;
    }
`;
document.head.appendChild(style);

// CSV出力機能
function exportToCSV(url, filename) {
    showNotification('CSV出力を開始しています...', 'info');
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('出力に失敗しました');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showNotification('CSV出力が完了しました', 'success');
        })
        .catch(error => {
            console.error('CSV出力エラー:', error);
            showNotification('CSV出力に失敗しました', 'error');
        });
}

// ページ固有の初期化
function initializePageSpecific() {
    const page = document.body.dataset.page;
    
    switch (page) {
        case 'dashboard-home':
            initializeHomePage();
            break;
        case 'kiosk-management':
            initializeKioskManagement();
            break;
        case 'attendance-history':
            initializeAttendanceHistory();
            break;
        case 'statistics':
            initializeStatistics();
            break;
        case 'settings':
            initializeSettings();
            break;
    }
}

// ホームページ固有の初期化
function initializeHomePage() {
    // クイックアクションボタン
    const quickActions = document.querySelectorAll('.quick-action');
    quickActions.forEach(action => {
        action.addEventListener('click', function() {
            const actionType = this.dataset.action;
            handleQuickAction(actionType);
        });
    });
}

// クイックアクション処理
function handleQuickAction(actionType) {
    switch (actionType) {
        case 'export-today':
            const today = new Date().toISOString().split('T')[0];
            exportToCSV(`/teacher-dashboard/attendance/export/?date=${today}`, `attendance_${today}.csv`);
            break;
        case 'refresh-data':
            refreshDashboardData();
            showNotification('データを更新しました', 'success');
            break;
    }
}

// 設定ページ固有の初期化
function initializeSettings() {
    const settingsForm = document.querySelector('#settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings(this);
        });
    }
    
    // パスワード変更フォーム
    const passwordForm = document.querySelector('#password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            changePassword(this);
        });
    }
}

// 設定保存
function saveSettings(form) {
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('設定を保存しました', 'success');
        } else {
            showNotification('設定の保存に失敗しました', 'error');
        }
    })
    .catch(error => {
        console.error('設定保存エラー:', error);
        showNotification('設定の保存に失敗しました', 'error');
    });
}

// ページ読み込み完了後に実行
document.addEventListener('DOMContentLoaded', function() {
    initializePageSpecific();
});

// グローバル関数として公開
window.showNotification = showNotification;
window.exportToCSV = exportToCSV;
window.refreshDashboardData = refreshDashboardData;