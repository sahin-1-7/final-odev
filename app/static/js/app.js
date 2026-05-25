// Zaman ve Görev Yönetimi Uygulaması - Global JS Etkileşimleri

document.addEventListener('DOMContentLoaded', function() {
    // 1. Dosya yükleme alanı (Avatar Seçimi) dosya ismi gösterme
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Dosya seçilmedi';
            const fileLabel = document.getElementById('avatar-label');
            if (fileLabel) {
                fileLabel.textContent = fileName;
            }
        });
    }

    // 2. Flash mesajlarının 5 saniye sonra otomatik kapanması
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // 3. Dil değişimini query params koruyarak gerçekleştirme yardımcı fonksiyonu
    const langLinks = document.querySelectorAll('a[href^="?lang="]');
    langLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const langVal = this.getAttribute('href').split('=')[1];
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('lang', langVal);
            window.location.href = currentUrl.toString();
        });
    });
});
