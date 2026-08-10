// AgroConnect Buyer Dashboard Interactive JS

document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Sidebar Drawer Toggler
    const hamburgerBtn = document.getElementById('hamburgerMenuBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const sidebar = document.getElementById('dashboardSidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (hamburgerBtn && sidebar && overlay) {
        hamburgerBtn.addEventListener('click', function() {
            sidebar.classList.add('open');
            overlay.classList.add('active');
        });
    }

    if (closeSidebarBtn && sidebar && overlay) {
        closeSidebarBtn.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    if (overlay && sidebar) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    // 2. Custom Toast System
    const toastContainer = document.querySelector('.toast-container');
    function showToast(message, isError = false) {
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white ${isError ? 'bg-danger' : 'bg-success'} border-0 show p-2 mb-2`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${isError ? 'fa-exclamation-circle' : 'fa-check-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    }
    
    // Register toast trigger globally
    window.showAgroToast = showToast;

    // 3. AJAX Wishlist Heart Toggle Trigger
    const wishlistBtns = document.querySelectorAll('.toggle-wishlist-btn');
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const heartIcon = this.querySelector('i');
            
            // Get CSRF Token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

            const formData = new FormData();
            formData.append('action', 'toggle');
            formData.append('product_id', productId);

            fetch('/buyer/wishlist/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'added') {
                    heartIcon.className = 'fas fa-heart text-danger';
                    showToast(data.message);
                } else if (data.status === 'removed') {
                    heartIcon.className = 'far fa-heart';
                    showToast(data.message);
                }
            })
            .catch(err => {
                console.error(err);
                showToast("Failed to update wishlist. Please try again.", true);
            });
        });
    });

    // 4. AJAX Notification read triggers
    const notificationRows = document.querySelectorAll('.notification-row');
    notificationRows.forEach(row => {
        const markBtn = row.querySelector('.btn-link');
        if (markBtn) {
            markBtn.addEventListener('click', function(e) {
                // If it is inside form, prevent double submits
                const notifId = row.getAttribute('data-notif-id');
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

                const formData = new FormData();
                formData.append('action', 'mark_read');
                formData.append('notification_id', notifId);

                fetch('/buyer/notifications/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        row.classList.remove('unread-highlight');
                        row.querySelector('.badge')?.remove();
                        markBtn.remove();
                        showToast("Notification marked as read.");
                    }
                })
                .catch(err => console.error(err));
            });
        }
    });
});
