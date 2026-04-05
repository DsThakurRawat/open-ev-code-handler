# CodeLens. Deployment Guide (Production)

Follow this guide to deploy **CodeLens. v1.0.0** to the professional cloud. This configuration uses **Vercel** for the frontend, **Render** for the backend, and **Supabase/Neon** for the PostgreSQL database.

---

## 1.  Setup the Database (PostgreSQL)

Since SQLite is disk-based and will be deleted at every restart on Render/Vercel, you **must** use a managed PostgreSQL service.

1.  **Go to [Supabase](https://supabase.com)** or [Neon](https://neon.tech).
2.  **Create a new Project** called "CodeLens".
3.  **Copy your Connection String** (it should look like `postgres://user:pass@host:5432/dbname`).
4.  **Important**: Keep this URL safe—it is your `DATABASE_URL`.

---

## 2.  Setup the Backend (Render)

Render will host your FastAPI API and your Dockerized environment.

1.  **Go to [Render Dashboard](https://dashboard.render.com)**.
2.  **New -> Web Service** and connect your GitHub repository.
3.  **Configure**:
    -   **Runtime**: `Docker`.
    -   **Environment Variables**:
        -   `DATABASE_URL`: (Paste your Supabase/Neon URL here).
        -   `API_KEY_ENABLED`: `true` (highly recommended for production).
        -   `API_KEY`: A strong secret password.
        -   `APP_ENV`: `production`.
4.  **Deploy**: Render will automatically build the `Dockerfile` in the root and start the service.
5.  **Identify**: Copy your Render URL (e.g., `https://codelens-api.onrender.com`).

---

## 3.  Setup the Frontend (Vercel)

Vercel will host your React/Vite dashboard.

1.  **Go to [Vercel](https://vercel.com)**.
2.  **Import** your `dashboard` folder (or the whole repository and set the root directory to `dashboard`).
3.  **Update `vercel.json`**:
    -   Open [`dashboard/vercel.json`](file:///Users/arshverma/GitHub/open-ev-code-handler/dashboard/vercel.json).
    -   Replace `https://YOUR_BACKEND_URL.render.com` with your **real** Render URL.
4.  **Deploy**: Vercel will build the React application and provide a global dashboard link.

---

## 4.  Running Remote Evaluations

Once deployed, you can run the benchmark script from your local machine (or any CI) against your **production** instance:

```bash
python scripts/evaluate.py --url https://your-render-url.com --api-key YOUR_SECRET_KEY
```

---

> [!CAUTION]
> **Database Migrations**: When you first deploy to a new PostgreSQL instance, the tables will be empty. The first request to the API will automatically trigger `create_db_and_tables()` via the lifespan hook—no manual SQL is required.

> [!TIP]
> **Vercel Rewrites**: The `vercel.json` rewrite rule is what allows the frontend to talk to the backend without CORS issues. Ensure the URL is exactly correct.
