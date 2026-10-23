# AWS Frontend Deployment Guide (React + Vite)

This guide documents deploying the production-built React frontend using **AWS S3 + CloudFront (CDN)** or **Vercel / Netlify**.

---

## Option 1: AWS S3 + CloudFront CDN (Global High Availability & Free SSL)

### Step 1: Build Production Assets
In your local terminal:
```bash
cd frontend
# Set production backend URL
$env:VITE_API_BASE_URL="https://api.yourdomain.com"
npm run build
```
This generates the optimized bundle in `frontend/dist/`.

### Step 2: Create Amazon S3 Bucket
1. Go to **Amazon S3** -> **Create bucket**.
2. **Bucket name:** `prj221-frontend-portal` (globally unique).
3. **Block Public Access settings:** Keep blocked (CloudFront will use Origin Access Control).
4. Click **Create bucket**.

### Step 3: Deploy Files to S3
```bash
aws s3 sync frontend/dist/ s3://prj221-frontend-portal/ --delete
```

### Step 4: Create CloudFront Distribution
1. Go to **CloudFront** -> **Create distribution**.
2. **Origin domain:** Select your S3 bucket `prj221-frontend-portal.s3.amazonaws.com`.
3. **Origin access:** Choose **Origin access control settings (recommended)** -> Create control setting.
4. **Viewer protocol policy:** **Redirect HTTP to HTTPS**.
5. **Allowed HTTP methods:** `GET, HEAD`.
6. Under **Custom error response**:
   * **Error code:** `403` and `404`
   * **Response code:** `200`
   * **Response page path:** `/index.html` *(Essential for React SPA routing)*.
7. Click **Create distribution**.

---

## Option 2: Deploy to Vercel / Netlify (One-Click Git Push)

1. Connect your GitHub repository to Vercel or Netlify.
2. **Root Directory:** `frontend`.
3. **Build Command:** `npm run build`.
4. **Output Directory:** `dist`.
5. **Environment Variable:**
   * `VITE_API_BASE_URL`: `https://api.yourdomain.com` (your deployed backend URL).
6. Enable automatic HTTPS and instant previews.
