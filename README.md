# Adarsh ID Cards - Public Website & Content Platform

A high-performance, SEO-optimized public marketing website and content management platform for Adarsh ID Cards. This repository hosts the public-facing portal and the underlying content pipelines that power the Adarsh brand presence.

## Primary Focus: Public Website
This platform is designed to provide a premium, fast, and visually stunning experience for potential clients:
- **Public Marketing Website**: Professional showcase of services and capabilities.
- **Trusted Clients Showcase**: Dynamic, brand-aware display of partner logos with auto-generated theme colors.
- **Content Pipeline**: Managed workflows for portfolio items, client testimonials, and business details.
- **Media Optimization**: Automated WebP conversion, watermarking, and video compression for high-performance delivery.
- **SEO Ready**: Dedicated metadata management and sitemap generation for maximum search visibility.

## Live Domains
- **Website**: [https://adarshbhopal.in](https://adarshbhopal.in)
- **Management Panel**: [https://panel.adarshbhopal.in](https://panel.adarshbhopal.in)

## Current Version
- **v3.18.01** (Decoupled & Optimized Release)

---

## Latest Feature: Persistent Logo Theme Colors
To ensure visual stability and premium aesthetics, the platform now computes representative theme colors once during client logo upload.
- **Stable Gradients**: Removes client-side flicker by persisting primary and dark hex colors in the database.
- **Performance**: Eliminates expensive canvas extraction on every page load.
- **Logic**: Handled by `WebsiteClientLogoService` using a light image pixel sampling algorithm.

---

## Adarsh Management Panel
While this repository focuses on the public-facing website, it also hosts the **Adarsh Management Panel** — a powerful 3-tier Role-Based Access platform for internal operations.

The Panel handles:
- **Full ID Card Lifecycle**: From organization onboarding to bulk data ingestion.
- **Advanced Export Pipelines**: PDF, XLSX, DOCX, and ZIP generations.
- **Reprint Workflows**: Dedicated status-tracking for requested and confirmed reprints.
- **Mobile PWA**: Field access for operators and clients.

**Access the Panel here:** [https://panel.adarshbhopal.in](https://panel.adarshbhopal.in)

---

## Tech Stack
| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Django 5.2.12, Python 3.11+ | Core application and API |
| **Frontend** | Tailwind CSS 4.0, Alpine.js, Vanilla JS | Modern, responsive UI |
| **Media** | Pillow, ffmpeg, WebP | Image/Video optimization and watermarking |
| **Infrastructure** | Redis, Gunicorn, Nginx | Caching, task management, and production serving |

---

## Setup and Local Development

### 1) Prerequisites
- Python 3.11+
- Node.js 18+ (for asset builds)
- ffmpeg (optional, for video processing)

### 2) Installation
```powershell
# Clone and enter directory
git clone <repository-url>
cd "Adarsh Web New"

# Setup virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3) Environment Configuration
Copy `.env.example` to `.env` and configure your `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS`.

### 4) Database & Assets
```powershell
# Apply migrations
python manage.py migrate

# Build frontend assets (pre-built assets are included in static/dist)
# Only needed if making CSS/JS changes
# npm install
# npx tailwindcss -i static/css/tailwind-input.css -o static/css/tailwind.css
```

### 5) Run Server
```powershell
python manage.py runserver
```
Website: `http://127.0.0.1:8000/`
Panel: `http://127.0.0.1:8000/panel/`

---

## Operations & Maintenance
- **Version Management**: Update `VERSION.txt` for all releases.
- **Asset Builds**: Always verify `static/dist/` contains the latest minified bundles before deployment.
- **System Check**: Always run `python manage.py check --deploy` before pushing to production.

---

## License
Proprietary. All rights reserved. Unauthorized copying, distribution, or modification is strictly prohibited.
