import random
from datetime import datetime

class RecommendationSystem:
    def __init__(self):
        self.daily_tips = [
            {
                'title': '🔒 Güçlü Şifre Kullanın',
                'description': 'En az 12 karakter, büyük-küçük harf, sayı ve özel karakter içeren şifreler kullanın.',
                'category': 'password'
            },
            {
                'title': '🔄 Yazılımları Güncel Tutun',
                'description': 'İşletim sistemi ve uygulamalarınızı düzenli olarak güncelleyin.',
                'category': 'update'
            },
            {
                'title': '📧 E-posta Bağlantılarına Dikkat',
                'description': 'Tanımadığınız gönderenlerden gelen e-postalardaki linklere tıklamadan önce düşünün.',
                'category': 'email'
            },
            {
                'title': '🛡️ Antivirüs Kullanın',
                'description': 'Güncel bir antivirüs programı kullanın ve düzenli tarama yapın.',
                'category': 'antivirus'
            },
            {
                'title': '💾 Yedekleme Yapın',
                'description': 'Önemli dosyalarınızın düzenli yedeğini alın.',
                'category': 'backup'
            },
            {
                'title': '🌐 HTTPS Kullanın',
                'description': 'Web sitelerinde "https://" ile başlayan güvenli bağlantıları tercih edin.',
                'category': 'web'
            },
            {
                'title': '📱 İki Faktörlü Doğrulama',
                'description': 'Mümkün olduğunca 2FA (Two-Factor Authentication) kullanın.',
                'category': 'authentication'
            },
            {
                'title': '💳 Online Alışveriş Güvenliği',
                'description': 'Sadece güvenilir ve tanınmış sitelerden alışveriş yapın.',
                'category': 'shopping'
            },
            {
                'title': '📞 Telefon Dolandırıcılığı',
                'description': 'Bilinmeyen numaralardan gelen şüpheli aramalara dikkat edin.',
                'category': 'phone'
            },
            {
                'title': '🔐 Sosyal Medya Gizliliği',
                'description': 'Sosyal medya hesaplarınızın gizlilik ayarlarını kontrol edin.',
                'category': 'social'
            },
            {
                'title': '💻 USB Güvenliği',
                'description': 'Bilinmeyen USB cihazları bilgisayarınıza takmayın.',
                'category': 'hardware'
            },
            {
                'title': '📊 Kişisel Bilgi Paylaşımı',
                'description': 'Kişisel bilgilerinizi gereksiz yere paylaşmaktan kaçının.',
                'category': 'privacy'
            }
        ]
        
        self.security_alerts = [
            {
                'type': 'warning',
                'title': '⚠️ Phishing Saldırı Artışı',
                'message': 'Son dönemde phishing e-postalarında artış gözlemlendi. E-postalarınızı dikkatli kontrol edin.',
                'level': 'medium'
            },
            {
                'type': 'info',
                'title': '🔄 Güvenlik Güncellemesi',
                'message': 'Popüler uygulamalarda kritik güvenlik güncellemeleri yayınlandı.',
                'level': 'low'
            },
            {
                'type': 'danger',
                'title': '🚨 Yeni Malware Tehdidi',
                'message': 'Yeni bir malware türü tespit edildi. Antivirüs tanımlarınızı güncelleyin.',
                'level': 'high'
            }
        ]
        
        self.cyber_crime_stats = [
            {
                'statistic': 'Phishing saldırıları 2023\'te %65 arttı',
                'description': 'E-posta tabanlı saldırılar en yaygın siber tehdit türü olmaya devam ediyor.'
            },
            {
                'statistic': 'Zayıf şifreler nedeniyle hesapların %81\'i risk altında',
                'description': 'Güçlü ve benzersiz şifreler kullanmak kritik önem taşıyor.'
            },
            {
                'statistic': 'Fidye yazılımı saldırıları her 11 saniyede bir gerçekleşiyor',
                'description': 'Düzenli yedekleme ve güvenlik önlemleri hayati önem taşıyor.'
            }
        ]
        
        self.threat_levels = {
            'phishing': 'Yüksek',
            'malware': 'Yüksek', 
            'identity_theft': 'Orta',
            'financial_fraud': 'Yüksek',
            'social_engineering': 'Orta'
        }

    def get_daily_recommendations(self):
        """Günlük tavsiyeler ve güvenlik bilgileri getir"""
        # Günün ipucu (sabit seed ile günlük değişir)
        today = datetime.now().date()
        random.seed(today.toordinal())
        
        daily_tip = random.choice(self.daily_tips)
        security_alert = random.choice(self.security_alerts)
        cyber_stat = random.choice(self.cyber_crime_stats)
        
        # Risk seviyeleri
        current_threats = {
            'phishing': {'level': 'Yüksek', 'color': 'red', 'trend': 'artış'},
            'malware': {'level': 'Orta', 'color': 'orange', 'trend': 'sabit'},
            'scam': {'level': 'Yüksek', 'color': 'red', 'trend': 'artış'},
            'identity_theft': {'level': 'Orta', 'color': 'orange', 'trend': 'azalış'}
        }
        
        return {
            'daily_tip': daily_tip,
            'security_alert': security_alert,
            'cyber_statistic': cyber_stat,
            'current_threats': current_threats,
            'general_recommendations': self._get_general_recommendations(),
            'quick_tips': self._get_quick_tips(),
            'timestamp': datetime.now().isoformat()
        }

    def get_recommendations_by_risk(self, risk_type, risk_score):
        """Risk türü ve skoruna göre özel tavsiyeler"""
        recommendations = []
        
        if risk_type == 'url':
            recommendations = self._get_url_recommendations(risk_score)
        elif risk_type == 'email':
            recommendations = self._get_email_recommendations(risk_score)
        elif risk_type == 'file':
            recommendations = self._get_file_recommendations(risk_score)
        
        return {
            'specific_recommendations': recommendations,
            'general_tips': self._get_general_tips_by_risk(risk_score),
            'prevention_steps': self._get_prevention_steps(risk_type)
        }

    def _get_general_recommendations(self):
        """Genel güvenlik tavsiyeleri"""
        return [
            'Düzenli olarak şifrelerinizi değiştirin',
            'Bilinmeyen kaynaklardan dosya indirmeyin',
            'Sistem güncellemelerini ihmal etmeyin',
            'E-posta eklerini açmadan önce kontrol edin',
            'Güvenlik yazılımınızı güncel tutun',
            'Şüpheli aktiviteleri bildirin',
            'Sosyal medyada kişisel bilgi paylaşımında dikkatli olun'
        ]

    def _get_quick_tips(self):
        """Hızlı güvenlik ipuçları"""
        tips = [
            {'icon': '🔒', 'text': 'Şifre yöneticisi kullanın'},
            {'icon': '📧', 'text': 'E-posta adresini doğrulayın'},
            {'icon': '🔗', 'text': 'Linklerin üzerine gelip kontrol edin'},
            {'icon': '💾', 'text': 'Önemli verileri yedekleyin'},
            {'icon': '🛡️', 'text': 'Güvenlik duvarını aktif tutun'},
            {'icon': '📱', 'text': '2FA kullanın'},
            {'icon': '🌐', 'text': 'VPN kullanmayı düşünün'},
            {'icon': '⚠️', 'text': 'Şüpheli aktiviteleri rapor edin'}
        ]
        
        # Her seferinde farklı 4 ipucu döndür
        return random.sample(tips, 4)

    def _get_url_recommendations(self, risk_score):
        """URL risk skoruna göre tavsiyeler"""
        if risk_score >= 70:
            return [
                'Bu URL\'ye kesinlikle erişmeyin',
                'Bağlantıyı paylaşan kişiyi uyarın',
                'URL\'yi güvenlik ekibine bildirin',
                'Tarayıcınızda güvenlik uyarılarını dikkate alın'
            ]
        elif risk_score >= 40:
            return [
                'Bu URL\'ye dikkatli yaklaşın',
                'Kişisel bilgi girmeyin',
                'Site sertifikasını kontrol edin',
                'Şüpheli durumda sayfayı kapatın'
            ]
        else:
            return [
                'URL güvenli görünse de dikkatli olun',
                'HTTPS bağlantısını tercih edin',
                'Site adresini çift kontrol edin'
            ]

    def _get_email_recommendations(self, risk_score):
        """E-posta risk skoruna göre tavsiyeler"""
        if risk_score >= 70:
            return [
                'Bu e-posta phishing saldırısı olabilir',
                'Hiçbir linke tıklamayın',
                'E-postayı spam olarak işaretleyin',
                'Göndericiyi engelleyin',
                'BT departmanını bilgilendirin'
            ]
        elif risk_score >= 40:
            return [
                'E-posta şüpheli görünüyor',
                'Gönderen adresini doğrulayın',
                'Bağlantılara dikkatli tıklayın',
                'Ek dosyaları açmayın'
            ]
        else:
            return [
                'E-posta güvenli görünüyor',
                'Yine de standart önlemleri alın',
                'Şüphelendiğinizde doğrulama yapın'
            ]

    def _get_file_recommendations(self, risk_score):
        """Dosya risk skoruna göre tavsiyeler"""
        if risk_score >= 70:
            return [
                'Bu dosyayı kesinlikle açmayın',
                'Dosyayı hemen silin',
                'Antivirüs taraması yapın',
                'Sistem güvenliğini kontrol edin'
            ]
        elif risk_score >= 40:
            return [
                'Dosyayı açmadan önce tarayın',
                'Kaynağını doğrulayın',
                'Yedek sistem üzerinde test edin',
                'İzole ortamda kontrol edin'
            ]
        else:
            return [
                'Dosya güvenli görünüyor',
                'Yine de antivirüs taraması yapın',
                'Güvenilir kaynaktan geldiğini doğrulayın'
            ]

    def _get_general_tips_by_risk(self, risk_score):
        """Risk skoruna göre genel ipuçları"""
        if risk_score >= 70:
            return [
                'Acil güvenlik önlemleri alın',
                'Şifrelerinizi değiştirin',
                'Hesap hareketlerinizi kontrol edin',
                'Güvenlik uzmanına danışın'
            ]
        elif risk_score >= 40:
            return [
                'Ekstra dikkatli olun',
                'Güvenlik yazılımınızı güncelleyin',
                'Sistemde anormal aktivite kontrol edin'
            ]
        else:
            return [
                'Standart güvenlik uygulamalarını sürdürün',
                'Düzenli güvenlik kontrolü yapın'
            ]

    def _get_prevention_steps(self, risk_type):
        """Risk türüne göre önleme adımları"""
        prevention_steps = {
            'url': [
                'URL kısaltma servislerini dikkatli kullanın',
                'Resmi web sitelerini yer imlerine ekleyin',
                'Tarayıcı güvenlik ayarlarını aktif edin',
                'DNS filtreleme kullanın'
            ],
            'email': [
                'Spam filtreleri aktif edin',
                'E-posta istemcinizi güncel tutun',
                'Bilinmeyen gönderenlerden gelen e-postaları otomatik blokla',
                'E-posta güvenlik eğitimleri alın'
            ],
            'file': [
                'Dosya indirmek için güvenilir kaynakları kullanın',
                'Gerçek zamanlı antivirüs koruması aktif edin',
                'Dosya uzantılarını görünür yapın',
                'Sandboxing teknolojileri kullanın'
            ]
        }
        
        return prevention_steps.get(risk_type, [])

    def get_threat_intelligence(self):
        """Güncel tehdit istihbaratı"""
        return {
            'trending_threats': [
                'AI destekli phishing saldırıları',
                'Deepfake ses dolandırıcılığı',
                'QR kod tabanlı saldırılar',
                'Supply chain saldırıları'
            ],
            'vulnerable_sectors': [
                'Finans',
                'Sağlık',
                'Eğitim',
                'E-ticaret'
            ],
            'recommended_actions': [
                'Çalışan eğitimlerini artırın',
                'Incident response planını güncelleyin',
                'Güvenlik monitoring\'i güçlendirin',
                'Zero-trust yaklaşımı benimseyin'
            ]
        } 