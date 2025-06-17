import os
import re
import requests
import hashlib
import time
from typing import Dict, List, Tuple, Optional
import logging
import pickle
import json
import torch
from scripts.url_model import URLDetectionModel

class HybridAIEngine:
    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HybridAIEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not HybridAIEngine._is_initialized:
            self.api_keys = {
                'virustotal': os.getenv('VIRUSTOTAL_API_KEY'),
                'safe_browsing': os.getenv('SAFE_BROWSING_API_KEY')
            }
            
            # Eğitilmiş model yükleme
            try:
                self.url_model = URLDetectionModel(
                    model_path='models/url/url_detection_model.pt',
                    tokenizer_path='models/url/tokenizer'
                )
                
                # Eğitilmiş modeli yükle
                if os.path.exists('models/url/url_detection_model.pt'):
                    self.url_model.load_model('models/url/url_detection_model.pt', 'models/url/tokenizer')
                    self.model_available = True
                    self.ai_available = True
                    logging.info("Eğitilmiş URL detection model başarıyla yüklendi")
                else:
                    self.model_available = False
                    self.ai_available = False
                    logging.warning("Eğitilmiş model dosyası bulunamadı")
                    
            except Exception as e:
                self.url_model = None
                self.model_available = False
                self.ai_available = False
                logging.error(f"Model yükleme hatası: {e}")
            
            HybridAIEngine._is_initialized = True

    def analyze_url_with_ai(self, url: str) -> Dict:
        """Pattern-based and ML-based URL analysis"""
        result = {
            'ai_score': 0,
            'confidence': 0,
            'ai_warnings': [],
            'api_checks': {}
        }
        
        try:
            # Pattern-based analysis
            try:
                pattern_score = self._analyze_url_patterns(url)
            except Exception as e:
                logging.error(f"Pattern analysis error: {e}")
                pattern_score = 50  # Default score for pattern analysis failure
            
            # ML model analysis
            ml_score = 0
            if self.model_available and self.url_model:
                try:
                    ml_result = self.url_model.analyze_url(url)
                    ml_score = ml_result['risk_score']
                    result['ai_warnings'].extend(ml_result.get('warnings', []))
                    result['confidence'] = ml_result.get('confidence', 0)
                except Exception as e:
                    logging.error(f"ML model analysis error: {e}")
                    ml_score = 0
                    result['ai_warnings'].append("ML model analizi başarısız")
            
            # Combine scores (60% ML, 40% pattern-based if ML available)
            if self.model_available and ml_score > 0:
                final_score = (ml_score * 0.6) + (pattern_score * 0.4)
            else:
                final_score = pattern_score
            
            # Update result
            result['ai_score'] = final_score
            if not result['confidence']:
                result['confidence'] = min(95, final_score + 5)
            
            # Add warnings based on patterns
            try:
                self._add_warnings(result, url, final_score)
            except Exception as e:
                logging.error(f"Warning generation error: {e}")
                result['ai_warnings'].append("Uyarı üretimi başarısız")
            
        except Exception as e:
            logging.exception(f"URL analysis error in AI engine: {e}")
            result['ai_warnings'].append(f"Analiz hatası: {str(e)}")
            result['ai_score'] = 50  # Default risk score for analysis failure
            result['confidence'] = 30  # Low confidence for error case
        
        return result

    def _analyze_url_patterns(self, url: str) -> float:
        """Pattern-based URL risk analysis"""
        score = 0
        url_lower = url.lower()
        
        # 1. Marka taklidi kontrolü
        brands = {
            'dropbox': ['dropbox'],
            'apple': ['apple', 'icloud'],
            'microsoft': ['microsoft', 'outlook', 'office'],
            'google': ['google', 'gmail'],
            'facebook': ['facebook', 'instagram'],
            'paypal': ['paypal'],
            'amazon': ['amazon'],
            'netflix': ['netflix'],
            'bank': ['bank', 'banking']
        }
        
        # Resmi domainler
        official_domains = {
            'dropbox': ['dropbox.com'],
            'apple': ['apple.com', 'icloud.com'],
            'microsoft': ['microsoft.com', 'live.com', 'outlook.com'],
            'google': ['google.com', 'gmail.com'],
            'facebook': ['facebook.com', 'instagram.com'],
            'paypal': ['paypal.com'],
            'amazon': ['amazon.com'],
            'netflix': ['netflix.com']
        }
        
        # Marka taklidi kontrolü
        for brand, keywords in brands.items():
            if any(keyword in url_lower for keyword in keywords):
                if brand in official_domains:
                    if not any(domain in url_lower for domain in official_domains[brand]):
                        score += 80  # Marka taklidi cezası
        
        # 2. Şüpheli TLD kontrolü
        suspicious_tlds = {
            '.online': 60, '.xyz': 55, '.top': 50, '.click': 60, '.link': 55,
            '.tk': 70, '.ml': 70, '.ga': 70, '.cf': 70, '.gq': 70,
            '.info': 45, '.biz': 40, '.site': 50, '.co': 35, '.pw': 65,
            '.cc': 45, '.work': 40, '.app': 30
        }
        
        domain_parts = url_lower.split('.')
        if len(domain_parts) > 1:
            tld = '.' + domain_parts[-1]
            if tld in suspicious_tlds:
                score += suspicious_tlds[tld]
        
        # 3. Şüpheli kelime kontrolü
        suspicious_words = {
            'verify': 50, 'verification': 50, 'login': 45, 'signin': 45,
            'secure': 40, 'account': 40, 'update': 40, 'confirm': 45,
            'access': 40, 'authenticate': 45, 'authorize': 45, 'files': 35,
            'support': 30, 'help': 25, 'service': 25, 'customer': 30,
            'password': 50, 'security': 40, 'wallet': 45, 'crypto': 50,
            'payment': 45, 'billing': 45, 'invoice': 40, 'document': 35
        }
        
        found_words = []
        for word, weight in suspicious_words.items():
            if word in url_lower:
                score += weight
                found_words.append(word)
        
        # Çoklu şüpheli kelime cezası
        if len(found_words) > 1:
            score += len(found_words) * 15
        
        # 4. URL yapısı kontrolü
        # Tire işareti kontrolü
        hyphen_count = url_lower.count('-')
        if hyphen_count > 0:
            score += min(hyphen_count * 25, 50)
        
        # Sayı kontrolü
        if re.search(r'\d{4,}', url_lower):
            score += 40  # Uzun sayı dizisi
        elif re.search(r'\d+', url_lower):
            score += 20  # Herhangi bir sayı
        
        # Alt domain kontrolü
        if len(domain_parts) > 3:
            score += (len(domain_parts) - 2) * 20
        
        # 5. Özel durumlar
        # IP adresi kontrolü (çok yüksek risk)
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_lower):
            score += 80  # Yüksek risk ama 100 değil
        
        # URL uzunluğu kontrolü (daha makul)
        if len(url) > 100:
            score += 25
        elif len(url) > 75:
            score += 15
        elif len(url) > 50:
            score += 10
        
        # Şüpheli karakter kontrolü (daha spesifik)
        if re.search(r'%[0-9a-fA-F]{2}', url_lower):
            score += 15  # URL encoding
        if re.search(r'[^\w\.-/:]', url_lower):
            score += 20  # Diğer şüpheli karakterler
        
        return min(100, score)

    def _add_warnings(self, result: Dict, url: str, risk_score: float):
        """Add detailed warnings"""
        url_lower = url.lower()
        
        if risk_score >= 70:
            result['ai_warnings'].append(f"⚠️ YÜKSEK RİSK - Risk Skoru: {risk_score:.1f}/100")
            
            # Spesifik uyarılar
            if any(brand in url_lower and f"{brand}.com" not in url_lower 
                  for brand in ['dropbox', 'apple', 'microsoft', 'google', 'facebook', 'paypal', 'amazon', 'netflix']):
                result['ai_warnings'].append("- Bilinen bir markanın taklidi tespit edildi")
            
            if '-' in url_lower:
                result['ai_warnings'].append("- URL'de şüpheli tire işareti kullanımı")
            
            if any(tld in url_lower for tld in ['.online', '.xyz', '.tk', '.ml', '.ga', '.cf', '.gq']):
                result['ai_warnings'].append("- Şüpheli domain uzantısı kullanımı")
            
            if re.search(r'\d{4,}', url_lower):
                result['ai_warnings'].append("- URL'de şüpheli sayı dizisi")
            
            if len(url_lower.split('.')) > 3:
                result['ai_warnings'].append("- Çok sayıda alt domain kullanımı")
            
            if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_lower):
                result['ai_warnings'].append("- IP adresi kullanımı tespit edildi")
            
        elif risk_score >= 50:
            result['ai_warnings'].append(f"⚠️ ORTA RİSK - Risk Skoru: {risk_score:.1f}/100")
            result['ai_warnings'].append("- URL'de şüpheli özellikler tespit edildi")
            
        elif risk_score >= 30:
            result['ai_warnings'].append(f"⚠️ DÜŞÜK RİSK - Risk Skoru: {risk_score:.1f}/100")
        else:
            result['ai_warnings'].append(f"✅ GÜVENLI - Risk Skoru: {risk_score:.1f}/100")
        
        # API checks for additional verification
        api_results = self._check_url_apis(url)
        if api_results:
            result['api_checks'] = api_results
            
            # Final score calculation with enhanced weighting
            final_score = self._combine_url_scores(risk_score, api_results)
            result['ai_score'] = final_score
        else:
            result['api_checks'] = {}
            result['ai_score'] = risk_score

    def _check_url_apis(self, url: str) -> Dict:
        """Check URL against various APIs"""
        results = {
            'safe_browsing': None,
            'virustotal': None,
            'phishtank': None,
            'total_score': 0
        }
        
        # Google Safe Browsing API
        if self.api_keys.get('safe_browsing'):
            results['safe_browsing'] = self._check_safe_browsing(url)
        
        # VirusTotal API
        if self.api_keys.get('virustotal'):
            results['virustotal'] = self._check_virustotal(url)
        
        # PhishTank (Free API)
        results['phishtank'] = self._check_phishtank(url)
        
        # Calculate total score
        scores = [r for r in results.values() if isinstance(r, (int, float))]
        if scores:
            results['total_score'] = sum(scores) / len(scores)
        
        return results

    def _check_safe_browsing(self, url: str) -> Optional[float]:
        """Check URL with Google Safe Browsing API"""
        if not self.api_keys.get('safe_browsing'):
            return None
        
        try:
            api_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
            params = {'key': self.api_keys['safe_browsing']}
            
            payload = {
                "client": {
                    "clientId": "securelens",
                    "clientVersion": "1.0"
                },
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }
            
            response = requests.post(api_url, json=payload, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'matches' in data and data['matches']:
                    return 100  # Threat detected
                else:
                    return 0    # Safe
            
        except Exception as e:
            logging.error(f"Safe Browsing API error: {e}")
        
        return None

    def _check_virustotal(self, url: str) -> Optional[float]:
        """Check URL with VirusTotal API"""
        if not self.api_keys.get('virustotal'):
            return None
        
        try:
            # URL encoding for VirusTotal
            url_id = hashlib.sha256(url.encode()).hexdigest()
            
            headers = {'x-apikey': self.api_keys['virustotal']}
            api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            
            response = requests.get(api_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                total = sum(stats.values()) if stats else 0
                
                if total > 0:
                    risk_ratio = (malicious + suspicious) / total
                    return min(100, risk_ratio * 100)
                
        except Exception as e:
            logging.error(f"VirusTotal API error: {e}")
        
        return None

    def _check_phishtank(self, url: str) -> Optional[float]:
        """Check URL with PhishTank API (Free)"""
        try:
            api_url = "http://checkurl.phishtank.com/checkurl/"
            
            # URL encoding
            url_encoded = requests.utils.quote(url, safe='')
            
            payload = {
                'url': url_encoded,
                'format': 'json',
                'app_key': 'securelens'  # Free usage
            }
            
            response = requests.post(api_url, data=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results', {}).get('in_database'):
                    if data['results'].get('valid'):
                        return 100  # Confirmed phishing
                return 0  # Not in phishing database
                
        except Exception as e:
            logging.error(f"PhishTank API error: {e}")
        
        return None

    def _combine_url_scores(self, ai_score: float, api_results: Dict) -> float:
        """Combine AI and API scores with enhanced weighting"""
        scores = [ai_score]
        weights = [0.6]  # Increased AI weight
        
        # Add API scores with adjusted weights
        if api_results.get('safe_browsing') is not None:
            scores.append(api_results['safe_browsing'])
            weights.append(0.2)  # Reduced API weight
        
        if api_results.get('virustotal') is not None:
            scores.append(api_results['virustotal'])
            weights.append(0.1)
        
        if api_results.get('phishtank') is not None:
            scores.append(api_results['phishtank'])
            weights.append(0.1)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
            
            # Calculate weighted average with emphasis on higher scores
            final_score = sum(s * w for s, w in zip(scores, weights))
            
            # Boost score if multiple high-risk indicators
            high_risk_count = sum(1 for s in scores if s > 70)
            if high_risk_count >= 2:
                final_score = min(100, final_score * 1.2)  # 20% boost for multiple high-risk indicators
            
            return min(100, final_score)
        
        return ai_score

    def get_status(self) -> Dict:
        """AI motorunun durumunu döndür"""
        return {
            'ai_available': self.model_available,
            'models_loaded': ['URL Detection Model'] if self.model_available else [],
            'apis_configured': [k for k, v in self.api_keys.items() if v],
            'status': 'model_mode' if self.model_available else 'fallback_mode'
        }

    def analyze_file_with_ai(self, filename, file_content=""):
        """Enhanced file analysis with EMBER-trained PyTorch model"""
        try:
            ai_score = 0
            ai_warnings = []
            confidence = 70
            malware_probability = 0
            
            # 1. PYTORCH MODEL PREDICTION (if available)
            model_prediction = self._predict_with_file_model(filename, file_content)
            if model_prediction:
                ai_score += model_prediction['model_score']
                confidence = max(confidence, model_prediction['confidence'])
                malware_probability = model_prediction['malware_probability']
                ai_warnings.extend(model_prediction['warnings'])
                
                # Add detailed model analysis
                if model_prediction['prediction'] == 1:  # Malicious
                    ai_warnings.append(f'🔴 EMBER Model: Malware tespit edildi (Confidence: {model_prediction["model_confidence"]:.1f}%)')
                else:
                    ai_warnings.append(f'🟢 EMBER Model: Dosya güvenli görünüyor (Confidence: {model_prediction["model_confidence"]:.1f}%)')
            
            # 2. RULE-BASED ANALYSIS (Backup/Enhancement)
            rule_score, rule_warnings = self._analyze_file_rules(filename, file_content)
            
            # 3. ENHANCED HYBRID SCORING
            if model_prediction:
                # Smart weighting based on detection confidence
                model_score = model_prediction['model_score']
                
                # Check for critical rule-based detections
                critical_warnings = [w for w in rule_warnings if '🚨' in w or 'KRİTİK' in w]
                
                if critical_warnings:
                    # Critical threats detected by rules - heavily favor rule-based
                    final_ai_score = (model_score * 0.2) + (rule_score * 0.8)
                    ai_warnings.append('🚨 Kritik Hibrit: %20 EMBER Model + %80 Kural (Kritik tehdit)')
                    # Ensure minimum score for critical threats
                    if final_ai_score < 85:
                        final_ai_score = max(final_ai_score, 85)
                elif rule_score > 80:
                    # High rule confidence
                    final_ai_score = (model_score * 0.3) + (rule_score * 0.7)
                    ai_warnings.append('⚠️ Yüksek Risk Hibrit: %30 EMBER Model + %70 Kural')
                elif model_score > 80:
                    # High model confidence
                    final_ai_score = (model_score * 0.8) + (rule_score * 0.2)
                    ai_warnings.append('🤖 Model Güven Hibrit: %80 EMBER Model + %20 Kural')
                else:
                    # Balanced approach for moderate scores
                    final_ai_score = (model_score * 0.6) + (rule_score * 0.4)
                    ai_warnings.append('📊 Dengeli Hibrit: %60 EMBER Model + %40 Kural')
                
                # Boost score if both methods agree on high risk
                if model_score > 70 and rule_score > 70:
                    boost_factor = 1.3 if critical_warnings else 1.2
                    final_ai_score = min(100, final_ai_score * boost_factor)
                    ai_warnings.append(f'⬆️ Konsensüs Artışı: Hem model hem kurallar yüksek risk tespit etti')
                
            else:
                # Fallback to enhanced rules only
                final_ai_score = rule_score
                ai_warnings.append('⚠️ Model bulunamadı, gelişmiş kural tabanlı analiz kullanılıyor')
            
            ai_warnings.extend(rule_warnings)
            
            # Cap values
            ai_score = min(final_ai_score, 100)
            malware_probability = min(malware_probability, 100)
            confidence = min(confidence, 100)
            
            return {
                'ai_score': ai_score,
                'ai_warnings': ai_warnings,
                'confidence': confidence,
                'malware_probability': malware_probability,
                'model_available': model_prediction is not None
            }
            
        except Exception as e:
            logging.error(f"File AI analysis error: {e}")
            return {
                'ai_score': 50,
                'ai_warnings': [f'AI analiz hatası: {str(e)}'],
                'confidence': 30,
                'malware_probability': 50,
                'model_available': False
            }
    
    def _predict_with_file_model(self, filename, file_content=""):
        """EMBER-trained PyTorch model prediction"""
        try:
            import torch
            import pickle
            import json
            import numpy as np
            from pathlib import Path
            
            # Model paths
            model_dir = Path("models/file")
            model_path = model_dir / "file_detection_model.pt"
            scaler_path = model_dir / "scaler.pkl"
            config_path = model_dir / "model_config.json"
            
            # Check if model files exist
            if not all(p.exists() for p in [model_path, scaler_path, config_path]):
                logging.warning("File detection model files not found")
                return None
            
            # Load model config
            with open(config_path, 'r', encoding='utf-8', errors='replace') as f:
                config = json.load(f)
            
            # Load scaler
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            
            # Load model
            from scripts.train_file_model import SimpleFileSecurityNet
            input_size = config['input_size']
            model = SimpleFileSecurityNet(input_size=input_size)
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
            model.eval()
            
            # Extract features from filename
            features = self._extract_file_features(filename, file_content)
            
            # Convert to numpy array with correct size
            if len(features) != input_size:
                # Pad or truncate to match model input size
                if len(features) < input_size:
                    features.extend([0.0] * (input_size - len(features)))
                else:
                    features = features[:input_size]
            
            # Scale features
            features_array = np.array(features).reshape(1, -1)
            features_scaled = scaler.transform(features_array)
            
            # Predict
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features_scaled)
                output = model(features_tensor)
                probabilities = torch.softmax(output, dim=1)
                
                prediction = torch.argmax(output, dim=1).item()
                confidence = probabilities[0][prediction].item()
                malware_prob = probabilities[0][1].item()  # Probability of being malicious
            
            # Calculate risk score
            model_score = malware_prob * 100
            
            warnings = []
            if prediction == 1:  # Malicious
                warnings.append(f'PyTorch Model: Malware riski yüksek (%{malware_prob*100:.1f})')
            
            return {
                'prediction': prediction,
                'model_score': model_score,
                'model_confidence': confidence * 100,
                'malware_probability': malware_prob * 100,
                'confidence': 85,  # High confidence with model
                'warnings': warnings
            }
            
        except Exception as e:
            logging.error(f"Model prediction error: {e}")
            return None
    
    def _extract_file_features(self, filename, file_content=""):
        """Enhanced feature extraction for better model prediction"""
        import math
        import re
        
        filename_lower = filename.lower()
        
        # 1. BASIC FILENAME FEATURES
        length = len(filename)
        dot_count = filename.count('.')
        digit_ratio = len([c for c in filename if c.isdigit()]) / max(len(filename), 1)
        uppercase_ratio = len([c for c in filename if c.isupper()]) / max(len(filename), 1)
        
        # 2. ENHANCED EXTENSION ANALYSIS
        dangerous_exts = ['.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', '.jar', '.app']
        suspicious_exts = ['.zip', '.rar', '.msi', '.deb', '.dmg', '.iso']
        
        parts = filename.split('.')
        extensions = [f'.{part.lower()}' for part in parts[1:]] if len(parts) > 1 else []
        
        # Dangerous extension score
        dangerous_ext_score = sum(1 for ext in extensions if ext in dangerous_exts)
        suspicious_ext_score = sum(1 for ext in extensions if ext in suspicious_exts)
        
        # 3. CRITICAL: DOUBLE EXTENSION DETECTION
        double_ext = 0
        deceptive_double_ext = 0
        
        if len(parts) > 2:
            double_ext = 1
            # Extra dangerous: document extensions followed by executable
            doc_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.png']
            if len(parts) >= 3:
                second_last_ext = f'.{parts[-2].lower()}'
                last_ext = f'.{parts[-1].lower()}'
                if second_last_ext in doc_exts and last_ext in dangerous_exts:
                    deceptive_double_ext = 1  # This is the smoking gun!
        
        # 4. MALWARE PATTERN DETECTION
        malware_patterns = [
            'crack', 'keygen', 'patch', 'serial', 'activator', 'hack', 'cheat',
            'trojan', 'virus', 'malware', 'backdoor', 'keylogger', 'spyware',
            'ransomware', 'worm', 'rootkit', 'exploit'
        ]
        
        social_eng_patterns = [
            'invoice', 'receipt', 'payment', 'refund', 'urgent', 'important',
            'confidential', 'secure', 'update', 'install', 'setup', 'download'
        ]
        
        malware_pattern_count = sum(1 for pattern in malware_patterns if pattern in filename_lower)
        social_pattern_count = sum(1 for pattern in social_eng_patterns if pattern in filename_lower)
        
        # 5. SYSTEM FILE MIMICKING
        system_names = ['svchost', 'winlogon', 'explorer', 'system32', 'notepad', 'calc', 'cmd', 'powershell']
        mimics_system = 1 if any(name in filename_lower for name in system_names) else 0
        
        # 6. ENTROPY CALCULATION
        if len(filename) > 0:
            prob = [filename.count(c)/len(filename) for c in set(filename)]
            entropy = -sum(p * math.log2(p) for p in prob if p > 0)
        else:
            entropy = 0
        
        # 7. SUSPICIOUS CHARACTERS
        has_numbers = 1 if any(c.isdigit() for c in filename) else 0
        has_spaces = 1 if ' ' in filename else 0
        has_special_chars = 1 if any(c in '!@#$%^&*()+=[]{}|;:,<>?~`' for c in filename) else 0
        has_underscores = 1 if '_' in filename else 0
        has_dashes = 1 if '-' in filename else 0
        
        # 8. LENGTH ANALYSIS
        very_short = 1 if length < 5 else 0
        very_long = 1 if length > 50 else 0
        
        # 9. VOWEL/CONSONANT ANALYSIS
        vowels = 'aeiouAEIOU'
        vowel_ratio = len([c for c in filename if c in vowels]) / max(len(filename), 1)
        
        # 10. ADVANCED PATTERN MATCHING
        # Suspicious number sequences
        has_version_pattern = 1 if re.search(r'\d+\.\d+', filename) else 0
        has_sequential_numbers = 1 if re.search(r'\d{3,}', filename) else 0
        
                # Create enhanced feature vector
        features = [
            # Basic features (12)
            length, dot_count, digit_ratio, uppercase_ratio,
            dangerous_ext_score, suspicious_ext_score, double_ext, deceptive_double_ext,
            malware_pattern_count, social_pattern_count, mimics_system, entropy,
            
            # Character analysis (8)
            vowel_ratio, has_numbers, has_spaces, has_special_chars,
            has_underscores, has_dashes, very_short, very_long,
            
            # Advanced patterns (6)
            has_version_pattern, has_sequential_numbers,
            len(extensions), max(len(ext) for ext in extensions) if extensions else 0,
            1 if any('.exe' in ext for ext in extensions) else 0,
            1 if any('.scr' in ext for ext in extensions) else 0,
            
            # Content-based features (if available) (4)
            len(file_content) if file_content else 0,
            1 if 'eval(' in file_content.lower() else 0 if file_content else 0,
            1 if 'exec(' in file_content.lower() else 0 if file_content else 0,
            1 if any(keyword in file_content.lower() for keyword in ['shell', 'cmd', 'powershell']) else 0 if file_content else 0
        ]
        
        # Pad to 50 features with calculated values (not random)
        while len(features) < 50:
            # Add meaningful derived features
            if len(features) < 35:
                features.extend([
                    length / 100.0,  # Normalized length
                    dot_count / 10.0,  # Normalized dot count
                    dangerous_ext_score * 0.5,  # Weighted dangerous extensions
                    deceptive_double_ext * 0.8,  # Heavily weight deceptive patterns
                    malware_pattern_count * 0.6,  # Weight malware patterns
                    social_pattern_count * 0.4   # Weight social engineering
                ])
            else:
                # Fill remaining with contextual features
                features.append(min(1.0, (length * dot_count * dangerous_ext_score) / 100.0))
        
        return features[:50]
    
    def _analyze_file_rules(self, filename, file_content=""):
        """Enhanced rule-based file analysis with stronger scoring"""
        score = 0
        warnings = []
        filename_lower = filename.lower()
        
        # 1. ENHANCED EXTENSION ANALYSIS
        dangerous_extensions = ['.exe', '.scr', '.bat', '.cmd', '.vbs', '.ps1', '.com', '.pif', '.jar']
        suspicious_extensions = ['.zip', '.rar', '.docm', '.xlsm', '.msi', '.deb', '.dmg']
        
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext in dangerous_extensions:
            score += 45  # Artırıldı
            warnings.append(f'Kural: Tehlikeli uzantı tespit edildi ({file_ext})')
        elif file_ext in suspicious_extensions:
            score += 25  # Artırıldı
            warnings.append(f'Kural: Şüpheli uzantı tespit edildi ({file_ext})')
        
        # 2. CRITICAL: DOUBLE EXTENSION DETECTION
        parts = filename.split('.')
        if len(parts) > 2:
            score += 30  # Base double extension penalty
            warnings.append('Kural: Çift uzantı tespit edildi')
            
            # EXTRA DANGEROUS: Document + Executable combination
            doc_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.png']
            if len(parts) >= 3:
                second_last_ext = f'.{parts[-2].lower()}'
                last_ext = f'.{parts[-1].lower()}'
                if second_last_ext in doc_exts and last_ext in dangerous_extensions:
                    score += 50  # MASSIVE PENALTY for deceptive double extension
                    warnings.append(f'🚨 Kural: KRİTİK TUZAK - Belge uzantısı ardından çalıştırılabilir ({second_last_ext}{last_ext})')
        
        # 3. MALWARE PATTERN ANALYSIS - Enhanced
        malware_patterns = [
            'crack', 'keygen', 'patch', 'serial', 'activator', 'hack', 'cheat',
            'trojan', 'virus', 'malware', 'backdoor', 'keylogger', 'spyware',
            'ransomware', 'worm', 'rootkit', 'exploit'
        ]
        
        social_eng_patterns = [
            'invoice', 'receipt', 'payment', 'refund', 'urgent', 'important',
            'confidential', 'secure', 'update', 'install', 'setup'
        ]
        
        found_malware = [pattern for pattern in malware_patterns if pattern in filename_lower]
        found_social = [pattern for pattern in social_eng_patterns if pattern in filename_lower]
        
        if found_malware:
            score += len(found_malware) * 25  # Artırıldı
            warnings.append(f'Kural: Malware pattern tespit edildi: {", ".join(found_malware[:3])}')
        
        if found_social:
            score += len(found_social) * 20  # Yeni eklendi
            warnings.append(f'Kural: Sosyal mühendislik pattern tespit edildi: {", ".join(found_social[:3])}')
        
        # 4. SYSTEM FILE MIMICKING
        system_names = ['svchost', 'winlogon', 'explorer', 'system32', 'notepad', 'calc', 'cmd', 'powershell']
        if any(name in filename_lower for name in system_names):
            score += 35  # Artırıldı
            warnings.append('Kural: Sistem dosyası taklidi tespit edildi')
        
        # 5. SUSPICIOUS FILENAME CHARACTERISTICS
        # Very short suspicious names
        if len(filename) < 5 and file_ext in dangerous_extensions:
            score += 25
            warnings.append('Kural: Çok kısa şüpheli dosya adı')
        
        # Numbers in filename (version spoofing)
        import re
        if re.search(r'\d{3,}', filename):
            score += 15
            warnings.append('Kural: Şüpheli sayı dizisi tespit edildi')
        
        # 6. CONTENT ANALYSIS (Enhanced)
        if file_content:
            content_lower = file_content.lower()
            
            # Malicious code patterns
            malicious_strings = ['eval(', 'exec(', 'shell_exec', 'system(', 'passthru(', 'popen(']
            found_malicious = [s for s in malicious_strings if s in content_lower]
            if found_malicious:
                score += len(found_malicious) * 25  # Artırıldı
                warnings.append('Kural: Tehlikeli kod yapıları tespit edildi')
            
            # Obfuscation patterns
            obfuscation_patterns = ['\\x', '%u', 'chr(', 'fromcharcode', 'base64']
            if any(pattern in content_lower for pattern in obfuscation_patterns):
                score += 30  # Artırıldı
                warnings.append('Kural: Kod gizleme tespit edildi')
            
            # Network activity indicators
            network_patterns = ['http://', 'https://', 'ftp://', 'download', 'upload']
            if any(pattern in content_lower for pattern in network_patterns):
                score += 20
                warnings.append('Kural: Ağ aktivitesi tespit edildi')
        
        # 7. FILENAME ENTROPY (complexity analysis)
        if len(filename) > 0:
            unique_chars = len(set(filename.lower()))
            if unique_chars / len(filename) > 0.8:  # Very high entropy
                score += 15
                warnings.append('Kural: Yüksek entropi (karmaşık) dosya adı')
        
        return min(score, 100), warnings

    def analyze_email_with_ai(self, email_content, email_subject="", sender_email=""):
        """Analyze email with AI models and pattern matching"""
        try:
            ai_score = 0
            ai_warnings = []
            confidence = 60  # Base confidence for email analysis
            sentiment_score = 0
            phishing_probability = 0
            
            # Combine all text for analysis
            full_text = f"{email_subject} {email_content}".lower()
            
            # 1. PHISHING PATTERNS ANALYSIS
            phishing_patterns = {
                'account_suspension': {
                    'patterns': ['suspend', 'deactivate', 'disable', 'block', 'freeze'],
                    'weight': 25,
                    'description': 'Account suspension threat'
                },
                'urgency_indicators': {
                    'patterns': ['urgent', 'immediate', 'asap', 'expire', 'deadline', 'limited time'],
                    'weight': 20,
                    'description': 'Urgency pressure tactics'
                },
                'verification_requests': {
                    'patterns': ['verify', 'confirm', 'validate', 'authenticate', 'update'],
                    'weight': 18,
                    'description': 'Verification/confirmation request'
                },
                'financial_threats': {
                    'patterns': ['payment', 'billing', 'charge', 'refund', 'fee', 'penalty'],
                    'weight': 22,
                    'description': 'Financial pressure/threat'
                },
                'reward_scams': {
                    'patterns': ['winner', 'prize', 'lottery', 'reward', 'congratulations', 'selected'],
                    'weight': 30,
                    'description': 'Reward/lottery scam indicators'
                },
                'security_alerts': {
                    'patterns': ['security alert', 'breach', 'unauthorized', 'suspicious activity'],
                    'weight': 25,
                    'description': 'Fake security alerts'
                }
            }
            
            # Check for phishing patterns
            pattern_matches = []
            for category, data in phishing_patterns.items():
                matches = [p for p in data['patterns'] if p in full_text]
                if matches:
                    score_boost = min(len(matches) * data['weight'], data['weight'] * 2)
                    ai_score += score_boost
                    phishing_probability += score_boost
                    pattern_matches.append(f"{data['description']}: {', '.join(matches[:2])}")
            
            if pattern_matches:
                ai_warnings.extend([f'AI: {match}' for match in pattern_matches[:3]])
            
            # 2. SENTIMENT ANALYSIS (Basic implementation)
            negative_words = [
                'urgent', 'immediate', 'suspend', 'block', 'expire', 'threat',
                'warning', 'alert', 'danger', 'risk', 'problem', 'error',
                'failure', 'unauthorized', 'breach', 'attack', 'malicious'
            ]
            
            positive_words = [
                'congratulations', 'winner', 'prize', 'reward', 'bonus',
                'free', 'gift', 'offer', 'opportunity', 'benefit', 'lucky'
            ]
            
            negative_count = sum(1 for word in negative_words if word in full_text)
            positive_count = sum(1 for word in positive_words if word in full_text)
            
            # Calculate sentiment (-1 to 1 scale)
            total_sentiment_words = negative_count + positive_count
            if total_sentiment_words > 0:
                sentiment_score = (positive_count - negative_count) / total_sentiment_words
                
                # Extreme sentiment can indicate manipulation
                if abs(sentiment_score) > 0.6:
                    ai_score += 15
                    ai_warnings.append(f'AI: Aşırı duygu manipülasyonu tespit edildi (skor: {sentiment_score:.2f})')
            
            # 3. URL ANALYSIS IN EMAIL
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            urls = re.findall(url_pattern, email_content, re.IGNORECASE)
            
            suspicious_url_patterns = [
                (r'bit\.ly|tinyurl\.com|goo\.gl', 10, 'Shortened URLs'),
                (r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', 20, 'IP address URLs'),
                (r'\.tk|\.ml|\.ga|\.cf', 15, 'Suspicious TLD'),
                (r'[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+\.[a-z]{2,4}', 12, 'Suspicious domain pattern')
            ]
            
            for url in urls:
                for pattern, score_add, description in suspicious_url_patterns:
                    if re.search(pattern, url, re.IGNORECASE):
                        ai_score += score_add
                        ai_warnings.append(f'AI: {description} tespit edildi')
                        break
            
            # URL quantity analysis
            if len(urls) > 3:
                ai_score += min(len(urls) * 5, 20)
                ai_warnings.append(f'AI: Çok fazla URL tespit edildi ({len(urls)} adet)')
            
            # 4. CONTENT STRUCTURE ANALYSIS
            # Check for HTML elements that might indicate phishing
            if '<' in email_content and '>' in email_content:
                confidence += 10  # Higher confidence with HTML content
                
                # Check for suspicious HTML patterns
                suspicious_html = [
                    (r'<form', 15, 'Form elements in email'),
                    (r'<script', 25, 'JavaScript in email'),
                    (r'style=["\'].*display:\s*none', 20, 'Hidden content'),
                    (r'<iframe', 18, 'Embedded frames')
                ]
                
                for pattern, score_add, description in suspicious_html:
                    if re.search(pattern, email_content, re.IGNORECASE):
                        ai_score += score_add
                        ai_warnings.append(f'AI: {description}')
            
            # 5. LANGUAGE AND CHARACTER ANALYSIS
            # Check for character encoding issues or suspicious characters
            if any(ord(c) > 127 for c in email_content[:1000]):  # Check first 1000 chars
                confidence += 5  # International characters are normal
            
            # Check for excessive punctuation
            exclamation_count = email_content.count('!')
            if exclamation_count > 3:
                score_add = min(exclamation_count * 3, 15)
                ai_score += score_add
                ai_warnings.append(f'AI: Aşırı ünlem işareti kullanımı ({exclamation_count})')
            
            # 6. LENGTH AND STRUCTURE ANALYSIS
            content_length = len(email_content)
            
            if content_length < 50:
                ai_score += 15
                ai_warnings.append('AI: Anormal şekilde kısa email içeriği')
            elif content_length > 10000:
                ai_score += 10
                ai_warnings.append('AI: Anormal şekilde uzun email içeriği')
            else:
                confidence += 10  # Normal length increases confidence
            
            # 7. TURKISH SPECIFIC PATTERNS - STRENGTHENED
            turkish_phishing_patterns = [
                'acil durum', 'hemen işlem', 'hesabınız askıya', 'doğrulama gerekli',
                'süre dolmak', 'kazandınız', 'ödül', 'ücretsiz', 'fırsat',
                'şifre sıfırla', 'erişim engellenecek', 'e-devlet', 'edevlet',
                'gov.tr', 'sistem güncelleme', 'güvenlik güncelleme', 'bloke edilecek',
                'hesap iptal', 'derhal', 'acilen', 'hemen tıkla'
            ]
            
            # Government spoofing detection
            government_patterns = ['e-devlet', 'edevlet', 'gov', 'devlet', 'resmi']
            gov_matches = [p for p in government_patterns if p in full_text]
            
            turkish_matches = [p for p in turkish_phishing_patterns if p in full_text]
            if turkish_matches:
                score_add = len(turkish_matches) * 20  # Increased from 12 to 20
                ai_score += score_add
                ai_warnings.append(f'AI: Türkçe phishing kalıpları: {", ".join(turkish_matches[:2])}')
            
            if gov_matches:
                gov_score = len(gov_matches) * 30  # Government spoofing penalty
                ai_score += gov_score
                ai_warnings.append(f'AI: Devlet kurumu taklidi tespit edildi: {", ".join(gov_matches[:2])}')
            
            # 8. FINAL CALCULATIONS
            # Normalize phishing probability
            phishing_probability = min(phishing_probability, 100) / 100.0
            
            # Adjust confidence based on number of analysis factors
            analysis_factors = len(ai_warnings)
            if analysis_factors > 5:
                confidence += 15  # High confidence with many factors
            elif analysis_factors > 2:
                confidence += 10  # Medium confidence
            
            # Cap values
            ai_score = min(ai_score, 100)
            confidence = min(confidence, 100)
            sentiment_score = max(-1, min(1, sentiment_score))
            
            return {
                'ai_score': ai_score,
                'ai_warnings': ai_warnings,
                'confidence': confidence,
                'sentiment_score': sentiment_score,
                'phishing_probability': phishing_probability,
                'urls_found': len(urls),
                'analysis_factors': analysis_factors
            }
            
        except Exception as e:
            logging.error(f"Email AI analysis error: {e}")
            return {
                'ai_score': 50,  # Default moderate risk
                'ai_warnings': [f'AI email analiz hatası: {str(e)}'],
                'confidence': 30,
                'sentiment_score': 0,
                'phishing_probability': 0.5,
                'urls_found': 0,
                'analysis_factors': 0
            } 