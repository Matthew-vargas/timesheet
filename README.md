# Timesheet Application

Multi-user timesheet application for consulting work tracking.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser to: `http://localhost:5000`

## Render Deployment

1. Push this repository to GitHub

2. Create new Web Service on Render.com

3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variable**: `SECRET_KEY` = (random string)

4. **IMPORTANT**: Add Persistent Disk
   - Go to "Disks" tab in Render dashboard
   - Mount Path: `/opt/render/project/src`
   - Size: 1GB minimum
   - This ensures data persists across deploys

5. Deploy!

## Features

- Multi-user support (Matthew/Joan)
- Create and save timesheets
- Calculate hours and amounts automatically
- Print/PDF export
- Persistent JSON database