# Forex AI Assistant

یک دستیار هوشمند برای تحلیل چارت‌های فارکس با استفاده از مدل‌های بینایی (Vision Models)

## ویژگی‌ها

- 📷 **انتخاب کادر** - با یک کلیک از هر بخش از صفحه عکس بگیرید
- 🤖 **تحلیل هوشمند** - تشخیص روند، سطوح حمایت/مقاومت، الگوهای کندلی
- 🔒 **امنیت کامل** - کلیدهای API در فضای امن ویندوز ذخیره می‌شوند
- 📡 **آنلاین/آفلاین** - پشتیبانی از مدل‌های محلی (Ollama) و ابری (Gemini, Claude, OpenAI)
- 📚 **تاریخچه** - ذخیره‌سازی خودکار تمام تحلیل‌ها
- ⚡ **هات‌کی** - Ctrl+Shift+S برای فعال‌سازی سریع

## نصب و راه‌اندازی

```bash
# ۱. کلون کردن مخزن
git clone https://github.com/masoud7777/forex-ai-assistant.git
cd forex-ai-assistant

# ۲. ایجاد محیط مجازی
python -m venv venv
venv\Scripts\activate  # در ویندوز

# ۳. نصب وابستگی‌ها
pip install -r requirements.txt

# ۴. اجرای برنامه
python -m src.main
