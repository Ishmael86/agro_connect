document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Mobile Sidebar drawer toggles
    const sidebarToggle = document.getElementById('sidebarToggle');
    const farmerSidebar = document.querySelector('.farmer-sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    
    if (sidebarToggle && farmerSidebar && sidebarOverlay) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            farmerSidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
        });
        
        sidebarOverlay.addEventListener('click', function() {
            farmerSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    // 2. Crop Image Upload Preview
    const imageUploadInput = document.querySelector('input[type="file"][name="main_image"]');
    const imagePreviewContainer = document.getElementById('imagePreview');
    
    if (imageUploadInput && imagePreviewContainer) {
        imageUploadInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('Image file size must be less than 5MB.');
                    this.value = '';
                    imagePreviewContainer.innerHTML = '';
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreviewContainer.innerHTML = `<img src="${e.target.result}" class="img-thumbnail rounded-3 shadow-sm" style="max-height: 200px; object-fit: cover; width: 100%;">`;
                };
                reader.readAsDataURL(file);
            } else {
                imagePreviewContainer.innerHTML = '';
            }
        });
    }

    // 3. Auto Scroll messages in chat threads
    const chatMessageList = document.getElementById('chatMessageList');
    if (chatMessageList) {
        chatMessageList.scrollTop = chatMessageList.scrollHeight;
    }

    // 4. Confirmation dialog modal prompts
    const deleteForms = document.querySelectorAll('.form-delete-confirm');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const confirmed = confirm('Are you sure you want to proceed with this destructive action? This cannot be undone.');
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });

    // 5. AJAX handler for marking notifications as read
    const notifReadButtons = document.querySelectorAll('.mark-notif-read-btn');
    notifReadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const notifId = this.getAttribute('data-notification-id');
            const token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            const container = this.closest('.notification-item-row');
            
            fetch('/farmer/notifications/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': token
                },
                body: `action=mark_read&notification_id=${notifId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (container) {
                        container.classList.remove('bg-light');
                        this.remove(); // Remove mark as read button
                    }
                    // Decrement notification counts in header badge
                    const countBadge = document.getElementById('headerNotificationCount');
                    if (countBadge) {
                        let currentCount = parseInt(countBadge.textContent);
                        if (currentCount > 1) {
                            countBadge.textContent = currentCount - 1;
                        } else {
                            countBadge.remove();
                        }
                    }
                }
            })
            .catch(error => console.error('Error marking notification as read:', error));
        });
    });
});
