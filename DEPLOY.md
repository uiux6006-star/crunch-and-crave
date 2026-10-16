# Crunch & Crave — PythonAnywhere par deploy

Ye guide website ko **free** mein live karti hai, is address par:
`https://AAPKA-USERNAME.pythonanywhere.com`

Neeche jahan bhi `AAPKA-USERNAME` likha hai, wahan apna PythonAnywhere username likhein.

---

## Step 1 — Code GitHub par daalein (apne computer par)

Ye kaam sirf ek dafa karna hai. Project folder mein terminal kholein:

```bash
git init
git add .
git commit -m "Crunch & Crave website"
git branch -M main
```

Phir https://github.com/new par ek naya repository banayein (naam: `crunch-and-crave`), aur GitHub jo 2 commands dikhaye wo chalayein:

```bash
git remote add origin https://github.com/AAPKA-GITHUB-NAAM/crunch-and-crave.git
git push -u origin main
```

> `.gitignore` pehle se bana hua hai, is liye `venv`, database, `.env` aur photos GitHub par **nahi** jayenge.

---

## Step 2 — PythonAnywhere account

1. https://www.pythonanywhere.com par **"Beginner" (free)** account banayein.
2. **Consoles** tab → **Bash** kholein.

---

## Step 3 — Server par code aur libraries

Bash console mein ek-ek karke chalayein:

```bash
git clone https://github.com/AAPKA-GITHUB-NAAM/crunch-and-crave.git
cd crunch-and-crave

mkvirtualenv --python=python3.13 cc-venv
pip install -r requirements.txt
```

> Django 6 ko Python 3.12 ya us se naya chahiye. Agar `python3.13` na mile to `python3.12` likhein.

---

## Step 4 — Secret settings (`.env` file)

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Upar wali command ek lambi random key print karegi. Ab file kholein:

```bash
nano .env
```

Ye 3 lines theek karein:

```
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<jo key abhi print hui wo yahan paste karein>
DJANGO_ALLOWED_HOSTS=AAPKA-USERNAME.pythonanywhere.com
```

Save karne ke liye `Ctrl+O`, phir `Enter`, phir bahar nikalne ke liye `Ctrl+X`.

> Free plan par Gmail SMTP block hota hai. Is liye email wali lines **khali chhor dein**. Orders phir bhi admin dashboard aur live alerts mein dikhenge.

---

## Step 5 — Database, CSS aur admin user

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

`migrate` poora menu (39 items, categories, promo codes) khud daal deta hai. `createsuperuser` admin ke liye apna **naya, mazboot password** maangega.

---

## Step 6 — Web app banayein

1. **Web** tab → **Add a new web app** → Next.
2. **Manual configuration** chunein (Django wala option *nahi*) → **Python 3.13** (ya jo Step 3 mein use kiya).
3. Web page par ye cheezein bharein:

| Setting | Value |
|---|---|
| **Source code** | `/home/AAPKA-USERNAME/crunch-and-crave` |
| **Virtualenv** | `/home/AAPKA-USERNAME/.virtualenvs/cc-venv` |

4. **WSGI configuration file** ke link par click karein. Us file ka **sara purana content mita kar** ye paste karein:

```python
import os
import sys

path = "/home/AAPKA-USERNAME/crunch-and-crave"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "njfastfood.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Save** karein.

5. Wapas **Web** tab mein, **Static files** section mein 2 lines add karein:

| URL | Directory |
|---|---|
| `/static/` | `/home/AAPKA-USERNAME/crunch-and-crave/staticfiles` |
| `/media/` | `/home/AAPKA-USERNAME/crunch-and-crave/media` |

6. **Security** section mein **Force HTTPS** ko **On** karein.
7. Upar hare rang ka **Reload** button dabayein.

Ab `https://AAPKA-USERNAME.pythonanywhere.com` kholein. Website live hai! 🎉
Admin panel: `https://AAPKA-USERNAME.pythonanywhere.com/admin/`

---

## Baad mein code update karna

Apne computer par kuch badlein, to:

```bash
git add .
git commit -m "Update"
git push
```

Phir PythonAnywhere ke Bash console mein:

```bash
cd ~/crunch-and-crave
workon cc-venv
git pull
python manage.py migrate
python manage.py collectstatic --noinput
```

Aakhir mein **Web** tab → **Reload** dabayein.

---

## Agar kuch na chale

| Masla | Hal |
|---|---|
| "Something went wrong" ya error page | **Web** tab → **Error log** kholein. Sab se neeche asli error likha hota hai. |
| `ImproperlyConfigured: Set DJANGO_SECRET_KEY` | `.env` file `crunch-and-crave` folder mein hai? `DJANGO_SECRET_KEY` bhara hai? |
| "Bad Request (400)" | `.env` mein `DJANGO_ALLOWED_HOSTS` bilkul aapke address jaisa hai? Shuru mein `https://` **na** likhein. |
| Page bina design ke (CSS nahi) | Step 5 ka `collectstatic` chalayein, aur Step 6.5 ki `/static/` mapping check karein. Phir **Reload**. |
| Upload ki hui photo nahi dikhti | Step 6.5 ki `/media/` mapping check karein. |

**Free plan ki zaroori baat:** har 3 mahine mein **Web** tab par **"Run until 3 months from today"** dabana parta hai, warna site band ho jati hai. PythonAnywhere iski yaad-dihani email bhejta hai.

---

## Demo patti band karna (agar kabhi asli dukaan banaye)

`.env` mein `DJANGO_DEMO_MODE=0` likhein, aur **Reload** karein.
