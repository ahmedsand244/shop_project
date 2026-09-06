/**
 * NEXUS STORE - CLIENT INTERACTION & AJAX ENGINE
 * Zero-Emoji Vector UI, Instant Live Search, Slide-Over Cart, Wishlist & Toasts
 */

// --- CSRF Helper ---
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

// --- SVG Icons Map ---
const SVG_ICONS = {
  check: `<svg class="svg-icon" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`,
  info: `<svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  alert: `<svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  cross: `<svg class="svg-icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  trash: `<svg class="svg-icon svg-icon-sm" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`,
  sun: `<svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
  moon: `<svg class="svg-icon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
  bag: `<svg class="svg-icon" viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`
};

// --- Toast Notification System ---
function showToast(title, message, type = 'success', duration = 3200) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const iconSvg = type === 'success' ? SVG_ICONS.check : (type === 'error' ? SVG_ICONS.cross : SVG_ICONS.info);

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon-wrap">${iconSvg}</div>
    <div>
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <div class="toast-progress"></div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-fadeout');
    setTimeout(() => toast.remove(), 260);
  }, duration);
}

// --- Theme Controller ---
function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark');
    document.documentElement.classList.remove('light');
  } else {
    document.documentElement.classList.add('light');
    document.documentElement.classList.remove('dark');
  }
  updateThemeIcon(savedTheme);

  const themeToggle = document.getElementById('theme-toggle-btn');
  if (themeToggle) {
    themeToggle.addEventListener('click', (e) => {
      e.preventDefault();
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      if (nextTheme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
      } else {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
      }
      localStorage.setItem('theme', nextTheme);
      updateThemeIcon(nextTheme);
      showToast('Theme Changed', `Switched to ${nextTheme.toUpperCase()} mode`, 'info', 2000);
    });
  }
}

function updateThemeIcon(theme) {
  const iconWrap = document.getElementById('theme-toggle-icon');
  if (iconWrap) {
    iconWrap.innerHTML = theme === 'dark' ? SVG_ICONS.sun : SVG_ICONS.moon;
  }
}

// --- Cart Drawer Controller ---
function initCartDrawer() {
  const backdrop = document.getElementById('cart-drawer-backdrop');
  const drawer = document.getElementById('cart-drawer');
  const openBtns = document.querySelectorAll('.trigger-cart-drawer');
  const closeBtns = document.querySelectorAll('.close-cart-drawer');

  openBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openCartDrawer();
    });
  });

  closeBtns.forEach(btn => {
    btn.addEventListener('click', closeCartDrawer);
  });

  if (backdrop) {
    backdrop.addEventListener('click', closeCartDrawer);
  }
}

function openCartDrawer() {
  const backdrop = document.getElementById('cart-drawer-backdrop');
  const drawer = document.getElementById('cart-drawer');
  if (backdrop && drawer) {
    backdrop.classList.add('active');
    drawer.classList.add('active');
    document.body.classList.add('cart-drawer-open');
    document.body.style.overflow = 'hidden';
    refreshCartDrawer();
  }
}

function closeCartDrawer() {
  const backdrop = document.getElementById('cart-drawer-backdrop');
  const drawer = document.getElementById('cart-drawer');
  if (backdrop && drawer) {
    backdrop.classList.remove('active');
    drawer.classList.remove('active');
    document.body.classList.remove('cart-drawer-open');
    document.body.style.overflow = '';
  }
}


async function refreshCartDrawer() {
  const itemsList = document.getElementById('drawer-items-list');
  const subtotalEl = document.getElementById('drawer-subtotal-val');
  const meterFill = document.getElementById('shipping-meter-fill');
  const meterText = document.getElementById('shipping-meter-text');

  if (!itemsList) return;

  try {
    const res = await fetch('/api/cart/drawer-content/');
    const data = await res.json();

    updateCartBadges(data.total_items);

    if (subtotalEl) {
      subtotalEl.textContent = `$${parseFloat(data.total_price).toFixed(2)}`;
    }

    const threshold = 100.0;
    const pct = Math.min(100, (data.total_price / threshold) * 100);
    if (meterFill) meterFill.style.width = `${pct}%`;
    if (meterText) {
      if (data.total_price >= threshold) {
        meterText.innerHTML = 'You have unlocked <strong>Complimentary Express Shipping</strong>!';
      } else {
        const diff = (threshold - data.total_price).toFixed(2);
        meterText.innerHTML = `Add <strong>$${diff}</strong> more for <strong>FREE Shipping</strong>`;
      }
    }

    if (!data.items || data.items.length === 0) {
      itemsList.innerHTML = `
        <div style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
          <div style="margin-bottom: 12px; opacity: 0.4;">${SVG_ICONS.bag}</div>
          <h3 style="font-size: 1.1rem; color: var(--text-primary); margin-bottom: 6px;">Your Bag is Empty</h3>
          <p style="font-size: 0.86rem; margin-bottom: 20px;">Explore our collections to select luxury goods.</p>
          <button class="btn-primary" onclick="closeCartDrawer(); window.location.href='/'" style="padding: 10px 20px; font-size: 0.86rem;">Start Shopping</button>
        </div>
      `;
      return;
    }

    itemsList.innerHTML = data.items.map(item => `
      <div class="drawer-item" id="drawer-item-${item.product_id}">
        <img src="${item.image_url || '/static/images/placeholder.svg'}" alt="${item.name}" class="drawer-item-img">
        <div class="drawer-item-details">
          <div class="drawer-item-name">${item.name}</div>
          <div class="drawer-item-price">$${parseFloat(item.price).toFixed(2)}</div>
          <div style="display: flex; align-items: center; justify-content: space-between; margin-top: auto;">
            <div class="quantity-stepper">
              <button type="button" class="qty-btn" onclick="updateCartQty(${item.product_id}, -1)">−</button>
              <span class="qty-val">${item.quantity}</span>
              <button type="button" class="qty-btn" onclick="updateCartQty(${item.product_id}, 1)">+</button>
            </div>
            <button type="button" class="btn-drawer-remove" onclick="removeCartItem(${item.product_id})" title="Remove item">
              ${SVG_ICONS.trash}
            </button>
          </div>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Error loading cart drawer:', err);
  }
}

async function addToCart(productId, quantity = 1) {
  try {
    const formData = new FormData();
    formData.append('quantity', quantity);

    const res = await fetch(`/api/cart/add/${productId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: formData
    });

    const data = await res.json();
    if (data.status === 'success') {
      updateCartBadges(data.total_items);
      showToast('Bag Updated', data.message || 'Product added to your bag.', 'success');
      openCartDrawer();
    }
  } catch (err) {
    showToast('Error', 'Unable to add product to cart', 'error');
  }
}

async function updateCartQty(productId, delta) {
  try {
    const formData = new FormData();
    formData.append('delta', delta);

    const res = await fetch(`/api/cart/update/${productId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: formData
    });

    const data = await res.json();
    if (data.status === 'success') {
      refreshCartDrawer();
      const fullCartRow = document.getElementById(`cart-row-${productId}`);
      if (fullCartRow) window.location.reload();
    }
  } catch (err) {
    console.error('Error updating qty:', err);
  }
}

async function removeCartItem(productId) {
  try {
    const res = await fetch(`/api/cart/remove/${productId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken }
    });

    const data = await res.json();
    if (data.status === 'success') {
      showToast('Item Removed', 'Product removed from your bag.', 'info');
      refreshCartDrawer();
      const fullCartRow = document.getElementById(`cart-row-${productId}`);
      if (fullCartRow) {
        fullCartRow.remove();
        window.location.reload();
      }
    }
  } catch (err) {
    console.error('Error removing item:', err);
  }
}

function updateCartBadges(count) {
  const badges = document.querySelectorAll('.cart-badge-counter');
  badges.forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? 'flex' : 'none';
  });
}

// --- Wishlist Toggle ---
async function toggleWishlist(productId, btnEl) {
  try {
    const res = await fetch(`/api/wishlist/toggle/${productId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken }
    });

    const data = await res.json();
    if (data.status === 'success') {
      const isAdded = data.is_added;
      if (btnEl) btnEl.classList.toggle('active', isAdded);

      const wishlistBadges = document.querySelectorAll('.wishlist-badge-counter');
      wishlistBadges.forEach(b => {
        b.textContent = data.wishlist_count;
        b.style.display = data.wishlist_count > 0 ? 'flex' : 'none';
      });

      showToast(
        isAdded ? 'Added to Wishlist' : 'Removed from Wishlist',
        isAdded ? 'Product saved to your favorites.' : 'Product removed from favorites.',
        'success'
      );
    } else if (data.status === 'login_required') {
      showToast('Sign In Required', 'Please sign in to save items to your wishlist.', 'info');
      setTimeout(() => window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname), 1200);
    }
  } catch (err) {
    showToast('Error', 'Unable to update wishlist', 'error');
  }
}

// --- Live Instant Search (Desktop & Mobile) ---
function initLiveSearch() {
  function bindSearch(inputEl, dropdownEl) {
    if (!inputEl || !dropdownEl) return;
    let debounceTimer;

    inputEl.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const q = e.target.value.trim();

      if (q.length < 2) {
        dropdownEl.innerHTML = '';
        dropdownEl.classList.remove('active');
        return;
      }

      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search/live/?q=${encodeURIComponent(q)}`);
          const data = await res.json();

          if (data.results && data.results.length > 0) {
            dropdownEl.innerHTML = data.results.map(p => `
              <a href="${p.url}" class="search-item">
                <img src="${p.image_url || '/static/images/placeholder.svg'}" alt="${p.name}" class="search-item-img">
                <div style="flex: 1;">
                  <div class="search-item-name">${highlightMatch(p.name, q)}</div>
                  <div class="search-item-price">$${parseFloat(p.price).toFixed(2)}</div>
                </div>
              </a>
            `).join('');
            dropdownEl.classList.add('active');
          } else {
            dropdownEl.innerHTML = `<div style="padding: 14px; text-align: center; color: var(--text-muted); font-size: 0.86rem;">No results found for "${q}"</div>`;
            dropdownEl.classList.add('active');
          }
        } catch (err) {
          console.error('Search error:', err);
        }
      }, 250);
    });

    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = inputEl.value.trim();
        if (q) {
          window.location.href = `/?q=${encodeURIComponent(q)}#products-section`;
        }
      }
    });

    document.addEventListener('click', (e) => {
      if (!inputEl.contains(e.target) && !dropdownEl.contains(e.target)) {
        dropdownEl.classList.remove('active');
      }
    });
  }

  // Desktop search
  bindSearch(document.getElementById('live-search-input'), document.getElementById('live-search-dropdown'));
  // Mobile search
  bindSearch(document.getElementById('mobile-search-input'), document.getElementById('mobile-search-dropdown'));

  // Mobile search drawer toggle
  const mobileSearchToggle = document.getElementById('mobile-search-toggle');
  const mobileSearchDrawer = document.getElementById('mobile-search-drawer');
  const mobileSearchClose = document.getElementById('mobile-search-close');
  const mobileSearchInput = document.getElementById('mobile-search-input');

  if (mobileSearchToggle && mobileSearchDrawer) {
    mobileSearchToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      mobileSearchDrawer.classList.toggle('active');
      if (mobileSearchDrawer.classList.contains('active') && mobileSearchInput) {
        setTimeout(() => mobileSearchInput.focus(), 150);
      }
    });
  }

  if (mobileSearchClose && mobileSearchDrawer) {
    mobileSearchClose.addEventListener('click', () => {
      mobileSearchDrawer.classList.remove('active');
    });
  }
}

function highlightMatch(text, query) {
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<span style="color: var(--accent-primary); font-weight: 800;">$1</span>');
}

// --- Quick View Modal ---
async function openQuickView(productId) {
  const backdrop = document.getElementById('quickview-modal-backdrop');
  const content = document.getElementById('quickview-modal-content');
  if (!backdrop || !content) return;

  backdrop.classList.add('active');
  content.innerHTML = `
    <div style="padding: 60px 20px; text-align: center; color: var(--text-secondary);">
      <div style="font-size: 0.95rem;">Loading product specification...</div>
    </div>
  `;

  try {
    const res = await fetch(`/api/product/${productId}/quick-view/`);
    const p = await res.json();

    content.innerHTML = `
      <div class="quickview-grid">
        <div class="quickview-img-wrap">
          <img src="${p.image_url}" alt="${p.name}">
        </div>
        <div class="quickview-info-col" style="display: flex; flex-direction: column; gap: 12px;">
          <span style="color: var(--accent-primary); font-weight: 700; font-size: 0.76rem; text-transform: uppercase;">${p.category_name}</span>
          <h2 style="font-size: 1.5rem; font-weight: 800;">${p.name}</h2>
          <div style="display: flex; align-items: baseline; gap: 10px;">
            <span style="font-size: 1.7rem; font-weight: 800; color: var(--text-primary);">$${p.price}</span>
            ${p.old_price ? `<span style="font-size: 1rem; color: var(--text-muted); text-decoration: line-through;">$${p.old_price}</span>` : ''}
            ${p.discount_percentage ? `<span class="discount-saving-tag">-${p.discount_percentage}% OFF</span>` : ''}
          </div>
          <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;">${p.short_description || p.description}</p>
          <div style="margin-top: auto; display: flex; gap: 10px;">
            <button class="btn-primary" style="flex: 1;" onclick="addToCart(${p.id}); closeQuickView();">
              Add to Bag
            </button>
            <a href="${p.url}" class="btn-secondary">
              Details →
            </a>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    content.innerHTML = '<div style="padding: 30px; text-align: center; color: var(--accent-rose);">Failed to load product.</div>';
  }
}

function closeQuickView() {
  const backdrop = document.getElementById('quickview-modal-backdrop');
  if (backdrop) backdrop.classList.remove('active');
}

// --- Coupon Application ---
async function applyCouponCode(code, callback) {
  if (!code) {
    showToast('Notice', 'Please enter a promo code', 'warning');
    return;
  }

  try {
    const formData = new FormData();
    formData.append('code', code);

    const res = await fetch('/api/coupon/validate/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: formData
    });

    const data = await res.json();
    if (data.status === 'success') {
      showToast('Coupon Applied', data.message, 'success');
      if (typeof callback === 'function') callback(data);
    } else {
      showToast('Invalid Coupon', data.message, 'error');
    }
  } catch (err) {
    showToast('Error', 'Unable to apply coupon', 'error');
  }
}

// --- Flash Sale Live Timer ---
function initFlashSaleCountdown() {
  const timerContainer = document.getElementById('flash-sale-timer');
  if (!timerContainer) return;

  const now = new Date().getTime();
  const targetTime = now + (11 * 60 * 60 * 1000) + (44 * 60 * 1000);

  function update() {
    const currentTime = new Date().getTime();
    const diff = targetTime - currentTime;

    if (diff <= 0) {
      timerContainer.innerHTML = '<span style="color: var(--accent-gold); font-weight: 700;">Offer Expired</span>';
      return;
    }

    const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((diff / 1000 / 60) % 60);
    const seconds = Math.floor((diff / 1000) % 60);

    const hEl = document.getElementById('timer-hours');
    const mEl = document.getElementById('timer-minutes');
    const sEl = document.getElementById('timer-seconds');

    if (hEl) hEl.textContent = String(hours).padStart(2, '0');
    if (mEl) mEl.textContent = String(minutes).padStart(2, '0');
    if (sEl) sEl.textContent = String(seconds).padStart(2, '0');
  }

  update();
  setInterval(update, 1000);
}

// --- Live Chat Unread Badge Poller ---
function initChatUnreadBadgePoller() {
  const badge = document.getElementById('nav-chat-unread-badge');
  if (!badge) return;

  async function checkUnread() {
    try {
      const res = await fetch('/api/chat/unread-count/');
      const data = await res.json();
      if (data.status === 'success') {
        if (data.customer_unread > 0) {
          badge.style.display = 'inline-block';
        } else {
          badge.style.display = 'none';
        }
      }
    } catch (err) {}
  }

  checkUnread();
  setInterval(checkUnread, 6000);
}

// --- User Profile Dropdown Controller ---
function initUserDropdown() {
  const wrapper = document.getElementById('user-menu-wrapper');
  const dropdown = document.getElementById('user-dropdown-menu');
  const btn = document.getElementById('user-dropdown-btn');
  if (!dropdown) return;

  if (btn) {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('active');
    });
  }

  // Close dropdown on click outside
  document.addEventListener('click', (e) => {
    if (dropdown.classList.contains('active')) {
      if (!wrapper || !wrapper.contains(e.target)) {
        dropdown.classList.remove('active');
      }
    }
  });

  // Close dropdown on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && dropdown.classList.contains('active')) {
      dropdown.classList.remove('active');
    }
  });
}

// --- Initialize On Load ---
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initCartDrawer();
  initLiveSearch();
  initUserDropdown();
  initFlashSaleCountdown();
  initChatUnreadBadgePoller();

  const qvBackdrop = document.getElementById('quickview-modal-backdrop');
  if (qvBackdrop) {
    qvBackdrop.addEventListener('click', (e) => {
      if (e.target === qvBackdrop) closeQuickView();
    });
  }
});

