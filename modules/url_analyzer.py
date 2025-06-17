import re
import urllib.parse
import tldextract
import whois
from datetime import datetime
import ssl
import socket
import requests
from .ai_engine import HybridAIEngine
import logging

class URLAnalyzer:
    def __init__(self):
        # Initialize AI engine with model support
        self.ai_engine = HybridAIEngine()
        
        # Get AI engine status
        ai_status = self.ai_engine.get_status()
        self.model_available = ai_status['ai_available']
        self.analysis_mode = 'hybrid_ai' if self.model_available else 'enhanced_rules'
        
        # Enhanced suspicious keywords with weights
        self.suspicious_keywords = {
            # High risk keywords
            'high_risk': {
                'free': 15, 'win': 20, 'winner': 25, 'urgent': 20, 'click': 10, 
                'now': 15, 'limited': 18, 'offer': 12, 'bonus': 20, 'gift': 18,
                'prize': 25, 'lottery': 30, 'congratulations': 20, 'bitcoin': 25,
                'crypto': 20, 'investment': 15, 'earn': 12, 'money': 15, 'cash': 18
            },
            # Medium risk keywords  
            'medium_risk': {
                'secure': 8, 'verify': 12, 'update': 10, 'confirm': 10, 
                'suspend': 15, 'account': 8, 'login': 10, 'password': 12,
                'paypal': 15, 'amazon': 10, 'bank': 15, 'credit': 12
            },
            # Phishing patterns
            'phishing': {
                'phishing': 50, 'scam': 45, 'fake': 40, 'suspicious': 30,
                'malware': 50, 'virus': 45, 'trojan': 50
            }
        }
        
        # Enhanced suspicious TLDs with risk scores
        self.suspicious_tlds = {
            '.tk': 35, '.ml': 35, '.ga': 35, '.cf': 35, '.pw': 30,
            '.top': 25, '.click': 30, '.download': 40, '.loan': 45,
            '.work': 20, '.review': 25, '.science': 30, '.racing': 35
        }
        
        # Known phishing/suspicious domains
        self.phishing_domains = {
            'bit.ly': 20, 'tinyurl.com': 20, 'short.link': 25, 'ow.ly': 15,
            't.co': 10, 'goo.gl': 15, 'tiny.cc': 20, 'is.gd': 15,
            'buff.ly': 10, 'soo.gd': 25, 'clicky.me': 30
        }
        
        # Legitimate domains (whitelist) - Enhanced with Turkish sites
        self.legitimate_domains = {
            # International sites
            'google.com', 'microsoft.com', 'apple.com', 'amazon.com',
            'facebook.com', 'twitter.com', 'linkedin.com', 'github.com',
            'stackoverflow.com', 'wikipedia.org', 'youtube.com', 'instagram.com',
            'whatsapp.com', 'telegram.org', 'discord.com', 'netflix.com',
            'spotify.com', 'paypal.com', 'ebay.com', 'airbnb.com',
            
            # Turkish Banks and Financial
            'garanti.com.tr', 'akbank.com', 'isbank.com.tr', 'yapikredi.com.tr',
            'ziraat.com.tr', 'vakifbank.com.tr', 'halkbank.com.tr', 'denizbank.com',
            'finansbank.com.tr', 'ingbank.com.tr', 'teb.com.tr', 'odeabank.com',
            'qnbfinansbank.com', 'sekerbankasi.com.tr', 'sekerbank.com.tr',
            
            # Turkish E-commerce
            'trendyol.com', 'hepsiburada.com', 'n11.com', 'gittigidiyor.com',
            'sahibinden.com', 'arabam.com', 'emlakjet.com', 'ciceksepeti.com',
            'getir.com', 'yemeksepeti.com', 'ticimax.com', 'pazarama.com',
            
            # Turkish News and Media
            'hurriyet.com.tr', 'sabah.com.tr', 'milliyet.com.tr', 'sozcu.com.tr', 
            'haberturk.com', 'ntv.com.tr', 'cnnturk.com', 'aa.com.tr',
            'trt.net.tr', 'star.com.tr', 'posta.com.tr', 'takvim.com.tr',
            
            # Turkish Retail and Shopping
            'a101.com.tr', 'bim.com.tr', 'migros.com.tr', 'carrefoursa.com',
            'teknosa.com', 'vatan.com', 'mediamarkt.com.tr', 'gold.com.tr',
            'defacto.com.tr', 'lcwaikiki.com', 'koton.com', 'mango.com',
            'zara.com', 'boyner.com.tr', 'beymen.com', 'morhipo.com',
            
            # Turkish Government and Education
            'turkiye.gov.tr', 'e-devlet.gov.tr', 'resmigazete.gov.tr',
            'meb.gov.tr', 'saglik.gov.tr', 'nvi.gov.tr', 'sgk.gov.tr',
            'tuik.gov.tr', 'maliye.gov.tr', 'adalet.gov.tr', 'jandarma.gov.tr',
            'erzurum.edu.tr', 'boun.edu.tr', 'metu.edu.tr', 'itu.edu.tr',
            'ankara.edu.tr', 'gazi.edu.tr', 'hacettepe.edu.tr', 'ytu.edu.tr',
            
            # Turkish Telecom and Utilities
            'turkcell.com.tr', 'vodafone.com.tr', 'turk.net', 'superonline.net',
            'ttnet.com.tr', 'migrosnet.com.tr', 'koc.net', 'millenicom.com.tr'
        }
        
        # URL pattern analysis
        self.suspicious_patterns = [
            (r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', 35, 'IP address instead of domain'),
            (r'[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+\.', 15, 'Multiple hyphens in domain'),
            (r'[0-9]{5,}', 20, 'Long number sequence'),
            (r'[a-zA-Z]{1}[0-9]{3,}[a-zA-Z]{1}', 15, 'Mixed alphanumeric pattern'),
            (r'www\d+\.', 25, 'Numbered subdomain'),
            (r'[a-zA-Z0-9]{20,}', 18, 'Very long domain name'),
            (r'\.php\?.*=.*&.*=', 12, 'Complex PHP parameters'),
            (r'[%][0-9a-fA-F]{2}', 10, 'URL encoding detected')
        ]

    def analyze(self, url):
        """Enhanced URL analysis with AI integration"""
        try:
            # URL'yi normalize et
            original_url = url
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            try:
                parsed_url = urllib.parse.urlparse(url)
                domain = parsed_url.netloc.lower()
                if not domain:
                    raise ValueError("Geçersiz URL formatı: domain bulunamadı")
            except Exception as e:
                raise ValueError(f"URL ayrıştırma hatası: {str(e)}")
            
            risk_score = 0
            warnings = []
            details = {}
            
            # 1. BASIC CHECKS
            try:
                basic_score, basic_warnings, basic_details = self._basic_analysis(url, domain)
                risk_score += basic_score
                warnings.extend(basic_warnings)
                details.update(basic_details)
            except Exception as e:
                logging.error(f"Basic analysis error: {e}")
                warnings.append("Temel analiz hatası")
                risk_score += 50  # Default risk for analysis failure
            
            # 2. ENHANCED RULE-BASED ANALYSIS
            try:
                rule_score, rule_warnings = self._enhanced_rule_analysis(url, domain)
                risk_score += rule_score
                warnings.extend(rule_warnings)
            except Exception as e:
                logging.error(f"Rule-based analysis error: {e}")
                warnings.append("Kural tabanlı analiz hatası")
                risk_score += 30  # Default risk for rule analysis failure
            
            # 3. AI-POWERED ANALYSIS
            try:
                ai_results = self.ai_engine.analyze_url_with_ai(url)
                ai_score = ai_results['ai_score']
                warnings.extend(ai_results['ai_warnings'])
                details['ai_confidence'] = ai_results['confidence']
                details['api_checks'] = ai_results['api_checks']
            except Exception as e:
                logging.error(f"AI analysis error: {e}")
                warnings.append("AI analizi hatası")
                ai_score = 50  # Default AI risk score
                details['ai_confidence'] = 30
            
            # 4. HYBRID SCORING - Eğitilmiş model ile optimal ağırlıklar
            if self.model_available and ai_score > 0:
                # Eğitilmiş ML model mevcut - dengeli ağırlık kullan
                final_score = (risk_score * 0.4) + (ai_score * 0.6)
                
                # Whitelist kontrolü - güvenilir siteler için ML'i sınırla
                if details.get('whitelisted', False):
                    final_score = min(final_score, 15)  # Güvenilir siteler max 15 puan
            else:
                # Sadece rule-based scoring kullan
                final_score = risk_score
            
            # 5. DETERMINE RISK LEVEL
            try:
                risk_level, color = self._determine_risk_level(final_score)
            except Exception as e:
                logging.error(f"Risk level determination error: {e}")
                risk_level = "Orta Risk"
                color = "orange"
            
            # AI güven analizi hesapla
            ai_confidence = self._calculate_ai_confidence(final_score, ai_results, details)
            
            return {
                'risk_score': round(min(final_score, 100), 1),
                'risk_level': risk_level,
                'color': color,
                'warnings': warnings,
                'details': details,
                'ai_confidence': ai_confidence,
                'recommendations': self._get_enhanced_recommendations(final_score, ai_results),
                'analysis_method': self.analysis_mode
            }
            
        except Exception as e:
            logging.exception(f"URL analysis failed: {e}")
            return {
                'risk_score': 50.0,
                'risk_level': 'Analiz Hatası',
                'color': 'gray',
                'warnings': [f'Analiz hatası: {str(e)}'],
                'details': {'error': str(e)},
                'recommendations': ['URL formatını kontrol edin', 'Geçerli bir URL girdiğinizden emin olun'],
                'analysis_method': 'error'
            }

    def _basic_analysis(self, url, domain):
        """Enhanced basic analysis"""
        score = 0
        warnings = []
        details = {}
        
        # Domain whitelist kontrolü (daha kesin eşleşme)
        is_whitelisted = False
        for legit_domain in self.legitimate_domains:
            if domain == legit_domain or domain.endswith('.' + legit_domain):
                is_whitelisted = True
                break
        
        details['whitelisted'] = is_whitelisted
        
        if is_whitelisted:
            # Güvenilir siteler için çok düşük başlangıç skoru
            score = 2  # Güvenilir siteler için çok düşük skor
            details['whitelist_bonus'] = True
            warnings.append('✅ Güvenilir domain tespit edildi')
        else:
            details['whitelist_bonus'] = False
            # Güvenilir olmayan siteler için başlangıç skoru
            score = 30  # Bilinmeyen siteler için başlangıç riski
        
        # HTTPS kontrolü
        if not url.startswith('https://'):
            if is_whitelisted:
                score += 10  # Reduced penalty for whitelisted sites
                warnings.append('HTTPS kullanmıyor ama güvenilir site')
            else:
                score += 25  # Full penalty for unknown sites
                warnings.append('URL HTTPS kullanmıyor - güvenli değil')
        details['https'] = url.startswith('https://')
        
        # URL uzunluğu analizi (whitelist için daha toleranslı)
        if len(url) > 100:
            if is_whitelisted:
                score += 5  # Minimal penalty for whitelisted sites
            else:
                score += 15
                warnings.append('Çok uzun URL')
        elif len(url) > 200:
            if is_whitelisted:
                score += 10
            else:
                score += 25
                warnings.append('Aşırı uzun URL - şüpheli')
            
        details['url_length'] = len(url)
        
        return score, warnings, details

    def _enhanced_rule_analysis(self, url, domain):
        """Enhanced rule-based analysis"""
        score = 0
        warnings = []
        
        # Enhanced keyword analysis
        keyword_score, keyword_warnings = self._analyze_keywords_weighted(url)
        score += keyword_score
        warnings.extend(keyword_warnings)
        
        # Domain analysis
        domain_score, domain_warnings = self._analyze_domain_enhanced(domain)
        score += domain_score
        warnings.extend(domain_warnings)
        
        # Pattern analysis
        pattern_score, pattern_warnings = self._analyze_patterns(url)
        score += pattern_score
        warnings.extend(pattern_warnings)
        
        # Subdomain analysis
        subdomain_score, subdomain_warnings = self._analyze_subdomains(domain)
        score += subdomain_score
        warnings.extend(subdomain_warnings)
        
        return score, warnings

    def _analyze_keywords_weighted(self, url):
        """Weighted keyword analysis"""
        score = 0
        warnings = []
        url_lower = url.lower()
        found_keywords = []
        
        # Check high risk keywords
        for keyword, weight in self.suspicious_keywords['high_risk'].items():
            if keyword in url_lower:
                score += weight
                found_keywords.append(f"{keyword}({weight})")
        
        # Check medium risk keywords
        for keyword, weight in self.suspicious_keywords['medium_risk'].items():
            if keyword in url_lower:
                score += weight
                found_keywords.append(f"{keyword}({weight})")
        
        # Check phishing keywords
        for keyword, weight in self.suspicious_keywords['phishing'].items():
            if keyword in url_lower:
                score += weight
                found_keywords.append(f"{keyword}({weight})")
        
        if found_keywords:
            warnings.append(f'Şüpheli kelimeler: {", ".join(found_keywords[:5])}')
        
        return score, warnings

    def _analyze_domain_enhanced(self, domain):
        """Enhanced domain analysis"""
        score = 0
        warnings = []
        
        try:
            extracted = tldextract.extract(domain)
            tld = '.' + extracted.suffix
            subdomain = extracted.subdomain
            main_domain = extracted.domain
            
            # TLD analysis with weights
            if tld in self.suspicious_tlds:
                tld_score = self.suspicious_tlds[tld]
                score += tld_score
                warnings.append(f'Şüpheli domain uzantısı: {tld} (+{tld_score})')
            
            # Phishing domain check
            full_domain = f"{main_domain}{tld}"
            if full_domain in self.phishing_domains:
                phish_score = self.phishing_domains[full_domain]
                score += phish_score
                warnings.append(f'Bilinen şüpheli domain: {full_domain} (+{phish_score})')
            
            # Domain age analysis (improved)
            try:
                domain_info = whois.whois(full_domain)
                if domain_info.creation_date:
                    if isinstance(domain_info.creation_date, list):
                        creation_date = domain_info.creation_date[0]
                    else:
                        creation_date = domain_info.creation_date
                    
                    domain_age = (datetime.now() - creation_date).days
                    
                    if domain_age < 7:
                        score += 40
                        warnings.append('Çok yeni domain (1 haftadan az)')
                    elif domain_age < 30:
                        score += 25
                        warnings.append('Yeni domain (30 günden az)')
                    elif domain_age < 90:
                        score += 10
                        warnings.append('Nispeten yeni domain (90 günden az)')
            except:
                score += 15
                warnings.append('Domain yaşı bilgisi alınamadı')
            
        except Exception as e:
            score += 20
            warnings.append(f'Domain analiz hatası: {str(e)}')
        
        return score, warnings

    def _analyze_patterns(self, url):
        """URL pattern analysis"""
        score = 0
        warnings = []
        
        for pattern, pattern_score, description in self.suspicious_patterns:
            if re.search(pattern, url):
                score += pattern_score
                warnings.append(f'{description} (+{pattern_score})')
        
        return score, warnings

    def _analyze_subdomains(self, domain):
        """Advanced subdomain analysis"""
        score = 0
        warnings = []
        
        subdomain_count = domain.count('.')
        if subdomain_count > 3:
            score += 20
            warnings.append(f'Çok fazla subdomain ({subdomain_count})')
        elif subdomain_count > 5:
            score += 35
            warnings.append(f'Aşırı subdomain sayısı ({subdomain_count})')
        
        # Check for suspicious subdomain patterns
        suspicious_subdomains = [
            'secure', 'login', 'verify', 'account', 'update',
            'confirm', 'support', 'service', 'admin'
        ]
        
        for sus_sub in suspicious_subdomains:
            if sus_sub in domain:
                score += 12
                warnings.append(f'Şüpheli subdomain: {sus_sub}')
                break
        
        return score, warnings

    def _calculate_hybrid_score(self, rule_score, ai_score):
        """Calculate hybrid score with intelligent weighting"""
        if not self.ai_engine.ai_available or ai_score == 0:
            return rule_score
        
        # Check if this is a whitelisted domain
        # We need to pass domain info somehow - let's modify this
        
        # Standard hybrid calculation: Rules 40% + AI 40% + APIs 20%
        hybrid_score = (rule_score * 0.4) + (ai_score * 0.4)
        
        # If rule score is very low (indicating whitelist), reduce AI influence
        if rule_score < 10:  # Strong indication of whitelisted domain
            # For whitelisted sites, trust rules more than AI
            hybrid_score = (rule_score * 0.8) + (ai_score * 0.2)
            # Cap the maximum score for whitelisted sites
            hybrid_score = min(hybrid_score, 25)
        
        return max(0, hybrid_score)

    def _calculate_ai_confidence(self, final_score, ai_results, details):
        """AI güven seviyesini hesapla"""
        confidence_factors = {
            'base_confidence': 50,  # Başlangıç güveni
            'model_bonus': 0,
            'whitelist_bonus': 0,
            'consistency_bonus': 0,
            'data_quality_bonus': 0
        }
        
        # Model kullanılabilirliği bonusu
        if self.model_available:
            confidence_factors['model_bonus'] = 25
        
        # Whitelist bonusu
        if details.get('whitelisted', False):
            confidence_factors['whitelist_bonus'] = 20
        
        # Rule-based ve AI tutarlılığı
        if ai_results and 'ai_score' in ai_results:
            rule_score = final_score - (ai_results['ai_score'] * 0.6)  # Yaklaşık rule score
            score_diff = abs(rule_score - ai_results['ai_score'])
            
            if score_diff < 10:  # Çok tutarlı
                confidence_factors['consistency_bonus'] = 15
            elif score_diff < 20:  # Tutarlı
                confidence_factors['consistency_bonus'] = 10
            elif score_diff < 30:  # Kısmen tutarlı
                confidence_factors['consistency_bonus'] = 5
        
        # Veri kalitesi bonusu
        if details.get('https', False):
            confidence_factors['data_quality_bonus'] += 5
        if len(details.get('warnings', [])) < 3:  # Az uyarı = daha net sonuç
            confidence_factors['data_quality_bonus'] += 5
        
        # Toplam güven seviyesi
        total_confidence = sum(confidence_factors.values())
        
        # 0-100 arasında normalize et
        normalized_confidence = min(100, max(20, total_confidence))
        
        # Güven seviyesi kategorisi
        if normalized_confidence >= 90:
            confidence_level = "Çok Yüksek"
            confidence_color = "#006400"  # Dark green
        elif normalized_confidence >= 75:
            confidence_level = "Yüksek"
            confidence_color = "#32CD32"  # Lime green
        elif normalized_confidence >= 60:
            confidence_level = "Orta"
            confidence_color = "#FFD700"  # Gold
        elif normalized_confidence >= 45:
            confidence_level = "Düşük"
            confidence_color = "#FFA500"  # Orange
        else:
            confidence_level = "Çok Düşük"
            confidence_color = "#DC143C"  # Crimson
        
        return {
            'score': round(normalized_confidence, 1),
            'level': confidence_level,
            'color': confidence_color,
            'factors': confidence_factors,
            'description': self._get_confidence_description(normalized_confidence)
        }

    def _get_confidence_description(self, confidence_score):
        """Güven seviyesi açıklaması"""
        if confidence_score >= 90:
            return "AI analizi son derece güvenilir. Sonuçlara kesin olarak güvenebilirsiniz."
        elif confidence_score >= 75:
            return "AI analizi güvenilir. Sonuçlar yüksek doğrulukta."
        elif confidence_score >= 60:
            return "AI analizi makul güvenilirlikte. Ek doğrulama önerilir."
        elif confidence_score >= 45:
            return "AI analizi düşük güvenilirlikte. Manuel doğrulama gerekli."
        else:
            return "AI analizi çok düşük güvenilirlikte. Sonuçları dikkatli değerlendirin."

    def _determine_risk_level(self, score):
        """Gelişmiş risk seviyesi belirleme - Daha hassas eğri"""
        if score >= 85:
            return 'Kritik Tehlike', '#8B0000'  # Dark red
        elif score >= 70:
            return 'Yüksek Risk', '#DC143C'     # Crimson
        elif score >= 55:
            return 'Orta-Yüksek Risk', '#FF6347' # Tomato
        elif score >= 40:
            return 'Orta Risk', '#FF8C00'       # Dark orange
        elif score >= 25:
            return 'Düşük-Orta Risk', '#FFA500' # Orange
        elif score >= 15:
            return 'Düşük Risk', '#FFD700'      # Gold
        elif score >= 8:
            return 'Minimal Risk', '#9ACD32'    # Yellow green
        elif score >= 3:
            return 'Güvenli', '#32CD32'         # Lime green
        else:
            return 'Çok Güvenli', '#006400'     # Dark green

    def _get_enhanced_recommendations(self, risk_score, ai_results):
        """Enhanced recommendations based on hybrid analysis"""
        recommendations = []
        
        if risk_score >= 80:
            recommendations.extend([
                '🚨 Bu URL\'ye kesinlikle erişmeyin!',
                '⚠️ Bilgisayarınızı antivirüs ile tarayın',
                '🔒 Kişisel bilgilerinizi asla girmeyin',
                '📧 URL\'yi güvenlik ekibinize bildirin'
            ])
        elif risk_score >= 60:
            recommendations.extend([
                '⚠️ Bu URL yüksek risk taşıyor',
                '🔍 Kaynağını mutlaka doğrulayın',
                '🛡️ VPN kullanarak erişmeyi düşünün',
                '💻 Sanal makine üzerinde test edin'
            ])
        elif risk_score >= 40:
            recommendations.extend([
                '🔍 Bu URL\'ye dikkatli yaklaşın',
                '✅ Resmi kaynaklardan doğrulayın',
                '🔒 Kişisel bilgi girmeden önce iki kez düşünün',
                '📱 Mobil cihazdan erişmeyi tercih edin'
            ])
        elif risk_score >= 20:
            recommendations.extend([
                '👁️ URL nispeten güvenli görünüyor',
                '🔍 Yine de dikkatli olun',
                '🌐 HTTPS bağlantısını tercih edin'
            ])
        else:
            recommendations.extend([
                '✅ URL güvenli görünüyor',
                '🛡️ Standart güvenlik önlemlerini almayı unutmayın'
            ])
        
        # AI-specific recommendations
        if self.ai_engine.ai_available:
            if ai_results['confidence'] > 80:
                recommendations.append('🤖 AI analizi yüksek güven seviyesi gösteriyor')
            
            api_checks = ai_results.get('api_checks', {})
            if any(score == 100 for score in api_checks.values() if isinstance(score, (int, float))):
                recommendations.append('⚠️ Güvenlik API\'leri tehdit tespit etti')
        
        return recommendations 