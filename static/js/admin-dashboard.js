/* AgroConnect Admin Panel Javascript actions */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Sidebar Toggle Drawer
    const sidebarToggle = document.getElementById('sidebarToggle');
    const adminSidebar = document.querySelector('.admin-sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    
    if (sidebarToggle && adminSidebar && sidebarOverlay) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            adminSidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
        });
        
        sidebarOverlay.addEventListener('click', function() {
            adminSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    // 2. Alert Dismiss Auto-fade timers
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 3. Confirm prompts on critical POST deletions or status updates
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const msg = btn.getAttribute('data-confirm') || "Are you sure you want to perform this action?";
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // 4. File uploads image previews
    const imageInputs = document.querySelectorAll('.image-preview-trigger');
    imageInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const targetId = input.getAttribute('data-preview-target');
            const targetImg = document.getElementById(targetId);
            if (targetImg && input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    targetImg.src = e.target.result;
                    targetImg.classList.remove('d-none');
                };
                reader.readAsDataURL(input.files[0]);
            }
        });
    });
});

// Helper: Setup Sales Line Chart
function initSalesChart(canvasId, labels, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Sales (GHS)',
                data: values,
                backgroundColor: 'rgba(25, 135, 84, 0.05)',
                borderColor: '#198754',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#198754',
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f3f4f6' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Helper: Setup Orders Doughnut Chart
function initOrdersChart(canvasId, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Delivered', 'Processing', 'Pending', 'Cancelled'],
            datasets: [{
                data: values,
                backgroundColor: ['#10b981', '#0d6efd', '#f59e0b', '#dc3545'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            cutout: '70%'
        }
    });
}
