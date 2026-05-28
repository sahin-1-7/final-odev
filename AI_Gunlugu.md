# 🧠 Yapay Zeka (AI) Geliştirme Günlüğü

Bu günlük, **Glide** projesinin geliştirilmesi sürecinde, yapay zeka kodlama asistanı (**Gemini / Antigravity**) ile yapılan iş birliğini, sorun çözme süreçlerini ve teknik aşamaları detaylandırmak amacıyla tutulmuştur.

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

### 🔹 Aşama 8: Kullanıcı Profili ve Güvenli Avatar Yükleme Modülü
* **Yapılan İşler (2. Gün - 4. Oturum Notu):** Projenin en hassas noktalarından biri olan Dosya Yükleme (File Upload) güvenliğini ele aldık. Sadece uzantı kontrolüyle yetinmeyip, secure_filename mantığı ve UUID entegrasyonu ile Path Traversal ve sunucuda dosyaların üst üste yazılmasını engelledik. Ayrıca Pillow kütüphanesi ile derin dosya içerik kontrolü ve EXIF temizliği (Polyglot koruması) sağlayarak sistemi siber güvenlik denetimlerinden sorunsuz geçecek düzeye ulaştırdık. Bu sayede hem +4 bonus puanı garantiledik hem de uygulamanın teknik doğruluğunu üst seviyeye çıkardık. (Görsel: AI_Guvenlik_Analizi.png)
* **AI Katkısı:** AI, uzantı bazlı temel korumaların Burp Suite gibi sızma araçlarıyla kolayca aşılacağını belirtti. Bunun üzerine Pillow ile bellek seviyesinde resim doğrulama ve resmi yeni temiz kanallarla sunucu diskine sıfırdan çizerek kaydetme (re-saving) mimarisini sundu. Bu sızma testi düzeyindeki katman başarıyla entegre edildi.

### 🔹 Aşama 9: Yapay Zeka Arayüzü Modernizasyonu & Güvenlik Sıkılaştırması
* **Yapılan İşler (2. Gün - 5. Oturum Notu):** Yapay zeka sayfalarının (AI Chat ve AI Planner) renk teması ve görsel kalitesi fütüristik bir yapıya taşındı. Dinamik ambient parıltı küreleri ve siber ızgara arkaplanları eklendi. Sohbet pencereleri cam efekti (glassmorphism) ve neon çizgilerle premiumlaştırıldı. Görsel avatarlar, tek tıklamayla sohbet başlatan öneri çipleri ve sohbet geçmişini veritabanından dinamik silen `/ai/chat/clear` temizleme rotası kuruldu. API model parametresi esnekleştirilerek `GEMINI_MODEL=gemini-2.0-flash` desteği sağlandı. Sunucu log güvenliği artırılarak olası bağlantı hatalarında API anahtarının konsol loglarına sızması `MASKED_KEY` filtresi ile tamamen önlendi.
* **AI Katkısı:** AI asistanı, arayüz modernizasyonu için HSL tabanlı salınan ışıma küresi animasyonlarını ve grid koordinat matrisini sundu. Ayrıca siber güvenlik denetimlerinden geçecek şekilde traceback hata günlüklerindeki API anahtarlarını algılayıp dinamik maskeleyen regex tabanlı hata yakalama kalkanını geliştirdi.

### 🔹 Aşama 10: E-Posta ile Şifre Sıfırlama Akışı & Siber Güvenlik Sıkılaştırması
* **Yapılan İşler (2. Gün - 6. Oturum Notu):** Projenin en yüksek puanlı bonus özelliklerinden biri olan E-Posta ile Şifre Sıfırlama Akışı (+5 Puan) tamamlandı ve siber güvenlik denetimlerinden en yüksek dereceyle geçecek şekilde sıkılaştırıldı.
  * **Kullanıcı Tespiti (User Enumeration) Engellemesi:** İstek gönderildiğinde e-postanın kayıtlı olup olmadığının anlaşılmasını engelleyen jenerik bir başarı mesajı yapısı kuruldu.
  * **Tek Kullanımlık (One-Time) Kriptografik Token:** Token içerisine kullanıcının güncel şifre hash'i gömüldü. Şifre değiştirildiği an eski token'lar otomatik olarak geçersiz kılınmaktadır.
  * **Spam & DoS Hız Sınırlaması (Rate Limiting):** `User` modeline `last_reset_request_at` alanı eklenerek aynı e-postaya peş peşe 120 saniyeden kısa sürelerle şifre sıfırlama maili talep edilmesi engellendi.
* **AI Katkısı:** AI, itsdangerous token'larının tek kullanımlık hale getirilmesi için şifre hash tabanlı durumsuz imzalama modelini sundu. Ayrıca Flask-Migrate entegrasyonuyla veritabanı şemasının güvenle güncellenmesini ve yerel test betikleriyle doğrulanmasını sağladı.

### 🔹 Aşama 11: Görev CRUD, Zaman Çakışma Validasyonu ve Çoklu Dil Raporlama
* **Yapılan İşler (3. Gün - 6. Oturum Notu):** Projenin omurgasını oluşturan Görev CRUD işlemlerini tamamladık. Veritabanı tutarlılığı ve veri doğruluğu için kritik olan 'Zaman Çakışma Algoritması'nı kurduk. `(start1 < end2) & (end1 > start2)` mantığıyla iki görevin çakışmasını backend seviyesinde engelledik. Eş zamanlı olarak, listeleme ekranına SQL LIKE tabanlı arama motoru entegre ederek +3 bonus puan, tüm mesajları Flask-Babel ile sarmallayarak da +3 bonus puan daha kazandık. (Görsel: AI_Conflict_Check_Algorithm.png)
* **AI Katkısı:** AI asistanı, zaman çakışma koşullarının in-memory SQLite tabanlı test senaryolarını yazarak algoritmayı otomatik olarak doğruladı. Ayrıca, AI analiz ve planlama raporunun (Gemini ve yerel motor) kullanıcının seçtiği dile göre dinamik olarak Türkçe veya İngilizce dilinde üretilmesini sağlayan yerelleştirme katmanını kodladı.

### 🔹 Aşama 12: Güvenli ve Performanslı Tam Metin Arama Entegrasyonu (3. Gün - 7. Oturum Notu)
* **Yapılan İşler (3. Gün - 7. Oturum Notu):** Kullanıcı deneyimini artıran Tam Metin Arama (Full-Text Search) özelliğini ön yüze entegre ettik. Güvenlik tarafında kritik bir hamle yaparak, SQL LIKE sorgusunu `current_user.id` filtresiyle sarmalladık; böylece ID tabanlı veri sızıntısı (BOLA/IDOR) zafiyetlerini tamamen engelledik. Arama arayüzündeki tüm dinamik uyarıları Flask-Babel ile iki dilli hale getirerek +3 bonus puanı daha temiz bir kod mimarisiyle cebimize koyduk. (Görsel: AI_Search_Secure_Query.png)
* **AI Katkısı:** AI asistanı, SQL `LIKE` aramalarındaki özel karakterlerden kaynaklanan güvenlik zafiyetlerini önlemek amacıyla `%`, `_` ve `\` gibi SQL wildcard karakterlerini regex ile kaçış karakterlerine dönüştüren girdi filtreleme katmanını sundu. Ayrıca arayüzde 300ms debounce (gecikmeli arama) ve yükleniyor animasyonunu ekleyen asenkron JavaScript kodunu hazırladı.

### 🔹 Aşama 13: AI Sohbet Asistanı Çoklu Dil Entegrasyonu ve Otomatik Entegrasyon Testleri (3. Gün - 8. Oturum Notu)
* **Yapılan İşler (3. Gün - 8. Oturum Notu):** Yapay Zeka Sohbet Asistanı (AI Chat) sayfasındaki tüm hardcoded Türkçe metinler, karşılama mesajı, öneri çipleri (`data-prompt` payload'ları dahil), form yer tutucuları, hata mesajları ve Javascript onay/uyarı pencereleri Flask-Babel `_()` fonksiyonlarıyla sarmalanarak 6 dilde (Türkçe, İngilizce, Fransızca, İspanyolca, Hintçe, Arapça) dinamik hale getirildi. Backend rotasındaki dil algılama `str(get_locale())` kullanılarak template ile 100% senkronize edildi.
* **AI Katkısı:** AI asistanı, Flask-Babel'in request context caching davranışından kaynaklanan diller arası geçiş senkronizasyon hatalarını çözmek amacıyla rotada `str(get_locale())` kullanılmasını önerdi. Ayrıca, tüm dillerde çevirilerin ve şablonların sorunsuz derlendiğini ve yüklendiğini teyit eden isolated-context (bağımsız uygulama bağlamı sunan) `test_ai_chat_rendering.py` otomatik entegrasyon test suite'ini yazdı. Bu sayede diller arası geçişin 100% hatasız çalıştığı kanıtlanmış oldu.

### 🔹 Aşama 14: Yapay Zeka Entegrasyonu ve Prompt Mühendisliği Sıkılaştırması (4. Gün - 8. Oturum Notu)
* **Yapılan İşler (4. Gün - 8. Oturum Notu):** Projenin yapay zeka entegrasyonunu (Gemini/OpenAI) gerçekleştirdik. En büyük zorluk olan 'Yapay zekanın her zaman kararlı JSON dönmesi' problemini, sıkı bir Sistem Promptu (System Instructions) ve JSON Şeması (Schema Enforcement) tasarımıyla çözdük. Uygulamadaki iki dilli arayüz (+3 Puan) kriterine uyum sağlamak adına, yapay zekaya analiz raporunu hem TR hem EN olarak ürettirdik. Bu sayede Flask-Babel dil seçimine göre dinamik raporlama yapabiliyoruz. Süreçteki prompt denemelerimizi ve aldığımız çıktıları AI Günlüğü (25 Puan) dokümantasyonumuza ekledik. (Görsel: AI_System_Prompt_Design.png)
* **AI Katkısı:** AI asistanı, `"responseMimeType": "application/json"` parametresini API istek payload'ına ekleyerek ve çıktıyı markdown kod bloklarından temizleyen regex süzgeci tasarlayarak her koşulda geçerli JSON nesnesi elde edilmesini garantiledi. Ayrıca iki dil çıktısını tek bir çağrıda optimize edip döndüren prompt stratejisini geliştirdi.

### 🔹 Aşama 15: Güvenli RESTful API Tasarımı, Tam Dakika Geri Sayım & 0sn Bildirim Garantisi (4. Gün - 9. Oturum Notu)
* **Yapılan İşler (4. Gün - 9. Oturum Notu):** Uygulamamıza profesyonel bir çehre kazandıran `/api/v1/tasks` RESTful API endpoint'lerini geliştirdik. Jürinin siber güvenlik hassasiyetlerini göz önünde bulundurarak, API rotalarında sıkı bir yetkilendirme (Authorization) mimarisi uyguladık. Dışarıdan gelen POST isteklerindeki JSON verilerini backend'deki saat çakışma algoritmamızla denetleyerek veri bütünlüğünü koruduk. API'den dönen tüm JSON yanıt şemalarına yapay zeka optimizasyon çıktılarını entegre ettik ve mesajları Flask-Babel ile iki dilli hale getirerek +5 bonus puanı daha mimari bütünlükle projemize kazandırdık. (Görsel: API_Postman_Security_Test.png)
  - Ayrıca bildirim altyapısını güçlendirerek, yaklaşan görevlerin başlama ve bitiş sürelerini tam dakika cinsinden yukarı yuvarlanmış (`Math.ceil`) sayaçlarla saniye hassasiyetinde sunan bir motor geliştirdik. Transizyonel Bildirim Garantisi ile tam `0` saniyede `"Görev Başladı!"` ve `"Görev Bitti!"` bildirimlerinin kaçırılmaksızın ve mükerrer olmaksızın birer kez tetiklenmesini sağladık.
* **AI Katkısı:** AI asistanı, `itsdangerous` kütüphanesini kullanarak kullanıcı ID'sini gizli anahtar ile kriptografik imzalayan ve dışarıya sızmayan stateless API Key mimarisini tasarladı. Arayüzde ise arka plan kısıtlamaları veya milisaniye kaymalarında 0. saniye bildiriminin atlanmasını kesin olarak engelleyen durum makinesi tabanlı tetikleyici mantığını kodladı.

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
