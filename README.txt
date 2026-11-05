# متجر العطّار — Python + Flask

## التشغيل على Windows
1. ثبّت Python من https://www.python.org/downloads/ مع تفعيل Add Python to PATH.
2. فك ضغط ملف المشروع.
3. افتح CMD داخل مجلد `alattar` (من شريط عنوان المجلد اكتب `cmd` ثم Enter).
4. نفّذ:
   ```bat
   py -m venv venv
   venv\Scripts\activate
   py -m pip install flask
   py app.py
   ```
5. افتح `http://127.0.0.1:5000` في المتصفح.

## الصور
ضع صورك الفعلية في `static/images/` بالأسماء التالية، أو عدّل اسم الصورة في `app.py`.
الأسماء: beans.jpg, lentils.jpg, freekeh.jpg, chickpeas.jpg, bulgur.jpg,
wheat_flour.jpg, wheat.jpg, oats.jpg, starch.jpg, baking_soda.jpg, zaatar.jpg,
zaatar_leaves.jpg, cinnamon.jpg, coffee.jpg, matcha.jpg.
إذا لم تضف الصور، سيظهر بديل زخرفي مؤقت بدل الصورة.

## تخصيص مهم قبل النشر
- تحقق من `WHATSAPP_NUMBER` في `app.py`؛ يجب أن يكون الرقم بصيغة دولية بدون +.
- الأسعار أُدرجت وفق قائمة الأسعار المتوفرة عند إنشاء المشروع، راجعها قبل البيع.
- الموقع نموذج أولي. قبل نشره علنًا، غيّر `SECRET_KEY` إلى قيمة عشوائية آمنة، عطّل debug، واستخدم استضافة HTTPS.
- لا يوجد دفع إلكتروني أو لوحة تحكم لإدارة المنتجات في هذا الإصدار.
