# 🧠 Yapay Zeka (AI) Geliştirme Günlüğü

Bu günlük, **Glide** projesinin geliştirilmesi sürecinde, geliştirici ile yapay zeka kodlama asistanı (**Gemini / Antigravity**) arasında yapılan iş birliğini, planlama aşamalarını, revizyonları, hata çözme süreçlerini ve en önemlisi her aşamadan edinilen kritik çıkarımları detaylandırmak amacıyla tutulmuştur.

---

## 📅 Aşamalar ve Geliştirme Süreci (Oturum Günlükleri)

### **Oturum 1 — 5 Mayıs — 19:00-20:30 (Mimarinin Belirlenmesi & User Modeli Tasarımı)**
*   **Yapılan İşler:** Projenin Flask mikro-çatısı kullanılarak modüler ve sürdürülebilir bir yapıda kurulmasına karar verildi. Spagetti kod yapısından kaçınılarak **Flask Blueprints** mimarisi tercih edildi.
*   **AI Planı ve Revizyonlar:** Ajan'a User modeli için Plan modunda istek verdim. İlk plan'da SQLAlchemy 1.x stili (`db.Column`) kullanıyordu. Ben 2.x istemiştim. *"`Mapped[str]` kullan"* diyerek planı revize ettirdim. İkinci planda email alanına `unique=True` koymuş ama validate_email kullanmamıştı. Bunu da ekledim çünkü kullanıcı boş veya hatalı e-posta girerse veritabanına kaydetmek istemiyorum. Plan'ı 2 turda olgunlaştırdıktan sonra kodu üretti. Üretilen koddaki `__repr__` metodunda f-string yerine `.format()` kullanmıştı; tutarlılık için f-string'e çevirdim.
*   **Bu oturumdan asıl öğrendiğim:** Planı sorgulamadan onaylasaydım eski stilde bir kodla başlayacaktım ve bu hatayı sonradan düzeltmek çok daha pahalı olacaktı.

---

### **Oturum 2 — 6 Mayıs — 14:00-15:30 (İlişkisel Veritabanı Tasarımı - ERD)**
*   **Yapılan İşler:** Kullanıcılar, Görevler ve Yapay Zeka Önerileri arasındaki ilişkileri barındıran ilişkisel veritabanı şeması (`User`, `Task`, `AISuggestion`) kurgulandı.
*   **AI Planı ve Revizyonlar:** AI ilk planında modeller arasında sadece basit ForeignKey bağlantıları yapıp bırakmıştı. Ben ise bir kullanıcı silindiğinde ona ait görevlerin ve önerilerin öksüz kalıp bütünlüğü bozmasını engellemek amacıyla `cascade="all, delete-orphan"` ilişkisel kısıtlamasının eklenmesini talep ettim. AI bu cascade mantığını modeller arasındaki `relationship` alanlarına yerleştirerek planı güncelledi.
*   **Bu oturumdan asıl öğrendiğim:** İlişkisel veritabanlarında `ON DELETE CASCADE` muadili cascade davranışlarının ORM seviyesinde baştan kurulmaması, ilerleyen süreçlerde veritabanı kirliliğine ve tutarsızlığına yol açmaktadır.

---

### **Oturum 3 — 10 Mayıs — 11:00-12:30 (Kimlik Doğrulama & Yetkilendirme)**
*   **Yapılan İşler:** Güvenli üye kayıt, şifreli giriş (`Werkzeug` kütüphanesi ile PBKDF2 şifreleme algoritması kullanılarak) ve çıkış işlemleri yapıldı.
*   **AI Planı ve Revizyonlar:** AI ilk planında şifreleri veritabanına doğrudan veya zayıf şifreleme yöntemleriyle kaydetmeye eğilimliydi. Bunu hemen güvenlik protokolü gereği hash'leme algoritmasıyla revize ettirdim. Rotalara `@login_required` ekleyerek panel güvenliğini sağladık.
*   **Bu oturumdan asıl öğrendiğim:** Kullanıcı şifre güvenliği hiçbir şekilde ertelenmemeli veya "yerel geliştirme aşamasında kalsın" denmemeli, baştan en yüksek kriptografik standartlarda ele alınmalıdır.

---

### **Oturum 4 — 12 Mayıs — 16:00-17:30 (Görev CRUD ve Arama Altyapısı)**
*   **Yapılan İşler:** Görevlerin periyoda ve öncelik sırasına göre filtrelenmesi, tamamlandı/tamamlanmadı durumlarının dinamik olarak değiştirilmesi ve SQL tabanlı arama motoru entegre edildi.
*   **AI Planı ve Revizyonlar:** AI ilk kodunda IDOR/BOLA açığına sebep olabilecek şekilde kullanıcı filtresi olmadan doğrudan görev id'si üzerinden arama yapıyordu. Arama sorgusuna kesin olarak `current_user.id` kısıtını ekleterek yetkisiz kullanıcıların diğer verileri okumasını engelledim.
*   **Bu oturumdan asıl öğrendiğim:** Bir kullanıcının veritabanı sorgusuna sarmalayıcı sahiplik filtresi eklemeden veri çekmek, en yaygın siber güvenlik zaafiyetlerine (BOLA) kapı aralamaktadır.

---

### **Oturum 5 — 15 Mayıs — 10:00-11:30 (Kural Tabanlı AI Zaman Analizi)**
*   **Yapılan İşler:** Görevleri analiz eden, zaman çakışmalarını bulan ve öncelik sıralaması yapan bir analiz motoru (`ai_engine.py`) tasarlandı.
*   **AI Planı ve Revizyonlar:** AI ilk başta karmaşık string karşılaştırmaları yapmayı planlıyordu. Bunu `parse_time_to_minutes` fonksiyonu ile saatleri dakikaya çevirip sayısal `max(S1, S2) < min(E1, E2)` matematiksel modeli ile karşılaştırarak basitleştirdik ve sınır durumları (edge-cases) kapsadık.
*   **Bu oturumdan asıl öğrendiğim:** String formatındaki karmaşık verileri sayısal tabana indirgemek, algoritmaların işlem yükünü azaltır ve sınır durumları daha hatasız yönetmemizi sağlar.

---

### **Oturum 6 — 18 Mayıs — 14:00-15:30 (Çoklu Dil Babel Entegrasyonu)**
*   **Yapılan İşler:** Uygulamanın Türkçe ve İngilizce dillerinde tam uyumlu çalışması için `Flask-Babel` entegrasyonu yapıldı.
*   **AI Planı ve Revizyonlar:** AI ilk planda dil derlemelerini yerel ortamda unuttu. Dil dosyalarının derlenmesi gerektiğini hatırlatarak `.po` dosyalarının `pybabel compile` komutuyla ikili `.mo` dosyalarına derlenmesini sağladım.
*   **Bu oturumdan asıl öğrendiğim:** Dil dosyaları sadece çevrilmekle kalmaz; üretim ortamında okunabilmesi için binary formata derlenmesi gerekir, aksi takdirde çeviriler aktif olmaz.

---

### **Oturum 7 — 20 Mayıs — 11:00-12:30 (Kod Refaktör & utils.py Kurulumu)**
*   **Yapılan İşler:** Kod kalitesini artırmak ve kod tekrarlarını engellemek amacıyla merkezi yardımcı modül mimarisine geçiş yapıldı.
*   **AI Planı ve Revizyonlar:** AI ilk başta rotalarda yinelenen e-posta ve saat dönüştürücü mantıklarını her rotanın içine tek tek yazmıştı. Bunu dairesel bağımlılık yaratmayan merkezi `app/utils.py` dosyasına taşıyarak kodu tamamen refaktör ettirdim.
*   **Bu oturumdan asıl öğrendiğim:** Kod tekrarını (DRY) sıfırlamak ve projeyi sürdürülebilir kılmak için yardımcı sınıfları projenin başında ortak bir utility modülüne taşımak kritik öneme sahiptir.

---

### **Oturum 8 — 22 Mayıs — 15:00-16:30 (Güvenli Profil Resmi Yükleme)**
*   **Yapılan İşler:** Profil resmi yükleme modülünün siber güvenlik sıkılaştırması ele alındı.
*   **AI Planı ve Revizyonlar:** AI sadece temel uzantı kontrolü yapmayı planlarken, Burp Suite gibi sızma test araçlarıyla uzantıların kolayca manipüle edileceğini söyleyerek Pillow ile resim derinliği doğrulama ve resmi sunucu diskine sıfırdan çizerek kaydetme (re-saving) mimarisini eklettim.
*   **Bu oturumdan asıl öğrendiğim:** Dosya yükleme güvenliklerinde sadece uzantı kontrolü (whitelist) yetmez; Pillow gibi kütüphanelerle içerik doğrulaması (EXIF temizliği/re-saving) yapmak polyglot saldırılarını tamamen engeller.

---

### **Oturum 9 — 23 Mayıs — 13:00-14:30 (Yapay Zeka Arayüz Modernizasyonu)**
*   **Yapılan İşler:** Yapay Zeka Sohbet Asistanı sayfalarını koyu tema cam estetiğiyle (glassmorphism), ambient neon parıltı küreleriyle ve siber koordinat ızgaralarıyla modernize ettik.
*   **AI Planı ve Revizyonlar:** AI sadece temel arayüz tasarımlarını sundu. Kullanıcının sohbet geçmişini temizleyebilmesi için `/ai/chat/clear` geçmişi güvenle silme rotasını ve fütüristik HSL parıltı animasyonlarını eklettim.
*   **Bu oturumdan asıl öğrendiğim:** Kullanıcı arayüzünde modern fütüristik ögeler ve yumuşak HSL geçişleri kullanmak, kullanıcı etkileşimini ve premium ürün algısını ciddi ölçüde artırmaktadır.

---

### **Oturum 10 — 25 Mayıs — 17:00-18:30 (E-Posta Şifre Sıfırlama Akışı)**
*   **Yapılan İşler:** Tek kullanımlık kriptografik token ve spam/DoS koruması (Rate Limiting) içeren şifre sıfırlama akışı entegre edildi.
*   **AI Planı ve Revizyonlar:** AI ilk planında token geçerliliğini süresiz yapıyordu. Token geçerliliğine 15 dakika kısıt eklettim ve token içine şifre hash'ini gömdürerek şifre değiştiğinde token'ın otomatik geçersiz kalmasını sağladım.
*   **Bu oturumdan asıl öğrendiğim:** E-posta sıfırlama gibi akışlarda kullanıcı tespiti (user enumeration) açıklarını engellemek adına kayıt durumundan bağımsız jenerik başarı mesajları dönmek şarttır.

---

### **Oturum 11 — 26 Mayıs — 10:00-11:30 (Zaman Çakışma Validasyonu ve CRUD)**
*   **Yapılan İşler:** Görev ekleme ve düzenleme modal pencereleri yapıldı. Zaman çakışma doğrulama algoritmaları entegre edildi.
*   **AI Planı ve Revizyonlar:** AI test senaryolarını canlı veritabanında çalıştırıyordu. Veritabanı kirliliğini önlemek amacıyla SQLite in-memory test senaryolarıyla izole bağlamda test etmesini sağladım.
*   **Bu oturumdan asıl öğrendiğim:** Test senaryolarını veritabanından bağımsız (in-memory) çalıştırmak, entegrasyon testlerinin çalışma hızını ve kararlılığını artırır.

---

### **Oturum 12 — 27 Mayıs — 14:00-15:30 (Asenkron Güvenli Arama Motoru)**
*   **Yapılan İşler:** AJAX çağrıları ve 300ms debounce (gecikmeli tetikleme) yapısıyla çalışan asenkron tam metin arama entegre edildi.
*   **AI Planı ve Revizyonlar:** AI ilk kodunda SQL sorgularını doğrudan çalıştırıyordu. SQL aramasında enjeksiyon ve mantıksal hataları önlemek adına `%` ve `_` karakterlerini regex ile kaçış karakterine dönüştüren girdi filtreleme katmanını eklettim.
*   **Bu oturumdan asıl öğrendiğim:** Asenkron aramalarda debounce kullanmamak sunucuya aşırı yük bindirir; girdi temizliği (input sanitization) ise SQL injection açıklarına karşı en güçlü kalkandır.

---

### **Oturum 13 — 27 Mayıs — 16:00-17:30 (AI Chat 6 Dil Entegrasyonu)**
*   **Yapılan İşler:** Yapay Zeka Sohbet Asistanı sayfasındaki tüm karşılama mesajlarını, öneri çiplerini ve form yer tutucularını Flask-Babel ile Türkçe, İngilizce, Fransızca, İspanyolca, Hintçe ve Arapça dillerinde dinamik hale getirdik.
*   **AI Planı ve Revizyonlar:** AI ilk planında Babel önbellek mekanizması nedeniyle diller arası geçişte hata veriyordu. Babel'in request context caching davranışını aşmak için rotada `str(get_locale())` kullanımına geçtik.
*   **Bu oturumdan asıl öğrendiğim:** Çok dilli uygulamalarda request bazlı yerelleştirme önbelleklemeleri diller arası geçişte senkronizasyon hatalarına sebep olabilir, bunu aşmak için çalışma anındaki dil durumunu doğrudan rotada çözümlemek gerekir.

---

### **Oturum 14 — 28 Mayıs — 11:00-12:30 (Yapay Zeka JSON Şeması & Prompt Mühendisliği)**
*   **Yapılan İşler:** Gemini API ile entegrasyon kuruldu ve Yapay Zeka Planlama arayüzleri tamamlandı.
*   **AI Planı ve Revizyonlar:** Yapay zekanın her zaman kararlı ve geçerli JSON dönmesi sorununu çözmek için AI'a sıkı bir Sistem Promptu (System Instructions) tasarlatıp `"responseMimeType": "application/json"` parametresini API istek payload'ına eklettim.
*   **Bu oturumdan asıl öğrendiğim:** Yapay zekadan alınacak çıktının kararlılığı, doğru yapılandırılmış JSON şemaları ve sistem talimatlarıyla doğrudan ilişkilidir, aksi halde parser hataları kaçınılmazdır.

---

### **Oturum 15 — 28 Mayıs — 15:00-16:30 (RESTful API & Geri Sayım Motoru)**
*   **Yapılan İşler:** `/api/v1/tasks` RESTful API endpoint'lerini geliştirdik. Arayüzde yer alan Bootstrap Toast geri sayım motorunu ve 0. saniyedeki işletim sistemi bildirimlerinin (Web Notifications) atlanmasını engelleyen durum makinesini kodladık.
*   **AI Planı ve Revizyonlar:** AI API anahtarlarını veritabanında saklamayı planlıyordu. Sızma riskine karşı `itsdangerous` ile stateless API Key mimarisini tasarlattım.
*   **Bu oturumdan asıl öğrendiğim:** Mobil veya dış entegrasyonlar için sunulan API anahtarlarının stateless olması veri sızıntılarını ve sunucu tarafındaki kilitlenmeleri önlemektedir.

---

### **Oturum 16 — 29 Mayıs — 11:00-12:30 (Canlıya Alma, Docker & SQLAlchemy 2.0 Geçişi)**
*   **Yapılan İşler:** Uygulamayı yerelden Render/Railway platformlarına taşıdık. SQLite yerine PostgreSQL veritabanını entegre ettik. Geliştirme sunucusu yerine üretim ortamında Gunicorn WSGI sunucusunu konumlandırdık. `render.yaml` ve `Dockerfile` ile IaC standartlarını tamamladık. Son derece önemli bir refaktör hamlesi yaparak, tüm SQLAlchemy modellerini modern **SQLAlchemy 2.0 Mapped & mapped_column** stiline yükselttik.
*   **AI Planı ve Revizyonlar:** AI ilk başta veritabanı bağlantı dizelerini koda gömmeyi planlıyordu. `DATABASE_URL` çevre değişkenleri izolasyonunu ve `postgres://` -> `postgresql://` otomatik düzeltme mantığını kurdurdum.
*   **Bu oturumdan asıl öğrendiğim:** Canlıya geçiş süreçlerinde `DATABASE_URL` gibi hassas bilgileri çevre değişkenleri üzerinden beslemek siber güvenlik zafiyetlerini önler; modern SQLAlchemy 2.0 söz dizimi ise modelleri geleceğe hazır ve tip güvenli kılar.

---

## 💡 Yapay Zeka Prompt Mühendisliği ve İş Birliği Örnekleri

### 💬 Örnek 1: Zaman Çakışması Algoritması Arayışı
*   **Kullanıcı İstemi:** *"Görevlerin saatlerinin çakışıp çakışmadığını bulan bir algoritma yazmak istiyorum. Saatler '09:30' ve '11:00' formatında string olarak tutuluyor. En verimli nasıl yapabiliriz?"*
*   **AI Çözümü:** AI, string saatleri doğrudan karşılaştırmak yerine bunları gece yarısından itibaren geçen dakika cinsine çevirerek (`09*60 + 30 = 570`) sayısal karşılaştırma yapmayı önerdi. Çakışma durumunu kontrol eden `max(t1_start, t2_start) < min(t1_end, t2_end)` formülünü sundu. Bu formül, tüm sınır durumları (edge-cases) kapsayarak mükemmel çalıştı.

### 💬 Örnek 2: Veritabanı İlişkilerinde Hata Giderme
*   **Kullanıcı İstemi:** *"Bir kullanıcıyı sildiğimde o kullanıcıya ait görevler veritabanında kalıyor ve veritabanı bütünlüğü bozuluyor. Bunu nasıl çözebilirim?"*
*   **AI Çözümü:** AI, SQLAlchemy ilişkisine `cascade="all, delete-orphan"` parametresinin eklenmesini önerdi ve bu parametrenin arka planda SQL düzeyinde `ON DELETE CASCADE` tetikleyicisi gibi çalışarak veritabanı tutarlılığını nasıl koruduğunu açıkladı.

---

## 🛠️ Karşılaşılan Zorluklar ve Çözülen Hatalar

1.  **UAC İzin Hataları (Windows):** Git kurulumu esnasında Windows Yönetici izin talebi nedeniyle kurulumun yarıda kalma riski oluştu. AI, beni uyararak ekrandaki yönetici iznine onay vermemi sağladı ve kurulumun başarıyla tamamlanmasına rehberlik etti.
2.  **Çeviri Derleme Sorunu:** Çeviri dosyaları (.po) oluşturulduktan sonra uygulamanın bunları okuyamaması sorunu yaşandı. AI, `.po` dosyalarının ikini (binary) `.mo` dosyalarına derlenmesi gerektiğini hatırlatarak `pybabel compile` komutlarının doğru çalıştırılmasını sağladı.
3.  **Zaman Dilimi Karşılaştırmaları:** Görevlerin oluşturulma tarihlerinin yerel zaman ile sunucu zamanı arasında fark göstermesi. AI önerisiyle tüm veritabanı zaman damgaları `datetime.utcnow` standardına çekildi ve istemci tarafında yerel saate dönüştürüldü.
4.  **Eksik Python Bağımlılıkları ve Canlı Doğrulama:** Geliştirici python ortamında `python-dotenv` ve `Flask-Mail` gibi kritik bağımlılıkların eksik olmasından ötürü başlatma hatası alındı. AI asistanının yönlendirmesiyle, `requirements.txt` dosyasındaki tüm paket sürümleri `pip install -r requirements.txt` komutuyla sisteme kuruldu, dairesel bağımlılık içermeyen temiz bir çalışma ortamı sağlanarak Flask sunucusu yerel olarak başarıyla doğrulandı.

---

## 📊 Yapay Zeka ile Geliştirme Sürecinin Değerlendirmesi

Yapay zeka asistanı ile çiftli programlama (pair programming) yapmak geliştirme sürecini yaklaşık **%60-70 oranında hızlandırmıştır**. Kod bloklarının hızlıca üretilmesinin yanı sıra, karşılaşılan hata çıktılarının AI'a doğrudan beslenmesiyle hata çözme süreleri dakikalar seviyesine inmiştir.

Özellikle mimari yapılandırma, güvenlik standartları (şifreleme, SQL enjeksiyon önleme) ve karmaşık çakışma algoritmalarının geliştirilmesinde AI asistanının sağladığı teorik ve pratik katkı, projenin akademik standartlarda başarıyla tamamlanmasında en büyük etken olmuştur.
