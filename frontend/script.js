/**
 * MoMo SMS Analytics Dashboard - Frontend JavaScript
 * Team Eight: James Giir Deng & Byusa M Martin De Poles
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const LEGACY_API_URL = 'http://localhost:8080';
const AUTH_HEADERS = {
    'Authorization': 'Basic ' + btoa('team5:ALU2025'),
    'Content-Type': 'application/json'
};

// Global variables
let currentPage = 1;
const pageSize = 20;
let allTransactions = [];
let filteredTransactions = [];
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check API status
    checkApiStatus();
    
    // Load dashboard data
    loadDashboardData();
    loadRecentTransactions();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize charts
    initializeCharts();
});

// Check API status
async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/system/health`);
        if (response.ok) {
            document.getElementById('apiStatus').className = 'badge bg-success';
            document.getElementById('apiStatus').textContent = 'Connected';
        } else {
            document.getElementById('apiStatus').className = 'badge bg-danger';
            document.getElementById('apiStatus').textContent = 'Disconnected';
        }
    } catch (error) {
        document.getElementById('apiStatus').className = 'badge bg-warning';
        document.getElementById('apiStatus').textContent = 'Error';
        console.error('API status check failed:', error);
    }
}

// Load dashboard statistics
async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats?days=30`, {
            headers: AUTH_HEADERS
        });
        
        if (!response.ok) throw new Error('Failed to fetch dashboard data');
        
        const data = await response.json();
        
        // Update statistics cards
        document.getElementById('totalTxns').textContent = data.total_transactions.toLocaleString();
        document.getElementById('totalAmount').textContent = formatCurrency(data.total_amount);
        document.getElementById('totalVolume').textContent = formatCurrency(data.total_amount);
        document.getElementById('avgTransaction').textContent = formatCurrency(data.average_transaction);
        document.getElementById('uniqueUsers').textContent = data.transaction_counts ? Object.keys(data.transaction_counts).length : 0;
        document.getElementById('daysCovered').textContent = data.daily_volume ? data.daily_volume.length : 0;
        
        // Update charts
        updateVolumeChart(data.daily_volume);
        updateTypeChart(data.transaction_counts);
        
        // Update sidebar stats
        updateSidebarStats(data);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data');
    }
}

// Load recent transactions
async function loadRecentTransactions() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    loadingSpinner.style.display = 'block';
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/transactions?skip=${(currentPage - 1) * pageSize}&limit=${pageSize}`,
            { headers: AUTH_HEADERS }
        );
        
        if (!response.ok) throw new Error('Failed to fetch transactions');
        
        const transactions = await response.json();
        allTransactions = [...allTransactions, ...transactions];
        filteredTransactions = [...allTransactions];
        
        renderTransactionsTable(transactions);
        updateTransactionCounts();
        
        // Hide load more button if no more transactions
        if (transactions.length < pageSize) {
            document.getElementById('loadMore').style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading transactions:', error);
        showError('Failed to load transactions');
    } finally {
        loadingSpinner.style.display = 'none';
    }
}

// Render transactions table
function renderTransactionsTable(transactions) {
    const tableBody = document.getElementById('transactionsTable');
    
    if (currentPage === 1) {
        tableBody.innerHTML = '';
    }
    
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.className = `transaction-row ${transaction.transaction_type}`;
        
        const date = new Date(transaction.date);
        const typeClass = transaction.transaction_type === 'received' ? 'amount-positive' : 'amount-negative';
        const typeIcon = transaction.transaction_type === 'received' ? 
            '<i class="bi bi-arrow-down-circle text-success"></i>' : 
            '<i class="bi bi-arrow-up-circle text-danger"></i>';
        
        row.innerHTML = `
            <td>${date.toLocaleDateString()} ${date.toLocaleTimeString()}</td>
            <td>
                <span class="badge ${getTypeBadgeClass(transaction.transaction_type)}">
                    ${typeIcon} ${transaction.transaction_type}
                </span>
            </td>
            <td>
                <strong>${transaction.sender_name || 'N/A'}</strong> 
                <i class="bi bi-arrow-right"></i> 
                <strong>${transaction.receiver_name || 'N/A'}</strong>
                <br>
                <small class="text-muted">${transaction.sender_phone || ''} → ${transaction.receiver_phone || ''}</small>
            </td>
            <td class="${typeClass}">${formatCurrency(transaction.amount)}</td>
            <td>${formatCurrency(transaction.balance_after)}</td>
            <td>
                <span class="badge bg-success">Completed</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-info me-1" onclick="viewTransactionDetails(${transaction.id})">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning" onclick="editTransaction(${transaction.id})">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Get badge class for transaction type
function getTypeBadgeClass(type) {
    const classes = {
        'received': 'bg-success',
        'sent': 'bg-danger',
        'deposit': 'bg-primary',
        'withdrawal': 'bg-warning',
        'payment': 'bg-info',
        'airtime': 'bg-secondary',
        'bill_payment': 'bg-dark',
        'cash_power': 'bg-purple'
    };
    return classes[type] || 'bg-secondary';
}

// Initialize charts
function initializeCharts() {
    // Volume chart
    const volumeCtx = document.getElementById('volumeChart').getContext('2d');
    charts.volumeChart = new Chart(volumeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Transaction Volume',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Volume: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
    
    // Type chart
    const typeCtx = document.getElementById('typeChart').getContext('2d');
    charts.typeChart = new Chart(typeCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#2ecc71', // received
                    '#e74c3c', // sent
                    '#3498db', // deposit
                    '#f39c12', // withdrawal
                    '#9b59b6', // payment
                    '#1abc9c', // airtime
                    '#34495e'  // bill_payment
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

// Update volume chart
function updateVolumeChart(dailyVolume) {
    if (!dailyVolume || !charts.volumeChart) return;
    
    const labels = dailyVolume.map(item => item.date);
    const data = dailyVolume.map(item => parseFloat(item.total) || 0);
    
    charts.volumeChart.data.labels = labels;
    charts.volumeChart.data.datasets[0].data = data;
    charts.volumeChart.update();
}

// Update type chart
function updateTypeChart(transactionCounts) {
    if (!transactionCounts || !charts.typeChart) return;
    
    const labels = Object.keys(transactionCounts);
    const data = Object.values(transactionCounts);
    
    charts.typeChart.data.labels = labels.map(label => 
        label.charAt(0).toUpperCase() + label.slice(1)
    );
    charts.typeChart.data.datasets[0].data = data;
    charts.typeChart.update();
}

// Update sidebar statistics
function updateSidebarStats(data) {
    document.getElementById('totalTxns').textContent = data.total_transactions.toLocaleString();
    document.getElementById('totalAmount').textContent = formatCurrency(data.total_amount);
}

// Update transaction counts
function updateTransactionCounts() {
    const receivedCount = allTransactions.filter(t => t.transaction_type === 'received').length;
    const sentCount = allTransactions.filter(t => t.transaction_type === 'sent').length;
    
    // You can update any UI elements with these counts if needed
    console.log(`Received: ${receivedCount}, Sent: ${sentCount}`);
}

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshData').addEventListener('click', function() {
        currentPage = 1;
        allTransactions = [];
        filteredTransactions = [];
        loadDashboardData();
        loadRecentTransactions();
        showToast('Data refreshed successfully!', 'success');
    });
    
    // Load more button
    document.getElementById('loadMore').addEventListener('click', function() {
        currentPage++;
        loadRecentTransactions();
    });
    
    // Apply filters
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    
    // Reset filters
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportTransactions);
    
    // Upload button
    document.getElementById('uploadBtn').addEventListener('click', uploadXMLFile);
    
    // Search input
    document.getElementById('searchInput').addEventListener('input', debounce(searchTransactions, 300));
}

// Apply filters
function applyFilters() {
    const typeFilter = document.getElementById('typeFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const minAmount = parseFloat(document.getElementById('minAmount').value) || 0;
    const maxAmount = parseFloat(document.getElementById('maxAmount').value) || Infinity;
    
    filteredTransactions = allTransactions.filter(transaction => {
        // Type filter
        if (typeFilter !== 'all' && transaction.transaction_type !== typeFilter) {
            return false;
        }
        
        // Date filter
        const transactionDate = new Date(transaction.date);
        if (startDate && transactionDate < new Date(startDate)) {
            return false;
        }
        if (endDate && transactionDate > new Date(endDate + 'T23:59:59')) {
            return false;
        }
        
        // Amount filter
        if (transaction.amount < minAmount || transaction.amount > maxAmount) {
            return false;
        }
        
        return true;
    });
    
    renderFilteredTransactions();
    showToast(`Filtered ${filteredTransactions.length} transactions`, 'info');
}

// Reset filters
function resetFilters() {
    document.getElementById('typeFilter').value = 'all';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('minAmount').value = '';
    document.getElementById('maxAmount').value = '';
    
    filteredTransactions = [...allTransactions];
    renderFilteredTransactions();
    showToast('Filters reset', 'info');
}

// Render filtered transactions
function renderFilteredTransactions() {
    const tableBody = document.getElementById('transactionsTable');
    tableBody.innerHTML = '';
    
    const visibleTransactions = filteredTransactions.slice(0, currentPage * pageSize);
    renderTransactionsTable(visibleTransactions);
}

// Search transactions
function searchTransactions() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (!searchTerm) {
        filteredTransactions = [...allTransactions];
        renderFilteredTransactions();
        return;
    }
    
    filteredTransactions = allTransactions.filter(transaction => {
        return (
            (transaction.sender_name && transaction.sender_name.toLowerCase().includes(searchTerm)) ||
            (transaction.receiver_name && transaction.receiver_name.toLowerCase().includes(searchTerm)) ||
            (transaction.transaction_id && transaction.transaction_id.toLowerCase().includes(searchTerm)) ||
            (transaction.body && transaction.body.toLowerCase().includes(searchTerm))
        );
    });
    
    renderFilteredTransactions();
    showToast(`Found ${filteredTransactions.length} results for "${searchTerm}"`, 'info');
}

// Export transactions
function exportTransactions() {
    try {
        const dataStr = JSON.stringify(filteredTransactions, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `momo-transactions-${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        showToast('Transactions exported successfully!', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showError('Failed to export transactions');
    }
}

// Upload XML file
async function uploadXMLFile() {
    const fileInput = document.getElementById('xmlFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressBar = document.getElementById('uploadProgress');
    const progressFill = progressBar.querySelector('.progress-bar');
    
    if (!fileInput.files.length) {
        showError('Please select a file to upload');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Show progress bar
    progressBar.style.display = 'block';
    uploadBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/parse/xml`, {
            method: 'POST',
            headers: {
                'Authorization': AUTH_HEADERS['Authorization']
            },
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            progressFill.style.width = `${progress}%`;
            
            if (progress >= 100) {
                clearInterval(interval);
                
                // Show success message
                document.getElementById('uploadSuccess').style.display = 'block';
                document.getElementById('uploadError').style.display = 'none';
                
                // Reset form
                fileInput.value = '';
                uploadBtn.disabled = false;
                progressBar.style.display = 'none';
                progressFill.style.width = '0%';
                
                // Refresh data after 3 seconds
                setTimeout(() => {
                    currentPage = 1;
                    allTransactions = [];
                    filteredTransactions = [];
                    loadDashboardData();
                    loadRecentTransactions();
                    document.getElementById('uploadSuccess').style.display = 'none';
                }, 3000);
            }
        }, 200);
        
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('errorMessage').textContent = error.message;
        document.getElementById('uploadError').style.display = 'block';
        document.getElementById('uploadSuccess').style.display = 'none';
        
        uploadBtn.disabled = false;
        progressBar.style.display = 'none';
        progressFill.style.width = '0%';
    }
}

// View transaction details
function viewTransactionDetails(transactionId) {
    // You can implement a modal or separate page for details
    alert(`Viewing transaction ${transactionId}. Implement details view here.`);
}

// Edit transaction
function editTransaction(transactionId) {
    // You can implement an edit form
    alert(`Editing transaction ${transactionId}. Implement edit functionality here.`);
}

// Utility functions
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-RW', {
        style: 'currency',
        currency: 'RWF',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showToast(message, type = 'info') {
    // You can implement a toast notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
}

function showError(message) {
    showToast(message, 'error');
    
    // You can implement a more prominent error display
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 end-0 m-3';
    errorDiv.style.zIndex = '9999';
    errorDiv.innerHTML = `
        <strong>Error!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

// Legacy API functions (for DSA testing)
async function testLinearSearch() {
    try {
        const response = await fetch(`${LEGACY_API_URL}/transactions`, {
            headers: AUTH_HEADERS
        });
        
        if (!response.ok) throw new Error('Legacy API failed');
        
        const data = await response.json();
        console.log('Linear search test:', data.length, 'transactions found');
        
        // Test dictionary lookup
        if (data.length > 0) {
            const firstId = data[0].id;
            const lookupResponse = await fetch(`${LEGACY_API_URL}/transactions/${firstId}`, {
                headers: AUTH_HEADERS
            });
            
            if (lookupResponse.ok) {
                console.log('Dictionary lookup successful');
            }
        }
        
    } catch (error) {
        console.error('Legacy API test failed:', error);
    }
}

// Run legacy API test on startup (optional)
// setTimeout(testLinearSearch, 2000);

// Make functions available globally for HTML onclick handlers
window.viewTransactionDetails = viewTransactionDetails;
window.editTransaction = editTransaction;