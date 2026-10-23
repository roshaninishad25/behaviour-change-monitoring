# AWS RDS PostgreSQL Setup Guide (PRJ_221)

This guide documents provisioning and connecting the managed PostgreSQL database on Amazon Web Services (AWS RDS) for Phase G.

---

## 1. Create RDS PostgreSQL Instance via AWS Console

1. **Sign in to AWS Management Console** and navigate to **Amazon RDS** -> **Databases** -> **Create database**.
2. **Database Engine:** Standard create -> **PostgreSQL**.
3. **Engine Version:** PostgreSQL 15.x or 16.x.
4. **Template:** Free Tier (or Production / Dev/Test).
5. **Settings:**
   * **DB instance identifier:** `prj221-db-instance`
   * **Master username:** `postgres`
   * **Master password:** `YourStrongSecurePasswordHere!123`
6. **Instance Configuration:**
   * **DB instance class:** `db.t3.micro` or `db.t4g.micro` (Free Tier eligible).
   * **Storage:** 20 GiB gp3 storage (with auto-scaling enabled up to 100 GiB).
7. **Connectivity:**
   * **Virtual Private Cloud (VPC):** Default VPC (or your custom application VPC).
   * **Public access:**
     * Set to **Yes** if accessing from local workstation/Vercel (requires strict Security Group IP whitelisting).
     * Set to **No** if backend is deployed in the same VPC (ECS / App Runner / EC2) — *Recommended for production*.
   * **VPC Security Group:** Create new security group: `prj221-rds-sg`.
     * **Inbound Rules:** Type: `PostgreSQL`, Port: `5432`, Source: Backend Security Group or Elastic IP.
8. **Initial Database Name:**
   * Under **Additional configuration** -> **Initial database name:** `prj_221`.
9. Click **Create database**. Provisioning takes 3–5 minutes.

---

## 2. Initialize Schema on RDS

Once the instance status turns **Available**, copy its **Endpoint** (e.g. `prj221-db-instance.xxxxxx.us-east-1.rds.amazonaws.com`).

Connect and execute the initialization script:

```bash
# Using psql:
psql -h prj221-db-instance.xxxxxx.us-east-1.rds.amazonaws.com -p 5432 -U postgres -d prj_221 -f deployment/aws/init_db.sql
```

Or run the Python seeding workflow targeting the RDS instance:
```bash
# In your .env:
DB_HOST=prj221-db-instance.xxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=prj_221
DB_USER=postgres
DB_PASSWORD=YourStrongSecurePasswordHere!123

python scripts/seed_database.py
```

---

## 3. Backup & Security Best Practices

1. **Automated Backups:** Enable automated daily snapshots with a 7-day retention period.
2. **Encryption at Rest:** Ensure AWS KMS encryption is enabled for the storage volume.
3. **SSL Enforcement:** AWS RDS PostgreSQL supports TLS connections by default (`sslmode=require`).
