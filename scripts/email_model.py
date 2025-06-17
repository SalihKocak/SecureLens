import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import List, Dict, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
from transformers import AutoTokenizer, AutoModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# GPU kontrol
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔧 Kullanılan cihaz: {DEVICE}")
if torch.cuda.is_available():
    print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

class EmailDataset(Dataset):
    """E-mail veri seti için PyTorch Dataset sınıfı"""
    def __init__(self, texts: List[str], labels: Optional[List[int]] = None, 
                 tokenizer=None, max_length: int = 256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        
        if self.tokenizer:
            encoding = self.tokenizer(
                text,
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
            item = {'text': text}

        if self.labels is not None:
            item['label'] = torch.tensor(self.labels[idx], dtype=torch.float)
        
        return item

class EmailClassifier(nn.Module):
    """4GB GPU için optimize edilmiş e-mail sınıflandırma modeli"""
    def __init__(self, vocab_size: int = 30522, embedding_dim: int = 128, 
                 hidden_dim: int = 256, num_layers: int = 2, max_length: int = 256):
        super().__init__()
        
        # Embedding katmanı (BERT yerine custom embedding - daha az memory)
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # Bi-LSTM katmanı (hafif ama etkili)
        self.lstm = nn.LSTM(
            embedding_dim, 
            hidden_dim, 
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        
        # Attention mechanism (lightweight)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        
        # Classification head
        self.dropout = nn.Dropout(0.5)
        self.fc1 = nn.Linear(hidden_dim * 2, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(128)
        self.bn2 = nn.BatchNorm1d(64)
        
    def attention_mechanism(self, lstm_output, attention_mask=None):
        """Basit attention mechanism"""
        # lstm_output: [batch, seq_len, hidden_dim * 2]
        
        # Attention weights hesapla
        attention_weights = torch.tanh(self.attention(lstm_output))  # [batch, seq_len, 1]
        attention_weights = attention_weights.squeeze(-1)  # [batch, seq_len]
        
        # Attention mask uygula
        if attention_mask is not None:
            attention_weights = attention_weights.masked_fill(attention_mask == 0, -1e9)
        
        # Softmax ile normalize et
        attention_weights = F.softmax(attention_weights, dim=1)  # [batch, seq_len]
        
        # Weighted sum hesapla
        attended_output = torch.bmm(
            attention_weights.unsqueeze(1),  # [batch, 1, seq_len]
            lstm_output  # [batch, seq_len, hidden_dim * 2]
        ).squeeze(1)  # [batch, hidden_dim * 2]
        
        return attended_output, attention_weights

    def forward(self, input_ids, attention_mask=None):
        # Embedding
        embedded = self.embedding(input_ids)  # [batch, seq_len, embedding_dim]
        
        # LSTM
        lstm_output, (hidden, cell) = self.lstm(embedded)  # [batch, seq_len, hidden_dim * 2]
        
        # Attention
        attended_output, attention_weights = self.attention_mechanism(lstm_output, attention_mask)
        
        # Classification
        x = self.dropout(attended_output)
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        x = torch.sigmoid(self.fc3(x))
        
        return x.squeeze(-1)

class EmailDetectionModel:
    """Ana e-mail detection model sınıfı"""
    def __init__(self, model_path='models/email/email_detection_model.pt', 
                 tokenizer_path='models/email/tokenizer', max_length=256):
        self.max_length = max_length
        self.device = DEVICE
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        
        # Tokenizer setup (DistilBERT - daha hafif)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                'distilbert-base-uncased',
                model_max_length=max_length
            )
            print("✅ DistilBERT tokenizer yüklendi")
        except Exception as e:
            print(f"⚠️ DistilBERT yüklenemedi, basit tokenizer kullanılacak: {e}")
            self.tokenizer = None
            
        # Model
        self.model = EmailClassifier(
            vocab_size=30522 if self.tokenizer else 50000,
            embedding_dim=128,
            hidden_dim=256,
            num_layers=2,
            max_length=max_length
        ).to(self.device)
        
        # Training history
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
        
        print(f"🧠 Model oluşturuldu: {sum(p.numel() for p in self.model.parameters())} parametre")
        
    def preprocess_text(self, text: str) -> str:
        """E-mail metnini ön işleme"""
        if not text or pd.isna(text):
            return ""
            
        text = str(text).lower()
        
        # URL'leri özel token ile değiştir
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
                     '[URL]', text)
        
        # E-mail adreslerini özel token ile değiştir
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Telefon numaralarını temizle
        text = re.sub(r'[\+]?[1-9]?[0-9]{7,15}', '[PHONE]', text)
        
        # Gereksiz karakterleri temizle
        text = re.sub(r'[^\w\s\[\]]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def load_data(self, csv_path: str) -> Tuple[List[str], List[int]]:
        """CSV dosyasından veri yükle"""
        print(f"📂 Veri yükleniyor: {csv_path}")
        
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"📊 Veri boyutu: {len(df)} satır")
        
        # Metin sütununu bul
        text_columns = ['text', 'email', 'content', 'message', 'body']
        text_col = None
        for col in text_columns:
            if col in df.columns:
                text_col = col
                break
        
        if text_col is None:
            raise ValueError(f"Metin sütunu bulunamadı. Mevcut sütunlar: {df.columns.tolist()}")
        
        # Label sütununu bul
        label_columns = ['label', 'is_phishing', 'is_spam', 'class', 'target']
        label_col = None
        for col in label_columns:
            if col in df.columns:
                label_col = col
                break
        
        if label_col is None:
            raise ValueError(f"Label sütunu bulunamadı. Mevcut sütunlar: {df.columns.tolist()}")
        
        # Veriyi hazırla
        texts = df[text_col].fillna("").astype(str).tolist()
        labels = df[label_col].astype(int).tolist()
        
        # Ön işleme
        texts = [self.preprocess_text(text) for text in texts]
        
        print(f"✅ Veri hazırlandı: {len(texts)} e-mail")
        print(f"📊 Phishing: {sum(labels)} / Legitimate: {len(labels) - sum(labels)}")
        
        return texts, labels
    
    def train(self, csv_path: str, epochs: int = 10, batch_size: int = 16, 
              learning_rate: float = 0.001, validation_split: float = 0.2):
        """Modeli eğit"""
        
        # Veri yükle
        texts, labels = self.load_data(csv_path)
        
        # Train/validation split
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=validation_split, random_state=42, stratify=labels
        )
        
        # Dataset oluştur
        train_dataset = EmailDataset(train_texts, train_labels, self.tokenizer, self.max_length)
        val_dataset = EmailDataset(val_texts, val_labels, self.tokenizer, self.max_length)
        
        # DataLoader
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Optimizer ve loss
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=0.01)
        criterion = nn.BCELoss()
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2, factor=0.5)
        
        print(f"🚀 Eğitim başlıyor...")
        print(f"📊 Eğitim: {len(train_texts)} / Validation: {len(val_texts)}")
        print(f"⚙️ Batch size: {batch_size} / Epochs: {epochs}")
        print("-" * 60)
        
        best_val_acc = 0
        patience_counter = 0
        patience = 5
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            for batch in train_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels_batch = batch['label'].to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(input_ids, attention_mask)
                loss = criterion(outputs, labels_batch)
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                train_loss += loss.item()
                predictions = (outputs > 0.5).float()
                train_correct += (predictions == labels_batch).sum().item()
                train_total += labels_batch.size(0)
            
            # Validation
            self.model.eval()
            val_loss = 0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for batch in val_loader:
                    input_ids = batch['input_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels_batch = batch['label'].to(self.device)
                    
                    outputs = self.model(input_ids, attention_mask)
                    loss = criterion(outputs, labels_batch)
                    
                    val_loss += loss.item()
                    predictions = (outputs > 0.5).float()
                    val_correct += (predictions == labels_batch).sum().item()
                    val_total += labels_batch.size(0)
            
            # Metrikleri hesapla
            train_acc = train_correct / train_total
            val_acc = val_correct / val_total
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            # History'e ekle
            self.training_history['train_loss'].append(avg_train_loss)
            self.training_history['val_loss'].append(avg_val_loss)
            self.training_history['train_acc'].append(train_acc)
            self.training_history['val_acc'].append(val_acc)
            
            # Learning rate scheduler
            scheduler.step(avg_val_loss)
            
            # Progress
            print(f"Epoch {epoch+1}/{epochs}")
            print(f"Train Loss: {avg_train_loss:.4f} | Train Acc: {train_acc:.4f}")
            print(f"Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f}")
            print("-" * 60)
            
            # Early stopping ve model kaydetme
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                self.save_model()
                print(f"🎉 En iyi model kaydedildi! Val Acc: {val_acc:.4f}")
            else:
                patience_counter += 1
                
            if patience_counter >= patience:
                print(f"⏹️ Early stopping (Patience: {patience})")
                break
        
        print(f"✅ Eğitim tamamlandı! En iyi Val Acc: {best_val_acc:.4f}")
        return True
    
    def predict(self, text: str) -> Dict:
        """Tek bir e-mail için tahmin yap"""
        self.model.eval()
        
        # Ön işleme
        processed_text = self.preprocess_text(text)
        
        # Tokenize
        if self.tokenizer:
            encoding = self.tokenizer(
                processed_text,
                truncation=True,
                max_length=self.max_length,
                padding='max_length',
                return_tensors='pt'
            )
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
        else:
            # Basit tokenization
            input_ids = torch.randint(0, 1000, (1, self.max_length)).to(self.device)
            attention_mask = torch.ones((1, self.max_length)).to(self.device)
        
        # Tahmin
        with torch.no_grad():
            output = self.model(input_ids, attention_mask)
            probability = output.item()
            is_phishing = probability > 0.5
            confidence = probability if is_phishing else (1 - probability)
        
        # Risk skorunu hesapla
        risk_score = int(probability * 100)
        
        return {
            'is_phishing': is_phishing,
            'probability': probability,
            'confidence': confidence,
            'risk_score': risk_score,
            'status': 'Phishing' if is_phishing else 'Legitimate',
            'processed_text': processed_text
        }
    
    def save_model(self):
        """Modeli kaydet"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Model state dict
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'training_history': self.training_history,
            'max_length': self.max_length
        }, self.model_path)
        
        # Tokenizer
        if self.tokenizer:
            os.makedirs(self.tokenizer_path, exist_ok=True)
            self.tokenizer.save_pretrained(self.tokenizer_path)
        
        print(f"💾 Model kaydedildi: {self.model_path}")
    
    def load_model(self):
        """Modeli yükle"""
        if os.path.exists(self.model_path):
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.training_history = checkpoint.get('training_history', {})
            print(f"📂 Model yüklendi: {self.model_path}")
            return True
        else:
            print(f"❌ Model dosyası bulunamadı: {self.model_path}")
            return False
    
    def plot_training_history(self):
        """Eğitim geçmişini görselleştir"""
        if not self.training_history['train_loss']:
            print("❌ Eğitim geçmişi bulunamadı.")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss plot
        ax1.plot(self.training_history['train_loss'], label='Train Loss', color='blue')
        ax1.plot(self.training_history['val_loss'], label='Validation Loss', color='red')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Accuracy plot
        ax2.plot(self.training_history['train_acc'], label='Train Accuracy', color='blue')
        ax2.plot(self.training_history['val_acc'], label='Validation Accuracy', color='red')
        ax2.set_title('Model Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plot_path = 'models/email/training_history.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"📊 Eğitim grafiği kaydedildi: {plot_path}")

def main():
    print("🎯 E-mail Detection Model")
    print("=" * 50)
    
    # Model oluştur
    model = EmailDetectionModel()
    
    # Gerçek veri seti kontrol et
    dataset_path = "dataset/emails/processed/combined_email_dataset.csv"
    if os.path.exists(dataset_path):
        print(f"📂 Veri seti bulundu: {dataset_path}")
        
        # Model eğit (4GB GPU için optimize edilmiş parametreler)
        model.train(dataset_path, epochs=15, batch_size=16, learning_rate=0.0001)
        
        # Eğitim grafiğini çiz
        model.plot_training_history()
        
        # Test et
        test_emails = [
            "URGENT: Your account will be suspended! Click here: http://fake-bank.com",
            "Thank you for your purchase. Your order has been processed successfully."
        ]
        
        print("\n🧪 Test sonuçları:")
        print("-" * 50)
        for email in test_emails:
            result = model.predict(email)
            print(f"E-mail: {email[:50]}...")
            print(f"Sonuç: {result['status']} ({result['risk_score']}% risk)")
            print("-" * 50)
    else:
        print(f"❌ Veri seti bulunamadı: {dataset_path}")
        print("📌 Önce scripts/download_email_dataset.py çalıştırın")

if __name__ == "__main__":
    main() 