/**
 * Stats Module - Updated for MongoDB Atlas Integration
 * Real-time statistics loading and display
 */

/**
 * Load real-time dashboard statistics from Atlas
 */
async function loadDashboardStats() {
    try {
        const response = await fetch('/dashboard-stats');
        const result = await response.json();
        
        if (result.success && result.data) {
            const stats = result.data;
            console.log('✅ Dashboard stats loaded:', stats);
            return stats;
        } else {
            console.warn('⚠️ Dashboard stats API failed, using template values');
            return null;
        }
    } catch (error) {
        console.error('❌ Dashboard stats error:', error);
        return null;
    }
}

/**
 * Load and display basic stats (legacy support)
 */
async function loadStats() {
    const stats = {
        urlCount: document.getElementById('urlCount'),
        threatCount: document.getElementById('threatCount'),
        blockedCount: document.getElementById('blockedCount'),
        accuracyRate: document.getElementById('accuracyRate')
    };
    
    try {
        const response = await fetch('/statistics');
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            
            // Update stats with animation
            animateValue(stats.urlCount, 0, data.total_queries || 1234, 1000);
            animateValue(stats.threatCount, 0, data.high_risk || 567, 1000);
            animateValue(stats.blockedCount, 0, data.blocked || 89, 1000);
            
            // Accuracy rate with percentage
            if (stats.accuracyRate) {
                stats.accuracyRate.textContent = (data.accuracy || 99.8) + '%';
            }
            
        } else {
            // Fallback with demo data
            setDemoStats(stats);
        }
        
    } catch (error) {
        console.error('Stats loading error:', error);
        setDemoStats(stats);
    }
}

/**
 * Set demo statistics when API fails
 */
function setDemoStats(stats) {
    animateValue(stats.urlCount, 0, 1234, 1000);
    animateValue(stats.threatCount, 0, 567, 1000);
    animateValue(stats.blockedCount, 0, 89, 1000);
    if (stats.accuracyRate) {
        stats.accuracyRate.textContent = '99.8%';
    }
}

/**
 * Animate number counting
 */
function animateValue(element, start, end, duration) {
    if (!element) return;
    
    const startTime = Date.now();
    const timer = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (end - start) * easeOut);
        
        element.textContent = formatNumber(current);
        
        if (progress >= 1) {
            clearInterval(timer);
            element.textContent = formatNumber(end);
        }
    }, 16); // ~60fps
}

/**
 * Format numbers for display
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
}

/**
 * Load daily tips
 */
function loadDailyTips() {
    const tipsContainer = document.getElementById('dailyTips');
    if (!tipsContainer) return;
    
    const tips = [
        '💡 Şüpheli e-postalardaki linklere tıklamadan önce fare imlecini üzerine getirin.',
        '🔒 Güvenlik güncellemelerini her zaman resmi kaynaklardan yapın.',
        '🚨 Bilinmeyen gönderenlerden gelen ekleri açmayın.',
        '🔐 Güçlü ve benzersiz şifreler kullanın.',
        '📧 Bankalar asla e-posta ile şifre sormaz.',
        '🌐 HTTPS olmayan sitelerde kişisel bilgi girmeyin.',
        '📱 Cihazlarınızda güncel antivirus yazılımı kullanın.'
    ];
    
    // Get random tip
    const randomTip = tips[Math.floor(Math.random() * tips.length)];
    tipsContainer.innerHTML = `<p>${randomTip}</p>`;
}

/**
 * Check AI status
 */
async function checkAIStatus() {
    const statusElement = document.getElementById('aiStatus');
    if (!statusElement) return;
    
    try {
        const response = await fetch('/ai-status');
        const result = await response.json();
        
        if (result.success && result.data.ai_available) {
            statusElement.className = 'inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium';
            statusElement.innerHTML = '<div class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>AI Sistemi Aktif';
        } else {
            statusElement.className = 'inline-flex items-center px-4 py-2 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium';
            statusElement.innerHTML = '<div class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>Kural Tabanlı Aktif';
        }
    } catch (error) {
        statusElement.className = 'inline-flex items-center px-4 py-2 bg-red-100 text-red-800 rounded-full text-sm font-medium';
        statusElement.innerHTML = '<div class="w-2 h-2 bg-red-500 rounded-full mr-2"></div>Sistem Çevrimdışı';
    }
}

/**
 * Hero Stats Counter Animation - Enhanced for real data
 */
function animateCounters() {
    // Hero section counters
    const heroCounters = document.querySelectorAll('.card-number[data-count]');
    
    heroCounters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-count'));
        animateCounterValue(counter, 0, target, 2000);
    });
    
    // Analysis stats counters
    const statsCounters = document.querySelectorAll('.stats-number-compact[data-count]');
    
    statsCounters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-count'));
        animateCounterValue(counter, 0, target, 1500);
    });
}

/**
 * Animate individual counter value
 */
function animateCounterValue(element, start, end, duration) {
    if (!element || isNaN(end)) return;
    
    let current = start;
    const increment = (end - start) / (duration / 16); // 60fps
    
    // Check if element has percentage unit
    const hasPercentage = element.innerHTML.includes('%');
    const unitSpan = element.querySelector('.card-unit');
    
    const updateCounter = () => {
        if (current < end) {
            current = Math.min(current + increment, end);
            
            // Format number based on value and type
            let displayValue;
            if (end >= 1000) {
                displayValue = Math.floor(current).toLocaleString('tr-TR');
            } else if (end % 1 !== 0) {
                displayValue = current.toFixed(1);
            } else {
                displayValue = Math.floor(current).toString();
            }
            
            // Update content with unit if needed
            if (hasPercentage && unitSpan) {
                element.innerHTML = displayValue + unitSpan.outerHTML;
            } else {
                element.textContent = displayValue;
            }
            
            requestAnimationFrame(updateCounter);
        } else {
            // Final formatting
            let finalValue;
            if (end >= 1000) {
                finalValue = end.toLocaleString('tr-TR');
            } else if (end % 1 !== 0) {
                finalValue = end.toString();
            } else {
                finalValue = end.toString();
            }
            
            // Set final content with unit if needed
            if (hasPercentage && unitSpan) {
                element.innerHTML = finalValue + unitSpan.outerHTML;
            } else {
                element.textContent = finalValue;
            }
        }
    };
    
    updateCounter();
}

/**
 * Initialize hero animations when section is visible
 */
function initHeroAnimations() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Start counter animations
                setTimeout(() => {
                    animateCounters();
                }, 500);
                
                // Disconnect observer after first trigger
                observer.disconnect();
            }
        });
    }, {
        threshold: 0.3
    });
    
    observer.observe(heroSection);
}

/**
 * Initialize stats animations when section is visible
 */
function initStatsAnimations() {
    const statsSection = document.querySelector('.analysis-stats-section');
    if (!statsSection) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Start counter animations
                setTimeout(() => {
                    animateStatsCounters();
                }, 300);
                
                // Disconnect observer after first trigger
                observer.disconnect();
            }
        });
    }, {
        threshold: 0.2
    });
    
    observer.observe(statsSection);
}

/**
 * Animate stats counters with real data
 */
function animateStatsCounters() {
    const counters = document.querySelectorAll('.stats-number-compact[data-count]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count')) || 0;
        const duration = 1500;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                const increment = Math.ceil((target - current) / 20);
                current = Math.min(current + increment, target);
                counter.textContent = current.toLocaleString('tr-TR');
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toLocaleString('tr-TR');
            }
        };
        
        updateCounter();
    });
}

/**
 * Refresh dashboard statistics
 */
async function refreshDashboardStats() {
    const stats = await loadDashboardStats();
    if (stats) {
        // Update last updated time
        const lastUpdatedElement = document.querySelector('.text-gray-600');
        if (lastUpdatedElement && lastUpdatedElement.textContent.includes('Son güncelleme')) {
            lastUpdatedElement.textContent = `Son güncelleme: ${stats.last_updated}`;
        }
        
        // Re-animate counters with new data
        animateStatsCounters();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Stats.js initialized');
    
    // Load basic stats
    loadStats();
    loadDailyTips();
    checkAIStatus();
    
    // Initialize animations immediately for visible elements
    setTimeout(() => {
        console.log('🎯 Starting counter animations');
        animateCounters();
    }, 500);
    
    // Also initialize intersection observers for scroll-triggered animations
    initHeroAnimations();
    initStatsAnimations();
    
    // Auto-refresh stats every 5 minutes
    setInterval(refreshDashboardStats, 5 * 60 * 1000);
}); 