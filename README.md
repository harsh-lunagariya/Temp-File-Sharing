# Temporary File Sharing Platform

A full-stack file sharing app built with Django REST Framework and React.

## Tech Stack

- Backend: Django, Django REST Framework, SQLite, django-cors-headers
- Frontend: React, Vite, Axios, TypeScript

## Features

- Upload a file and receive a unique 6-digit key
- Download a file with the key exactly once
- Expire the key immediately after a successful download
- Track uploads from the current browser session

## Local Setup

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

If needed, copy `.env.example` to `.env` and adjust `VITE_API_BASE_URL`.
