# 🧠 Yapay Zeka (AI) Geliştirme Günlüğü

Bu günlük, **Akıllı Görev ve Zaman Yönetim Sistemi** projesinin geliştirilmesi sürecinde, yapay zeka kodlama asistanı (**Gemini / Antigravity**) ile yapılan iş birliğini, sorun çözme süreçlerini ve teknik aşamaları detaylandırmak amacıyla tutulmuştur.

---

## 📅 Aşamalar ve Geliştirme Süreci

### 🔹 Aşama 1: Proje Temellerinin Atılması & Mimarinin Belirlenmesi
* **Yapılan İşler:** Projenin Flask mikro-çatısı kullanılarak modüler ve sürdürülebilir bir yapıda kurulmasına karar verildi. AI'ın yönlendirmesiyle spagetti kod yapısından kaçınılarak **Flask Blueprints** mimarisi tercih edildi.
* **AI Katkısı:** Projenin dizin yapısı, eklentilerin (`extensions.py`) ve konfigürasyonların (`config.py`) ayrıştırılması AI tarafından şablon olarak sunuldu.
* **Karşılaşılan Teknik Sorun:** Flask-SQLAlchemy ve Flask-Migrate'in uygulama fabrikası (Application Factory) yapısında dairesel içe aktarma (circular import) hatalarına neden olması.
* **Çözüm:** AI, `db` nesnesinin `extensions.py` içinde tanımlanıp `create_app` içerisinde `db.init_app(app)` ile başlatılmasını sağlayarak dairesel bağımlılık hatasını tamamen çözdü.

### 🔹 Aşama 2: Veritabanı Modellerinin Tasarımı (ERD)
* **Yapılan İşler:** Kullanıcılar, Görevler ve Yapay Zeka Önerileri arasındaki ilişkileri barındıran ilişkisel veritabanı tasarımı yapıldı.
* **Modeller:**
  * `User`: Kullanıcı bilgilerini ve profil resmi (avatar) verisini tutar.
  * `Task`: Görev başlığı, açıklaması, önceliği, periyodu (günlük/haftalık/aylık) ve saat aralıklarını tutar.
  * `AISuggestion`: Yapay zekanın kullanıcıya özel ürettiği planlama raporlarını arşivler.
* **AI Katkısı:** Modeller arasındaki `1-to-Many` (Bire-Çok) ilişkilerin `backref` ve `cascade="all, delete-orphan"` özellikleri ile kurulması sağlandı. Böylece bir kullanıcı silindiğinde ona ait görevler ve AI önerileri de veritabanından güvenli bir şekilde silinmektedir.

### 🔹 Aşama 3: Kimlik Doğrulama & Yetkilendirme (Auth Blueprint)
* **Yapılan İşler:** Güvenli üye kayıt, şifrelenmiş giriş (`Werkzeug` kütüphanesi ile PBKDF2 şifreleme algoritması kullanılarak) ve çıkış işlemleri yapıldı.
* **AI Katkısı:** `Flask-Login` entegrasyonu ile `@login_required` dekoratörleri kullanılarak tüm görev sayfaları yetkisiz erişimlere karşı koruma altına alındı. AI ayrıca şifre sıfırlama talepleri için e-posta entegrasyon şablonunu hazırladı.

### 🔹 Aşama 4: Akıllı Arama, Filtreleme ve CRUD İşlemleri
* **Yapılan İşler:** Görevlerin periyoda ve öncelik sırasına göre filtrelenmesi, tamamlandı/tamamlanmadı durumlarının dinamik olarak değiştirilmesi ve SQL tabanlı arama motoru entegre edildi.
* **AI Katkısı:** SQL `LIKE` tabanlı arama sorgularının Flask-SQLAlchemy üzerinde güvenli ve optimize bir şekilde çalıştırılması için `filter((Task.title.like(f"%{search_query}%")) | ...)` yapısı kuruldu. Bu sayede SQL enjeksiyon riskleri önlenmiş oldu.

### 🔹 Aşama 5: Kural Tabanlı Akıllı Yapay Zeka Motoru (`ai_engine.py`)
* **Yapılan İşler:** Sisteme gerçek bir yapay zeka vizyonu katmak üzere görevleri analiz eden bir analiz ve optimizasyon motoru tasarlandı.
* **AI Katkısı:** AI ile yapılan beyin fırtınası sonucunda şu algoritmik yapı kuruldu:
  * **Zaman Çakışması Kontrolü:** Görevlerin saat aralıkları dakikaya dönüştürülerek (`parse_time_to_minutes`) çakışma durumları matematiksel olarak analiz edildi.
  * **Ağırlıklı Öncelik Sıralaması:** Görevler önceliklerine (`High: 3`, `Medium: 2`, `Low: 1`) ve başlangıç saatlerine göre akıllıca sıralandı.
  * **Kişiselleştirilmiş Öneriler:** Çok fazla yüksek öncelikli görev barındıran günlerde kullanıcıya 80/20 kuralını hatırlatan dinamik geri bildirimler eklendi.

### 🔹 Aşama 6: Çoklu Dil Desteği (Flask-Babel) & Arayüz Cilalama
* **Yapılan İşler:** Uygulamanın Türkçe ve İngilizce dillerinde tam uyumlu çalışması için `Flask-Babel` entegrasyonu yapıldı. Arayüz için göz yormayan, modern ve şık bir koyu tema (dark-theme) tasarımı uygulandı.
* **AI Katkısı:** Babel konfigürasyonu (`babel.cfg`), `.pot` ve `.po` çeviri dosyalarının derlenmesi için gerekli CLI komutları ve session tabanlı dil seçici fonksiyonu AI rehberliğinde yazıldı.

### 🔹 Aşama 7: Kod İyileştirme (Refactoring) & Merkezi Mimari Kurulumu
* **Yapılan İşler:** Kod kalitesini artırmak ve kod tekrarlarını engellemek amacıyla merkezi yardımcı modül mimarisine geçiş yapıldı. `app/utils.py` oluşturuldu. Rotalardaki (`auth/routes.py`, `tasks/routes.py`, `ai_engine.py`) yinelenen yardımcı fonksiyonlar (şifre sıfırlama e-postası, saat dakika dönüştürücüler vb.) bu merkezde toplandı.
* **AI Katkısı:** AI ile yapılan planlama doğrultusunda, çalışan sistem fonksiyonlarına en ufak bir zarar verilmeden kodlar başarıyla refaktör edildi. Dairesel bağımlılık yaratmayan merkezi içe aktarım (import) sistemi kuruldu.

---

## 💡 Yapay Zeka Prompt Mühendisliği ve İş Birliği Örnekleri

### 💬 Örnek 1: Zaman Çakışması Algoritması Arayışı
* **Kullanıcı İstemi:** *"Görevlerin saatlerinin çakışıp çakışmadığını bulan bir algoritma yazmak istiyorum. Saatler '09:30' ve '11:00' formatında string olarak tutuluyor. En verimli nasıl yapabiliriz?"*
* **AI Çözümü:** AI, string saatleri doğrudan karşılaştırmak yerine bunları gece yarısından itibaren geçen dakika cinsine çevirerek (`09*60 + 30 = 570`) sayısal karşılaştırma yapmayı önerdi. Çakışma durumunu kontrol eden `max(t1_start, t2_start) < min(t1_end, t2_end)` formülünü sundu. Bu formül, tüm sınır durumları (edge-cases) kapsayarak mükemmel çalıştı.

### 💬 Örnek 2: Veritabanı İlişkilerinde Hata Giderme
* **Kullanıcı İstemi:** *"Bir kullanıcıyı sildiğimde o kullanıcıya ait görevler veritabanında kalıyor ve veritabanı bütünlüğü bozuluyor. Bunu nasıl çözebilirim?"*
* **AI Çözümü:** AI, SQLAlchemy ilişkisine `cascade="all, delete-orphan"` parametresinin eklenmesini önerdi ve bu parametrenin arka planda SQL düzeyinde `ON DELETE CASCADE` tetikleyicisi gibi çalışarak veritabanı tutarlılığını nasıl koruduğunu açıkladı.

---

## 🛠️ Karşılaşılan Zorluklar ve Çözülen Hatalar

1. **UAC İzin Hataları (Windows):** Git kurulumu esnasında Windows Yönetici izin talebi nedeniyle kurulumun yarıda kalma riski oluştu. AI, beni uyararak ekrandaki yönetici iznine onay vermemi sağladı ve kurulumun başarıyla tamamlanmasına rehberlik etti.
2. **Çeviri Derleme Sorunu:** Çeviri dosyaları (.po) oluşturulduktan sonra uygulamanın bunları okuyamaması sorunu yaşandı. AI, `.po` dosyalarının ikili (binary) `.mo` dosyalarına derlenmesi gerektiğini hatırlatarak `pybabel compile` komutlarının doğru çalıştırılmasını sağladı.
3. **Zaman Dilimi Karşılaştırmaları:** Görevlerin oluşturulma tarihlerinin yerel zaman ile sunucu zamanı arasında fark göstermesi. AI önerisiyle tüm veritabanı zaman damgaları `datetime.utcnow` standardına çekildi ve istemci tarafında yerel saate dönüştürüldü.
4. **Eksik Python Bağımlılıkları ve Canlı Doğrulama:** Geliştirici python ortamında `python-dotenv` ve `Flask-Mail` gibi kritik bağımlılıkların eksik olmasından ötürü başlatma hatası alındı. AI asistanının yönlendirmesiyle, `requirements.txt` dosyasındaki tüm paket sürümleri `pip install -r requirements.txt` komutuyla sisteme kuruldu, dairesel bağımlılık içermeyen temiz bir çalışma ortamı sağlanarak Flask sunucusu yerel olarak başarıyla doğrulandı.

---

## 📊 Yapay Zeka ile Geliştirme Sürecinin Değerlendirmesi

Yapay zeka asistanı ile çiftli programlama (pair programming) yapmak geliştirme sürecini yaklaşık **%60-70 oranında hızlandırmıştır**. Kod bloklarının hızlıca üretilmesinin yanı sıra, karşılaşılan hata çıktılarının AI'a doğrudan beslenmesiyle hata çözme süreleri dakikalar seviyesine inmiştir. 

Özellikle mimari yapılandırma, güvenlik standartları (şifreleme, SQL enjeksiyon önleme) ve karmaşık çakışma algoritmalarının geliştirilmesinde AI asistanının sağladığı teorik ve pratik katkı, projenin akademik standartlarda başarıyla tamamlanmasında en büyük etken olmuştur.
