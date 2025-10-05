CREATE TABLE IF NOT EXISTS athletes (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(100),
  gender VARCHAR(10),
  birth_date DATE,
  weight_kg DECIMAL(5,2),
  ftp_watts INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rides (
  id SERIAL PRIMARY KEY,
  athlete_id INTEGER REFERENCES athletes(id) ON DELETE CASCADE,
  ride_date TIMESTAMP NOT NULL,
  distance_km DECIMAL(6,2),
  duration_min INTEGER,
  avg_power_watts INTEGER,
  avg_heart_rate INTEGER,
  tss DECIMAL(5,2),
  source VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_feedback (
  id SERIAL PRIMARY KEY,
  ride_id INTEGER REFERENCES rides(id) ON DELETE CASCADE,
  advice TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
