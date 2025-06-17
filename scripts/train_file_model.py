#!/usr/bin/env python3
"""
Basit Dosya Güvenlik Analizi Modeli
GTX 1650 optimize edilmiş
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from pathlib import Path

class SimpleFileSecurityNet(nn.Module):
    def __init__(self, input_size=24):
        super().__init__()
        
        # GTX 1650 için optimize edilmiş küçük model
        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(), 
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 2)  # Binary classification
        )
    
    def forward(self, x):
        return self.network(x)

def create_model_config(input_size, feature_names):
    """Model konfigürasyonu oluştur"""
    
    config = {
        "model_type": "FileSecurityNet",
        "input_size": input_size,
        "num_classes": 2,
        "feature_names": feature_names,
        "architecture": {
            "hidden_layers": [64, 32, 16],
            "dropout_rates": [0.3, 0.2, 0.0],
            "activation": "ReLU"
        },
        "training_params": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 50,
            "optimizer": "Adam"
        },
        "performance": {},
        "created_with": "SecureLens File Analyzer v1.0"
    }
    
    return config

def train_model():
    """Model eğitim fonksiyonu"""
    
    print("🎯 Dosya Güvenlik Modeli Eğitimi")
    print("=" * 50)
    
    # GPU kontrolü
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"📱 Device: {device}")
    
    if device.type == 'cuda':
        print(f"   🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"   💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    
    # Data yükleme
    train_path = "data/file_security/file_security_train.csv"
    test_path = "data/file_security/file_security_test.csv"
    
    if not Path(train_path).exists():
        print("❌ Training data bulunamadı!")
        print("📥 Önce dataset oluşturun:")
        print("   python scripts/process_manual_dataset.py")
        return False
    
    print("📂 Dataset yükleniyor...")
    train_df = pd.read_csv(train_path, encoding='utf-8')
    test_df = pd.read_csv(test_path, encoding='utf-8')
    
    print(f"   📊 Train: {len(train_df)} samples")
    print(f"   📊 Test: {len(test_df)} samples")
    
    # Features hazırlama
    feature_cols = [col for col in train_df.columns if col not in ['filename', 'label']]
    print(f"   🔢 Features: {len(feature_cols)}")
    
    X_train = train_df[feature_cols].values
    y_train = train_df['label'].values
    X_test = test_df[feature_cols].values  
    y_test = test_df['label'].values
    
    # Feature scaling
    print("⚖️ Feature scaling...")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Tensor'e dönüştür
    X_train = torch.FloatTensor(X_train).to(device)
    y_train = torch.LongTensor(y_train).to(device)
    X_test = torch.FloatTensor(X_test).to(device)
    y_test = torch.LongTensor(y_test).to(device)
    
    # Model oluştur
    input_size = X_train.shape[1]
    model = SimpleFileSecurityNet(input_size=input_size).to(device)
    
    print(f"🧠 Model oluşturuldu:")
    print(f"   📐 Input size: {input_size}")
    print(f"   🔢 Parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Loss ve optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # Training parametreleri
    epochs = 50
    batch_size = 32
    
    print(f"\n🚀 Eğitim başlıyor...")
    print(f"   🔄 Epochs: {epochs}")
    print(f"   📦 Batch size: {batch_size}")
    
    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        num_batches = 0
        
        # Mini-batch training
        for i in range(0, len(X_train), batch_size):
            batch_X = X_train[i:i+batch_size]
            batch_y = y_train[i:i+batch_size]
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        
        # Her 10 epoch'ta rapor
        if (epoch + 1) % 10 == 0:
            print(f"   📈 Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    print("✅ Eğitim tamamlandı!")
    
    # Evaluation
    print("\n🧪 Model test ediliyor...")
    model.eval()
    
    with torch.no_grad():
        test_outputs = model(X_test)
        _, predicted = torch.max(test_outputs.data, 1)
        
        # CPU'ya taşı (sklearn için)
        y_test_cpu = y_test.cpu().numpy()
        predicted_cpu = predicted.cpu().numpy()
        
        accuracy = (predicted == y_test).float().mean().item()
        
        print(f"✅ Test Accuracy: {accuracy:.4f} ({accuracy*100:.1f}%)")
        
        # Detaylı metriker
        print(f"\n📊 Detaylı Sonuçlar:")
        print(classification_report(y_test_cpu, predicted_cpu, 
                                  target_names=['Benign', 'Malicious']))
        
        # Confusion matrix
        cm = confusion_matrix(y_test_cpu, predicted_cpu)
        print(f"\n🎯 Confusion Matrix:")
        print(f"          Predicted")
        print(f"        Benign Malicious")
        print(f"Actual Benign   {cm[0,0]:4d}    {cm[0,1]:4d}")
        print(f"       Malicious {cm[1,0]:4d}    {cm[1,1]:4d}")
    
    # Model kaydetme
    print(f"\n💾 Model kaydediliyor...")
    
    # Model directory oluştur
    model_dir = Path("models/file")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Model weights kaydet
    model_path = model_dir / "file_detection_model.pt"
    torch.save(model.state_dict(), model_path)
    print(f"   📁 Model: {model_path}")
    
    # Scaler kaydet
    import pickle
    scaler_path = model_dir / "scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   📁 Scaler: {scaler_path}")
    
    # Config kaydet
    config = create_model_config(input_size, feature_cols)
    config["performance"] = {
        "test_accuracy": float(accuracy),
        "test_samples": len(y_test_cpu),
        "confusion_matrix": cm.tolist()
    }
    
    config_path = model_dir / "model_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"   📁 Config: {config_path}")
    
    # Örnek test
    print(f"\n🔍 Örnek Tahmin Testi:")
    
    # İlk 5 test sample'ını test et
    sample_indices = range(min(5, len(test_df)))
    
    for i in sample_indices:
        # EMBER dataset'inde filename yok, sample ID kullan
        sample_id = f"EMBER_sample_{i}"
        true_label = test_df.iloc[i]['label']
        
        # Model prediction
        sample_input = X_test[i:i+1]
        with torch.no_grad():
            output = model(sample_input)
            prob = torch.softmax(output, dim=1)
            pred_label = torch.argmax(output, dim=1).item()
            confidence = prob[0][pred_label].item()
        
        true_str = "🔴 Malicious" if true_label == 1 else "🟢 Benign"
        pred_str = "🔴 Malicious" if pred_label == 1 else "🟢 Benign"
        correct = "✅" if true_label == pred_label else "❌"
        
        print(f"   {correct} {sample_id}")
        print(f"      Gerçek: {true_str}")
        print(f"      Tahmin: {pred_str} (Confidence: {confidence:.3f})")
    
    print(f"\n🎉 Model başarıyla eğitildi ve kaydedildi!")
    print(f"📂 Model dosyaları: models/file/")
    
    return True

if __name__ == "__main__":
    train_model() 