# AWS Backend Deployment Guide (FastAPI + ML Models)

This guide documents deploying the containerized FastAPI backend on AWS for Phase G.

---

## Option 1: AWS App Runner (Fastest & Fully Managed Serverless Container)

AWS App Runner is recommended for containerized FastAPI apps because it automatically manages load balancing, auto-scaling, TLS certificates, and health checks.

### 1. Build and Push Container to Amazon ECR
```bash
# 1. Log in to your Amazon ECR registry
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 2. Create repository
aws ecr create-repository --repository-name prj221-backend --region us-east-1

# 3. Build image
docker build -f deployment/Dockerfile.backend -t prj221-backend .

# 4. Tag and push
docker tag prj221-backend:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/prj221-backend:latest
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/prj221-backend:latest
```

### 2. Create App Runner Service
1. In the AWS App Runner console, click **Create service**.
2. **Source:** Container registry -> Amazon ECR.
3. Select your pushed image: `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/prj221-backend:latest`.
4. **Service name:** `prj221-backend-service`.
5. **Port:** `8000`.
6. **Environment Variables:**
   * `DB_HOST`: Your RDS Endpoint
   * `DB_PORT`: `5432`
   * `DB_NAME`: `prj_221`
   * `DB_USER`: `postgres`
   * `DB_PASSWORD`: `YourPassword`
   * `JWT_SECRET_KEY`: `<YourSecretKey>`
   * `FACULTY_INVITE_CODE`: `<YourInviteCode>`
7. Click **Create & deploy**.
8. App Runner will provision an HTTPS endpoint (e.g., `https://xxxxxx.us-east-1.awsapprunner.com`).

---

## Option 2: Amazon EC2 with Docker & Nginx (Traditional VM)

If deploying to an EC2 Ubuntu instance:

1. Launch `t3.medium` or `t3.large` instance (2 vCPUs, 4GB RAM recommended for scikit-learn + shap).
2. Install Docker & Docker Compose:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose git
   sudo usermod -aG docker $USER
   ```
3. Clone repository and set `.env`:
   ```bash
   git clone <YOUR_REPO_URL>
   cd PRJ_221
   cp .env.production.example .env
   # Edit .env with your RDS endpoint and credentials
   nano .env
   ```
4. Start with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```
5. Configure Certbot for free Let's Encrypt SSL/HTTPS:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d api.yourdomain.com
   ```
