# Exhibitor Registration Form – Kerala Healthcare Expo 2026

## What's included
- `index.html` — Full registration form (matches your screenshots exactly)
- `server.py` — Flask backend that stores all submissions in SQLite DB
- `exhibitors.db` — Created automatically on first run
- `uploads/` — Created automatically, stores uploaded files

## Requirements
- Python 3.8+
- Flask (`pip install flask`)

## Run the server

```bash
python server.py
```

Then open your browser to: **http://localhost:5000**

## Database

Data is stored in `exhibitors.db` (SQLite). You can view it with:
- [DB Browser for SQLite](https://sqlitebrowser.org/) (free GUI)
- Or run: `sqlite3 exhibitors.db "SELECT * FROM exhibitors;"`

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Show the registration form |
| POST | `/submit` | Submit form data → saved to DB |
| GET | `/registrations` | View all registrations as JSON |

## Form Sections
1. Company Information (Name, Brand, Website, Industry, Year Established)
2. Company Description
3. Contact Person Details (Name, Email, Phone, WhatsApp, Country, City)
4. Exhibition Participation Details
5. Booth Requirements (Type, Size, Staff, Power, Internet)
6. Marketing & Promotion (Sponsorship, Speaking, Product Launch)
7. Documents Upload (Logo, Product Images, Brochure, Business Certificate)
8. Additional Information (Special Requirements)
9. Agreement Section (Terms & Conditions, Marketing Consent)
