// AgroConnect JavaScript Interactivity

document.addEventListener('DOMContentLoaded', function() {
    // 1. Setup CSRF Token Helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // 2. Custom Toast System
    function showToast(message, isError = false) {
        let container = document.querySelector('.messages-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'messages-container';
            container.style.cssText = 'position: fixed; top: 90px; right: 20px; z-index: 9999; min-width: 350px; max-width: 500px;';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `alert alert-dismissible fade show alert-${isError ? 'danger' : 'success'} message-item`;
        toast.style.cssText = `
            box-shadow: 0 8px 25px rgba(0,0,0,0.15); 
            border: none; 
            border-radius: 12px; 
            margin-bottom: 15px;
            border-left: 4px solid;
            animation: slideInRight 0.5s ease-out;
        `;
        
        toast.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-shrink-0 me-3">
                    <i class="fas ${isError ? 'fa-exclamation-triangle fa-lg' : 'fa-check-circle fa-lg'}" style="color: ${isError ? '#dc3545' : '#198754'};"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <strong class="message-title" style="font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                            ${isError ? 'Error!' : 'Success!'}
                        </strong>
                        <button type="button" class="btn-close btn-close-custom" data-bs-dismiss="alert" aria-label="Close"
                                style="font-size: 0.7rem; padding: 0.5rem;"></button>
                    </div>
                    <div class="message-content" style="line-height: 1.4; font-size: 0.9rem;">
                        ${message}
                    </div>
                    <div class="progress mt-2" style="height: 3px; background-color: rgba(0,0,0,0.1);">
                        <div class="progress-bar progress-bar-${isError ? 'danger' : 'success'}" 
                             role="progressbar" 
                             style="width: 100%; transition: width 5s linear;">
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(toast);
        
        const progressBar = toast.querySelector('.progress-bar');
        if (progressBar) {
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 100);
        }
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                toast.style.transition = 'all 0.5s ease';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 500);
            }
        }, 5000);
        
        toast.addEventListener('click', function(e) {
            if (!e.target.classList.contains('btn-close')) {
                this.style.opacity = '0';
                this.style.transform = 'translateX(100%)';
                this.style.transition = 'all 0.5s ease';
                setTimeout(() => {
                    if (this.parentNode) {
                        this.remove();
                    }
                }, 500);
            }
        });
    }

    // Export global toast triggers for inline usage
    window.showAgroToast = showToast;

    function toggleWishlist(btn) {
        const isAuth = btn.getAttribute('data-authenticated') === 'true';
        const accountType = btn.getAttribute('data-account-type');
        
        if (!isAuth) {
            showToast('Please log in or register an account to add crops to your wishlist.', true);
            return;
        }
        
        if (accountType === 'FARMER') {
            showToast('Farmers are not allowed to use the wishlist feature.', true);
            return;
        }
        
        const icon = btn.querySelector('i');
        if (icon.classList.contains('far')) {
            icon.classList.remove('far');
            icon.classList.add('fas');
            icon.style.color = '#ef4444';
            showToast('Added to Wishlist!');
        } else {
            icon.classList.remove('fas');
            icon.classList.add('far');
            icon.style.color = '';
            showToast('Removed from Wishlist!');
        }
    }
    window.toggleWishlist = toggleWishlist;

    // 3. Register Form Account Type Toggle
    const tabFarmer = document.getElementById('tab-farmer');
    const tabBuyer = document.getElementById('tab-buyer');
    const farmerFieldsBlock = document.getElementById('farmer-specific-fields');
    
    if (tabFarmer && tabBuyer && farmerFieldsBlock) {
        // Look for the radios generated by Django
        const radioFarmer = document.querySelector('input[name="account_type"][value="FARMER"]');
        const radioBuyer = document.querySelector('input[name="account_type"][value="BUYER"]');

        function setAccountType(type) {
            if (type === 'FARMER') {
                tabFarmer.classList.add('active');
                tabBuyer.classList.remove('active');
                farmerFieldsBlock.style.display = 'block';
                if (radioFarmer) radioFarmer.checked = true;
                
                // Add required attribute
                document.getElementById('id_farm_name').required = true;
                document.getElementById('id_region').required = true;
                document.getElementById('id_location').required = true;
            } else {
                tabFarmer.classList.remove('active');
                tabBuyer.classList.add('active');
                farmerFieldsBlock.style.display = 'none';
                if (radioBuyer) radioBuyer.checked = true;

                // Remove required attribute
                document.getElementById('id_farm_name').required = false;
                document.getElementById('id_region').required = false;
                document.getElementById('id_location').required = false;
            }
        }

        tabFarmer.addEventListener('click', () => setAccountType('FARMER'));
        tabBuyer.addEventListener('click', () => setAccountType('BUYER'));

        // Initialize based on radio state or default
        if (radioFarmer && radioFarmer.checked) {
            setAccountType('FARMER');
        } else {
            setAccountType('BUYER');
        }
    }

    // 4. Password Visibility Toggle
    document.querySelectorAll('.password-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    });

    // 5. Product Image Gallery Switcher
    const thumbnails = document.querySelectorAll('.gallery-thumbnails img');
    const mainImg = document.getElementById('main-product-image');
    if (thumbnails.length > 0 && mainImg) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                mainImg.src = this.dataset.largeSrc || this.src;
            });
        });
    }

    // 6. Quantity Selector Inputs (+ / - buttons)
    const detailQtyWrapper = document.querySelector('.detail-qty-wrapper');
    if (detailQtyWrapper) {
        const minusBtn = detailQtyWrapper.querySelector('.qty-minus');
        const plusBtn = detailQtyWrapper.querySelector('.qty-plus');
        const input = detailQtyWrapper.querySelector('.qty-input');
        const maxVal = parseInt(input.dataset.maxStock || 100);

        minusBtn.addEventListener('click', () => {
            let val = parseInt(input.value) || 1;
            if (val > 1) {
                input.value = val - 1;
            }
        });

        plusBtn.addEventListener('click', () => {
            let val = parseInt(input.value) || 1;
            if (val < maxVal) {
                input.value = val + 1;
            } else {
                showToast(`Cannot exceed available stock of ${maxVal} units.`, true);
            }
        });

        input.addEventListener('change', () => {
            let val = parseInt(input.value);
            if (isNaN(val) || val < 1) {
                input.value = 1;
            } else if (val > maxVal) {
                input.value = maxVal;
                showToast(`Only ${maxVal} units available in stock.`, true);
            }
        });
    }

    // 7. AJAX - Add to Cart
    document.querySelectorAll('.ajax-add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            const quantityInput = document.querySelector(`.qty-input[data-product-id="${productId}"]`) || document.querySelector('.qty-input');
            const qty = quantityInput ? quantityInput.value : 1;

            const formData = new FormData();
            formData.append('quantity', qty);

            fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => { throw new Error(data.message || 'Error occurred'); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    showToast(data.message);
                    // Update all cart count badges
                    document.querySelectorAll('.cart-badge').forEach(badge => {
                        badge.textContent = data.cart_count;
                        badge.style.display = data.cart_count > 0 ? 'inline-block' : 'none';
                    });
                }
            })
            .catch(error => {
                showToast(error.message, true);
            });
        });
    });

    // 8. AJAX - Cart Update and Remove on Cart Page
    document.querySelectorAll('.cart-qty-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            const action = this.dataset.action;
            updateCartQuantity(itemId, action);
        });
    });

    document.querySelectorAll('.cart-remove-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            removeCartItem(itemId);
        });
    });

    function updateCartQuantity(itemId, action) {
        const formData = new FormData();
        formData.append('action', action);

        fetch(`/cart/update/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = document.getElementById(`cart-row-${itemId}`);
                if (data.item_quantity === 0) {
                    // Remove row from table
                    if (row) {
                        row.style.opacity = '0';
                        setTimeout(() => {
                            row.remove();
                            checkEmptyCart();
                        }, 300);
                    }
                } else {
                    // Update row elements
                    const qtyInput = row.querySelector('.cart-qty-input');
                    if (qtyInput) qtyInput.value = data.item_quantity;

                    const subtotalEl = row.querySelector('.cart-item-subtotal');
                    if (subtotalEl) subtotalEl.textContent = data.item_subtotal;
                }

                // Update summary block
                updateCartTotals(data);
                showToast(data.message);
            } else {
                showToast(data.message, true);
            }
        })
        .catch(error => {
            showToast("Failed to update cart.", true);
        });
    }

    function removeCartItem(itemId) {
        fetch(`/cart/remove/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = document.getElementById(`cart-row-${itemId}`);
                if (row) {
                    row.style.opacity = '0';
                    setTimeout(() => {
                        row.remove();
                        checkEmptyCart();
                    }, 300);
                }

                // Update summary block
                updateCartTotals(data);
                showToast(data.message);
            } else {
                showToast(data.message, true);
            }
        })
        .catch(error => {
            showToast("Failed to remove item.", true);
        });
    }

    function updateCartTotals(data) {
        // Update cart counters
        document.querySelectorAll('.cart-badge').forEach(badge => {
            badge.textContent = data.cart_count;
            badge.style.display = data.cart_count > 0 ? 'inline-block' : 'none';
        });

        // Update totals on page
        const subtotalEl = document.getElementById('cart-subtotal-summary');
        const totalEl = document.getElementById('cart-total-summary');
        
        if (subtotalEl) subtotalEl.textContent = data.cart_subtotal;
        if (totalEl) totalEl.textContent = data.cart_total;
    }

    function checkEmptyCart() {
        const tableBody = document.querySelector('.cart-table tbody');
        if (tableBody && tableBody.children.length === 0) {
            const container = document.getElementById('cart-container');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-5">
                        <div class="mb-4">
                            <i class="fas fa-shopping-basket fa-4x text-muted" style="color: var(--primary-green-light) !important;"></i>
                        </div>
                        <h3>Your cart is empty! 🌱</h3>
                        <p class="text-muted mb-4">Discover fresh products directly from local farmers.</p>
                        <a href="/products/" class="btn btn-primary-green">Shop Fresh Produce</a>
                    </div>
                `;
            }
        }
    }
});
