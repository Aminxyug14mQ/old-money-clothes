document.addEventListener('DOMContentLoaded', function() {
    // إضافة تأكيد للطلب عبر واتساب
    const whatsappButtons = document.querySelectorAll('a[href*="wa.me"]');
    whatsappButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('سيتم نقلک إلى واتساب لإکمال الطلب. هل تريد المتابعة؟')) {
                e.preventDefault();
            }
        });
    });
    
    // تأثيرات للصور
    const productImages = document.querySelectorAll('.product-image img');
    productImages.forEach(img => {
        img.addEventListener('mouseenter', () => {
            img.style.transform = 'scale(1.05)';
            img.style.transition = 'transform 0.3s ease';
        });
        
        img.addEventListener('mouseleave', () => {
            img.style.transform = 'scale(1)';
        });
    });
});
