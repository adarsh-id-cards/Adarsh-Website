# Adarsh ID Cards — Marketing & Management Ecosystem

A professional, production-grade Django ecosystem designed for ID card brand presence and website content management. This platform integrates a high-performance public website with a streamlined administration dashboard for management.

## 🚀 Version 3.19.0 — Clean Release
This release focuses on simplifying administrative tasks, consolidating dashboard access, removing unused roles (Pro/Client-impersonation), and optimization of static resource bundles.

---

## 🏗️ System Architecture & Design

### 1. High-Level Topology
The system operates on a consolidated architecture:
- **Public Surface (Website)**: SEO-optimized marketing portal for clients and prospects, accessible at the root (`/`).
- **Management Dashboard**: Secure administrative dashboard located under `/dash/` for site administrators and operators.

### 2. Service-Oriented Design (Thin Views, Heavy Services)
The codebase follows a strict "Fat Service" pattern to ensure business logic is decoupled and testable:
- **Views**: Responsible only for request validation, permission checking, and response formatting (HTML/JSON).
- **Services**: Encapsulate all database operations and complex logic (e.g., `WebsiteClientLogoService`, `ActivityService`).
- **Models**: Clean data definitions ensuring high query performance.

---

## 🎨 Website Engine & Content Pipeline

### 1. Trusted Clients System (Persistent Aesthetics)
- **Dominant Color Extraction**: samples uploaded client logos to find dominant "Primary" and "Accent" colors.
- **Color Persistence**: Stored as hex values in the database, allowing the frontend to render stable, CSS-variable-driven gradients instantly without JS flicker.
- **Auto-WebP**: All client logos are automatically converted to WebP and optimized for size.

### 2. Media Optimization Pipeline
- **Image Processing**: Automatic watermarking (tiled text/logo), progressive quality reduction, and format normalization via `Pillow`.
- **Lazy Loading**: Native lazy-loading integration to achieve high Core Web Vitals scores.

### 3. SEO Implementation
- **Dynamic Meta Tags**: Every portfolio category and item has dedicated `meta_title` and `meta_description` fields.
- **Sitemap Generator**: Automated generation of `sitemap.xml` including images and priorities.
- **Canonicalization**: Enforced canonical URLs to prevent duplicate content issues.

---

## 🔐 Security & Access Control

### 1. Simplified Access Management
The authentication system is simplified to support two roles:
- **Admin**: Full dashboard authority and configuration access.
- **Operator**: Operational access limited to website content management tasks.

### 2. Permission Gating
The `PermissionService` provides a unified API to check access without redundant role checks or impersonation capabilities, keeping permissions direct and secure.

---

## 🛠️ Infrastructure & Deployment

### 1. The Stack
- **Database**: SQLite (Development) / PostgreSQL (Production).
- **Caching**: Django default cache for page impressions and API rate limiting.
- **Static Assets**: WhiteNoise for compressed, long-lived browser caching of CSS/JS.

### 2. Frontend Asset Pipeline
- **Bundle Pipeline**: `build_bundles.py` concatenates and minifies JS/CSS into high-performance distribution files (`static/dist/`).
- **Active Bundles**:
  - `dist/js/core.min.js`: Core client utility scripts loaded on admin/dashboard pages.
  - `dist/css/core.min.css`: Shared typography and utility styles.
  - `dist/css/wa.min.css`: Dashboard components and layouts.

---

## 📂 Repository Structure
```text
├── config/             # Project configuration (settings, wsgi, root URLconf)
├── core/               # Shared services, middleware, migrations, and base models
├── website/            # Public-facing landing page logic and content models
├── manage_website/     # Administrative views for managing website content
├── accounts/           # User authentication, OTP views, and profile management
├── static/             # Static files, including /dist/ production bundles
└── templates/          # Responsive Django templates (with Tailwind/Alpine.js integration)
```

---

## 🚀 Setup & Local Development

1. **Env Setup**: Create a `.env` file from `.env.example`.
2. **Dependencies**: `pip install -r requirements.txt`.
3. **Database**: `python manage.py migrate`.
4. **Asset Build**: Compile minified distribution bundles:
   ```bash
   python build_bundles.py
   ```
5. **Run Dev Server**: `python manage.py runserver`.

---

## 📝 License
Proprietary Platform. Developed for Adarsh ID Cards.
Unauthorized distribution or modification is strictly prohibited.
