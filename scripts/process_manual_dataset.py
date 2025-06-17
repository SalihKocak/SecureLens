
import os
import sys
import pandas as pd
import numpy as np
import json
from pathlib import Path

def process_ember_dataset(data_path="data/ember_dataset"):
    """EMBER dataset'ini işle"""
    
    print("🔥 EMBER Dataset İşleniyor...")
    
    # Data directory kontrolü
    ember_path = Path(data_path)
    if not ember_path.exists():
        print(f"❌ {data_path} bulunamadı!")
        print("📥 EMBER dataset'ini şuraya çıkart:")
        print(f"   {ember_path.absolute()}")
        return False
    
    # JSON dosyalarını ara
    json_files = list(ember_path.glob("**/*.jsonl")) + list(ember_path.glob("**/*.json"))
    
    if not json_files:
        print("❌ JSON dosyaları bulunamadı!")
        return False
    
    print(f"📁 {len(json_files)} JSON dosyası bulundu")
    
    # İlk dosyayı incele
    sample_file = json_files[0]
    print(f"🔍 Örnek dosya: {sample_file}")
    
    try:
        with open(sample_file, 'r', encoding='utf-8', errors='replace') as f:
            sample_data = json.loads(f.readline())
        
        print(f"📊 Örnek veri yapısı:")
        print(f"   🔑 Keys: {list(sample_data.keys())}")
        
        if 'label' in sample_data:
            print(f"   🏷️ Label: {sample_data['label']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return False

def process_kaggle_dataset(data_path="data/kaggle_malware"):
    """Kaggle Malware Classification dataset'ini işle"""
    
    print("🏆 Kaggle Malware Dataset İşleniyor...")
    
    kaggle_path = Path(data_path)
    if not kaggle_path.exists():
        print(f"❌ {data_path} bulunamadı!")
        print("📥 Kaggle dataset'ini şuraya çıkart:")
        print(f"   {kaggle_path.absolute()}")
        return False
    
    # CSV dosyalarını ara
    csv_files = list(kaggle_path.glob("**/*.csv"))
    asm_files = list(kaggle_path.glob("**/*.asm"))
    
    print(f"📁 {len(csv_files)} CSV, {len(asm_files)} ASM dosyası bulundu")
    
    if csv_files:
        # İlk CSV'yi incele
        sample_csv = csv_files[0]
        print(f"🔍 Örnek CSV: {sample_csv}")
        
        try:
            df_sample = pd.read_csv(sample_csv, nrows=5, encoding='utf-8')
            print(f"📊 CSV yapısı:")
            print(f"   📏 Shape: {df_sample.shape}")
            print(f"   🔑 Columns: {list(df_sample.columns)}")
            print("\n📋 İlk 3 satır:")
            print(df_sample.head(3))
            
        except Exception as e:
            print(f"❌ CSV okuma hatası: {e}")
    
    return len(csv_files) > 0 or len(asm_files) > 0

def create_sample_dataset_if_missing():
    """Eğer hiç dataset yoksa küçük örnek oluştur"""
    
    print("🎯 Küçük Örnek Dataset Oluşturuluyor...")
    
    # Data directory oluştur
    data_dir = Path("data/file_security")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Gerçekçi dosya adları ve özellikleri
    sample_size = 5000
    
    malicious_patterns = [
        # Şüpheli uzantılar
        "document.pdf.exe", "invoice.docx.scr", "photo.jpg.bat",
        "update.exe.com", "setup.msi.pif", "readme.txt.cmd",
        
        # Çift uzantı
        "important.doc.exe", "bill.pdf.scr", "vacation.zip.bat",
        
        # Şüpheli isimler
        "svchost.exe", "winlogon.scr", "explorer.bat",
        "system32.exe", "notepad.com", "calc.pif",
        
        # Türkçe tuzaklar
        "fatura.pdf.exe", "özgeçmiş.docx.scr", "fotoğraf.jpg.bat",
        "günceleme.exe.com", "program.msi.pif"
    ]
    
    benign_patterns = [
        # Normal programlar
        "setup.exe", "install.msi", "program.exe",
        "update.exe", "launcher.exe", "client.exe",
        
        # Sistem dosyaları
        "kernel32.dll", "user32.dll", "ntdll.dll",
        "msvcrt.dll", "advapi32.dll", "shell32.dll",
        
        # Belgeler (güvenli)
        "document.pdf", "spreadsheet.xlsx", "presentation.pptx",
        "image.jpg", "video.mp4", "audio.mp3"
    ]
    
    filenames = []
    labels = []
    features = []
    
    # Malicious dosyalar (50%)
    for i in range(sample_size // 2):
        base_name = np.random.choice(malicious_patterns)
        filename = f"{base_name.split('.')[0]}_{i}.{'.'.join(base_name.split('.')[1:])}"
        
        filenames.append(filename)
        labels.append(1)  # Malicious
        
        # Features çıkar
        feature_vector = extract_filename_features(filename, is_malicious=True)
        features.append(feature_vector)
    
    # Benign dosyalar (50%)
    for i in range(sample_size // 2):
        base_name = np.random.choice(benign_patterns)
        filename = f"{base_name.split('.')[0]}_{i}.{'.'.join(base_name.split('.')[1:])}"
        
        filenames.append(filename)
        labels.append(0)  # Benign
        
        # Features çıkar
        feature_vector = extract_filename_features(filename, is_malicious=False)
        features.append(feature_vector)
    
    # DataFrame oluştur
    feature_names = [
        'length', 'dot_count', 'digit_ratio', 'uppercase_ratio',
        'suspicious_ext', 'double_ext', 'entropy', 'vowel_ratio',
        'has_numbers', 'has_spaces', 'has_special_chars', 'has_system_name'
    ]
    
    # PE-like binary features ekle
    for i in range(12):
        feature_names.append(f'pe_feature_{i}')
    
    df = pd.DataFrame(features, columns=feature_names)
    df['filename'] = filenames
    df['label'] = labels
    
    # Train/test split
    train_size = int(0.8 * sample_size)
    indices = np.random.permutation(sample_size)
    
    train_indices = indices[:train_size]
    test_indices = indices[train_size:]
    
    train_df = df.iloc[train_indices]
    test_df = df.iloc[test_indices]
    
    # Save
    train_path = data_dir / "file_security_train.csv"
    test_path = data_dir / "file_security_test.csv"
    
    train_df.to_csv(train_path, index=False, encoding='utf-8')
    test_df.to_csv(test_path, index=False, encoding='utf-8')
    
    print(f"✅ Örnek dataset oluşturuldu:")
    print(f"   📁 Train: {train_path} ({len(train_df)} samples)")
    print(f"   📁 Test: {test_path} ({len(test_df)} samples)")
    
    # İstatistikler
    print(f"\n📊 Dataset İstatistikleri:")
    print(f"   🟢 Benign: {len(df[df['label'] == 0])}")
    print(f"   🔴 Malicious: {len(df[df['label'] == 1])}")
    print(f"   📏 Ortalama uzunluk: {df['length'].mean():.1f}")
    print(f"   📈 Çift uzantı oranı: %{df['double_ext'].mean()*100:.1f}")
    
    # Örnekler göster
    print(f"\n🔍 Örnek Malicious Dosyalar:")
    malicious_samples = train_df[train_df['label'] == 1]['filename'].head(5)
    for filename in malicious_samples:
        print(f"   🔴 {filename}")
    
    print(f"\n🔍 Örnek Benign Dosyalar:")
    benign_samples = train_df[train_df['label'] == 0]['filename'].head(5)
    for filename in benign_samples:
        print(f"   🟢 {filename}")
    
    return True

def extract_filename_features(filename, is_malicious=False):
    """Dosya adından güvenlik özelliklerini çıkar"""
    
    # Temel özellikler
    length = len(filename)
    dot_count = filename.count('.')
    digit_ratio = len([c for c in filename if c.isdigit()]) / len(filename)
    uppercase_ratio = len([c for c in filename if c.isupper()]) / len(filename)
    
    # Şüpheli uzantılar
    suspicious_exts = ['.scr', '.pif', '.bat', '.cmd', '.com', '.vbs', '.js']
    suspicious_ext = 1 if any(filename.lower().endswith(ext) for ext in suspicious_exts) else 0
    
    # Çift uzantı
    parts = filename.split('.')
    double_ext = 1 if len(parts) > 2 else 0
    
    # Entropi (karmaşıklık)
    import math
    prob = [filename.count(c)/len(filename) for c in set(filename)]
    entropy = -sum(p * math.log2(p) for p in prob if p > 0)
    
    # Sesli harf oranı
    vowels = 'aeiouAEIOU'
    vowel_ratio = len([c for c in filename if c in vowels]) / len(filename)
    
    # Diğer özellikler
    has_numbers = 1 if any(c.isdigit() for c in filename) else 0
    has_spaces = 1 if ' ' in filename else 0
    has_special_chars = 1 if any(c in '!@#$%^&*()+=[]{}|;:,<>?' for c in filename) else 0
    
    # Sistem dosya adları
    system_names = ['svchost', 'winlogon', 'explorer', 'system32', 'notepad', 'calc']
    has_system_name = 1 if any(name in filename.lower() for name in system_names) else 0
    
    # Binary özellikler (PE dosya simülasyonu)
    pe_features = []
    if is_malicious:
        # Malicious dosyalar için şüpheli değerler
        pe_features = [
            np.random.uniform(0.7, 1.0),  # High entropy sections
            np.random.uniform(0.6, 0.9),  # Suspicious imports ratio
            np.random.uniform(0.0, 0.3),  # Low legitimate API calls
            np.random.uniform(0.7, 1.0),  # High packed sections
            np.random.uniform(0.8, 1.0),  # Suspicious strings ratio
            np.random.uniform(0.0, 0.2),  # Low version info completeness
            np.random.uniform(0.9, 1.0),  # High obfuscation indicators
            np.random.uniform(0.7, 1.0),  # Suspicious section names
            np.random.uniform(0.0, 0.3),  # Low digital signature validity
            np.random.uniform(0.8, 1.0),  # High runtime packer indicators
            np.random.uniform(0.6, 0.9),  # Network activity indicators
            np.random.uniform(0.7, 1.0),  # Anti-analysis features
        ]
    else:
        # Benign dosyalar için normal değerler
        pe_features = [
            np.random.uniform(0.2, 0.5),  # Normal entropy
            np.random.uniform(0.1, 0.4),  # Normal imports
            np.random.uniform(0.7, 1.0),  # High legitimate API usage
            np.random.uniform(0.0, 0.3),  # Low packed sections
            np.random.uniform(0.1, 0.4),  # Low suspicious strings
            np.random.uniform(0.7, 1.0),  # Complete version info
            np.random.uniform(0.0, 0.2),  # Low obfuscation
            np.random.uniform(0.1, 0.4),  # Normal section names
            np.random.uniform(0.7, 1.0),  # Valid digital signature
            np.random.uniform(0.0, 0.2),  # No runtime packers
            np.random.uniform(0.0, 0.3),  # Limited network activity
            np.random.uniform(0.0, 0.2),  # No anti-analysis
        ]
    
    # Tüm özellikleri birleştir
    features = [
        length, dot_count, digit_ratio, uppercase_ratio,
        suspicious_ext, double_ext, entropy, vowel_ratio,
        has_numbers, has_spaces, has_special_chars, has_system_name
    ] + pe_features
    
    return features

def main():
    """Ana işlev"""
    
    print("🎯 Manuel Dataset İşleyici")
    print("=" * 50)
    
    # Hangi dataset'ler mevcut kontrol et
    datasets_found = []
    
    # EMBER kontrol
    if Path("data/ember_dataset").exists():
        datasets_found.append("EMBER")
        if process_ember_dataset():
            print("✅ EMBER dataset hazır!")
    
    # Kaggle kontrol  
    if Path("data/kaggle_malware").exists():
        datasets_found.append("Kaggle")
        if process_kaggle_dataset():
            print("✅ Kaggle dataset hazır!")
    
    # Hiç dataset yoksa örnek oluştur
    if not datasets_found:
        print("📥 Hiç manuel dataset bulunamadı.")
        print("🎯 Küçük örnek dataset oluşturuluyor...")
        
        if create_sample_dataset_if_missing():
            print("✅ Örnek dataset hazır!")
            datasets_found.append("Sample")
    
    if datasets_found:
        print(f"\n🚀 Hazır dataset'ler: {', '.join(datasets_found)}")
        print("\n📝 Sonraki adım:")
        print("   python scripts/train_file_model.py")
    else:
        print("\n❌ Hiç dataset hazırlanamadı!")
        
        print("\n📥 Manuel indirme seçenekleri:")
        print("1. EMBER: https://github.com/elastic/ember/releases")
        print("2. Kaggle: https://www.kaggle.com/c/malware-classification") 
        print("3. BODMAS: https://whyisyoung.github.io/BODMAS/")

if __name__ == "__main__":
    main() 