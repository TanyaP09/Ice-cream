-- Users table: stores account and profile info
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  weight_kg NUMERIC(6,2),
  height_cm NUMERIC(6,2),
  age INT,
  sex TEXT,
  region TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Ice creams table: nutrition info per 100g
CREATE TABLE IF NOT EXISTS ice_creams (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  calories NUMERIC(8,2) NOT NULL,
  carbohydrates NUMERIC(8,2) NOT NULL,
  proteins NUMERIC(8,2) NOT NULL,
  fats NUMERIC(8,2) NOT NULL,
  sugar NUMERIC(8,2) NOT NULL,
  rysk INT NOT NULL
);

-- Relation table: what user ate and when
CREATE TABLE IF NOT EXISTS user_ice_creams (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ice_cream_id INT NOT NULL REFERENCES ice_creams(id) ON DELETE CASCADE,
  eaten_date DATE NOT NULL,
  amount_grams NUMERIC(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Seed data for demo
INSERT INTO ice_creams (name, calories, carbohydrates, proteins, fats, sugar, rysk)
VALUES
  ('Vanilla Classic', 200, 24, 4, 10, 18, 2),
  ('Chocolate Bomb', 230, 27, 4, 12, 22, 3),
  ('Berry Sorbet', 140, 32, 1, 0, 28, 1),
  ('Pistachio', 210, 23, 5, 11, 17, 2)
ON CONFLICT (name) DO NOTHING;
