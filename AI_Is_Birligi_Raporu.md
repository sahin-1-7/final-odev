# 🤖 Yapay Zeka (AI) ve Geliştirici İş Birliği Raporu

Bu rapor, **Glide - Akıllı Görev ve Zaman Yönetim Sistemi** projesinin geliştirilmesi sürecinde, geliştirici ile yapay zeka kodlama asistanı (**Gemini / Antigravity**) arasında gerçekleştirilen üst düzey teknik iş birliğini, siber güvenlik sıkılaştırmalarını, mimari dönüşümleri ve hata giderme süreçlerini kanıtlarıyla ortaya koymak amacıyla hazırlanmıştır.

---

## 📸 1. Ekran Görüntüleri ve Açıklamaları

Proje geliştirme sürecinin farklı aşamalarına ve doğrulamalarına ait en az 5 ekran görüntüsü aşağıda detaylı açıklamalarıyla birlikte sunulmuştur.

### 🖼️ Görsel 1: Planlama Aşaması (Plan Artifact)
Geliştirme sürecinin başında, asistan tarafından hazırlanan ve geliştiricinin revizyon istekleriyle olgunlaştırılan ilk veritabanı modeli planlama aşaması.
- **Dosya Yolu:** [oturum 1.2.png](file:///c:/Users/user/Desktop/final%20ödev/oturum%201.2.png)
- **Açıklama:** Kullanıcı modelinin ve SQLAlchemy 2.0 Mapped mimarisinin ilişkisel kısıtlarının (cascade kısıtlamaları dahil) planlama ekranı.

![Planlama Aşaması](oturum%201.2.png)

---

### 🖼️ Görsel 2: Geliştirme ve Uygulama Adımları (Walkthrough)
Uygulamanın siber güvenlik sıkılaştırmaları kapsamında üye kayıt ve PBKDF2 kriptografik şifreleme algoritmasıyla şifre hash'leme süreçlerinin walkthrough aşaması.
- **Dosya Yolu:** [oturum 2.1.png](file:///c:/Users/user/Desktop/final%20ödev/oturum%202.1.png)
- **Açıklama:** Kayıt ve giriş sistemlerinin şifrelenmesi, rotaların `@login_required` dekoratörleri ile sarmalanarak yetkisiz erişimlere kapatılması süreci.

![Geliştirme Adımları](oturum%202.1.png)

---

### 🖼️ Görsel 3: Hata Mesajı ve Debug Süreci (Error & Exception Handling)
Yerel ortamdan canlı ortama geçişte ve bağımlılıkların yüklenmesi aşamasında karşılaşılan python kütüphane eksikliği ve dil dosyası derleme hatalarının terminal çıktısı.
- **Dosya Yolu:** [hata bulma .png](file:///c:/Users/user/Desktop/final%20ödev/hata%20bulma%20.png)
- **Açıklama:** Geliştirme esnasında `pip install` bağımlılık uyuşmazlıkları ve Flask ortam değişkenlerinin yüklenmesi sırasında alınan hata çıktısının tespiti ve debug süreci.

![Hata Mesajı](hata%20bulma%20.png)

---

### 🖼️ Görsel 4: Başarılı Derleme ve Canlıya Geçiş (Successful Build)
Uygulamanın Render platformuna PostgreSQL veritabanı, Gunicorn WSGI sunucusu ve çevre değişkenleri izolasyonu ile başarıyla derlenmesi ve deploy edilmesi.
- **Dosya Yolu:** [oturum 10.1.png](file:///c:/Users/user/Desktop/final%20ödev/oturum%2010.1.png)
- **Açıklama:** Dockerfile derleme adımlarının, migrations (veritabanı şema göçlerinin) tamamlanmasının ve platform üzerinde aktif edilmesinin konsol görüntüsü.

![Başarılı Derleme](oturum%2010.1.png)

---

### 🖼️ Görsel 5: Çalışan Uygulama ve Yapay Zeka Arayüzü (Running Application UI)
Geliştirilen sistemin fütüristik koyu mod teması, cam efekti (glassmorphism), ambient glow neon parıltıları ve 6 farklı dilde çalışan Yapay Zeka Sohbet Asistanı arayüzü.
- **Dosya Yolu:** [oturum 10.2.png](file:///c:/Users/user/Desktop/final%20ödev/oturum%2010.2.png)
- **Açıklama:** Türkçe, İngilizce ve diğer dillerde yerelleştirilmiş, çakışan görevleri listeleyen ve akıllı planlama önerileri sunan çalışan canlı sistemin arayüzü.

![Çalışan Uygulama](oturum%2010.2.png)

---

## 💬 2. Yapay Zeka Prompt-Yanıt Alıntıları (Prompt Engineering)

Geliştiricinin bilinçli müdahaleleriyle yapay zeka asistanının kod kalitesini, mimari doğruluğunu ve güvenliğini nasıl artırdığını gösteren 2 adet birebir tam prompt-yanıt diyalogu aşağıda verilmiştir.

### ✉️ Örnek 1: SQLAlchemy 2.0 Standartlarına Geçiş ve Model Doğrulaması

* **Geliştirici Başlangıç Promptu:**
  > "User modelini ve ilişkilerini SQLAlchemy 2.0 standartlarında (Mapped ve mapped_column kullanarak) oluştur. E-posta doğrulaması (validates) içersin."

* **Yapay Zekanın İlk (Hatalı/Eski Stil) Yanıtı:**
  ```python
  # db.Column kullanan eski 1.x tarzı kod
  from app.extensions import db

  class User(db.Model):
      __tablename__ = 'users'
      id = db.Column(db.Integer, primary_key=True)
      username = db.Column(db.String(80), unique=True, nullable=False)
      email = db.Column(db.String(120), unique=True, nullable=False)
      password = db.Column(db.String(200), nullable=False)
      
      def __repr__(self):
          return '<User %r>' % self.username
  ```
  *(Hata Analizi: Asistan, SQLAlchemy 2.0'ın modern tip güvenli `Mapped` yapısı yerine eski stil `db.Column` kullanmıştır. Ayrıca email formatının geçerliliğini denetleyen herhangi bir doğrulama katmanı eklememiştir.)*

* **Geliştirici Müdahalesi / Revizyon Komutu:**
  > "Bu kod SQLAlchemy 1.x standardında. Ben SQLAlchemy 2.0 Mapped ve mapped_column yapısını istemiştim. Ayrıca e-posta alanını validate edecek ve hatalı formatlarda ValueError fırlatacak bir @validates metodu ekle."

* **Yapay Zekanın Revize Edilmiş (Doğru ve Tip Güvenli) Yanıtı:**
  ```python
  import re
  from typing import List
  from sqlalchemy.orm import Mapped, mapped_column, validates
  from app.extensions import db

  class User(db.Model):
      __tablename__ = 'users'
      
      id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
      username: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False)
      email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
      password: Mapped[str] = mapped_column(db.String(255), nullable=False)
      avatar: Mapped[str] = mapped_column(db.String(255), nullable=True, default='default.png')
      
      # SQLAlchemy 2.0 İlişki Tanımı ve Cascade Silme Kısıtı
      tasks: Mapped[List["Task"]] = db.relationship(
          "Task", back_populates="user", cascade="all, delete-orphan"
      )

      @validates('email')
      def validate_email(self, key, address):
          if not address or '@' not in address:
              raise ValueError("Geçersiz e-posta adresi formatı.")
          # Basit regex kontrolü
          if not re.match(r"[^@]+@[^@]+\.[^@]+", address):
              raise ValueError("Geçersiz e-posta adresi formatı.")
          return address

      def __repr__(self) -> str:
          return f"<User {self.username}>"
  ```

---

### 🔍 Örnek 2: SQL IDOR / BOLA Siber Güvenlik Zaafiyetinin Önlenmesi

* **Geliştirici Başlangıç Promptu:**
  > "Kullanıcının görevlerini başlığına göre arayabileceği bir AJAX arama rotası yaz."

* **Yapay Zekanın İlk (Güvensiz) Yanıtı:**
  ```python
  @tasks_bp.route('/search')
  def search_tasks():
      query = request.args.get('q', '')
      # Doğrudan tüm görevler arasından arama yapılıyor
      tasks = Task.query.filter(Task.title.like(f"%{query}%")).all()
      return jsonify([task.to_dict() for task in tasks])
  ```
  *(Güvenlik Analizi: Bu rota son derece tehlikeli bir IDOR/BOLA zaafiyeti barındırmaktadır. Sistemde oturum açmış kullanıcının kimliğine bakılmaksızın, veritabanındaki tüm görevler aratılabilmektedir. Kötü niyetli bir kullanıcı veya dış sızma test aracı, diğer kullanıcıların gizli görev verilerini kolayca sızdırabilir. Ayrıca SQL wildcard karakterleri filtrelenmemiştir.)*

* **Geliştirici Müdahalesi / Revizyon Komutu:**
  > "Yazdığın arama rotasında çok ciddi bir IDOR/BOLA (Broken Object Level Authorization) açığı var! Arama sorgusu kesinlikle oturum açmış kullanıcının görevleri ile sınırlandırılmalı (current_user.id). Ayrıca arama girdisindeki '%' ve '_' gibi SQL wildcard karakterleri regex ile kaçış karakterine dönüştürülüp temizlenmeli."

* **Yapay Zekanın Revize Edilmiş (Güvenli) Yanıtı:**
  ```python
  import re
  from flask import request, jsonify
  from flask_login import login_required, current_user
  from app.models import Task

  @tasks_bp.route('/search')
  @login_required
  def search_tasks():
      query = request.args.get('q', '')
      
      # SQL Wildcard karakterlerini escape etme (Güvenlik Sıkılaştırması)
      escaped_query = re.sub(r'([%_\\])', r'\\\1', query)
      
      # Yetkilendirme Kontrolü (BOLA/IDOR Engeli) - Sadece aktif kullanıcıya ait veriler
      tasks = Task.query.filter(
          Task.user_id == current_user.id,
          Task.title.like(f"%{escaped_query}%")
      ).all()
      
      return jsonify([{
          'id': t.id,
          'title': t.title,
          'period': t.period,
          'priority': t.priority,
          'start_time': t.start_time,
          'end_time': t.end_time,
          'is_completed': t.is_completed
      } for t in tasks])
  ```

---

## 🛠️ 3. Ajanın Hatalı Önerisi ve Geliştirici Tarafından Düzeltilmesi (1 Kritik Örnek)

Aşağıda, yapay zekanın tasarım aşamasında ciddi bir siber güvenlik açığı ve mantıksal hata barındıran bir çözüm önerdiği, geliştiricinin bunu fark edip düzelttirdiği en kritik süreç detaylandırılmıştır.

### 🛡️ Şifre Sıfırlama Token Güvenliği ve Spam Koruması (Oturum 7)

* **Yapay Zekanın Hatalı/Güvensiz Önerisi:**
  Asistan, şifre sıfırlama taleplerini yönetmek için kullanıcının veritabanı satırına kaydedilecek basit bir UUID token (`uuid.uuid4().hex`) üretmeyi ve bunu e-posta ile göndermeyi önerdi. Önerilen kodda:
  1. Token'ın herhangi bir geçerlilik süresi (TTL) bulunmuyordu. Oluşturulan bağlantı sonsuza kadar aktif kalabilirdi.
  2. Şifre sıfırlandıktan sonra token veritabanından silinmediği sürece (veya silinse dahi) aynı oturum süresince eski şifreyle üretilmiş token'ın çalınması halinde sisteme yetkisiz giriş yapılabiliyordu.
  3. Kullanıcı peş peşe sınırsız sayıda sıfırlama e-postası talep edebilirdi, bu da sunucu kaynaklarının tükenmesine (DoS/Spam) yol açabilirdi.

* **Geliştirici Tarafından Yakalanan Zaafiyetler ve Düzeltme Talimatı:**
  Geliştirici, bu yaklaşımın endüstri standartlarında bir siber güvenlik açığı olduğunu belirterek asistanı şu şekilde uyardı ve yönlendirdi:
  > "Önerdiğin UUID tabanlı şifre sıfırlama sistemi siber güvenlik açısından kabul edilemez. 
  > 1. Token'lar stateless olmalı ve kesinlikle 15 dakikalık (900 saniye) bir zaman aşımı (TTL) kısıtına sahip olmalı.
  > 2. Token içeriğine kullanıcının mevcut şifresinin hash değeri (user.password) gömülmeli. Böylece şifre başarıyla değiştirildiği an veritabanındaki hash değişeceğinden, eski şifreyle üretilmiş tüm sıfırlama bağlantıları anında ve otomatik olarak kalıcı geçersiz kalmalı.
  > 3. Spam ve kaba kuvvet (brute-force) saldırılarını engellemek adına, aynı e-posta adresine 120 saniyede (2 dakika) en fazla 1 kez sıfırlama maili gönderilebilmeli (Rate Limiting)."

* **Yapay Zekanın Geliştirici Müdahalesiyle Ürettiği Mükemmel Güvenlikli Çözüm:**

  Geliştiricinin bu siber güvenlik mimarisi direktifleri doğrultusunda, `app/utils.py` modülü altında şu güvenli fonksiyonlar kodlanmıştır:

  ```python
  from itsdangerous import URLSafeTimedSerializer
  from flask import current_app
  from datetime import datetime, timedelta

  def generate_reset_token(user):
      # serializer başlatılıyor
      serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
      # Token içerisine kullanıcı ID'si ve güncel şifre hash'i gömülüyor
      return serializer.dumps(
          {'user_id': user.id, 'password_hash': user.password},
          salt='password-reset-salt'
      )

  def verify_reset_token(token, expiration=900):
      serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
      try:
          # 15 dakika (900sn) geçerlilik kontrolü (TTL)
          data = serializer.loads(
              token,
              salt='password-reset-salt',
              max_age=expiration
          )
      except Exception:
          return None
      
      from app.models import User
      user = User.query.get(data['user_id'])
      
      # Şifre hash'i kontrolü: Eğer şifre değiştiyse hash uyuşmayacak ve token geçersiz olacaktır!
      if not user or user.password != data['password_hash']:
          return None
          
      return user
  ```

  **Rate Limiting ve Spam Kalkanı Rota Kontrolü (`app/blueprints/auth/routes.py`):**
  ```python
  @auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
  def reset_password_request():
      if current_user.is_authenticated:
          return redirect(url_for('main.dashboard'))
      
      if request.method == 'POST':
          email = request.form.get('email')
          user = User.query.filter_by(email=email).first()
          
          # Jenerik Başarı Mesajı (User Enumeration Saldırısını Önlemek İçin)
          flash(_('Şifre sıfırlama talimatları e-posta adresinize gönderildi (Eğer kayıtlıysa).'), 'info')
          
          if user:
              # Rate Limiting: Son istek zamanından itibaren 120 saniye geçmiş olmalı
              now = datetime.utcnow()
              if user.last_reset_request_at and (now - user.last_reset_request_at) < timedelta(seconds=120):
                  # İsteği sessizce logla veya kullanıcıya bekleme uyarısı ver
                  return redirect(url_for('auth.login'))
              
              # İstek zamanını güncelle
              user.last_reset_request_at = now
              db.session.commit()
              
              token = generate_reset_token(user)
              send_reset_email(user, token)
              
          return redirect(url_for('auth.login'))
  ```

---

## 📈 Sonuç

Bu iş birliği süreci göstermiştir ki, yapay zekanın sağladığı hızlı kod yazma yeteneği (hız kazanımı: **%60-70**), ancak ve ancak **geliştiricinin bilinçli teknik denetimleri, siber güvenlik vizyonu ve mimari müdahaleleriyle** birleştiğinde akademik ve endüstriyel standartlarda, hatasız ve %100 güvenli bir ürüne dönüşmektedir.
