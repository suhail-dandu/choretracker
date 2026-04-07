# 🌟 Kids Chore & Pocket Money Tracker

A full-featured Django web application that gamifies household chores for kids.
Parents assign tasks, kids complete them, points are earned, and pocket money is paid out!

---

## ✨ Features

| Feature | Description |
|---|---|
| 👨‍👩‍👧‍👦 Family System | One family per invite code, parents + kids |
| 📋 Chore Management | Create, assign, and track tasks with points |
| ✅ Approval Workflow | Kids submit → Parent approves → Points awarded |
| 💰 Points & Money | 100 pts = €1 (configurable per family) |
| 🏆 Leaderboard | Live rankings across all kids |
| 🏅 Badges | Auto-awarded for milestones |
| 💳 Pocket Money Payout | Pay out and reset points |
| 📊 History & Reports | Full audit log + CSV export |
| 📱 Mobile Responsive | Works beautifully on phones |

---

## 🏗️ Project Structure

```
choretracker/
├── choretracker/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/              # Custom User + Family + Badge models
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── context_processors.py
├── chores/                # Chore + Assignment + Transaction models
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── family/                # Family management UI
│   ├── views.py
│   └── urls.py
├── dashboard/             # Dashboard + Leaderboard
│   ├── views.py
│   └── urls.py
├── templates/             # All HTML templates
│   ├── base.html
│   ├── accounts/
│   ├── chores/
│   ├── dashboard/
│   └── family/
├── static/                # CSS, JS, images
├── requirements.txt
├── render.yaml            # Render.com deployment
└── Procfile               # Gunicorn process
```

---

## 🚀 Local Setup (Step-by-Step)

### Prerequisites
- Python 3.10+ installed
- Git installed

### Step 1 — Clone / Download
```bash
# If using git:
git clone <your-repo-url>
cd choretracker

# Or just unzip the downloaded archive and cd into it
```

### Step 2 — Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Environment Variables
```bash
# Copy the example env file
cp .env.example .env

# Edit .env — at minimum set a SECRET_KEY:
# SECRET_KEY=my-super-secret-key-change-me-123
```

> **Tip:** Generate a good secret key:
> ```python
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### Step 5 — Run Migrations
```bash
python manage.py migrate
```

### Step 6 — Create Superuser (optional, for /admin panel)
```bash
python manage.py createsuperuser
```

### Step 7 — Run Development Server
```bash
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000** 🎉

---

## 👨‍👩‍👧 How to Use the App

### First Time Setup (Parent)
1. Go to `/accounts/register/` → **Create a Family**
2. Enter family name, currency, and your parent account details
3. You'll be logged in and see your **Family Invite Code** on the dashboard

### Adding Kids
**Option A — Parent adds directly:**
- Go to **Manage → Family → Add Child**
- Enter child's name, username, choose an avatar, set a password

**Option B — Kid joins with code:**
- Kid goes to `/accounts/join/`
- Enters the **Invite Code** from the parent dashboard
- Creates their own account and picks an avatar

### Creating & Assigning Chores
1. Go to **Manage → Chores Library → New Chore**
2. Fill in title, description, points (positive = reward, negative = penalty)
3. Click **Assign** → choose the kid and due date

### The Approval Workflow
```
Parent assigns chore
       ↓
Kid sees chore on dashboard / "My Chores"
       ↓
Kid clicks "Done!" and optionally leaves a note
       ↓
Parent sees pending approval (badge on navbar)
       ↓
Parent clicks Approve ✅ or Reject ❌
       ↓
If approved: points are immediately credited to kid
```

### Paying Out Pocket Money
1. Go to kid's profile (via leaderboard or Family page)
2. Click **Pay Out** button
3. Confirm — points reset to 0, payout recorded in history

---

## 🌐 Deployment on Render.com (Free Tier)

Render offers a free PostgreSQL database + free web service tier.

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/choretracker.git
git push -u origin main
```

### Step 2 — Create a Render Account
Go to [render.com](https://render.com) and sign up with GitHub.

### Step 3 — New PostgreSQL Database
1. Click **New → PostgreSQL**
2. Name: `choretracker-db`
3. Select **Free** tier
4. Click **Create Database**
5. Copy the **Internal Database URL**

### Step 4 — New Web Service
1. Click **New → Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name:** `choretracker`
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
     ```
   - **Start Command:**
     ```
     gunicorn choretracker.wsgi:application
     ```

### Step 5 — Set Environment Variables
In the Render dashboard → Environment:

| Key | Value |
|---|---|
| `SECRET_KEY` | (click "Generate" or paste a random key) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DATABASE_URL` | (paste your PostgreSQL internal URL) |

### Step 6 — Deploy!
Click **Create Web Service**. Render will:
1. Install dependencies
2. Run `collectstatic`
3. Run `migrate`
4. Start gunicorn

Your app will be live at `https://choretracker.onrender.com` 🚀

> **Note:** Free Render services spin down after 15 minutes of inactivity and take ~30s to wake up on first request. This is normal on the free tier.

---

## 🚂 Alternative: Deploy on Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set env vars
railway variables set SECRET_KEY=your-key DEBUG=False
```

---

## 🐍 Alternative: Deploy on PythonAnywhere

1. Sign up at [pythonanywhere.com](https://pythonanywhere.com) (free tier)
2. Open a **Bash console**:
```bash
git clone https://github.com/YOUR_USERNAME/choretracker.git
cd choretracker
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```
3. Go to **Web** tab → Add a new web app → Manual configuration → Python 3.11
4. Set **WSGI file** path and **virtualenv** path
5. Add environment variables in the WSGI config file

---

## 🔧 Configuration

### Points ↔ Money Conversion
Configurable per family in **Settings**:
- Default: `100 points = €1.00`
- Change in Family Settings page or Django admin

### Adding Custom Chore Icons
Edit the `CATEGORY_CHOICES` in `chores/models.py` to add new categories with emoji icons.

### Changing Available Avatars
Edit `AVATAR_CHOICES` in `accounts/models.py` to change the emoji avatars kids can pick.

---

## 🗄️ Database Schema (Key Models)

```
Family ──────────────────────────── invite_code, currency_symbol, points_per_unit
  │
  ├── User (accounts) ─────────────── role (parent/child), avatar, total_points
  │     └── Badge ─────────────────── badge_type, awarded_at
  │
  └── Chore ───────────────────────── title, points, category, is_recurring
        └── ChoreAssignment ─────────── assigned_to, due_date, status, points_awarded
              └── PointTransaction ──── points, reason, balance_after (audit log)

PocketMoneyPayout ────────────────── kid, amount_euros, points_at_payout, month
```

---

## 🎨 UI Design

The app uses a **vibrant, gamified** design with:
- **Fredoka One** display font (playful, rounded)
- **Nunito** body font (friendly, readable)
- Purple/pink gradient primary palette
- Stat cards with gradient backgrounds
- Animated avatar circles
- Progress bars on leaderboard
- CSS-only float animations
- Bootstrap 5 grid + components
- Bootstrap Icons throughout
- Fully mobile responsive

---

## 🔒 Security Notes

Before going live, make sure:
- `DEBUG=False` in production
- `SECRET_KEY` is random and kept secret (never commit it)
- `ALLOWED_HOSTS` is set to your domain
- Use HTTPS (Render provides this automatically)
- Change any default passwords

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + Django 5.0 |
| Frontend | Bootstrap 5 + jQuery 3.7 + Bootstrap Icons |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Static Files | WhiteNoise |
| Deployment | Render / Railway / PythonAnywhere |
| Fonts | Google Fonts (Fredoka One + Nunito) |

---

## 🤝 Contributing

Feel free to fork and improve! Some ideas:
- Email notifications when chore is approved/rejected
- Weekly digest email to parents
- Mobile app (React Native / Flutter)
- Photo proof upload when completing chore
- Chore trading between siblings
- Savings goals tracker

---

Made with ❤️ for families who want to make chores fun!
