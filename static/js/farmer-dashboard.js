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
    const mainImageInput = document.querySelector('input[name="main_image"]');
    const additionalImagesInput = document.querySelector('input[name="images"]');
    const previewContainer = document.getElementById('imagePreview');

    if (previewContainer) {
        // Save initial HTML to fallback to if no new files are chosen
        previewContainer.dataset.existingPreview = previewContainer.innerHTML;

        function updatePreviews() {
            previewContainer.innerHTML = '';
            let hasImages = false;

            // Handle main cover image preview
            if (mainImageInput && mainImageInput.files && mainImageInput.files[0]) {
                const file = mainImageInput.files[0];
                if (file.size > 5 * 1024 * 1024) {
                    alert('Cover Image file size must be less than 5MB.');
                    mainImageInput.value = '';
                } else {
                    hasImages = true;
                    const previewDiv = document.createElement('div');
                    previewDiv.className = 'w-100 mb-3 text-start';
                    previewDiv.innerHTML = `
                        <span class="text-success font-xs fw-bold d-block mb-1">New Cover Image:</span>
                        <img id="main-image-preview-el" class="img-thumbnail rounded-3 shadow-sm" style="max-height: 160px; object-fit: cover; width: 100%;">
                    `;
                    previewContainer.appendChild(previewDiv);
                    
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('main-image-preview-el').src = e.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            }

            // Handle additional images previews
            if (additionalImagesInput && additionalImagesInput.files && additionalImagesInput.files.length > 0) {
                const addDiv = document.createElement('div');
                addDiv.className = 'w-100 text-start';
                addDiv.innerHTML = `
                    <span class="text-success font-xs fw-bold d-block mb-1">New Additional Images:</span>
                    <div class="d-flex gap-2 flex-wrap" id="additional-previews-container"></div>
                `;
                previewContainer.appendChild(addDiv);
                
                const container = document.getElementById('additional-previews-container');
                
                Array.from(additionalImagesInput.files).forEach((file, index) => {
                    if (file.size > 5 * 1024 * 1024) {
                        alert(`Additional image "${file.name}" must be less than 5MB.`);
                        return;
                    }
                    hasImages = true;
                    const imgEl = document.createElement('img');
                    imgEl.className = 'img-thumbnail rounded-2 shadow-sm';
                    imgEl.style.cssText = 'width: 72px; height: 72px; object-fit: cover;';
                    container.appendChild(imgEl);

                    const reader = new FileReader();
                    reader.onload = function(e) {
                        imgEl.src = e.target.result;
                    };
                    reader.readAsDataURL(file);
                });
            }

            if (!hasImages) {
                previewContainer.innerHTML = previewContainer.dataset.existingPreview;
            }
        }

        if (mainImageInput) {
            mainImageInput.addEventListener('change', updatePreviews);
        }
        if (additionalImagesInput) {
            additionalImagesInput.addEventListener('change', updatePreviews);
        }
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
