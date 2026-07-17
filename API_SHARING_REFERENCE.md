# Adarsh Web-Share API Reference

This document describes the API endpoints exposed by the landing website to share portfolio categories, products (images/videos), and active clients with the panel subdomain application.

---

## 🔐 Authentication

All sharing endpoints are server-to-server and require token authentication.

* **Header Name**: `X-API-KEY`
* **Query Parameter Alternative**: `api_key` (e.g. `?api_key=YOUR_SECRET_KEY`)

The secret API key is configured using the environment variable `WEB_APP_API_KEY`. If not defined, it defaults to the secure fallback key.

---

## 🔗 Endpoint Details

### 1. Get Categories and Products List

Expose all active categories along with their nested active products (images and videos). Absolute media URLs are generated dynamically based on the requesting host.

* **URL**: `/api/web-share/portfolio/`
* **Method**: `GET`
* **Format**: JSON

#### Response Example (200 OK)
```json
{
  "success": true,
  "categories": [
    {
      "id": 1,
      "name": "ID Cards",
      "slug": "id-cards",
      "icon": "fas fa-id-card",
      "description": "Premium printed ID cards.",
      "is_bento": true,
      "bento_size": "large",
      "order": 0,
      "products": [
        {
          "id": 10,
          "title": "Corporate Glossy ID Card",
          "slug": "corporate-glossy-id-card",
          "description": "Standard dimensions with high gloss overlay.",
          "item_type": "image",
          "orientation": "portrait",
          "media_url": "https://www.adarshbhopal.in/media/images/Products/id_card_front.webp",
          "video_url": "",
          "video_fallback_url": "",
          "video_stream_url": "",
          "video_thumbnail_url": "https://www.adarshbhopal.in/media/images/Products/id_card_front.webp",
          "is_featured": true,
          "order": 0,
          "created_at": "2026-07-17T11:45:00.123456"
        }
      ]
    }
  ]
}
```

---

### 2. Get Client Logo List

Expose all local website client logo profiles, visibility flags, display ordering, and synced record counts.

* **URL**: `/api/web-share/clients/`
* **Method**: `GET`
* **Format**: JSON

#### Response Example (200 OK)
```json
{
  "success": true,
  "clients": [
    {
      "id": 5,
      "name": "Vibrant Public School",
      "email": "vibrant@example.com",
      "logo_url": "https://www.adarshbhopal.in/media/images/Clients/vibrant_logo.webp",
      "website_is_visible": true,
      "website_display_order": 0,
      "total_records": 1250,
      "created_at": "2026-07-17T10:30:15.000000",
      "updated_at": "2026-07-17T11:20:10.000000"
    }
  ]
}
```

---

## 🚫 Error Responses

### Unauthorized (401 Unauthorized)
Returned if the `X-API-KEY` header or `api_key` query parameter is missing, empty, or incorrect.
```json
{
  "success": false,
  "message": "Unauthorized. A valid X-API-KEY is required."
}
```

---

## 🛠️ Verification & Curl Examples

### Test via Header
```bash
curl -X GET \
  -H "X-API-KEY: adarsh_secure_fallback_key_2026_web_app" \
  https://www.adarshbhopal.in/api/web-share/portfolio/
```

### Test via Query Parameter
```bash
curl -X GET "https://www.adarshbhopal.in/api/web-share/clients/?api_key=adarsh_secure_fallback_key_2026_web_app"
```
