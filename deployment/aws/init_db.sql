-- PRJ_221 PostgreSQL Database Initialization Schema (AWS RDS / PostgreSQL 14+)

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Student'
);

-- Index for case-insensitive email lookups during login
CREATE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email));

-- 2. Behaviour Records Table
CREATE TABLE IF NOT EXISTS behaviour_records (
    record_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    course_id VARCHAR(50) NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence >= 1 AND sequence <= 8),
    freq_course_view INTEGER NOT NULL DEFAULT 0,
    freq_forum_consume INTEGER NOT NULL DEFAULT 0,
    freq_forum_contribute INTEGER NOT NULL DEFAULT 0,
    freq_lecture_view INTEGER NOT NULL DEFAULT 0,
    regularity_course_view DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (regularity_course_view >= 0.0 AND regularity_course_view <= 1.0),
    regularity_lecture_view DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (regularity_lecture_view >= 0.0 AND regularity_lecture_view <= 1.0),
    regularity_forum_consume DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (regularity_forum_consume >= 0.0 AND regularity_forum_consume <= 1.0),
    regularity_forum_contribute DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (regularity_forum_contribute >= 0.0 AND regularity_forum_contribute <= 1.0),
    session_count INTEGER NOT NULL DEFAULT 0,
    total_duration INTEGER NOT NULL DEFAULT 0,
    active_days INTEGER NOT NULL DEFAULT 0,
    final_grade DOUBLE PRECISION,
    CONSTRAINT uq_user_sequence UNIQUE (user_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_behaviour_user_seq ON behaviour_records(user_id, sequence);

-- 3. Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    bci DOUBLE PRECISION,
    behavior_state VARCHAR(50) NOT NULL,
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_user_time ON predictions(user_id, predicted_at DESC);

-- 4. Anomalies Table
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    anomaly_flag INTEGER NOT NULL CHECK (anomaly_flag IN (-1, 1)),
    anomaly_score DOUBLE PRECISION NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomalies_user_time ON anomalies(user_id, detected_at DESC);

-- 5. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_time ON recommendations(user_id, created_at DESC);

-- 6. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    priority VARCHAR(50) NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_user_time ON alerts(user_id, created_at DESC);
