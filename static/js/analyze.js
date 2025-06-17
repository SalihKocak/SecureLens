/**
 * Analyze Page JavaScript
 * Handles analysis forms and interactions
 */

// Global variables to store last analysis data
let lastAnalysisType = null;
let lastAnalysisData = null;
let lastAnalysisResult = null; // Store the last analysis result for PDF generation

// Initialize analyze page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Analyze page initialized');
    
    // Get analysis type from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const analysisType = urlParams.get('type') || 'url';
    
    // Set initial analysis type
    setAnalysisType(analysisType);
    
    // Show/hide appropriate nav buttons
    showNavigationButtons('analyze');
    
    // Initialize event listeners
    initializeEventListeners();
});

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    console.log('🔧 Initializing event listeners...');
    
    // Analysis type buttons (all selectors including new analysis-tab)
    const typeButtons = document.querySelectorAll('.type-btn, .type-btn-enhanced, .dashboard-card[data-type], .analysis-tab');
    console.log('Found type buttons:', typeButtons.length);
    
    typeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.getAttribute('data-type');
            console.log('Type button clicked:', type);
            setAnalysisType(type);
        });
    });
    
    // Set default analysis type on page load
    setTimeout(() => {
        console.log('Setting default analysis type...');
        setAnalysisType('url');
    }, 100);
    
    console.log('✅ Event listeners initialized');
}

/**
 * Initialize file handling event listeners
 */
function initializeFileHandlers() {
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
    }
    
    if (fileUploadArea) {
        // Drag and drop handlers
        fileUploadArea.addEventListener('dragover', handleDragOver);
        fileUploadArea.addEventListener('dragleave', handleDragLeave);
        fileUploadArea.addEventListener('drop', handleFileDrop);
        
        // Click handler for file selection
        fileUploadArea.addEventListener('click', function() {
            fileInput.click();
        });
    }
}

/**
 * Handle file selection
 */
function handleFileSelection(event) {
    const files = event.target.files;
    console.log('Files selected in handleFileSelection:', files.length);
    console.log('File input element:', event.target);
    console.log('File input ID:', event.target.id);
    
    if (files.length > 0) {
        console.log('Displaying selected files...');
        displaySelectedFiles(files);
    } else {
        console.log('No files to display');
    }
}

/**
 * Handle drag over event
 */
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.add('dragover');
}

/**
 * Handle drag leave event
 */
function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
}

/**
 * Handle file drop
 */
function handleFileDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    console.log('Files dropped:', files.length);
    
    if (files.length > 0) {
        // Set files to input element
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.files = files;
        }
        displaySelectedFiles(files);
    }
}

/**
 * Display selected files
 */
function displaySelectedFiles(files) {
    const fileUploadArea = document.getElementById('fileUploadArea');
    if (!fileUploadArea) return;
    
    // Create file list display
    let fileListHTML = `
        <div class="selected-files">
            <h4 class="text-lg font-semibold text-gray-900 mb-3">
                <i class="fas fa-file-check text-green-500 mr-2"></i>
                Analiz Edilecek Dosyalar (${files.length})
            </h4>
            <div class="text-sm text-blue-600 mb-3">
                <i class="fas fa-info-circle mr-1"></i>
                Dosya adları AI sistemine gönderilecek, dosya içeriği yüklenmeyecek
            </div>
            <div class="file-list space-y-2">
    `;
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileSize = formatFileSize(file.size);
        const fileIcon = getFileIcon(file.name);
        
        fileListHTML += `
            <div class="file-item flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                <div class="flex items-center">
                    <i class="${fileIcon} text-blue-500 mr-3"></i>
                    <div>
                        <div class="font-medium text-gray-900">${file.name}</div>
                        <div class="text-sm text-gray-500">${fileSize} • ${file.type || 'Bilinmeyen tür'}</div>
                    </div>
                </div>
                <button onclick="removeFile(${i})" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }
    
    fileListHTML += `
            </div>
            <div class="mt-4 flex gap-3">
                <button onclick="document.getElementById('fileInput').click()" class="file-select-btn">
                    <i class="fas fa-plus mr-2"></i>
                    Daha Fazla Dosya Ekle
                </button>
                <button onclick="clearFileSelection()" class="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors">
                    <i class="fas fa-trash mr-2"></i>
                    Temizle
                </button>
            </div>
        </div>
    `;
    
    fileUploadArea.innerHTML = fileListHTML;
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get file icon based on extension
 */
function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    const iconMap = {
        'pdf': 'fas fa-file-pdf',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'xls': 'fas fa-file-excel',
        'xlsx': 'fas fa-file-excel',
        'ppt': 'fas fa-file-powerpoint',
        'pptx': 'fas fa-file-powerpoint',
        'txt': 'fas fa-file-alt',
        'zip': 'fas fa-file-archive',
        'rar': 'fas fa-file-archive',
        '7z': 'fas fa-file-archive',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'png': 'fas fa-file-image',
        'gif': 'fas fa-file-image',
        'mp4': 'fas fa-file-video',
        'avi': 'fas fa-file-video',
        'mp3': 'fas fa-file-audio',
        'wav': 'fas fa-file-audio',
        'exe': 'fas fa-file-code',
        'msi': 'fas fa-file-code'
    };
    
    return iconMap[extension] || 'fas fa-file';
}

/**
 * Remove file from selection
 */
function removeFile(index) {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files) return;
    
    // Create new FileList without the removed file
    const dt = new DataTransfer();
    const files = Array.from(fileInput.files);
    
    files.forEach((file, i) => {
        if (i !== index) {
            dt.items.add(file);
        }
    });
    
    fileInput.files = dt.files;
    
    if (fileInput.files.length > 0) {
        displaySelectedFiles(fileInput.files);
    } else {
        clearFileSelection();
    }
}

/**
 * Clear file selection
 */
function clearFileSelection() {
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');
    
    if (fileInput) {
        fileInput.value = '';
    }
    
    if (fileUploadArea) {
        fileUploadArea.innerHTML = `
            <div class="file-upload-content">
                <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
                <p class="text-lg font-medium text-gray-700 mb-2">Dosyayı sürükleyin veya seçin</p>
                <p class="text-sm text-gray-500 mb-4">Maksimum dosya boyutu: 50MB</p>
                <button type="button" class="file-select-btn" onclick="document.getElementById('fileInput').click()">
                    Dosya Seç
                </button>
            </div>
        `;
    }
}

/**
 * Set analysis type and update UI
 */
function setAnalysisType(type) {
    console.log(`🔄 Setting analysis type: ${type}`);
    
    // Clear previous results when switching analysis type
    clearResults();
    
    // Update type buttons - Include all button types including analysis-tab
    const typeButtons = document.querySelectorAll('.type-btn, .type-btn-enhanced, .dashboard-card[data-type], .analysis-tab');
    console.log('Updating type buttons:', typeButtons.length);
    
    typeButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-type') === type) {
            btn.classList.add('active');
            console.log(`✅ Activated button: ${type}`);
        }
    });
    
    // Update forms
    const forms = document.querySelectorAll('.analysis-form');
    console.log('Found forms:', forms.length);
    
    forms.forEach(form => {
        form.classList.remove('active');
    });
    
    const activeFormId = type + 'Form';
    const activeForm = document.getElementById(activeFormId);
    console.log(`Looking for form: ${activeFormId}`, activeForm);
    
    if (activeForm) {
        activeForm.classList.add('active');
        console.log(`✅ Activated form: ${activeFormId}`);
    } else {
        console.error(`❌ Form not found: ${activeFormId}`);
    }
    
    // Update page header
    updatePageHeader(type);
    
    console.log(`✅ Analysis type set to: ${type}`);
}

/**
 * Update page header based on analysis type
 */
function updatePageHeader(type) {
    const typeConfig = {
        url: {
            title: 'SecureLens <span class="text-cyan-300">URL Güvenlik Analizi</span>',
            description: 'Web sitelerinin güvenlik durumunu AI ile analiz edin',
            icon: 'fas fa-globe'
        },
        email: {
            title: 'SecureLens <span class="text-cyan-300">E-posta Güvenlik Analizi</span>', 
            description: 'E-posta içeriğini spam ve phishing açısından kontrol edin',
            icon: 'fas fa-envelope'
        },
        file: {
            title: 'SecureLens <span class="text-cyan-300">Dosya Güvenlik Analizi</span>',
            description: 'Dosyalarınızı malware ve virüs açısından tarayın',
            icon: 'fas fa-file-shield'
        }
    };
    
    const config = typeConfig[type] || typeConfig.url;
    
    // Update title
    const titleElement = document.getElementById('analysisTypeTitle');
    if (titleElement) {
        titleElement.innerHTML = config.title;
    }
    
    // Update description
    const descElement = document.getElementById('analysisTypeDescription');
    if (descElement) {
        descElement.textContent = config.description;
    }
    
    // Update icon
    const iconElement = document.getElementById('analysisTypeIcon');
    if (iconElement) {
        iconElement.innerHTML = `<i class="${config.icon}"></i>`;
    }
}

/**
 * Perform analysis based on type
 */
function performAnalysis(type, event) {
    console.log('=== ANALYSIS START ===');
    console.log('Type:', type);
    console.log('Event:', event);
    
    // Prevent form submission if called from form
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log(`Performing ${type} analysis...`);
    
    // Get input data
    const inputData = getInputData(type);
    console.log('Input data received:', inputData);
    console.log('Input data type:', typeof inputData);
    console.log('Input data length:', inputData ? inputData.length : 'null');
    
    // Check input data based on type
    if (type === 'file') {
        if (!inputData || !inputData.fileName || inputData.fileName.trim() === '') {
            console.error('No file name provided');
            showNotification('Lütfen dosya adını girin', 'warning');
            return false;
        }
    } else if (type === 'email') {
        if (!inputData || !inputData.emailContent || inputData.emailContent.trim() === '') {
            console.error('No email content provided');
            showNotification('Lütfen e-posta içeriğini girin', 'warning');
            return false;
        }
    } else {
        if (!inputData || inputData.trim() === '') {
            console.error('No input data found or empty string');
            showNotification('Lütfen analiz edilecek veriyi girin', 'warning');
            return false;
        }
    }
    
    // Store last analysis data for refresh functionality
    lastAnalysisType = type;
    
    // Store analysis data
    lastAnalysisData = inputData;
    console.log('Stored last analysis data:', { type, inputData });
    
    // Show loading state
    console.log('Showing loading state...');
    showAnalysisLoading(type);
    
    // Perform real analysis
    console.log('Starting real analysis...');
    performRealAnalysis(type, inputData);
    
    return false; // Prevent any form submission
}

/**
 * Perform real analysis with API call
 */
async function performRealAnalysis(type, inputData) {
    try {
        let apiEndpoint = '';
        let requestData = {};
        
        console.log(`Starting ${type} analysis with data:`, inputData);
        
        // Prepare API request based on type
        switch(type) {
            case 'url':
                apiEndpoint = '/analyze-url';
                requestData = { url: inputData };
                break;
                
            case 'email':
                apiEndpoint = '/analyze-email';
                requestData = { 
                    email_text: inputData.emailContent,
                    sender_email: inputData.emailSender || '',
                    subject: inputData.emailSubject || ''
                };
                break;
                
            case 'file':
                // For file analysis, we'll send file data as JSON
                apiEndpoint = '/analyze-file';
                requestData = { 
                    filename: inputData.fileName,
                    file_content: inputData.fileContent || ''
                };
                break;
                
            default:
                console.error('Unknown analysis type:', type);
                showAnalysisError('Bilinmeyen analiz türü');
                return;
        }
        
        // For URL and Email analysis
        console.log(`Making request to ${apiEndpoint} with data:`, requestData);
        
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Response status:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Analysis result:', result);
        
        if (result.success) {
            showResults(result);
        } else {
            throw new Error(result.error || 'Analiz başarısız');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        showAnalysisError(error.message || 'Bilinmeyen hata oluştu');
    }
}

/**
 * Show analysis loading state
 */
function showAnalysisLoading(type) {
    const resultsContainer = document.getElementById('analysisResults');
    const resultsContent = document.getElementById('resultsContent');
    
    if (resultsContainer && resultsContent) {
        resultsContainer.style.display = 'block';
        resultsContent.innerHTML = `
            <div class="analysis-loading">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                </div>
                <h4 class="text-lg font-semibold text-gray-900 mb-2">Analiz Yapılıyor...</h4>
                <p class="text-sm text-gray-600 mb-4">AI modelleri ${getAnalysisTypeName(type)} verilerini inceliyor</p>
                <div class="analysis-steps">
                    <div class="step active">
                        <i class="fas fa-search"></i>
                        <span>Veri İnceleme</span>
                    </div>
                    <div class="step">
                        <i class="fas fa-brain"></i>
                        <span>AI Analizi</span>
                    </div>
                    <div class="step">
                        <i class="fas fa-shield-alt"></i>
                        <span>Güvenlik Değerlendirmesi</span>
                    </div>
                </div>
            </div>
        `;
        
        // Animate steps
        setTimeout(() => {
            const steps = resultsContent.querySelectorAll('.step');
            if (steps[1]) steps[1].classList.add('active');
        }, 1000);
        
        setTimeout(() => {
            const steps = resultsContent.querySelectorAll('.step');
            if (steps[2]) steps[2].classList.add('active');
        }, 2000);
    }
    
    showNotification(`${getAnalysisTypeName(type)} analizi başlatıldı`, 'info', 2000);
}

/**
 * Show analysis results
 */
function showResults(result) {
    console.log('showResults called with:', result);
    
    const resultsContainer = document.getElementById('analysisResults');
    const resultsContent = document.getElementById('resultsContent');
    
    if (!resultsContainer || !resultsContent) {
        console.error('Results container not found');
        showNotification('Sonuç alanı bulunamadı', 'error');
        return;
    }
    
    // Check if result has success property
    if (result.success === false) {
        console.error('API returned error:', result.error);
        showAnalysisError(result.error || 'API hatası');
        return;
    }
    
    // Extract data from API response safely
    const data = result.data || result;
    console.log('Extracted data:', data);
    
    // Safe data extraction with defaults
    const riskScore = data.risk_score !== undefined ? data.risk_score : 0;
    const riskLevel = data.risk_level || 'Bilinmeyen';
    const analysisMethod = data.analysis_method || 'Hibrit Analiz';
    const threats = data.threats || data.warnings || [];
    const recommendations = data.recommendations || [];
    
    // Store the result for PDF generation
    lastAnalysisResult = {
        riskScore: riskScore,
        riskLevel: riskLevel,
        analysisMethod: analysisMethod,
        threats: threats,
        recommendations: recommendations,
        timestamp: new Date(),
        analysisType: getCurrentAnalysisType(),
        analysisTitle: getAnalysisTitle()
    };
    
    console.log('Processed data:', { riskScore, riskLevel, analysisMethod, threats, recommendations });
    
    try {
        // Scroll to results area smoothly
        setTimeout(() => {
            resultsContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 300);
        
        resultsContent.innerHTML = `
            <div class="analysis-results-container">
                <div class="analysis-result-modern">
                
                <!-- Modern Results Header -->
                <div class="results-header-modern">
                    <div class="results-header-content">
                        <div class="results-title-section">
                            <div class="results-icon ${getRiskClass(riskLevel)}">
                                <i class="fas ${getRiskIcon(riskLevel)}"></i>
                            </div>
                            <div class="results-title-info">
                                <h3 class="results-main-title">${getAnalysisTitle()} Analizi Tamamlandı</h3>
                                <p class="results-subtitle">
                                    <i class="fas fa-clock mr-2"></i>
                                    ${new Date().toLocaleString('tr-TR')} • ${analysisMethod}
                                </p>
                            </div>
                        </div>
                        
                        <!-- Central Risk Score -->
                        <div class="central-risk-score ${getRiskClass(riskLevel)}">
                            <div class="risk-score-value">${riskScore}</div>
                            <div class="risk-score-label">Risk Skoru</div>
                            <div class="risk-level-badge ${getRiskClass(riskLevel)}">${riskLevel}</div>
                        </div>
                    </div>
                    
                    <!-- Quick Stats Bar -->
                    <div class="quick-stats-bar">
                        <div class="stat-item">
                            <div class="stat-icon stat-icon-blue">
                                <i class="fas fa-brain"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-label">AI Modeli</div>
                                <div class="stat-value">Hibrit Sistem</div>
                            </div>
                        </div>
                        <div class="stat-divider"></div>
                        <div class="stat-item">
                            <div class="stat-icon ${threats.length > 0 ? 'stat-icon-red' : 'stat-icon-green'}">
                                <i class="fas ${threats.length > 0 ? 'fa-shield-alt' : 'fa-check-shield'}"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-label">Tehdit Sayısı</div>
                                <div class="stat-value">${threats.length} ${threats.length === 1 ? 'Adet' : 'Adet'}</div>
                            </div>
                        </div>
                        <div class="stat-divider"></div>
                        <div class="stat-item">
                            <div class="stat-icon ${recommendations.length > 0 ? 'stat-icon-yellow' : 'stat-icon-gray'}">
                                <i class="fas fa-lightbulb"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-label">Öneri Sayısı</div>
                                <div class="stat-value">${recommendations.length} ${recommendations.length === 1 ? 'Adet' : 'Adet'}</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Main Content Cards -->
                <div class="results-content-modern">
                
                    ${threats && threats.length > 0 ? `
                        <!-- Threats Section -->
                        <div class="content-card threats-card">
                            <div class="card-header-modern card-header-danger">
                                <div class="card-header-left">
                                    <div class="card-icon-modern card-icon-danger">
                                        <i class="fas fa-exclamation-triangle"></i>
                                    </div>
                                    <div class="card-title-modern">
                                        <h4>Güvenlik Tehditleri</h4>
                                        <p>${threats.length} adet tehdit tespit edildi</p>
                                    </div>
                                </div>
                                <div class="threat-severity-badge">
                                    <i class="fas fa-shield-alt"></i>
                                    <span>Yüksek Risk</span>
                                </div>
                            </div>
                            <div class="card-content-modern">
                                ${threats.map((threat, index) => `
                                    <div class="modern-list-item threat-item">
                                        <div class="item-number">${String(index + 1).padStart(2, '0')}</div>
                                        <div class="item-content">
                                            <div class="item-text">${threat}</div>
                                        </div>
                                        <div class="item-indicator danger-indicator">
                                            <i class="fas fa-exclamation-circle"></i>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : `
                        <!-- No Threats Section -->
                        <div class="content-card success-card">
                            <div class="card-header-modern card-header-success">
                                <div class="card-header-left">
                                    <div class="card-icon-modern card-icon-success">
                                        <i class="fas fa-check-shield"></i>
                                    </div>
                                    <div class="card-title-modern">
                                        <h4>Güvenlik Durumu</h4>
                                        <p>Hiçbir tehdit tespit edilmedi</p>
                                    </div>
                                </div>
                                <div class="success-severity-badge">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Güvenli</span>
                                </div>
                            </div>
                            <div class="card-content-modern success-content">
                                <div class="success-message">
                                    <div class="success-icon">
                                        <i class="fas fa-shield-check"></i>
                                    </div>
                                    <div class="success-text">
                                        <h5>Analiz Başarılı</h5>
                                        <p>İncelenen içerik güvenlik açısından herhangi bir risk teşkil etmiyor. Tüm kontroller başarıyla geçildi.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `}
                
                    ${recommendations && recommendations.length > 0 ? `
                        <!-- Recommendations Section -->
                        <div class="content-card recommendations-card">
                            <div class="card-header-modern card-header-info">
                                <div class="card-header-left">
                                    <div class="card-icon-modern card-icon-info">
                                        <i class="fas fa-lightbulb"></i>
                                    </div>
                                    <div class="card-title-modern">
                                        <h4>Güvenlik Önerileri</h4>
                                        <p>${recommendations.length} adet iyileştirme önerisi</p>
                                    </div>
                                </div>
                                <div class="info-severity-badge">
                                    <i class="fas fa-info-circle"></i>
                                    <span>Öneri</span>
                                </div>
                            </div>
                            <div class="card-content-modern">
                                ${recommendations.map((rec, index) => `
                                    <div class="modern-list-item recommendation-item">
                                        <div class="item-number">${String(index + 1).padStart(2, '0')}</div>
                                        <div class="item-content">
                                            <div class="item-text">${rec}</div>
                                        </div>
                                        <div class="item-indicator info-indicator">
                                            <i class="fas fa-lightbulb"></i>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                
                    <!-- Modern Action Bar -->
                    <div class="modern-action-bar">
                        <div class="action-buttons-group">
                            <button onclick="refreshAnalysis()" class="modern-action-btn primary-btn">
                                <div class="btn-icon">
                                    <i class="fas fa-redo"></i>
                                </div>
                                <div class="btn-content">
                                    <div class="btn-title">Yeniden Analiz</div>
                                    <div class="btn-subtitle">Tekrar kontrol et</div>
                                </div>
                            </button>
                            
                            <button onclick="downloadReport()" class="modern-action-btn success-btn">
                                <div class="btn-icon">
                                    <i class="fas fa-download"></i>
                                </div>
                                <div class="btn-content">
                                    <div class="btn-title">Rapor İndir</div>
                                    <div class="btn-subtitle">PDF formatında</div>
                                </div>
                            </button>
                            
                            <button onclick="clearResults()" class="modern-action-btn secondary-btn">
                                <div class="btn-icon">
                                    <i class="fas fa-broom"></i>
                                </div>
                                <div class="btn-content">
                                    <div class="btn-title">Temizle</div>
                                    <div class="btn-subtitle">Sonuçları sil</div>
                                </div>
                            </button>
                            
                            <a href="/analyze" class="modern-action-btn info-btn">
                                <div class="btn-icon">
                                    <i class="fas fa-plus"></i>
                                </div>
                                <div class="btn-content">
                                    <div class="btn-title">Yeni Analiz</div>
                                    <div class="btn-subtitle">Baştan başla</div>
                                </div>
                            </a>
                        </div>
                        
                        <!-- Analysis Info Footer -->
                        <div class="analysis-info-footer">
                            <div class="ai-badge">
                                <div class="ai-badge-icon">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="ai-badge-text">
                                    <div class="ai-badge-title">SecureLens AI</div>
                                    <div class="ai-badge-subtitle">Hibrit Güvenlik Sistemi</div>
                                </div>
                            </div>
                            <div class="analysis-timestamp">
                                <i class="fas fa-clock"></i>
                                <span>Analiz: ${new Date().toLocaleString('tr-TR')}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            </div>
        `;
        
        resultsContainer.style.display = 'block';
        showNotification('Analiz tamamlandı!', 'success');
        
    } catch (error) {
        console.error('Error rendering results:', error);
        showAnalysisError('Sonuçları gösterirken hata oluştu: ' + error.message);
    }
}

/**
 * Show analysis error
 */
function showAnalysisError(errorMessage) {
    const resultsContent = document.getElementById('resultsContent');
    if (!resultsContent) return;
    
    resultsContent.innerHTML = `
        <div class="analysis-error">
            <div class="error-icon mb-4">
                <i class="fas fa-exclamation-triangle text-red-500 text-3xl"></i>
            </div>
            <h4 class="text-lg font-semibold text-gray-900 mb-2">Analiz Hatası</h4>
            <p class="text-sm text-gray-600 mb-4">${errorMessage}</p>
            <button onclick="location.reload()" class="retry-btn">
                <i class="fas fa-redo mr-2"></i>
                Tekrar Dene
            </button>
        </div>
    `;
    
    showNotification('Analiz sırasında hata oluştu', 'error');
}

/**
 * Get input data based on analysis type
 */
function getInputData(type) {
    console.log(`Getting input data for type: ${type}`);
    
    switch(type) {
        case 'url':
            const urlInput = document.getElementById('urlInput');
            const urlValue = urlInput ? urlInput.value.trim() : null;
            console.log(`URL input value: "${urlValue}"`);
            return urlValue;
            
        case 'email':
            const emailInput = document.getElementById('emailInput');
            const emailSenderInput = document.getElementById('emailSenderInput');
            const emailSubjectInput = document.getElementById('emailSubjectInput');
            
            console.log('Email input elements:', { emailInput, emailSenderInput, emailSubjectInput });
            
            const emailContent = emailInput ? emailInput.value.trim() : '';
            const emailSender = emailSenderInput ? emailSenderInput.value.trim() : '';
            const emailSubject = emailSubjectInput ? emailSubjectInput.value.trim() : '';
            
            console.log('Email data:', {
                contentLength: emailContent.length,
                sender: emailSender,
                subject: emailSubject
            });
            
            if (!emailContent) {
                console.log('No email content provided');
                return null;
            }
            
            const emailResult = {
                emailContent: emailContent,
                emailSender: emailSender,
                emailSubject: emailSubject
            };
            
            console.log('Returning email data:', emailResult);
            return emailResult;
            
        case 'file':
            const fileNameInput = document.getElementById('fileNameInput');
            const fileContentInput = document.getElementById('fileContentInput');
            
            console.log('File name input element:', fileNameInput);
            console.log('File content input element:', fileContentInput);
            
            const fileName = fileNameInput ? fileNameInput.value.trim() : '';
            const fileContent = fileContentInput ? fileContentInput.value.trim() : '';
            
            console.log('File name:', fileName);
            console.log('File content length:', fileContent.length);
            
            if (!fileName) {
                console.log('No file name provided');
                return null;
            }
            
            const fileResult = {
                fileName: fileName,
                fileContent: fileContent
            };
            
            console.log('Returning file data:', fileResult);
            return fileResult;
            
        default:
            console.log(`Unknown analysis type: ${type}`);
            return null;
    }
}

/**
 * Get analysis type name in Turkish
 */
function getAnalysisTypeName(type) {
    const typeNames = {
        'url': 'URL',
        'email': 'E-posta', 
        'file': 'Dosya'
    };
    return typeNames[type] || 'Bilinmeyen';
}

/**
 * Get analysis method name in Turkish
 */
function getAnalysisMethodName(method) {
    const methodNames = {
        'rule_based': 'Kural Tabanlı',
        'ai_model': 'AI Model',
        'hybrid': 'Hibrit (Kural + AI)',
        'api_service': 'Harici API',
        'error': 'Hata'
    };
    return methodNames[method] || 'Bilinmeyen';
}

/**
 * Download analysis report as PDF
 */
async function downloadReport() {
    console.log('📄 Starting PDF report generation...');
    
    try {
        // Check if we have analysis results
        const resultsContainer = document.getElementById('analysisResults');
        if (!resultsContainer || resultsContainer.style.display === 'none') {
            showNotification('İndirilecek analiz sonucu bulunamadı', 'warning');
            return;
        }

        // Show loading notification
        showNotification('PDF raporu oluşturuluyor...', 'info', 3000);
        
        // Debug: Show what data we have
        console.log('lastAnalysisResult:', lastAnalysisResult);
        if (lastAnalysisResult) {
            console.log('Risk Score değeri:', lastAnalysisResult.riskScore);
            console.log('Risk Level değeri:', lastAnalysisResult.riskLevel);
        }

        // Get the results content
        const resultsContent = document.getElementById('resultsContent');
        if (!resultsContent) {
            showNotification('Rapor içeriği bulunamadı', 'error');
            return;
        }

        // Create a temporary container for PDF generation
        const tempContainer = document.createElement('div');
        tempContainer.style.position = 'absolute';
        tempContainer.style.left = '-9999px';
        tempContainer.style.top = '0';
        tempContainer.style.width = '800px'; // Fixed width for better compatibility
        tempContainer.style.backgroundColor = 'white';
        tempContainer.style.padding = '40px';
        tempContainer.style.fontFamily = 'Arial, sans-serif';
        tempContainer.style.fontSize = '14px';
        tempContainer.style.lineHeight = '1.6';
        document.body.appendChild(tempContainer);

        // Create PDF content
        const pdfContent = createPDFContent();
        console.log('Oluşturulan PDF içeriği:', pdfContent);
        tempContainer.innerHTML = pdfContent;
        
        // Debug: Check if content was added
        console.log('Temp container içeriği:', tempContainer.innerHTML.length, 'karakter');

        // Generate PDF using html2canvas and jsPDF
        const canvas = await html2canvas(tempContainer, {
            scale: 1.5,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: tempContainer.offsetWidth,
            height: tempContainer.offsetHeight,
            logging: false,
            removeContainer: true,
            foreignObjectRendering: false
        });

        // Remove temporary container
        document.body.removeChild(tempContainer);

        // Create PDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 297; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;
        let position = 0;

        // Add first page
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;

        // Add additional pages if needed
        while (heightLeft >= 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
        }

        // Generate filename with timestamp
        const now = new Date();
        const timestamp = now.toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_');
        const analysisType = getCurrentAnalysisType();
        const filename = `SecureLens_${getAnalysisTypeName(analysisType)}_Raporu_${timestamp}.pdf`;

        // Download the PDF
        pdf.save(filename);

        showNotification('PDF raporu başarıyla indirildi', 'success');
        console.log('✅ PDF report generated successfully');

    } catch (error) {
        console.error('Error generating PDF report:', error);
        showNotification('PDF raporu oluşturulurken hata oluştu: ' + error.message, 'error');
    }
}

/**
 * Create PDF content from analysis results
 */
function createPDFContent() {
    // Check if we have stored analysis result
    if (!lastAnalysisResult) {
        return '<div style="color: #ef4444; font-size: 16px; padding: 20px;">PDF oluşturmak için analiz sonucu bulunamadı. Lütfen önce bir analiz yapın.</div>';
    }

    const result = lastAnalysisResult;
    console.log('PDF oluşturuluyor, analiz sonucu:', result);
    
    const reportDate = result.timestamp.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    // Debug: Check if risk score exists and is valid
    console.log('Risk Score:', result.riskScore, 'Type:', typeof result.riskScore);
    console.log('Risk Level:', result.riskLevel);
    
    // Ensure we have a valid risk score
    let displayRiskScore = result.riskScore;
    if (displayRiskScore === undefined || displayRiskScore === null || displayRiskScore === '') {
        displayRiskScore = '0';
    }
    
    // Convert to string to ensure display
    displayRiskScore = String(displayRiskScore);

    // Get risk color
    const riskClass = getRiskClass(result.riskLevel);
    let riskColor = '#6b7280';
    if (riskClass === 'risk-high') riskColor = '#ef4444';
    else if (riskClass === 'risk-medium') riskColor = '#f59e0b';
    else if (riskClass === 'risk-low') riskColor = '#10b981';

    // Create PDF header - Using simple HTML structure
    let pdfHTML = `
        <div style="font-family: Arial, sans-serif; width: 100%; max-width: 800px; margin: 0 auto; color: #333;">
            <!-- Header Section -->
            <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #3b82f6;">
                <h1 style="margin: 0 0 10px 0; font-size: 32px; color: #1f2937;">SecureLens</h1>
                <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 16px;">Hybrid AI Security Platform</p>
                <h2 style="margin: 0 0 10px 0; font-size: 24px; color: #374151;">${result.analysisTitle}</h2>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">Rapor Tarihi: ${reportDate}</p>
            </div>
    `;

        // Add analysis summary - Ultra Simple Version
    pdfHTML += `
            <!-- Risk Score Section -->
            <table style="width: 100%; margin-bottom: 30px; border-collapse: collapse;">
                <tr>
                    <td style="text-align: center; padding: 30px; background: #f8f9fa; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 25px 0; font-size: 22px; color: #333;">ANALIZ ÖZETİ</h3>
                        
                        <!-- Risk Score Box -->
                        <table style="margin: 0 auto 25px auto; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 40px; background: white; border: 4px solid ${riskColor}; text-align: center;">
                                    <div style="font-size: 72px; font-weight: bold; color: ${riskColor}; margin-bottom: 10px;">
                                        ${displayRiskScore}
                                    </div>
                                    <div style="font-size: 16px; color: #666; margin-bottom: 15px;">
                                        Risk Skoru (0-100)
                                    </div>
                                    <div style="font-size: 24px; color: ${riskColor}; font-weight: bold;">
                                        ${result.riskLevel || 'Bilinmeyen'}
                                    </div>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Stats -->
                        <div style="text-align: left; margin: 0 auto; max-width: 400px;">
                            <p style="margin-bottom: 12px; font-size: 16px;">
                                <strong>Analiz Yöntemi:</strong> ${result.analysisMethod}
                            </p>
                            <p style="margin-bottom: 12px; font-size: 16px;">
                                <strong>Tespit Edilen Tehdit:</strong> ${result.threats.length} Adet
                            </p>
                            <p style="margin-bottom: 12px; font-size: 16px;">
                                <strong>Güvenlik Önerisi:</strong> ${result.recommendations.length} Adet
                            </p>
                        </div>
                    </td>
                </tr>
            </table>
    `;

         // Add threats section if any
     if (result.threats && result.threats.length > 0) {
         pdfHTML += `
             <!-- Threats Section -->
             <div style="margin-bottom: 30px; padding: 20px; background: #fff5f5; border: 1px solid #ef4444;">
                 <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #ef4444; text-align: center;">
                     ⚠️ Tespit Edilen Güvenlik Tehditleri (${result.threats.length} Adet)
                 </h3>
         `;
         
         result.threats.forEach((threat, index) => {
             pdfHTML += `
                 <div style="margin-bottom: 15px; padding: 15px; background: white; border-left: 4px solid #ef4444;">
                     <strong>${index + 1}.</strong> ${threat}
                 </div>
             `;
         });
         
         pdfHTML += `
             </div>
         `;
         } else {
         pdfHTML += `
             <!-- Safe Status Section -->
             <div style="margin-bottom: 30px; padding: 20px; background: #f0fff4; border: 1px solid #10b981; text-align: center;">
                 <h3 style="margin: 0 0 15px 0; font-size: 18px; color: #10b981;">
                     ✅ Güvenlik Durumu
                 </h3>
                 <div style="padding: 15px; background: white;">
                     <p style="margin: 0 0 10px 0; font-size: 16px; font-weight: bold; color: #10b981;">
                         🛡️ Analiz Başarılı
                     </p>
                     <p style="margin: 0; color: #374151;">
                         İncelenen içerik güvenlik açısından herhangi bir risk teşkil etmiyor.
                     </p>
                 </div>
             </div>
         `;
    }

         // Add recommendations section if any
     if (result.recommendations && result.recommendations.length > 0) {
         pdfHTML += `
             <!-- Recommendations Section -->
             <div style="margin-bottom: 30px; padding: 20px; background: #eff6ff; border: 1px solid #3b82f6;">
                 <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #3b82f6; text-align: center;">
                     💡 Güvenlik Önerileri (${result.recommendations.length} Adet)
                 </h3>
         `;
         
         result.recommendations.forEach((rec, index) => {
             pdfHTML += `
                 <div style="margin-bottom: 15px; padding: 15px; background: white; border-left: 4px solid #3b82f6;">
                     <strong>${index + 1}.</strong> ${rec}
                 </div>
             `;
         });
         
         pdfHTML += `
             </div>
         `;
    }

         // Add footer
     const now = new Date();
     pdfHTML += `
             <!-- Footer -->
             <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; text-align: center; color: #666; font-size: 12px;">
                 <p style="margin: 0 0 5px 0;">Bu rapor SecureLens Hybrid AI Security Platform tarafından otomatik olarak oluşturulmuştur.</p>
                 <p style="margin: 0;">© ${now.getFullYear()} SecureLens - Tüm hakları saklıdır.</p>
             </div>
         </div>
     `;

    return pdfHTML;
}

/**
 * Clear analysis results and inputs
 */
function clearResults() {
    console.log('🧹 Clearing results and inputs...');
    
    // Clear results display
    const resultsContainer = document.getElementById('analysisResults');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
        const resultsContent = document.getElementById('resultsContent');
        if (resultsContent) {
            resultsContent.innerHTML = '';
        }
    }
    
    // Clear all input fields
    const urlInput = document.getElementById('urlInput');
    const emailInput = document.getElementById('emailInput');
    const fileInput = document.getElementById('fileInput');
    
    if (urlInput) urlInput.value = '';
    if (emailInput) emailInput.value = '';
    if (fileInput) {
        fileInput.value = '';
        // Also clear file upload area display
        clearFileSelection();
    }
    
    // Clear stored analysis data
    lastAnalysisType = null;
    lastAnalysisData = null;
    lastAnalysisResult = null;
    
    // Show notification
    showNotification('Tüm veriler temizlendi', 'success');
    
    console.log('✅ Results and inputs cleared');
}

/**
 * Refresh analysis - repeat last analysis with same data
 */
function refreshAnalysis() {
    console.log('🔄 Refreshing analysis...');
    
    // Check if we have last analysis data
    if (!lastAnalysisType || !lastAnalysisData) {
        showNotification('Tekrar analiz edilecek veri bulunamadı', 'warning');
        console.log('No last analysis data found');
        return;
    }
    
    console.log('Repeating last analysis:', { type: lastAnalysisType, data: lastAnalysisData });
    
    // For file analysis, we need to check if we can still access the files
    if (lastAnalysisType === 'file') {
        // Check if the stored data is still valid
        if (!lastAnalysisData || lastAnalysisData.length === 0) {
            showNotification('Dosya verileri artık mevcut değil. Lütfen dosyaları tekrar seçin.', 'warning');
            return;
        }
        
        // Try to access the first file to check if file data is still valid
        try {
            const firstFileInfo = lastAnalysisData[0];
            const firstFile = firstFileInfo.file || firstFileInfo;
            if (!firstFile || !firstFile.name) {
                throw new Error('File data is no longer accessible');
            }
            // Try to access file properties to ensure it's still valid
            const testSize = firstFile.size;
        } catch (error) {
            console.log('File data is no longer accessible:', error);
            showNotification('Dosya verileri artık erişilebilir değil. Lütfen dosyaları tekrar seçin.', 'warning');
            return;
        }
    }
    
    // Show notification about what's being re-analyzed
    const analysisTypeName = getAnalysisTypeName(lastAnalysisType);
            showNotification(`${analysisTypeName} analizi tekrarlanıyor...`, 'info', 2000);
    
    // Show loading state
    showAnalysisLoading(lastAnalysisType);
    
    // Perform the analysis again with the same data
    try {
        performRealAnalysis(lastAnalysisType, lastAnalysisData);
    } catch (error) {
        console.error('Error during refresh analysis:', error);
        showAnalysisError('Analiz tekrarlanırken hata oluştu: ' + error.message);
    }
    
    console.log('✅ Analysis refresh started');
}

/**
 * Get current analysis type from URL parameter or active form
 */
function getCurrentAnalysisType() {
    // First check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const typeFromUrl = urlParams.get('type');
    if (typeFromUrl && ['url', 'email', 'file'].includes(typeFromUrl)) {
        return typeFromUrl;
    }
    
    // Check which form is active
    const activeForm = document.querySelector('.analysis-form.active');
    if (activeForm) {
        if (activeForm.id === 'urlForm') return 'url';
        if (activeForm.id === 'emailForm') return 'email';
        if (activeForm.id === 'fileForm') return 'file';
    }
    
    // Default to url
    return 'url';
}

/**
 * Get analysis title based on current type
 */
function getAnalysisTitle() {
    const type = getCurrentAnalysisType();
    const titles = {
        'url': 'URL Güvenlik Analizi',
        'email': 'E-posta Güvenlik Analizi',
        'file': 'Dosya Güvenlik Analizi'
    };
    return titles[type] || 'Güvenlik Analizi';
}

/**
 * Get CSS class for risk level
 */
function getRiskClass(riskLevel) {
    const riskLower = (riskLevel || '').toLowerCase();
    
    if (riskLower.includes('yüksek') || riskLower.includes('high') || riskLower.includes('tehlikeli')) {
        return 'risk-high';
    } else if (riskLower.includes('orta') || riskLower.includes('medium') || riskLower.includes('şüpheli')) {
        return 'risk-medium';
    } else if (riskLower.includes('düşük') || riskLower.includes('low') || riskLower.includes('güvenli')) {
        return 'risk-low';
    } else {
        return 'risk-unknown';
    }
}

/**
 * Get icon for risk level
 */
function getRiskIcon(riskLevel) {
    const riskLower = (riskLevel || '').toLowerCase();
    
    if (riskLower.includes('yüksek') || riskLower.includes('high') || riskLower.includes('tehlikeli')) {
        return 'fa-exclamation-triangle';
    } else if (riskLower.includes('orta') || riskLower.includes('medium') || riskLower.includes('şüpheli')) {
        return 'fa-exclamation-circle';
    } else if (riskLower.includes('düşük') || riskLower.includes('low') || riskLower.includes('güvenli')) {
        return 'fa-check-circle';
    } else {
        return 'fa-question-circle';
    }
}

/**
 * Test function for debugging
 */
function testAnalysis() {
    console.log('Testing analysis...');
    
    // Test URL analysis
    fetch('/analyze-url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: 'https://google.com' })
    })
    .then(response => {
        console.log('Test response status:', response.status);
        return response.json();
    })
    .then(result => {
        console.log('Test result:', result);
        if (result.success) {
            showResults(result);
        } else {
            console.error('Test failed:', result.error);
        }
    })
    .catch(error => {
        console.error('Test error:', error);
    });
}

/**
 * Navigation functions
 */
function showNavigationButtons(currentPage) {
    const homeBtn = document.getElementById('navHomeBtn');
    const analyzeBtn = document.getElementById('navAnalyzeBtn');
    const dashboardBtn = document.getElementById('navDashboardBtn');
    
    const mobileHomeBtn = document.getElementById('mobileHomeBtn');
    const mobileAnalyzeBtn = document.getElementById('mobileAnalyzeBtn');
    const mobileDashboardBtn = document.getElementById('mobileDashboardBtn');
    
    // Hide all dynamic buttons first
    if (homeBtn) homeBtn.classList.add('hidden');
    if (analyzeBtn) analyzeBtn.classList.add('hidden');
    if (dashboardBtn) dashboardBtn.classList.add('hidden');
    
    if (mobileHomeBtn) mobileHomeBtn.classList.add('hidden');
    if (mobileAnalyzeBtn) mobileAnalyzeBtn.classList.add('hidden');
    if (mobileDashboardBtn) mobileDashboardBtn.classList.add('hidden');
    
    // Show appropriate buttons based on current page
    if (currentPage === 'analyze') {
        // Analiz sayfasında home ve dashboard butonlarını göster
        if (homeBtn) homeBtn.classList.remove('hidden');
        if (dashboardBtn) dashboardBtn.classList.remove('hidden');
        if (mobileHomeBtn) mobileHomeBtn.classList.remove('hidden');
        if (mobileDashboardBtn) mobileDashboardBtn.classList.remove('hidden');
    }
}

// Export functions for global access
window.performAnalysis = performAnalysis;
window.setAnalysisType = setAnalysisType;
window.testAnalysis = testAnalysis;
window.getCurrentAnalysisType = getCurrentAnalysisType;
window.getAnalysisTitle = getAnalysisTitle;
window.getRiskClass = getRiskClass;
window.getRiskIcon = getRiskIcon;
window.clearResults = clearResults;
window.refreshAnalysis = refreshAnalysis;
window.removeFile = removeFile;
window.clearFileSelection = clearFileSelection;
window.showNavigationButtons = showNavigationButtons;
window.initializeEventListeners = initializeEventListeners;  // Add this for core.js access 