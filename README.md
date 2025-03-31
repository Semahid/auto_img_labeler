# Auto Image Labeler - Kullanım Kılavuzu

Auto Image Labeler, görüntülerde nesne tespiti yapan, etiketleme işlemlerini kolaylaştıran ve YOLO formatında veri setleri oluşturmaya yardımcı olan bir uygulamadır.

## İçindekiler

- [Kurulum](#kurulum)
- [Ana Ekran](#ana-ekran)
- [Görüntü Yükleme ve Gezinme](#görüntü-yükleme-ve-gezinme)
- [Manuel Etiketleme](#manuel-etiketleme)
- [Otomatik Etiketleme](#otomatik-etiketleme)
- [Etiketleri Kaydetme](#etiketleri-kaydetme)
- [Veri Setini Bölümleme](#veri-setini-bölümleme)

## Kurulum

1. Gerekli bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

## Ana Ekran

Uygulama aşağıdaki bölümlerden oluşmaktadır:

- **Görüntü Alanı**: Resimleri görüntülemek ve etiketlemek için kullanılan ana alan.
- **Kontrol Paneli**: Sağ tarafta bulunan kontrol butonları ve ayarlar.
  - Navigasyon Butonları (Önceki/Sonraki)
  - Klasör Açma
  - Etiketleri Kaydetme
  - Etiketleri Temizleme
  - Sınıf Yönetimi
  - Model Yönetimi
  - Veri Seti Yönetimi
  - Format Seçimi

## Görüntü Yükleme ve Gezinme

1. **Klasör Açma**: "Open Folder" butonuna tıklayarak resim dosyalarını içeren bir klasör seçin.
2. **Resimler Arası Gezinme**: 
   - "Next" ve "Previous" butonlarını kullanarak resimler arasında geçiş yapabilirsiniz.
   - Alternatif olarak sağ/sol ok tuşlarını kullanabilirsiniz.

## Manuel Etiketleme

1. **Dikdörtgen Çizme**: 
   - Görüntü üzerinde fare ile tıklayıp sürükleyerek yeni bir dikdörtgen çizin.
   - Minimum 5x5 piksel boyutunda olmalıdır.

2. **Dikdörtgen Düzenleme**:
   - Mevcut bir dikdörtgene tıklayarak seçin.
   - Seçili dikdörtgeni fare ile sürükleyerek taşıyabilirsiniz.
   - Kenarlar ve köşelerden tutarak yeniden boyutlandırabilirsiniz.
   - DELETE tuşu ile seçili dikdörtgeni silebilirsiniz.

3. **Sınıf Yönetimi**:
   - "Classes" bölümünden mevcut bir sınıf seçin.
   - "Add Class" butonu ile yeni sınıflar ekleyebilirsiniz.
   - "Set Class to Selected" butonu ile seçili dikdörtgenin sınıfını değiştirebilirsiniz.

## Otomatik Etiketleme

1. **Model Yükleme**:
   - "Model Management" bölümünden "Open folder" butonuna tıklayarak bir YOLOv8 modeli (.pt) seçin.
   - Güven eşiğini ayarlayın (varsayılan: 0.5).

2. **Etiketleme**:
   - **Tek Resim**: "Auto label current image" butonuna tıklayarak görüntülenen resim için otomatik nesne tespiti yapın.
   - **Toplu İşlem**: "Simple Auto label all image" butonu ile klasördeki tüm resimleri otomatik olarak etiketleyin.

## Etiketleri Kaydetme

1. **Format Seçimi**:
   - "Output Format" bölümünden istediğiniz formatı seçin:
     - YOLO Format (sınıf_id, x_merkez, y_merkez, genişlik, yükseklik) - normalize edilmiş
     - Standard Format (x, y, genişlik, yükseklik, sınıf_id) - piksel değerleri

2. **Kaydetme**:
   - "Save Annotations" butonuna tıklayarak etiketleri kaydedin.
   - Etiketler, görüntülerin bulunduğu klasörde "annotations" adlı bir alt klasöre kaydedilir.
   - Sınıf bilgileri "classes.json" dosyasında saklanır.

## Veri Setini Bölümleme

YOLO eğitimi için veri setinizi train, validation ve test olarak bölebilirsiniz:

1. **Oranları Ayarlama**:
   - "Data splitter" bölümünden train, validation ve test için yüzde oranlarını belirleyin.
   - Oranların toplamı 100 olmalıdır.

2. **Bölümlendirme**:
   - "Split dataset" butonuna tıklayın.
   - Çıktı klasörünü seçin.
   - İşlem tamamlandığında otomatik olarak:
     - Train, validation ve test alt klasörleri oluşturulur.
     - data.yaml dosyası oluşturulur.
     - Tüm veri seti bir zip dosyası olarak paketlenir.

## Kısayollar

- **Sağ/Sol Ok**: Sonraki/önceki görüntüye geçiş
- **DELETE**: Seçili dikdörtgeni sil
