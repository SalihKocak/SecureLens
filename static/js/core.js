/**
 * SecureLens Core JavaScript Module
 * Essential functions and utilities
 */

// Global variables
const SecureLens = {
    config: {
        API_BASE: '',
        ANIMATION_DURATION: 300
    },
    state: {
        currentTheme: 'light',
        isPageLoading: false,
        loadingTimeout: null
    }
};

/**
 * Simple and Effective Page Loading System
 */
function showPageLoading() {
    if (SecureLens.state.isPageLoading) return;
    
    SecureLens.state.isPageLoading = true;
    console.log('🔄 Showing page loading...');
    
    // Immediately hide all content
    const mainContent = document.querySelector('main');
    const navigation = document.querySelector('nav');
    
    if (mainContent) {
        mainContent.style.display = 'none';
    }
    
    if (navigation) {
        navigation.style.opacity = '0.5';
    }
    
    // Create or show loading overlay
    let overlay = document.getElementById('page-loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'page-loading-overlay';
        overlay.innerHTML = `
            <div class="fixed inset-0 bg-white z-50 flex items-center justify-center">
                <div class="flex flex-col items-center space-y-6">
                    <div class="relative">
                        <div class="w-16 h-16 relative">
                            <div class="absolute inset-0 border-4 border-blue-100 rounded-full"></div>
                            <div class="absolute inset-0 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                            <div class="absolute inset-2 border-2 border-blue-300 border-r-transparent rounded-full animate-spin-reverse"></div>
                            <div class="absolute inset-0 flex items-center justify-center">
                                <i class="fas fa-shield-alt text-blue-600 text-xl"></i>
                            </div>
                        </div>
                    </div>
                    <div class="text-center">
                        <div class="text-gray-800 font-semibold text-lg mb-1">Sayfa Yükleniyor</div>
                        <div class="text-gray-500 text-sm">Lütfen bekleyiniz...</div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.style.display = 'block';
    }
}

/**
 * Hide Page Loading - Balanced System
 */
function hidePageLoading() {
    console.log('✅ Hiding page loading...');
    
    SecureLens.state.isPageLoading = false;
    
    const overlay = document.getElementById('page-loading-overlay') || document.getElementById('initial-page-overlay');
    const mainContent = document.querySelector('main');
    
    if (mainContent) {
        // Show content with smooth animation
        mainContent.style.transition = 'all 0.5s ease-out';
        mainContent.style.opacity = '1';
        mainContent.style.transform = 'translateY(0)';
    }
    
    // Hide loading overlay
    if (overlay) {
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.3s ease-out';
        
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }
    
    console.log('✅ Page loading hidden successfully');
}

// Initialize core functions
document.addEventListener('DOMContentLoaded', function() {
    const pageId = document.querySelector('meta[name="page-id"]')?.content || 'unknown';
    console.log(`🛡️ SecureLens Core initialized for page: ${pageId}`);
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Page-specific initialization for analyze page
    if (pageId === 'analyze') {
        console.log('🔧 Initializing analyze page...');
        // Wait for analyze.js to load then initialize
        setTimeout(() => {
            if (typeof window.initializeEventListeners === 'function') {
                console.log('🔧 Calling analyze page event listeners...');
                window.initializeEventListeners();
            } else {
                console.log('⚠️ Analyze event listeners not available yet');
            }
        }, 50);
    }
    
    // Initialize theme
    initializeTheme();
    
    // Initialize navbar
    initializeNavbar();
    
    // Initialize page preloading
    initPagePreloading();
    
    // Initialize page transition system
    initPageTransitions();
    
    // Page-specific initialization timing
    const pageLoadTimes = {
        'home': 100,      // Ana sayfa hızlı
        'analyze': 150,   // Analiz sayfası orta
        'dashboard': 200  // Dashboard yavaş (çizelgeler var)
    };
    
    const delay = pageLoadTimes[pageId] || 150;
    console.log(`⏰ Page load delay: ${delay}ms for ${pageId}`);
    
    setTimeout(() => {
        hidePageLoading();
    }, delay);
});

/**
 * Simple Page Transition System
 */
function initPageTransitions() {
    // Handle browser navigation
    window.addEventListener('beforeunload', function() {
        showPageLoading();
    });
    
    // Handle page load completion
    window.addEventListener('load', function() {
        console.log('🎯 Window load event triggered');
        setTimeout(() => {
            hidePageLoading();
        }, 100);
    });
    
    // Fallback timeout
    setTimeout(() => {
        if (SecureLens.state.isPageLoading) {
            console.log('⏰ Force hiding loading after timeout');
            hidePageLoading();
        }
    }, 3000);
}

/**
 * Page Preloading System
 */
function initPagePreloading() {
    // Preload critical pages
    const pagesToPreload = ['/analyze', '/dashboard', '/'];
    
    pagesToPreload.forEach(page => {
        if (window.location.pathname !== page) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = page;
            document.head.appendChild(link);
        }
    });
    
    // Preload navigation links on hover
    document.querySelectorAll('a[href^="/"]').forEach(link => {
        link.addEventListener('mouseenter', function() {
            if (this.href && !this.dataset.preloaded) {
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = this.href;
                document.head.appendChild(prefetchLink);
                this.dataset.preloaded = 'true';
            }
        });
    });
}

/**
 * Initialize global event listeners
 */
function initializeEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // ESC key for general escape actions
        if (e.key === 'Escape') {
            // Close guide modal if open
            const guideModal = document.getElementById('guideModal');
            if (guideModal && !guideModal.classList.contains('hidden')) {
                closeGuideModal();
            }
            // Close any other open dropdowns, modals etc.
            closeDropdowns();
        }
    });

    // Global click listener for guide modal backdrop
    document.addEventListener('click', function(e) {
        const guideModal = document.getElementById('guideModal');
        if (guideModal && e.target === guideModal && !guideModal.classList.contains('hidden')) {
            closeGuideModal();
        }
    });
}

/**
 * Navigation functions
 */
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }
}

function closeDropdowns() {
    // Close any open dropdown menus
    const dropdowns = document.querySelectorAll('.dropdown-menu');
    dropdowns.forEach(dropdown => {
        dropdown.classList.add('hidden');
    });
}

/**
 * Guide Modal Functions
 */
function showGuideModal() {
    const modal = document.getElementById('guideModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Prevent body scrolling
        document.body.style.overflow = 'hidden';
        
        // Force a reflow and animate in
        modal.offsetHeight;
        
        setTimeout(() => {
            const content = modal.querySelector('.bg-white');
            content.style.transform = 'scale(1) translateY(0)';
            content.style.opacity = '1';
        }, 50);
        
        console.log('📖 Guide modal opened - perfectly centered');
    }
}

function closeGuideModal() {
    const modal = document.getElementById('guideModal');
    if (modal) {
        // Animate out
        const content = modal.querySelector('.bg-white');
        content.style.transform = 'scale(0.9) translateY(20px)';
        content.style.opacity = '0';
        content.style.transition = 'all 0.3s ease-in';
        
        setTimeout(() => {
            modal.classList.add('hidden');
            // Restore body scrolling
            document.body.style.overflow = '';
            
            // Reset transform for next opening
            content.style.transform = 'scale(0.9) translateY(20px)';
            content.style.opacity = '0';
            content.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
        }, 300);
        
        console.log('📖 Guide modal closed');
    }
}

// Close modal on outside click
document.addEventListener('click', function(e) {
    const modal = document.getElementById('guideModal');
    if (modal && e.target === modal) {
        closeGuideModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeGuideModal();
    }
});

/**
 * Theme management
 */
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    SecureLens.state.currentTheme = savedTheme;
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = SecureLens.state.currentTheme;
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    SecureLens.state.currentTheme = newTheme;
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    
    console.log(`Theme changed to: ${newTheme}`);
}

/**
 * Utility functions
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Text copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        console.log('Text copied to clipboard (fallback)');
    }
}

/**
 * Enhanced notification system with stacking support
 */
function showNotification(message, type = 'info', duration = 4000) {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create or get notification container
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    const notificationId = 'notification-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    notification.id = notificationId;
    
    // Set notification styles based on type
    const typeStyles = {
        'success': 'bg-green-500 border-green-600 text-white',
        'error': 'bg-red-500 border-red-600 text-white',
        'warning': 'bg-yellow-500 border-yellow-600 text-white',
        'info': 'bg-blue-500 border-blue-600 text-white'
    };
    
    const typeIcons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    notification.className = `
        ${typeStyles[type] || typeStyles.info}
        px-4 py-3 rounded-lg shadow-lg border-l-4 
        transform transition-all duration-300 ease-in-out
        translate-x-full opacity-0
        flex items-center gap-3 min-w-0
    `;
    
    notification.innerHTML = `
        <div class="flex-shrink-0">
            <i class="${typeIcons[type] || typeIcons.info}"></i>
        </div>
        <div class="flex-1 min-w-0">
            <p class="text-sm font-medium break-words">${message}</p>
        </div>
        <button onclick="removeNotification('${notificationId}')" 
                class="flex-shrink-0 ml-2 text-white/80 hover:text-white transition-colors">
            <i class="fas fa-times text-xs"></i>
        </button>
    `;
    
    // Add to container at the top (new notifications appear at top)
    container.insertBefore(notification, container.firstChild);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full', 'opacity-0');
        notification.classList.add('translate-x-0', 'opacity-100');
    }, 10);
    
    // Auto remove after specified duration
    const timeoutId = setTimeout(() => {
        removeNotification(notificationId);
    }, duration);
    
    // Store timeout ID for manual removal
    notification.dataset.timeoutId = timeoutId;
    
    // Limit number of notifications (max 5)
    const notifications = container.children;
    if (notifications.length > 5) {
        // Remove the oldest notification (last child)
        removeNotification(notifications[notifications.length - 1].id);
    }
}

/**
 * Remove specific notification
 */
function removeNotification(notificationId) {
    const notification = document.getElementById(notificationId);
    if (!notification) return;
    
    // Clear timeout if exists
    if (notification.dataset.timeoutId) {
        clearTimeout(parseInt(notification.dataset.timeoutId));
    }
    
    // Animate out
    notification.classList.remove('translate-x-0', 'opacity-100');
    notification.classList.add('translate-x-full', 'opacity-0');
    
    // Remove from DOM after animation
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
            
            // Remove container if empty
            const container = document.getElementById('notification-container');
            if (container && container.children.length === 0) {
                container.parentNode.removeChild(container);
            }
        }
    }, 300);
}

/**
 * Clear all notifications
 */
function clearAllNotifications() {
    const container = document.getElementById('notification-container');
    if (container) {
        const notifications = Array.from(container.children);
        notifications.forEach(notification => {
            removeNotification(notification.id);
        });
    }
}

/**
 * Quick Analysis Functions
 */
function startAnalysis(type) {
    console.log(`Starting ${type} analysis...`);
    
    // Show loading notification (shorter duration)
    showNotification(`${getAnalysisTypeName(type)} analizi başlatılıyor...`, 'info', 2000);
    
    // Redirect to analysis page with type parameter
    setTimeout(() => {
        window.location.href = `/analyze?type=${type}`;
    }, 1000);
}

function getAnalysisTypeName(type) {
    const typeNames = {
        'url': 'URL',
        'email': 'E-posta',
        'file': 'Dosya'
    };
    return typeNames[type] || 'Bilinmeyen';
}

/**
 * Initialize navbar functionality
 */
function initializeNavbar() {
    // Determine current page
    const currentPath = window.location.pathname;
    const isHomePage = currentPath === '/';
    const isAnalyzePage = currentPath === '/analyze';
    const isDashboardPage = currentPath === '/dashboard';
    
    // Get navigation buttons
    const navHomeBtn = document.getElementById('navHomeBtn');
    const navLiveFeedBtn = document.getElementById('navLiveFeedBtn');
    const mobileHomeBtn = document.getElementById('mobileHomeBtn');
    const mobileLiveFeedBtn = document.getElementById('mobileLiveFeedBtn');
    
    // Reset visibility
    [navHomeBtn, navLiveFeedBtn, mobileHomeBtn, mobileLiveFeedBtn]
        .forEach(btn => btn && btn.classList.add('hidden'));
    
    if (isHomePage) {
        // Home page: Show Live Feed button (Guide button is always visible)
        navLiveFeedBtn && navLiveFeedBtn.classList.remove('hidden');
        mobileLiveFeedBtn && mobileLiveFeedBtn.classList.remove('hidden');
    } else {
        // Other pages: Show Home button (Guide button remains always visible)
        navHomeBtn && navHomeBtn.classList.remove('hidden');
        mobileHomeBtn && mobileHomeBtn.classList.remove('hidden');
    }
    
    // Add scroll effect to navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    console.log(`🧭 Navbar initialized for ${currentPath} - Guide button always visible`);
}

// Export global functions for compatibility
window.SecureLens = SecureLens;
window.scrollToSection = scrollToSection;
window.toggleMobileMenu = toggleMobileMenu;
window.toggleTheme = toggleTheme;
window.formatDateTime = formatDateTime;
window.formatNumber = formatNumber;
window.copyToClipboard = copyToClipboard;
window.showNotification = showNotification;
window.removeNotification = removeNotification;
window.clearAllNotifications = clearAllNotifications;
window.startAnalysis = startAnalysis; 