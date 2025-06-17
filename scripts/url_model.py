import os
import json
from urllib.parse import urlparse
from datetime import datetime
import re
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
    from transformers import AutoTokenizer
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name()}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    TORCH_AVAILABLE = True
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch yüklenemedi. Pattern-based analiz kullanılacak.")

class URLDataset(Dataset):
    """URL veri seti için PyTorch Dataset sınıfı"""
    def __init__(self, urls: List[str], labels: Optional[List[int]] = None, tokenizer=None, max_length: int = 100):
        self.urls = urls
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.urls)

    def __getitem__(self, idx):
        url = self.urls[idx]
        if self.tokenizer:
            encoding = self.tokenizer(
                url,
                truncation=True,
                max_length=self.max_length,
                padding='max_length',
                return_tensors='pt'
            )
            item = {
                'input_ids': encoding['input_ids'].squeeze(),
                'attention_mask': encoding['attention_mask'].squeeze()
            }
        else:
            item = {'url': url}

        if self.labels is not None:
            item['label'] = torch.tensor(self.labels[idx], dtype=torch.float)
        
        return item

class URLClassifier(nn.Module):
    """URL sınıflandırma için PyTorch modeli"""
    def __init__(self, vocab_size: int, embedding_dim: int = 128, max_length: int = 100, num_filters: int = 128):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # CNN katmanları
        self.conv_blocks = nn.ModuleList([
            nn.Conv1d(embedding_dim, num_filters, kernel_size=k) 
            for k in [3, 4, 5]  # Farklı kernel boyutları
        ])
        
        # Dropout ve normalization (LayerNorm kullan)
        self.dropout = nn.Dropout(0.3)
        self.layer_norm = nn.LayerNorm(num_filters * 3)  # BatchNorm yerine LayerNorm
        
        # Fully connected katmanlar
        self.fc1 = nn.Linear(num_filters * 3, 128)  # Her conv çıkışından bir feature
        self.fc2 = nn.Linear(128, 1)

    def forward(self, input_ids, attention_mask=None):
        # Embedding katmanı [batch, seq_len] -> [batch, seq_len, embedding_dim]
        x = self.embedding(input_ids)
        
        # Attention mask uygula (eğer varsa)
        if attention_mask is not None:
            x = x * attention_mask.unsqueeze(-1)
        
        # Conv1d için boyut değiştir [batch, embedding_dim, seq_len]
        # x boyutunu kontrol et ve uygun şekilde transpose et
        if len(x.shape) == 3:
            x = x.transpose(1, 2)
        elif len(x.shape) == 2:
            x = x.unsqueeze(0).transpose(1, 2)  # Batch boyutu ekle
        
        # Parallel CNN bloklarını uygula
        conv_outputs = []
        for conv in self.conv_blocks:
            conv_out = F.relu(conv(x))
            # Global max pooling
            pooled = F.adaptive_max_pool1d(conv_out, 1).squeeze(-1)
            conv_outputs.append(pooled)
        
        # Concat ve normalization
        x = torch.cat(conv_outputs, dim=1)
        x = self.layer_norm(x)
        x = self.dropout(x)
        
        # FC katmanları
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.sigmoid(self.fc2(x))
        
        return x.squeeze(-1)  # [batch_size] boyutuna getir

class URLDetectionModel:
    def __init__(self, model_path='models/url/url_detection_model.pt', tokenizer_path='models/url/tokenizer', 
                 max_length=100, embedding_dim=128, num_filters=128):
        self.max_length = max_length
        self.embedding_dim = embedding_dim
        self.num_filters = num_filters
        self.device = DEVICE
        
        # Tokenizer'ı yükle/oluştur
        try:
            # Yeni tokenizer oluştur
            self.tokenizer = AutoTokenizer.from_pretrained(
                'bert-base-uncased',
                model_max_length=max_length,
                padding_side='right',
                truncation_side='right'
            )
            
            # Tokenizer'ı kaydet
            os.makedirs(tokenizer_path, exist_ok=True)
            self.tokenizer.save_pretrained(tokenizer_path)
            print(f"Tokenizer başarıyla oluşturuldu")
            
            # Model oluştur
            self.model = URLClassifier(
                vocab_size=self.tokenizer.vocab_size,
                embedding_dim=embedding_dim,
                max_length=max_length,
                num_filters=num_filters
            ).to(self.device)
            
            print(f"Model başarıyla oluşturuldu")
            
        except Exception as e:
            print(f"Model/Tokenizer oluşturulurken hata: {e}")
            self.tokenizer = None
            self.model = None
            return
        
        # Genişletilmiş güvenilir domainler listesi
        self.trusted_domains = {
            # Büyük Teknoloji Şirketleri
            'google.com': ['accounts', 'mail', 'drive', 'docs', 'cloud', 'photos', 'calendar', 'meet', 'play', 'store', 'classroom'],
            'apple.com': ['support', 'id', 'www', 'icloud', 'developer', 'beta', 'discussions', 'gsp'],
            'microsoft.com': ['login', 'account', 'office', 'azure', 'teams', 'outlook', 'live', 'windows', 'docs', 'support'],
            'office.com': ['www', 'login', 'outlook', 'teams', 'onedrive', 'sharepoint'],
            'office365.com': ['outlook', 'teams', 'sharepoint', 'onedrive', 'mail'],
            'live.com': ['login', 'account', 'outlook'],
            'outlook.com': ['www', 'office', 'login'],
            'amazon.com': ['www', 'signin', 'aws', 'console', 'seller', 'prime', 'music', 'drive', 'photos'],
            'meta.com': ['www', 'business', 'developers'],
            
            # Sosyal Medya
            'facebook.com': ['www', 'm', 'business', 'developers', 'workplace'],
            'instagram.com': ['www', 'business', 'api', 'help'],
            'twitter.com': ['www', 'api', 'developer', 'business', 'help'],
            'linkedin.com': ['www', 'business', 'learning', 'developer', 'help'],
            'youtube.com': ['www', 'studio', 'music', 'tv', 'kids'],
            
            # E-posta ve İletişim
            'gmail.com': ['www', 'mail', 'calendar'],
            'yahoo.com': ['www', 'mail', 'finance', 'sports'],
            'proton.me': ['www', 'mail', 'calendar', 'drive'],
            
            # Ödeme Sistemleri
            'paypal.com': ['www', 'signin', 'checkout', 'business'],
            'stripe.com': ['www', 'dashboard', 'connect', 'billing'],
            'wise.com': ['www', 'help', 'blog'],
            'github.com': ['www', 'gist', 'raw']
        }
        
        # Typosquatting kontrol listesi
        self.typo_patterns = {
            'o': ['0', 'q'],
            'i': ['1', 'l', '!'],
            'l': ['1', 'i', '|'],
            'e': ['3', 'a'],
            'a': ['4', '@', 'e'],
            's': ['5', '$'],
            't': ['7', '+'],
            'b': ['8', '6'],
            'g': ['9', 'q'],
            'm': ['rn', 'nn'],
            'w': ['vv', 'uu'],
            'n': ['m', 'h'],
            'h': ['n', 'b'],
            'y': ['j', 'v'],
            'k': ['c', 'x'],
        }
        
        # Şüpheli pattern'lar
        self.suspicious_patterns = {
            'domain_patterns': {
                r'\d{2,}': 30,  # Çoklu sayı
                r'-.*-': 40,    # Çoklu tire
                r'[0-9]+[a-z]+[0-9]+': 35,  # Sayı-harf-sayı karışımı
                r'[a-z]{1}[0-9]{3,}': 25,  # Harf sonrası uzun sayı
                r'[a-z]{15,}': 20,  # Çok uzun domain
            },
            'path_patterns': {
                r'/[a-z0-9]{20,}': 30,  # Uzun rastgele path
                r'\?.*&.*&': 25,        # Çoklu parametre
                r'\.php\?': 15,         # PHP parametresi
                r'%[0-9a-f]{2}': 10,    # URL encoding
            },
            'tld_risk': {
                '.tk': 70, '.ml': 70, '.ga': 70, '.cf': 70, '.gq': 70,
                '.xyz': 50, '.top': 45, '.click': 60, '.link': 55,
                '.online': 40, '.site': 35, '.info': 30, '.biz': 25
            }
        }
        
        # Şüpheli URL kalıpları ve puanları
        self.suspicious_patterns = {
            'domain_patterns': {
                r'\d{4,}': 40,  # Uzun sayı dizisi
                r'-{2,}': 30,   # Çoklu tire
                r'[^a-zA-Z0-9-.]': 35,  # Özel karakterler
                r'[a-zA-Z0-9]{20,}': 25  # Çok uzun domain
            },
            'path_patterns': {
                r'login|signin|account': 20,
                r'verify|confirm|secure': 25,
                r'update|password|reset': 30,
                r'payment|credit|bank': 35,
                r'bitcoin|crypto|wallet': 40
            },
            'tld_risk': {
                '.tk': 70, '.ml': 70, '.ga': 70, '.cf': 70, '.gq': 70,
                '.xyz': 60, '.top': 55, '.click': 50, '.link': 45,
                '.online': 40, '.site': 35, '.biz': 30
            }
        }
        
        # Öğrenme geçmişi
        self.learning_history = {
            'detected_threats': [],
            'confirmed_threats': [],
            'false_positives': [],
            'analysis_updates': []
        }

    def preprocess_url(self, url):
        """URL'yi model için hazırla"""
        # URL'yi küçük harfe çevir ve normalize et
        url = url.lower().strip()
        
        # URL'yi parçalara ayır
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path
        
        # Özel karakterleri ayır ve boşluklarla değiştir
        processed = f"{domain} {path}"
        processed = re.sub(r'[^\w\s-]', ' ', processed)
        
        # Fazla boşlukları temizle
        processed = ' '.join(processed.split())
        
        return processed

    def predict(self, url):
        """URL'nin risk skorunu tahmin et"""
        if self.model is None:
            return {"error": "Model yüklenemedi"}

        try:
            # URL'yi ön işle
            processed_url = self.preprocess_url(url)
            
            # Tokenize et ve tensor'a çevir
            encoding = self.tokenizer(
                processed_url,
                truncation=True,
                max_length=self.max_length,
                padding='max_length',
                return_tensors='pt'
            )
            
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
            
            # Boyut kontrolü - tensoru düzelt
            if input_ids.dim() == 1:
                input_ids = input_ids.unsqueeze(0)
            if attention_mask.dim() == 1:
                attention_mask = attention_mask.unsqueeze(0)
            
            # Tahmin yap
            with torch.no_grad():
                prediction = self.model(input_ids, attention_mask)
                
            # Sonucu güvenli şekilde çıkart
            if prediction.numel() > 0:
                # Tensor'dan sayısal değeri çıkar
                if prediction.dim() == 0:  # 0-dim tensor
                    risk_score = float(prediction.item() * 100)
                elif prediction.dim() == 1 and len(prediction) > 0:  # 1-dim tensor
                    risk_score = float(prediction[0].item() * 100)
                else:  # 2-dim veya daha fazla
                    risk_score = float(prediction.flatten()[0].item() * 100)
            else:
                risk_score = 50.0
            
            # Sonuçları hazırla
            result = {
                "url": url,
                "risk_score": risk_score,
                "risk_level": "YÜKSEK" if risk_score >= 70 else "ORTA" if risk_score >= 40 else "DÜŞÜK",
                "warnings": self._generate_warnings(url, risk_score)
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Tahmin sırasında hata: {str(e)}"}

    def _generate_warnings(self, url, risk_score):
        """Risk skoruna ve URL özelliklerine göre uyarılar oluştur"""
        warnings = []
        
        if risk_score >= 70:
            warnings.append(f"⚠️ YÜKSEK RİSK - Risk Skoru: {risk_score:.1f}/100")
            
            # URL yapısını kontrol et
            if '-' in url:
                warnings.append("- URL'de şüpheli tire işareti kullanımı")
            
            # Yaygın markaları kontrol et
            brands = ['google', 'facebook', 'apple', 'microsoft', 'amazon', 'paypal']
            domain = urlparse(url).netloc.lower()
            for brand in brands:
                if brand in domain and not domain.startswith(f"www.{brand}."):
                    warnings.append(f"- Muhtemel {brand.title()} taklidi")
            
            # Şüpheli TLD'leri kontrol et
            suspicious_tlds = ['.xyz', '.tk', '.online', '.site', '.info']
            if any(url.lower().endswith(tld) for tld in suspicious_tlds):
                warnings.append("- Şüpheli domain uzantısı")
        
        return warnings

    def analyze_url(self, url: str) -> dict:
        """URL analizi - Hem ML model hem de pattern-based analiz kullanır"""
        try:
            # 1. Güvenilir domain kontrolü
            if self.is_trusted_domain(url):
                return {
                    'url': url,
                    'is_malicious': False,
                    'risk_score': 5,
                    'risk_level': 'DÜŞÜK RİSK',
                    'confidence': 0.95,
                    'warnings': ['✅ Güvenilir domain'],
                    'analysis_type': 'whitelist'
                }
            
            # 2. Pattern-based analiz
            pattern_result = self._pattern_based_analysis(url)
            
            # 3. ML model analizi (eğer varsa)
            ml_result = None
            if TORCH_AVAILABLE and self.model is not None and self.tokenizer is not None:
                try:
                    ml_result = self._ml_based_analysis(url)
                except Exception as e:
                    print(f"ML analizi hatası: {e}")
            
            # 4. Sonuçları birleştir
            if ml_result:
                # ML model ve pattern analizi birleştir
                final_score = (pattern_result['risk_score'] * 0.4 + ml_result['risk_score'] * 0.6)
                is_malicious = final_score >= 70 or ml_result['is_malicious']
                warnings = pattern_result['warnings'] + ml_result.get('warnings', [])
                analysis_type = 'hybrid'
            else:
                # Sadece pattern analizi
                final_score = pattern_result['risk_score']
                is_malicious = pattern_result['is_malicious']
                warnings = pattern_result['warnings']
                analysis_type = 'pattern_based'
            
            # Risk seviyesini belirle
            risk_level = self._get_risk_level(final_score)
            
            return {
                'url': url,
                'is_malicious': is_malicious,
                'risk_score': min(100, final_score),
                'risk_level': risk_level,
                'confidence': min(0.95, final_score / 100 + 0.2),
                'warnings': warnings,
                'analysis_type': analysis_type
            }
            
        except Exception as e:
            return {
                'url': url,
                'is_malicious': True,
                'risk_score': 100,
                'risk_level': 'HATA',
                'confidence': 0.99,
                'warnings': [f'Analiz hatası: {str(e)}'],
                'analysis_type': 'error'
            }

    def _pattern_based_analysis(self, url: str) -> dict:
        """Pattern-based URL analizi"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        risk_score = 0
        warnings = []
        
        # 1. Güvenilir domain kontrolü
        if self.is_trusted_domain(url):
            return {
                'url': url,
                'is_malicious': False,
                'risk_score': 5,
                'confidence': 0.95,
                'warnings': ['✅ Güvenilir domain'],
                'analysis_type': 'whitelist'
            }
        
        # 2. Typosquatting kontrolü (sadece güvenilir olmayan domainler için)
        if not self.is_trusted_domain(url) and self.is_possible_typosquatting(domain):
            risk_score += 80
            warnings.append('⚠️ Olası typosquatting tespit edildi')
        
        # Domain pattern kontrolü
        for pattern, score in self.suspicious_patterns['domain_patterns'].items():
            if re.search(pattern, domain):
                risk_score += score
                warnings.append('⚠️ Şüpheli domain yapısı')
        
        # Path pattern kontrolü
        for pattern, score in self.suspicious_patterns['path_patterns'].items():
            if re.search(pattern, path):
                risk_score += score
                warnings.append('⚠️ Şüpheli URL yolu')
        
        # 5. TLD risk kontrolü
        tld = '.' + domain.split('.')[-1] if '.' in domain else ''
        if tld in self.suspicious_patterns['tld_risk']:
            score = self.suspicious_patterns['tld_risk'][tld]
            risk_score += score
            warnings.append(f'⚠️ Riskli domain uzantısı: {tld}')
        
        return {
            'risk_score': min(100, risk_score),
            'is_malicious': risk_score >= 70,
            'warnings': warnings
        }

    def _ml_based_analysis(self, url: str) -> dict:
        """ML model tabanlı analiz"""
        if not TORCH_AVAILABLE or not self.model or not self.tokenizer:
            raise Exception("ML model kullanılamıyor")
        
        # URL'yi tokenize et
        processed_url = self.preprocess_url(url)
        encoding = self.tokenizer(
            processed_url,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Boyut kontrolü
        if input_ids.dim() == 1:
            input_ids = input_ids.unsqueeze(0)
        if attention_mask.dim() == 1:
            attention_mask = attention_mask.unsqueeze(0)
        
        # Tahmin yap
        with torch.no_grad():
            prediction = self.model(input_ids, attention_mask)
            
            # Güvenli sonuç çıkarma
            if isinstance(prediction, torch.Tensor):
                if prediction.dim() == 0:
                    risk_score = float(prediction.item() * 100)
                    is_malicious = risk_score > 50
                elif prediction.dim() == 1:
                    risk_score = float(prediction[0].item() * 100)
                    is_malicious = risk_score > 50
                else:
                    risk_score = float(prediction[0][0].item() * 100)
                    is_malicious = risk_score > 50
            else:
                risk_score = 50.0
                is_malicious = False
        
        return {
            'risk_score': risk_score,
            'is_malicious': is_malicious,
            'warnings': [f'🤖 ML Model Risk Skoru: {risk_score:.1f}/100']
        }

    def _get_risk_level(self, score: float) -> str:
        """Risk seviyesini belirle"""
        if score >= 70:
            return 'YÜKSEK RİSK'
        elif score >= 40:
            return 'ORTA RİSK'
        else:
            return 'DÜŞÜK RİSK'

    def is_trusted_domain(self, url: str) -> bool:
        """Güvenilir domain kontrolü"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            parts = domain.split('.')
            if len(parts) >= 2:
                main_domain = '.'.join(parts[-2:])
                subdomain = '.'.join(parts[:-2]) if len(parts) > 2 else ''
                
                if main_domain in self.trusted_domains:
                    if not subdomain:
                        return True
                    
                    for trusted_sub in self.trusted_domains[main_domain]:
                        if subdomain == trusted_sub or subdomain.endswith('.' + trusted_sub):
                            return True
            
            return False
        except:
            return False

    def is_possible_typosquatting(self, domain: str) -> bool:
        """Domain'in typosquatting olup olmadığını kontrol et"""
        try:
            # Önce güvenilir domain olup olmadığını kontrol et
            if self.is_trusted_domain(f"https://{domain}"):
                return False  # Güvenilir domain ise typosquatting değil
                
            base_domain = domain.split('.')[-2] if len(domain.split('.')) > 1 else domain
            base_domain = base_domain.lower()
            
            # Normalize domain
            normalized = base_domain
            for char, replacements in self.typo_patterns.items():
                for replacement in replacements:
                    normalized = normalized.replace(replacement, char)
            
            # Popüler domainlerle karşılaştır (sadece güvenilir olmayan domainler için)
            for target in self.trusted_domains.keys():
                target_base = target.split('.')[0]
                # Tam eşleşme varsa typosquatting değil
                if normalized == target_base:
                    continue
                # Küçük fark varsa typosquatting olabilir
                if 1 <= self._levenshtein_distance(normalized, target_base) <= 2:
                    return True
            
            return False
        except:
            return False  # Hata durumunda güvenli varsay

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """İki string arasındaki Levenshtein mesafesini hesapla"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def update_learning_history(self, url: str, result: dict, feedback: dict = None):
        """Öğrenme geçmişini güncelle"""
        entry = {
            'url': url,
            'result': result,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        
        if result['is_malicious'] and feedback and feedback.get('is_correct'):
            self.learning_history['confirmed_threats'].append(entry)
        elif result['is_malicious'] and feedback and not feedback.get('is_correct'):
            self.learning_history['false_positives'].append(entry)
        elif result['is_malicious']:
            self.learning_history['detected_threats'].append(entry)

    def save_learning_history(self, file_path: str = 'data/learning_history.json'):
        """Öğrenme geçmişini kaydet"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.learning_history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Öğrenme geçmişi kaydedilemedi: {e}")
            return False

    def load_learning_history(self, file_path: str = 'data/learning_history.json'):
        """Öğrenme geçmişini yükle"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.learning_history = json.load(f)
            return True
        except Exception as e:
            print(f"Öğrenme geçmişi yüklenemedi: {e}")
            return False

    def build_model(self):
        """CNN modelini oluştur"""
        if not TORCH_AVAILABLE:
            print("PyTorch yüklü değil. Model oluşturulamıyor.")
            return None
        
        try:
            # Text vectorization katmanı
            self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
            
            # Model mimarisi
            model = URLClassifier(
                vocab_size=self.tokenizer.vocab_size,
                embedding_dim=128,
                max_length=self.max_length
            )
            
            self.model = model
            return model
        except Exception as e:
            print(f"Model oluşturma hatası: {e}")
            return None

    def train(self, train_data, train_labels, validation_data=None, validation_labels=None,
              epochs=10, batch_size=256, learning_rate=0.001, early_stopping_patience=3):
        """Modeli eğit"""
        if not TORCH_AVAILABLE or not self.model:
            print("Model eğitimi için PyTorch gerekli")
            return None
        
        try:
            # Veri setlerini hazırla
            train_dataset = URLDataset(train_data, train_labels, self.tokenizer, self.max_length)
            train_loader = DataLoader(
                train_dataset, 
                batch_size=batch_size, 
                shuffle=True, 
                num_workers=4 if torch.cuda.is_available() else 0,
                pin_memory=torch.cuda.is_available()
            )
            
            if validation_data is not None and validation_labels is not None:
                val_dataset = URLDataset(validation_data, validation_labels, self.tokenizer, self.max_length)
                val_loader = DataLoader(
                    val_dataset, 
                    batch_size=batch_size, 
                    shuffle=False, 
                    num_workers=4 if torch.cuda.is_available() else 0,
                    pin_memory=torch.cuda.is_available()
                )
            
            # Optimizer ve loss function
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
            criterion = torch.nn.BCELoss()
            
            # Learning rate scheduler
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min', factor=0.5, patience=2, verbose=True
            )
            
            # Early stopping için değişkenler
            best_val_loss = float('inf')
            patience_counter = 0
            best_model_state = None
            
            # Eğitim döngüsü
            for epoch in range(epochs):
                # Training
                self.model.train()
                total_loss = 0
                correct_predictions = 0
                total_predictions = 0
                
                for batch_idx, batch in enumerate(train_loader):
                    optimizer.zero_grad()
                    
                    input_ids = batch['input_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels = batch['label'].to(self.device)
                    
                    outputs = self.model(input_ids, attention_mask)
                    loss = criterion(outputs, labels)
                    
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                    predictions = (outputs >= 0.5).float()
                    correct_predictions += (predictions == labels).sum().item()
                    total_predictions += labels.size(0)
                    
                    # Her 100 batch'te bir ilerleme göster
                    if (batch_idx + 1) % 100 == 0:
                        print(f'Batch {batch_idx+1}/{len(train_loader)}, Loss: {loss.item():.4f}')
                
                avg_train_loss = total_loss / len(train_loader)
                train_accuracy = correct_predictions / total_predictions
                
                print(f'Epoch {epoch+1}/{epochs}:')
                print(f'Training Loss: {avg_train_loss:.4f}')
                print(f'Training Accuracy: {train_accuracy:.4f}')
                
                # Validation
                if validation_data is not None:
                    self.model.eval()
                    val_loss = 0
                    val_correct = 0
                    val_total = 0
                    
                    with torch.no_grad():
                        for batch in val_loader:
                            input_ids = batch['input_ids'].to(self.device)
                            attention_mask = batch['attention_mask'].to(self.device)
                            labels = batch['label'].to(self.device)
                            
                            outputs = self.model(input_ids, attention_mask)
                            loss = criterion(outputs, labels)
                            
                            val_loss += loss.item()
                            predictions = (outputs >= 0.5).float()
                            val_correct += (predictions == labels).sum().item()
                            val_total += labels.size(0)
                    
                    avg_val_loss = val_loss / len(val_loader)
                    val_accuracy = val_correct / val_total
                    
                    print(f'Validation Loss: {avg_val_loss:.4f}')
                    print(f'Validation Accuracy: {val_accuracy:.4f}')
                    
                    # Learning rate güncelle
                    scheduler.step(avg_val_loss)
                    
                    # Early stopping kontrolü
                    if avg_val_loss < best_val_loss:
                        best_val_loss = avg_val_loss
                        best_model_state = self.model.state_dict().copy()
                        patience_counter = 0
                    else:
                        patience_counter += 1
                        
                    if patience_counter >= early_stopping_patience:
                        print(f'Early stopping triggered after {epoch+1} epochs')
                        # En iyi modeli geri yükle
                        self.model.load_state_dict(best_model_state)
                        break
                
                print('-' * 50)
            
            return self.model
            
        except Exception as e:
            print(f"Eğitim hatası: {e}")
            return None

    def save_model(self, model_path='models/url/url_detection_model.pt', tokenizer_path='models/url/tokenizer'):
        """Model ve tokenizer'ı kaydet"""
        try:
            # Model dizinini oluştur
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Model state dict'i kaydet
            if self.model is not None:
                torch.save(self.model.state_dict(), model_path)
                print(f"Model kaydedildi: {model_path}")
            
            # Tokenizer'ı kaydet
            if self.tokenizer is not None:
                os.makedirs(tokenizer_path, exist_ok=True)
                self.tokenizer.save_pretrained(tokenizer_path)
                print(f"Tokenizer kaydedildi: {tokenizer_path}")
            
            return True
        except Exception as e:
            print(f"Model kaydedilirken hata oluştu: {e}")
            return False

    def load_model(self, model_path='models/url/url_detection_model.pt', tokenizer_path='models/url/tokenizer'):
        """Kaydedilmiş model ve tokenizer'ı yükle"""
        if not TORCH_AVAILABLE:
            print("PyTorch yüklü değil. Model yüklenemiyor.")
            return False
        
        try:
            # Önce tokenizer'ı yükle
            if os.path.exists(tokenizer_path):
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
                print("Tokenizer başarıyla yüklendi")
            else:
                print("Tokenizer dosyası bulunamadı")
                return False
            
            # Sonra modeli yükle
            if os.path.exists(model_path):
                self.model = URLClassifier(
                    vocab_size=self.tokenizer.vocab_size,
                    embedding_dim=self.embedding_dim,
                    max_length=self.max_length,
                    num_filters=self.num_filters
                )
                
                # Model state'ini yükle
                state_dict = torch.load(model_path, map_location=self.device)
                
                # BatchNorm uyumsuzluğunu çöz
                filtered_state_dict = {}
                for key, value in state_dict.items():
                    # BatchNorm'daki running stats'ı atla
                    if 'running_mean' not in key and 'running_var' not in key and 'num_batches_tracked' not in key:
                        filtered_state_dict[key] = value
                
                self.model.load_state_dict(filtered_state_dict, strict=False)
                self.model.to(self.device)
                self.model.eval()
                
                print("Eğitilmiş model başarıyla yüklendi")
                return True
            else:
                print("Model dosyası bulunamadı")
                return False
                
        except Exception as e:
            print(f"Model yükleme hatası: {e}")
            return False 