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

### Environment Settings

This project reads shared local config from the root `.env` file.

- `FRONTEND_HOST` and `FRONTEND_PORT` control Vite dev server binding
- `BACKEND_HOST` and `BACKEND_PORT` are the values to use when starting Django
- `VITE_API_BASE_URL` defaults to `/api` so one frontend tunnel can proxy to Django locally
- `DJANGO_ALLOWED_HOSTS` and `DJANGO_CORS_ALLOWED_ORIGINS` should include your ngrok domains when testing from other devices

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Ngrok Testing With One Tunnel

1. Keep `VITE_API_BASE_URL=/api` in `.env`
2. Start Django with the host and port from `.env`
3. Start Vite with `npm run dev`
4. Create one ngrok tunnel for the frontend port only
5. Put the public frontend URL into `DJANGO_CORS_ALLOWED_ORIGINS`
6. Restart Django and Vite after changing `.env`
