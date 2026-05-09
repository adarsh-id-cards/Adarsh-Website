# Adarsh ID Cards — Advanced Marketing & Management Ecosystem

A professional, production-grade Django ecosystem designed for high-scale ID card operations and a premium public brand presence. This platform integrates a high-performance public website with a sophisticated 3-tier administrative engine.

## 🚀 Version 3.18.01 — Production Release
This release focuses on total decoupling, sidebar-centric navigation, and optimized media pipelines.

---

## 🏗️ System Architecture & Design

### 1. High-Level Topology
The system operates on a dual-surface architecture, separated by domain-level routing but sharing a unified service layer:
- **Public Surface (Website)**: SEO-optimized marketing portal for clients and prospects.
- **Operations Surface (Panel)**: Enterprise-grade management interface for admins, operators, and clients.

### 2. Request Lifecycle & Routing
A custom `SubdomainRoutingMiddleware` acts as the primary traffic controller:
1. **Domain Detection**: Intercepts every request to detect if it matches `WEBSITE_DOMAIN` or `PANEL_DOMAIN`.
2. **URLConf Switching**: Dynamically sets `request.urlconf` to either `config.urls_website` or `config.urls_panel`.
3. **Context Injection**: Injects environment-specific context (like `current_client` for scoped domains) into the request object.

### 3. Service-Oriented Design (Thin Views, Heavy Services)
The codebase follows a strict "Fat Service" pattern to ensure business logic is reusable across Desktop views, Mobile APIs, and Background tasks:
- **Views**: Responsible only for request validation, permission checking, and response formatting (HTML/JSON).
- **Services**: Encapsulate all database operations, external API calls, and complex logic (e.g., `WebsiteClientLogoService`, `ActivityService`).
- **Models**: Clean data definitions with minimal logic, ensuring high query performance.

---

## 🎨 Website Engine & Content Pipeline

### 1. Trusted Clients System (Persistent Aesthetics)
Replaces legacy runtime color extraction with a high-performance persistence model:
- **Sampling Algorithm**: When a client logo is uploaded, the `WebsiteClientLogoService` samples the image to find the dominant "Primary" and "Accent" colors.
- **Persistence**: These colors are stored as hex values in the database, allowing the frontend to render stable, CSS-variable-driven gradients instantly without JS flicker.
- **Auto-WebP**: All client logos are automatically converted to WebP and optimized for size.

### 2. Media Optimization Pipeline
The platform includes a dedicated pipeline for handling heavy marketing assets:
- **Image Processing**: Automatic watermarking (tiled text/logo), progressive quality reduction, and format normalization via `Pillow`.
- **Video Compression (FFmpeg)**: Integrated support for compressing high-resolution reels into H.264/AAC MP4s, ensuring smooth playback on mobile devices.
- **Lazy Loading & Performance**: Built-in support for responsive images and lazy-loading attributes to achieve high Core Web Vitals scores.

### 3. SEO Implementation
- **Dynamic Meta Tags**: Every portfolio category and item has dedicated `meta_title` and `meta_description` fields.
- **Sitemap Generator**: Automated generation of `sitemap.xml` including images and priorities.
- **Canonicalization**: Middleware-level enforcement of canonical URLs to prevent duplicate content issues.

---

## 🔐 Security & Access Control

### 1. 3-Tier Role-Based Authentication (RBA)
The platform uses a standalone authentication system decoupled from legacy dependencies:
- **Admin**: Full system authority and configuration access.
- **Pro User**: Owner-grade access with advanced dashboard metrics and impersonation capabilities.
- **Operator**: Task-focused access limited to specific operational features (e.g., "Manage Clients", "Verify Cards").

### 2. Permission Service
The `PermissionService` provides a unified API to check access:
- **Double-Gating**: Client staff permissions are always gated by the status of the parent Client account.
- **Impersonation Guard**: Strict checks to ensure Pro users can only impersonate eligible clients.

---

## 🛠️ Infrastructure & Deployment

### 1. The Stack
- **Database**: PostgreSQL (Production) / SQLite (Development).
- **Caching & Rate Limiting**: Redis-backed cache for OTPs, session management, and API throttling.
- **Background Tasks**: Thread-pooled execution for heavy exports (PDF/XLSX) and bulk uploads.
- **Static Assets**: WhiteNoise for compressed, long-lived browser caching of CSS/JS.

### 2. Frontend Asset Pipeline
- **Tailwind 4.0 CLI**: Uses the latest standalone JIT engine for ultra-fast CSS generation.
- **Bundle Pipeline**: `build_bundles.py` concatenates and minifies module-based JS/CSS into high-performance distribution files (`static/dist/`).
- **Standardized UI**: Global services for Modals (`ModalManager`), Toasts, and Dropdowns ensure UI consistency.

---

## 📂 Repository Structure
```text
├── config/             # Core settings and URL topologies
├── core/               # Shared services, middleware, and base models
├── website/            # Public site logic and marketing content pipeline
├── manage_website/     # Administrative interface for the public website
├── accounts/           # Auth system, OTP, and profile management
├── static/             # Assets, including the /dist/ production bundles
├── templates/          # Responsive Django templates (Alpine.js integrated)
└── VERSION.txt         # Current release version (3.18.01)
```

---

## 🚀 Setup & Deployment

### Local Development
1. **Env Setup**: Create a `.env` file from `.env.example`.
2. **Dependencies**: `pip install -r requirements.txt`.
3. **Database**: `python manage.py migrate`.
4. **Asset Build**: If modifying styles, use the Tailwind CLI or the provided `build_bundles.py` script.
5. **Run**: `python manage.py runserver`.

### Production Deployment
1. **Check**: `python manage.py check --deploy`.
2. **Collect**: `python manage.py collectstatic --noinput`.
3. **Gunicorn**: Deploy via Gunicorn using the provided `gunicorn_example.service` configuration.
4. **SSL**: Ensure `WEBSITE_DOMAIN` and `PANEL_DOMAIN` are correctly set in `.env`.

---

## 📝 License & Contact
Proprietary Platform. Developed for Adarsh ID Cards.
Unauthorized distribution or modification is strictly prohibited.
