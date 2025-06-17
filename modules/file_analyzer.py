import os
import re
from .ai_engine import HybridAIEngine

class FileAnalyzer:
    def __init__(self):
        # Initialize AI engine
        self.ai_engine = HybridAIEngine()
        
        # Tehlikeli dosya uzantıları
        self.dangerous_extensions = [
            '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.vbe',
            '.js', '.jar', '.ws', '.wsf', '.wsc', '.wsh', '.ps1', '.ps1xml',
            '.ps2', '.ps2xml', '.psc1', '.psc2', '.msh', '.msh1', '.msh2',
            '.mshxml', '.msh1xml', '.msh2xml', '.scf', '.lnk', '.inf',
            '.reg', '.app', '.deb', '.pkg', '.dmg', '.iso', '.img', '.bin',
            '.cue', '.mdf', '.toast', '.vcd', '.crx'
        ]
        
        # Şüpheli uzantılar (orta risk)
        self.suspicious_extensions = [
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.cab',
            '.msi', '.deb', '.rpm', '.apk', '.ipa', '.docm', '.xlsm',
            '.pptm', '.dotm', '.xltm', '.potm', '.ppam', '.xlam', '.docx',
            '.xlsx', '.pptx', '.pdf', '.rtf', '.swf', '.fla'
        ]
        
        # Güvenli uzantılar
        self.safe_extensions = [
            '.txt', '.doc', '.xls', '.ppt', '.jpg', '.jpeg', '.png', '.gif',
            '.bmp', '.mp3', '.mp4', '.avi', '.mov', '.wav', '.ogg', '.flac',
            '.css', '.html', '.htm', '.xml', '.json', '.csv', '.log'
        ]
        
        # Şüpheli kelimeler
        self.suspicious_keywords = [
            'crack', 'keygen', 'patch', 'serial', 'license', 'activator',
            'hack', 'cheat', 'trojan', 'virus', 'malware', 'backdoor',
            'keylogger', 'spyware', 'ransomware', 'worm', 'rootkit',
            'invoice', 'receipt', 'payment', 'refund', 'statement',
            'urgent', 'important', 'confidential', 'secure', 'update',
            'installer', 'setup', 'download', 'free', 'premium'
        ]
        
        # Şüpheli dosya adı kalıpları
        self.suspicious_patterns = [
            r'.*crack.*',
            r'.*keygen.*',
            r'.*patch.*',
            r'.*serial.*',
            r'.*invoice.*\.(exe|scr|bat)',
            r'.*receipt.*\.(exe|scr|bat)',
            r'.*photo.*\.(exe|scr|bat)',
            r'.*video.*\.(exe|scr|bat)',
            r'.*document.*\.(exe|scr|bat)',
            r'.*\.(jpg|png|pdf|doc)\.exe',
            r'.*setup.*\.(exe|msi)',
            r'.*install.*\.(exe|msi)',
            r'.*update.*\.(exe|bat|scr)'
        ]

    def analyze(self, filename, file_content=""):
        """Enhanced file analysis with AI integration"""
        try:
            if not filename or len(filename.strip()) < 1:
                return {
                    'risk_score': 0.0,
                    'risk_level': 'Geçersiz Dosya',
                    'color': 'gray',
                    'warnings': ['Geçersiz dosya adı'],
                    'details': {},
                    'recommendations': ['Geçerli bir dosya adı girin'],
                    'analysis_method': 'error'
                }
            
            filename = filename.strip()
            risk_score = 0
            warnings = []
            details = {}
            
            # 1. BASIC FILE ANALYSIS
            basic_score, basic_warnings, basic_details = self._basic_file_analysis(filename)
            risk_score += basic_score
            warnings.extend(basic_warnings)
            details.update(basic_details)
            
            # 2. ENHANCED RULE-BASED ANALYSIS
            rule_score, rule_warnings = self._enhanced_rule_analysis(filename, file_content)
            risk_score += rule_score
            warnings.extend(rule_warnings)
            
            # 3. AI-POWERED ANALYSIS
            ai_results = self.ai_engine.analyze_file_with_ai(filename, file_content)
            ai_score = ai_results['ai_score']
            warnings.extend(ai_results['ai_warnings'])
            details['ai_confidence'] = ai_results['confidence']
            details['malware_probability'] = ai_results['malware_probability']
            
            # 4. HYBRID SCORING
            final_score = self._calculate_hybrid_score(risk_score, ai_score, ai_results)
            
            # 5. DETERMINE RISK LEVEL
            risk_level, color = self._determine_risk_level(final_score)
            
            return {
                'risk_score': round(min(final_score, 100), 1),
                'risk_level': risk_level,
                'color': color,
                'warnings': warnings,
                'details': details,
                'recommendations': self._get_enhanced_recommendations(final_score, ai_results),
                'analysis_method': 'hybrid_ai' if self.ai_engine.ai_available else 'enhanced_rules'
            }
            
        except Exception as e:
            return {
                'risk_score': 50.0,
                'risk_level': 'Analiz Hatası',
                'color': 'gray',
                'warnings': [f'Dosya analizi sırasında hata: {str(e)}'],
                'details': {},
                'recommendations': ['Dosya adını kontrol edip tekrar deneyin'],
                'analysis_method': 'error'
            }

    def _get_file_extension(self, filename):
        """Dosya uzantısını al"""
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ''

    def _analyze_extension(self, extension):
        """Dosya uzantısını analiz et"""
        score = 0
        warnings = []
        
        if not extension:
            score += 10
            warnings.append('Dosya uzantısı yok')
        elif extension in self.dangerous_extensions:
            score += 50
            warnings.append(f'Tehlikeli dosya uzantısı: {extension}')
        elif extension in self.suspicious_extensions:
            score += 20
            warnings.append(f'Şüpheli dosya uzantısı: {extension}')
        elif extension in self.safe_extensions:
            score += 0  # Güvenli uzantı
        else:
            score += 15
            warnings.append(f'Bilinmeyen dosya uzantısı: {extension}')
        
        return score, warnings

    def _analyze_filename(self, filename):
        """Dosya adı yapısını analiz et"""
        score = 0
        warnings = []
        
        # Dosya adı uzunluğu
        if len(filename) > 100:
            score += 15
            warnings.append('Çok uzun dosya adı')
        
        # Çok kısa dosya adı
        if len(filename) < 3:
            score += 20
            warnings.append('Çok kısa dosya adı')
        
        # Çift uzantı kontrolü
        parts = filename.split('.')
        if len(parts) > 2:
            # İkinci uzantı tehlikeli mi?
            if len(parts) >= 3:
                second_ext = '.' + parts[-2].lower()
                if second_ext in self.dangerous_extensions:
                    score += 40
                    warnings.append('Gizli tehlikeli uzantı tespit edildi')
        
        # Büyük/küçük harf karışımı
        if filename != filename.lower() and filename != filename.upper():
            # Normal durum, skor ekleme
            pass
        elif filename.isupper():
            score += 10
            warnings.append('Tamamı büyük harf')
        
        return score, warnings

    def _check_suspicious_keywords(self, filename):
        """Şüpheli kelime kontrolü"""
        score = 0
        warnings = []
        filename_lower = filename.lower()
        
        found_keywords = []
        for keyword in self.suspicious_keywords:
            if keyword in filename_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            score += len(found_keywords) * 10
            warnings.append(f'Şüpheli kelimeler: {", ".join(found_keywords[:5])}')
        
        return score, warnings

    def _check_suspicious_patterns(self, filename):
        """Şüpheli dosya adı kalıplarını kontrol et"""
        score = 0
        warnings = []
        filename_lower = filename.lower()
        
        for pattern in self.suspicious_patterns:
            if re.match(pattern, filename_lower):
                score += 30
                warnings.append('Şüpheli dosya adı kalıbı tespit edildi')
                break
        
        return score, warnings

    def _analyze_characters(self, filename):
        """Karakter analizi"""
        score = 0
        warnings = []
        
        # Unicode karakterler
        if not filename.isascii():
            score += 15
            warnings.append('ASCII olmayan karakterler içeriyor')
        
        # Özel karakterler
        special_chars = ['@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=']
        special_count = sum(filename.count(char) for char in special_chars)
        if special_count > 2:
            score += 10
            warnings.append('Çok fazla özel karakter')
        
        # Sayı oranı
        digit_count = sum(c.isdigit() for c in filename)
        if digit_count > len(filename) * 0.5:
            score += 15
            warnings.append('Çok fazla sayı içeriyor')
        
        # Boşluk karakterleri
        if '  ' in filename:  # Çift boşluk
            score += 10
            warnings.append('Anormal boşluk kullanımı')
        
        return score, warnings

    def _get_recommendations(self, risk_score, extension):
        """Risk skoruna göre tavsiyeler"""
        recommendations = []
        
        if risk_score >= 80:
            recommendations.extend([
                'Bu dosyayı kesinlikle açmayın!',
                'Dosyayı hemen silin',
                'Antivirüs taraması yapın',
                'Sistem güvenliğinizi kontrol edin'
            ])
        elif risk_score >= 60:
            recommendations.extend([
                'Bu dosya çok riskli görünüyor',
                'Açmadan önce antivirüs taraması yapın',
                'Kaynağını doğrulayın',
                'Güvenilir kaynaklardan dosya indirin'
            ])
        elif risk_score >= 40:
            recommendations.extend([
                'Bu dosya şüpheli görünüyor',
                'Antivirüs ile tarayın',
                'Kaynağını kontrol edin',
                'Dikkatli olun'
            ])
        elif risk_score >= 20:
            recommendations.extend([
                'Dosya nispeten güvenli görünüyor',
                'Yine de dikkatli olun',
                'Bilinmeyen kaynaklardan dosya açmayın'
            ])
        else:
            recommendations.extend([
                'Dosya güvenli görünüyor',
                'Standart güvenlik önlemlerini almayı unutmayın'
            ])
        
        # Uzantıya özel tavsiyeler
        if extension in self.dangerous_extensions:
            recommendations.append(f'{extension} dosyaları potansiyel olarak tehlikelidir')
        
        return recommendations

    def _basic_file_analysis(self, filename):
        """Enhanced basic file analysis"""
        score = 0
        warnings = []
        details = {}
        
        # Dosya uzantısını al
        file_extension = self._get_file_extension(filename)
        details['extension'] = file_extension
        details['filename'] = filename
        
        # Uzantı analizi
        ext_score, ext_warnings = self._analyze_extension(file_extension)
        score += ext_score
        warnings.extend(ext_warnings)
        
        # Dosya adı analizi
        name_score, name_warnings = self._analyze_filename(filename)
        score += name_score
        warnings.extend(name_warnings)
        
        return score, warnings, details

    def _enhanced_rule_analysis(self, filename, file_content):
        """Enhanced rule-based analysis"""
        score = 0
        warnings = []
        
        # Şüpheli kelime kontrolü
        keyword_score, keyword_warnings = self._check_suspicious_keywords(filename)
        score += keyword_score
        warnings.extend(keyword_warnings)
        
        # Şüpheli kalıp kontrolü
        pattern_score, pattern_warnings = self._check_suspicious_patterns(filename)
        score += pattern_score
        warnings.extend(pattern_warnings)
        
        # Dosya boyutu ve karakter analizi
        char_score, char_warnings = self._analyze_characters(filename)
        score += char_score
        warnings.extend(char_warnings)
        
        # İçerik analizi (eğer varsa)
        if file_content:
            content_score, content_warnings = self._analyze_file_content(file_content)
            score += content_score
            warnings.extend(content_warnings)
        
        return score, warnings

    def _analyze_file_content(self, content):
        """Analyze file content for suspicious patterns"""
        score = 0
        warnings = []
        content_lower = content.lower()
        
        # Suspicious strings in content
        malware_strings = [
            'backdoor', 'trojan', 'virus', 'malware', 'keylogger',
            'crypter', 'stealer', 'ransomware', 'botnet', 'exploit',
            'shellcode', 'payload', 'injection', 'bypass', 'rootkit'
        ]
        
        found_strings = []
        for mal_str in malware_strings:
            if mal_str in content_lower:
                found_strings.append(mal_str)
        
        if found_strings:
            score += len(found_strings) * 15
            warnings.append(f'Şüpheli içerik tespit edildi: {", ".join(found_strings[:3])}')
        
        # Check for encoded content
        if any(char in content for char in ['\\x', '%u', 'eval(', 'exec(']):
            score += 20
            warnings.append('Kodlanmış veya gizlenmiş içerik tespit edildi')
        
        return score, warnings

    def _calculate_hybrid_score(self, rule_score, ai_score, ai_results):
        """Calculate hybrid score combining rules and AI"""
        if self.ai_engine.ai_available and ai_score > 0:
            # Weighted combination: Rules 50% + AI 50% for files
            hybrid_score = (rule_score * 0.5) + (ai_score * 0.5)
            
            # Boost for high malware probability
            malware_prob = ai_results.get('malware_probability', 0)
            if malware_prob > 80:
                hybrid_score = min(100, hybrid_score * 1.4)
            
            # Confidence adjustment
            confidence = ai_results.get('confidence', 0)
            if confidence > 90:
                return hybrid_score
            elif confidence < 50:
                # Lower confidence, rely more on rules
                return (rule_score * 0.7) + (ai_score * 0.3)
            
            return hybrid_score
        else:
            # Fallback to enhanced rule-based scoring
            return rule_score

    def _determine_risk_level(self, score):
        """Improved risk level determination for better user experience"""
        if score >= 90:
            return 'Çok Tehlikeli', 'red'
        elif score >= 70:
            return 'Yüksek Risk', 'red'
        elif score >= 50:
            return 'Orta Risk', 'orange'
        elif score >= 30:
            return 'Düşük Risk', 'yellow'
        elif score >= 10:
            return 'Minimal Risk', 'green'
        else:
            return 'Güvenli', 'green'

    def _get_enhanced_recommendations(self, risk_score, ai_results):
        """Enhanced recommendations based on hybrid analysis"""
        recommendations = []
        
        if risk_score >= 80:
            recommendations.extend([
                '🚨 Bu dosya çok tehlikeli!',
                '🗑️ Dosyayı derhal silin',
                '🚫 Kesinlikle açmayın veya çalıştırmayın',
                '🛡️ Sistem taraması yapın',
                '📧 Güvenlik uzmanına bildirin'
            ])
        elif risk_score >= 60:
            recommendations.extend([
                '⚠️ Bu dosya yüksek risk taşıyor',
                '🔍 Açmadan önce detaylı tarama yapın',
                '🌐 Kaynağını mutlaka doğrulayın',
                '💻 İzole ortamda test edin',
                '📞 IT destek ekibine danışın'
            ])
        elif risk_score >= 40:
            recommendations.extend([
                '🔍 Bu dosyaya dikkatli yaklaşın',
                '✅ Antivirüs taraması yapın',
                '🔗 Kaynağını kontrol edin',
                '📱 Güvenli modda açmayı deneyin'
            ])
        elif risk_score >= 20:
            recommendations.extend([
                '👁️ Dosya nispeten güvenli görünüyor',
                '🔍 Yine de dikkatli olun',
                '🛡️ Düzenli güvenlik taraması yapın'
            ])
        else:
            recommendations.extend([
                '✅ Dosya güvenli görünüyor',
                '🛡️ Standart güvenlik önlemlerini almayı unutmayın'
            ])
        
        # AI-specific recommendations
        if self.ai_engine.ai_available:
            malware_prob = ai_results.get('malware_probability', 0)
            if malware_prob > 80:
                recommendations.append('🤖 AI: Yüksek malware olasılığı tespit edildi')
            
            confidence = ai_results.get('confidence', 0)
            if confidence > 90:
                recommendations.append('🤖 AI analizi yüksek güven seviyesi gösteriyor')
        
        return recommendations 