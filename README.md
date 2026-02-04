# Matrimony Matchmaking App (Flask + SQLite)

A learning/demo matrimonial matchmaking web app with:
- Email + password authentication (session-based)
- Profile form (Google Form–like)
- Secure profile image upload (JPG/JPEG/PNG)
- Match scoring (0–100) with weighted components
- Visibility gating: full profile visible only when score ≥ 90%

## Tech
- Backend: Flask
- Frontend: HTML/CSS/JS
- DB: SQLite

## Project structure
Matches the structure requested in the prompt.

## Run locally (Windows PowerShell)
From the repo root:

```powershell
cd "c:\Users\nitin\Downloads\website\matrimony_app"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Demo accounts
Seeded automatically on first run:
- `aisha@example.com`
- `rahul@example.com`
- `neha@example.com`

Password for all: `Password@123`

## Notes
- Images are stored in `static/uploads/`.
- This is a demo; for production consider:
  - CSRF protection (Flask-WTF)
  - Rate limiting
  - Stronger password policy + email verification
  - PIL-based image validation + resizing
  - Proper contact/messaging workflow
