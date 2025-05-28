# MatchOverflow 💕

A modern student matching platform that uses AI to help students find study buddies or dates based on compatibility.

## Features

- 🎯 AI-powered matching using OpenAI's GPT-3.5
- 👤 Profile creation with interests and preferences
- 💬 Detailed match preferences for better compatibility
- 📸 Profile picture uploads
- 🔍 Smart matching algorithm with 80%+ compatibility threshold
- 💕 Mutual match notifications
- 📱 Mobile-responsive design

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite (easily switchable to PostgreSQL)
- **Authentication**: JWT tokens
- **AI**: OpenAI API for compatibility analysis
- **Frontend**: Vanilla JavaScript with modern CSS

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd matchoverflow
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 5. Run the application
```bash
uvicorn app.main:app --reload
```

The app will be available at `http://localhost:8000`

## Deployment to Digital Ocean

### 1. Create a Droplet
- Choose Ubuntu 22.04 LTS
- Select appropriate size (Basic plan is fine)
- Add SSH keys

### 2. Initial Server Setup
```bash
ssh root@your-server-ip
apt update && apt upgrade -y
apt install python3-pip python3-venv nginx -y
```

### 3. Clone and Setup Application
```bash
cd /var/www
git clone <your-repo-url>
cd matchoverflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Create systemd service
Create `/etc/systemd/system/matchoverflow.service`:
```ini
[Unit]
Description=MatchOverflow FastAPI app
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/matchoverflow
Environment="PATH=/var/www/matchoverflow/venv/bin"
ExecStart=/var/www/matchoverflow/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

### 5. Configure Nginx
Create `/etc/nginx/sites-available/matchoverflow`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. Enable and start services
```bash
ln -s /etc/nginx/sites-available/matchoverflow /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx
systemctl enable matchoverflow
systemctl start matchoverflow
```

## Environment Variables

- `SECRET_KEY`: JWT secret key for authentication
- `OPENAI_API_KEY`: OpenAI API key for AI matching (optional, falls back to basic algorithm)

## Database

The app uses SQLite by default. To switch to PostgreSQL for production:

1. Install PostgreSQL driver: `pip install psycopg2-binary`
2. Update `DATABASE_URL` in your `.env` file
3. Update `app/models/database.py` to use PostgreSQL URL

## API Documentation

Once running, visit:
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

MIT License 