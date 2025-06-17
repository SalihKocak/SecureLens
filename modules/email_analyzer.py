import re
import urllib.parse
import tldextract
from datetime import datetime
import ssl
import socket
import requests
from .ai_engine import HybridAIEngine
import logging
import langdetect
from bs4 import BeautifulSoup

class EmailAnalyzer:
    def __init__(self):
        # Initialize AI engine with model support
        self.ai_engine = HybridAIEngine()
        
        # Get AI engine status
        ai_status = self.ai_engine.get_status()
        self.model_available = ai_status['ai_available']
        self.analysis_mode = 'hybrid_ai' if self.model_available else 'enhanced_rules'
        
        # Enhanced suspicious keywords with weights for emails
        self.suspicious_keywords = {
            # High risk keywords
            'high_risk': {
                'urgent': 25, 'immediately': 20, 'suspend': 30, 'blocked': 25,
                'verify': 20, 'confirm': 18, 'expire': 22, 'expired': 25,
                'winner': 30, 'lottery': 35, 'prize': 28, 'congratulations': 25,
                'free': 15, 'bonus': 20, 'gift': 18, 'offer': 12,
                'bitcoin': 30, 'crypto': 25, 'investment': 20, 'earn': 15,
                'click here': 20, 'act now': 25, 'limited time': 18
            },
            # Medium risk keywords  
            'medium_risk': {
                'account': 10, 'login': 12, 'password': 15, 'security': 8,
                'update': 10, 'notification': 8, 'alert': 12, 'warning': 10,
                'paypal': 15, 'amazon': 10, 'bank': 15, 'credit': 12,
                'payment': 12, 'invoice': 10, 'receipt': 8, 'refund': 15
            },
            # Phishing patterns
            'phishing': {
                'phishing': 50, 'scam': 45, 'fake': 40, 'suspicious': 30,
                'malware': 50, 'virus': 45, 'trojan': 50, 'deactivate': 35,
                'restore': 20, 'reactivate': 25, 'validate': 18
            },
            # Turkish specific - STRENGTHENED
            'turkish_high_risk': {
                'acil': 35, 'hemen': 30, 'askıya': 40, 'bloke': 35,
                'doğrula': 30, 'onayla': 25, 'süre': 25, 'kazandınız': 40,
                'para': 25, 'ödül': 35, 'hediye': 25, 'teklif': 18,
                'ücretsiz': 20, 'bonus': 25, 'fırsat': 20, 'sıfırla': 35,
                'engellenecek': 40, 'iptal': 30, 'devlet': 45, 'edevlet': 50,
                'gov': 45, 'resmi': 35, 'sistem': 20, 'güncelleme': 25
            }
        }
        
        # Suspicious sender domains
        self.suspicious_sender_domains = {
            # Temporary email services
            '10minutemail.com': 40, 'guerrillamail.com': 35, 'mailinator.com': 30,
            'tempmail.org': 35, 'yopmail.com': 30, 'throwaway.email': 40,
            
            # Suspicious TLDs for email - STRENGTHENED
            '.tk': 50, '.ml': 50, '.ga': 50, '.cf': 50, '.pw': 45,
            '.top': 35, '.click': 40, '.online': 35, '.work': 30,
            '.racing': 45, '.science': 40, '.download': 45
        }
        
        # Legitimate email domains (whitelist)
        self.legitimate_sender_domains = {
            # Major email providers
            'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com',
            'icloud.com', 'protonmail.com', 'live.com', 'msn.com',
            
            # Turkish email providers
            'mynet.com', 'turk.net', 'superonline.net', 'ttnet.com.tr',
            
            # Business/Corporate
            'microsoft.com', 'google.com', 'apple.com', 'amazon.com',
            'paypal.com', 'ebay.com', 'facebook.com', 'twitter.com',
            
            # Turkish Banks and Financial
            'garanti.com.tr', 'akbank.com', 'isbank.com.tr', 'yapikredi.com.tr',
            'ziraat.com.tr', 'vakifbank.com.tr', 'halkbank.com.tr', 'denizbank.com',
            
            # Turkish E-commerce
            'trendyol.com', 'hepsiburada.com', 'n11.com', 'gittigidiyor.com',
            'sahibinden.com', 'getir.com', 'yemeksepeti.com'
        }
        
        # Suspicious email patterns
        self.suspicious_patterns = [
            (r'[Cc]lick\s+here\s+now', 20, 'Aggressive call to action'),
            (r'[Aa]ct\s+now', 25, 'Urgent action required'),
            (r'[Ll]imited\s+time', 18, 'Time pressure tactic'),
            (r'[Uu]rgent[!]*', 22, 'Urgency indicator'),
            (r'[Cc]ongratulations[!]+', 25, 'Fake congratulations'),
            (r'[Yy]ou\s+have\s+won', 30, 'Lottery/prize scam'),
            (r'[Vv]erify\s+your\s+account', 20, 'Account verification phishing'),
            (r'[Cc]lick\s+the\s+link\s+below', 18, 'Phishing link'),
            (r'[Ss]uspended\s+account', 25, 'Account suspension threat'),
            (r'[Ee]xpires?\s+in\s+\d+', 20, 'Expiration pressure'),
            (r'[Ff]ree\s+money', 25, 'Money scam'),
            (r'[Ii]mmediate\s+action', 22, 'Immediate action required'),
            (r'\$\d+[,.]?\d*\s+million', 35, 'Large money amount'),
            (r'[Bb]itcoin.*investment', 30, 'Crypto scam'),
            (r'[Pp]hishing.*attempt', 50, 'Phishing warning'),
            
            # Turkish patterns - STRENGTHENED
            (r'[Hh]emen\s+tıkla', 35, 'Turkish urgent click'),
            (r'[Aa]cil.*işlem', 40, 'Turkish urgent action'),
            (r'[Hh]esabınız.*askıya', 45, 'Turkish account suspension'),
            (r'[Dd]oğrula.*hesap', 35, 'Turkish account verification'),
            (r'[Ü]cretsiz.*para', 35, 'Turkish free money'),
            (r'[Kk]azandınız.*ödül', 40, 'Turkish prize won'),
            (r'[Şş]ifre.*sıfırla', 40, 'Turkish password reset'),
            (r'[Ee]rişim.*engellenecek', 45, 'Turkish access blocked threat'),
            (r'[Ee]-[Dd]evlet', 50, 'Turkish government spoofing'),
            (r'[Gg]üvenlik.*güncelleme', 35, 'Turkish security update'),
            (r'[Ss]istem.*güncelleme', 30, 'Turkish system update')
        ]
        
        # URL patterns in emails
        self.url_patterns = [
            (r'bit\.ly/', 15, 'Shortened URL'),
            (r'tinyurl\.com/', 15, 'Shortened URL'),
            (r'goo\.gl/', 12, 'Google shortened URL'),
            (r't\.co/', 10, 'Twitter shortened URL'),
            (r'[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+\.[a-z]{2,4}', 18, 'Suspicious domain pattern'),
            (r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', 25, 'IP address in URL'),
            (r'\.tk/', 20, 'Suspicious TLD'),
            (r'\.ml/', 20, 'Suspicious TLD'),
            (r'\.ga/', 20, 'Suspicious TLD'),
            (r'\.cf/', 20, 'Suspicious TLD')
        ]

    def analyze(self, email_content, email_subject="", sender_email=""):
        """Enhanced email analysis with AI integration"""
        try:
            if not email_content or len(email_content.strip()) < 5:
                return {
                    'risk_score': 0.0,
                    'risk_level': 'Geçersiz Email',
                    'color': 'gray',
                    'warnings': ['Geçersiz email içeriği'],
                    'details': {},
                    'recommendations': ['Geçerli bir email içeriği girin'],
                    'analysis_method': 'error'
                }
            
            email_content = email_content.strip()
            email_subject = email_subject.strip() if email_subject else ""
            sender_email = sender_email.strip() if sender_email else ""
            
            risk_score = 0
            warnings = []
            details = {}
            
            # 1. BASIC EMAIL ANALYSIS
            try:
                basic_score, basic_warnings, basic_details = self._basic_email_analysis(
                    email_content, email_subject, sender_email
                )
                risk_score += basic_score
                warnings.extend(basic_warnings)
                details.update(basic_details)
            except Exception as e:
                logging.error(f"Basic email analysis error: {e}")
                warnings.append("Temel email analizi hatası")
                risk_score += 50
            
            # 2. ENHANCED RULE-BASED ANALYSIS
            try:
                rule_score, rule_warnings = self._enhanced_rule_analysis(
                    email_content, email_subject, sender_email
                )
                risk_score += rule_score
                warnings.extend(rule_warnings)
            except Exception as e:
                logging.error(f"Rule-based email analysis error: {e}")
                warnings.append("Kural tabanlı email analizi hatası")
                risk_score += 30
            
            # 3. AI-POWERED ANALYSIS
            try:
                ai_results = self.ai_engine.analyze_email_with_ai(
                    email_content, email_subject, sender_email
                )
                ai_score = ai_results['ai_score']
                warnings.extend(ai_results['ai_warnings'])
                details['ai_confidence'] = ai_results['confidence']
                details['sentiment_score'] = ai_results.get('sentiment_score', 0)
                details['phishing_probability'] = ai_results.get('phishing_probability', 0)
            except Exception as e:
                logging.error(f"AI email analysis error: {e}")
                warnings.append("AI email analizi hatası")
                ai_score = 50
                details['ai_confidence'] = 30
            
            # 4. HYBRID SCORING
            final_score = self._calculate_hybrid_score(risk_score, ai_score, details)
            
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
            logging.exception(f"Email analysis failed: {e}")
            return {
                'risk_score': 50.0,
                'risk_level': 'Analiz Hatası',
                'color': 'gray',
                'warnings': [f'Email analiz hatası: {str(e)}'],
                'details': {'error': str(e)},
                'recommendations': ['Email formatını kontrol edin', 'Email içeriğini tekrar gözden geçirin'],
                'analysis_method': 'error'
            }

    def _basic_email_analysis(self, email_content, subject, sender):
        """Basic email analysis"""
        score = 0
        warnings = []
        details = {}
        
        # Sender domain analysis
        sender_score, sender_warnings, sender_details = self._analyze_sender_domain(sender)
        score += sender_score
        warnings.extend(sender_warnings)
        details.update(sender_details)
        
        # Subject analysis
        subject_score, subject_warnings = self._analyze_subject(subject)
        score += subject_score
        warnings.extend(subject_warnings)
        details['subject_analysis'] = {'score': subject_score, 'warnings': len(subject_warnings)}
        
        # Content length analysis
        content_length = len(email_content)
        details['content_length'] = content_length
        
        if content_length < 50:
            score += 15
            warnings.append('Çok kısa email içeriği')
        elif content_length > 5000:
            score += 10
            warnings.append('Çok uzun email içeriği')
        
        # HTML analysis
        html_score, html_warnings = self._analyze_html_content(email_content)
        score += html_score
        warnings.extend(html_warnings)
        details['contains_html'] = '<' in email_content and '>' in email_content
        
        # Language detection
        try:
            detected_lang = langdetect.detect(email_content)
            details['detected_language'] = detected_lang
            if detected_lang not in ['en', 'tr']:
                score += 5
                warnings.append(f'Beklenmeyen dil tespit edildi: {detected_lang}')
        except:
            details['detected_language'] = 'unknown'
            score += 8
            warnings.append('Dil tespit edilemedi')
        
        return score, warnings, details

    def _analyze_sender_domain(self, sender_email):
        """Analyze sender email domain"""
        score = 0
        warnings = []
        details = {}
        
        if not sender_email or '@' not in sender_email:
            score += 20
            warnings.append('Geçersiz gönderen email adresi')
            details['sender_valid'] = False
            return score, warnings, details
        
        try:
            domain = sender_email.split('@')[1].lower()
            details['sender_domain'] = domain
            details['sender_valid'] = True
            
            # Whitelist check
            if domain in self.legitimate_sender_domains:
                details['sender_whitelisted'] = True
                warnings.append('✅ Güvenilir gönderen domaini')
                # Güvenilir domainler için çok düşük skor
                score = max(0, score - 10)
            else:
                details['sender_whitelisted'] = False
                
                # Suspicious domain check
                for sus_domain, sus_score in self.suspicious_sender_domains.items():
                    if domain == sus_domain or domain.endswith(sus_domain):
                        score += sus_score
                        warnings.append(f'Şüpheli gönderen domaini: {domain} (+{sus_score})')
                        break
                else:
                    # Unknown domain - mild penalty
                    score += 10
                    warnings.append('Bilinmeyen gönderen domaini')
            
                         # Check for spoofed email patterns
            if self._is_spoofed_email(sender_email):
                score += 25
                warnings.append('Sahte email adresi şüphesi')
                details['spoofing_detected'] = True
            else:
                details['spoofing_detected'] = False
            
            # Government domain spoofing check
            if self._is_government_spoofing(sender_email):
                score += 50  # Heavy penalty for government spoofing
                warnings.append('⚠️ DEVLET KURUMU TAKLİDİ TESPİT EDİLDİ!')
                details['government_spoofing'] = True
            else:
                details['government_spoofing'] = False
                
        except Exception as e:
            score += 25
            warnings.append(f'Gönderen analiz hatası: {str(e)}')
            details['sender_valid'] = False
        
        return score, warnings, details

    def _is_spoofed_email(self, email):
        """Check for email spoofing patterns"""
        try:
            local_part, domain = email.split('@')
            
            # Check for suspicious patterns in local part
            suspicious_local_patterns = [
                r'admin\d+', r'support\d+', r'service\d+', r'security\d+',
                r'no-reply\d+', r'noreply\d+', r'info\d+', r'help\d+'
            ]
            
            for pattern in suspicious_local_patterns:
                if re.search(pattern, local_part, re.IGNORECASE):
                    return True
            
            # Check for mixed case in suspicious way
            if local_part.count('.') > 3 or local_part.count('-') > 3:
                return True
                
            return False
        except:
            return False

    def _is_government_spoofing(self, email):
        """Check for government domain spoofing"""
        if not email or '@' not in email:
            return False
        
        try:
            domain = email.split('@')[1].lower()
            
            # Turkish government domains and their spoofing attempts
            government_keywords = [
                'edevlet', 'e-devlet', 'gov', 'devlet', 'tc', 'turkiye',
                'saglik', 'maliye', 'meb', 'nvi', 'sgk', 'jandarma',
                'emniyet', 'adalet', 'tuik', 'resmi'
            ]
            
            # Check if domain contains government keywords but uses suspicious TLD
            suspicious_gov_tlds = ['.tk', '.ml', '.ga', '.cf', '.pw', '.top', '.click', '.online']
            
            for keyword in government_keywords:
                if keyword in domain:
                    # If government keyword exists, check TLD
                    for sus_tld in suspicious_gov_tlds:
                        if domain.endswith(sus_tld):
                            return True
                    
                    # Check if it's not official .gov.tr or .tr domain
                    if not (domain.endswith('.gov.tr') or domain.endswith('.tr')):
                        if any(ext in domain for ext in ['.com', '.net', '.org']):
                            return True
            
            return False
        except:
            return False

    def _analyze_subject(self, subject):
        """Analyze email subject"""
        score = 0
        warnings = []
        
        if not subject:
            score += 10
            warnings.append('Email konusu yok')
            return score, warnings
        
        subject_lower = subject.lower()
        
        # Check for excessive punctuation
        exclamation_count = subject.count('!')
        if exclamation_count > 1:
            score += min(exclamation_count * 5, 20)
            warnings.append(f'Aşırı ünlem işareti kullanımı ({exclamation_count})')
        
        # Check for ALL CAPS
        if subject.isupper() and len(subject) > 10:
            score += 15
            warnings.append('Tamamen büyük harf kullanımı')
        
        # Keyword analysis in subject
        for category, keywords in self.suspicious_keywords.items():
            for keyword, weight in keywords.items():
                if keyword in subject_lower:
                    score += weight
                    warnings.append(f'Şüpheli konu kelimesi: {keyword} (+{weight})')
        
        return score, warnings

    def _analyze_html_content(self, content):
        """Analyze HTML content in email"""
        score = 0
        warnings = []
        
        if '<' not in content or '>' not in content:
            return score, warnings
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for suspicious links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href:
                    # Check for URL patterns
                    for pattern, pattern_score, description in self.url_patterns:
                        if re.search(pattern, href):
                            score += pattern_score
                            warnings.append(f'{description} tespit edildi: {href[:50]}...')
                            break
            
            # Check for hidden content
            hidden_elements = soup.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden'))
            if hidden_elements:
                score += 20
                warnings.append(f'Gizli HTML içeriği tespit edildi ({len(hidden_elements)} adet)')
            
            # Check for suspicious form elements
            forms = soup.find_all('form')
            if forms:
                score += 15
                warnings.append('Email içinde form tespit edildi')
            
            # Check for JavaScript
            scripts = soup.find_all('script')
            if scripts:
                score += 25
                warnings.append('Email içinde JavaScript tespit edildi')
                
        except Exception as e:
            score += 10
            warnings.append(f'HTML analiz hatası: {str(e)}')
        
        return score, warnings

    def _enhanced_rule_analysis(self, content, subject, sender):
        """Enhanced rule-based email analysis"""
        score = 0
        warnings = []
        
        # Combined content analysis (subject + content)
        full_text = f"{subject} {content}".lower()
        
        # Keyword analysis with weights
        keyword_score, keyword_warnings = self._analyze_keywords_weighted(full_text)
        score += keyword_score
        warnings.extend(keyword_warnings)
        
        # Pattern analysis
        pattern_score, pattern_warnings = self._analyze_patterns(full_text)
        score += pattern_score
        warnings.extend(pattern_warnings)
        
        # URL analysis
        url_score, url_warnings = self._analyze_urls_in_content(content)
        score += url_score
        warnings.extend(url_warnings)
        
        # Urgency analysis
        urgency_score, urgency_warnings = self._analyze_urgency_indicators(full_text)
        score += urgency_score
        warnings.extend(urgency_warnings)
        
        return score, warnings

    def _analyze_keywords_weighted(self, text):
        """Weighted keyword analysis for email content"""
        score = 0
        warnings = []
        found_keywords = []
        
        # Check all keyword categories
        for category, keywords in self.suspicious_keywords.items():
            for keyword, weight in keywords.items():
                if keyword in text:
                    score += weight
                    found_keywords.append(f"{keyword}({weight})")
        
        if found_keywords:
            warnings.append(f'Şüpheli kelimeler: {", ".join(found_keywords[:5])}')
            
            # Bonus for multiple suspicious keywords
            if len(found_keywords) > 3:
                bonus = min(len(found_keywords) * 5, 25)
                score += bonus
                warnings.append(f'Çoklu şüpheli kelime bonusu: +{bonus}')
        
        return score, warnings

    def _analyze_patterns(self, text):
        """Pattern analysis for email content"""
        score = 0
        warnings = []
        
        for pattern, pattern_score, description in self.suspicious_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                total_score = min(len(matches) * pattern_score, pattern_score * 2)
                score += total_score
                warnings.append(f'{description} ({len(matches)} adet) (+{total_score})')
        
        return score, warnings

    def _analyze_urls_in_content(self, content):
        """Analyze URLs found in email content"""
        score = 0
        warnings = []
        
        # Find URLs in content
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, content, re.IGNORECASE)
        
        for url in urls:
            # Basic URL analysis
            if len(url) > 100:
                score += 10
                warnings.append(f'Uzun URL tespit edildi: {url[:50]}...')
            
            # Check for suspicious patterns
            for pattern, pattern_score, description in self.url_patterns:
                if re.search(pattern, url):
                    score += pattern_score
                    warnings.append(f'{description}: {url[:50]}...')
        
        if len(urls) > 5:
            score += 15
            warnings.append(f'Çok fazla URL ({len(urls)} adet)')
        
        return score, warnings

    def _analyze_urgency_indicators(self, text):
        """Analyze urgency and pressure tactics"""
        score = 0
        warnings = []
        
        urgency_patterns = [
            (r'act\s+now', 20, 'Immediate action pressure'),
            (r'expires?\s+(today|tomorrow|soon)', 18, 'Expiration pressure'),
            (r'limited\s+time', 15, 'Time limitation pressure'),
            (r'hurry\s+up', 12, 'Hurry pressure'),
            (r'don\'t\s+wait', 10, 'Wait pressure'),
            (r'immediate(ly)?', 15, 'Immediacy pressure'),
            
            # Turkish urgency patterns
            (r'acil\s+durum', 20, 'Turkish urgent situation'),
            (r'hemen\s+işlem', 18, 'Turkish immediate action'),
            (r'süre\s+dolmak', 15, 'Turkish time expiring'),
            (r'geç\s+kalma', 12, 'Turkish don\'t be late')
        ]
        
        urgency_count = 0
        for pattern, pattern_score, description in urgency_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += pattern_score
                warnings.append(f'{description} (+{pattern_score})')
                urgency_count += 1
        
        # Bonus for multiple urgency indicators
        if urgency_count > 1:
            bonus = min(urgency_count * 8, 25)
            score += bonus
            warnings.append(f'Çoklu aciliyet göstergesi bonusu: +{bonus}')
        
        return score, warnings

    def _calculate_hybrid_score(self, rule_score, ai_score, details):
        """Calculate hybrid score for email analysis"""
        if not self.ai_engine.ai_available or ai_score == 0:
            return rule_score
        
        # Check if sender is whitelisted
        if details.get('sender_whitelisted', False):
            # For whitelisted senders, trust rules more than AI
            hybrid_score = (rule_score * 0.7) + (ai_score * 0.3)
            # Cap maximum score for whitelisted senders
            hybrid_score = min(hybrid_score, 30)
        else:
            # Standard hybrid calculation: 50% rules + 50% AI
            hybrid_score = (rule_score * 0.5) + (ai_score * 0.5)
        
        return max(0, hybrid_score)

    def _calculate_ai_confidence(self, final_score, ai_results, details):
        """Calculate AI confidence for email analysis"""
        confidence_factors = {
            'base_confidence': 50,
            'model_bonus': 0,
            'sender_bonus': 0,
            'consistency_bonus': 0,
            'data_quality_bonus': 0
        }
        
        # Model availability bonus
        if self.model_available:
            confidence_factors['model_bonus'] = 25
        
        # Sender reliability bonus
        if details.get('sender_whitelisted', False):
            confidence_factors['sender_bonus'] = 20
        elif details.get('sender_valid', False):
            confidence_factors['sender_bonus'] = 10
        
        # Data quality factors
        if details.get('detected_language') in ['en', 'tr']:
            confidence_factors['data_quality_bonus'] += 5
        if details.get('content_length', 0) > 100:
            confidence_factors['data_quality_bonus'] += 5
        if not details.get('spoofing_detected', False):
            confidence_factors['data_quality_bonus'] += 10
        
        # Consistency check
        if ai_results and 'ai_score' in ai_results:
            rule_score = final_score - (ai_results['ai_score'] * 0.5)
            score_diff = abs(rule_score - ai_results['ai_score'])
            
            if score_diff < 15:
                confidence_factors['consistency_bonus'] = 15
            elif score_diff < 25:
                confidence_factors['consistency_bonus'] = 10
        
        # Calculate total confidence
        total_confidence = sum(confidence_factors.values())
        normalized_confidence = min(100, max(25, total_confidence))
        
        # Confidence level
        if normalized_confidence >= 90:
            confidence_level = "Çok Yüksek"
            confidence_color = "#006400"
        elif normalized_confidence >= 75:
            confidence_level = "Yüksek"
            confidence_color = "#32CD32"
        elif normalized_confidence >= 60:
            confidence_level = "Orta"
            confidence_color = "#FFD700"
        elif normalized_confidence >= 45:
            confidence_level = "Düşük"
            confidence_color = "#FFA500"
        else:
            confidence_level = "Çok Düşük"
            confidence_color = "#DC143C"
        
        return {
            'score': round(normalized_confidence, 1),
            'level': confidence_level,
            'color': confidence_color,
            'factors': confidence_factors,
            'description': self._get_confidence_description(normalized_confidence)
        }

    def _get_confidence_description(self, confidence_score):
        """Get confidence description"""
        if confidence_score >= 90:
            return "Email analizi son derece güvenilir. Sonuçlara kesin olarak güvenebilirsiniz."
        elif confidence_score >= 75:
            return "Email analizi güvenilir. Sonuçlar yüksek doğrulukta."
        elif confidence_score >= 60:
            return "Email analizi makul güvenilirlikte. Ek doğrulama önerilir."
        elif confidence_score >= 45:
            return "Email analizi düşük güvenilirlikte. Manuel doğrulama gerekli."
        else:
            return "Email analizi çok düşük güvenilirlikte. Sonuçları dikkatli değerlendirin."

    def _determine_risk_level(self, score):
        """Determine risk level for email"""
        if score >= 80:
            return 'Kritik Tehlike', '#8B0000'
        elif score >= 65:
            return 'Yüksek Risk', '#DC143C'
        elif score >= 50:
            return 'Orta-Yüksek Risk', '#FF6347'
        elif score >= 35:
            return 'Orta Risk', '#FF8C00'
        elif score >= 20:
            return 'Düşük-Orta Risk', '#FFA500'
        elif score >= 10:
            return 'Düşük Risk', '#FFD700'
        elif score >= 5:
            return 'Minimal Risk', '#9ACD32'
        else:
            return 'Güvenli', '#32CD32'

    def _get_enhanced_recommendations(self, risk_score, ai_results):
        """Get enhanced recommendations for email"""
        recommendations = []
        
        if risk_score >= 70:
            recommendations.extend([
                '🚨 Bu email yüksek risk taşıyor - dikkatli olun!',
                '❌ Email içindeki linklere tıklamayın',
                '🔒 Kişisel bilgilerinizi asla paylaşmayın',
                '🗑️ Email\'i spam olarak işaretleyin',
                '⚠️ Göndereni engelleyin'
            ])
        elif risk_score >= 50:
            recommendations.extend([
                '⚠️ Bu email şüpheli görünüyor',
                '🔍 Gönderen adresini dikkatli kontrol edin',
                '🔗 Linklere tıklamadan önce URL\'i kontrol edin',
                '📞 Gönderenle başka bir yoldan iletişime geçin'
            ])
        elif risk_score >= 30:
            recommendations.extend([
                '👁️ Bu email orta risk seviyesinde',
                '✅ Gönderen adresini doğrulayın',
                '🔍 Email içeriğini dikkatli okuyun',
                '🛡️ Şüpheli durumda email\'i silmekten çekinmeyin'
            ])
        elif risk_score >= 15:
            recommendations.extend([
                '✅ Email nispeten güvenli görünüyor',
                '👁️ Yine de dikkatli olun',
                '🔗 Linklere tıklamadan önce kontrol edin'
            ])
        else:
            recommendations.extend([
                '✅ Email güvenli görünüyor',
                '🛡️ Standart güvenlik önlemlerini almayı unutmayın'
            ])
        
        # AI-specific recommendations
        if self.ai_engine.ai_available and ai_results:
            if ai_results.get('phishing_probability', 0) > 0.8:
                recommendations.append('🤖 AI modeli yüksek phishing olasılığı tespit etti')
            if ai_results.get('sentiment_score', 0) < -0.5:
                recommendations.append('🤖 Email içeriği olumsuz duygu analizi gösteriyor')
        
        return recommendations

    def get_status(self):
        """Get email analyzer status"""
        return {
            'model_available': self.model_available,
            'analysis_mode': self.analysis_mode,
            'ai_engine_status': self.ai_engine.get_status() if self.ai_engine else None
        } 