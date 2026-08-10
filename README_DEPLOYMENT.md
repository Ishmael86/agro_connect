# Deployment Notes for AgroConnect

## Required environment variables

- `SECRET_KEY`
- `DEBUG` (set to `False` in production)
- `ALLOWED_HOSTS` (JSON array or comma-separated string)
- `DATABASE_URL` (optional; uses SQLite by default)

Example `.env` contents:

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=["yourdomain.com", "www.yourdomain.com"]
DATABASE_URL=postgres://user:password@host:port/dbname
```

## Static files

Run:

```bash
python manage.py collectstatic --noinput
```

## Heroku / container deployment

- `Procfile` is included for Heroku style deployments.
- `runtime.txt` specifies Python 3.12.5.

## Notes

- `.gitignore` now excludes `.env`, `db.sqlite3`, and `staticfiles/`
- `settings.py` loads environment variables from `.env` and honors `DEBUG`, `ALLOWED_HOSTS`, and `DATABASE_URL`.
