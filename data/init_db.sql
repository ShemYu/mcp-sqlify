-- users table
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  age INTEGER,
  country TEXT
);

-- orders table
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  amount REAL,
  order_date TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sample data for users
INSERT INTO users (name, age, country) VALUES
  ('Alice', 30, 'Taiwan'),
  ('Bob', 25, 'USA'),
  ('Charlie', 35, 'UK');

-- Sample data for orders
INSERT INTO orders (user_id, amount, order_date) VALUES
  (1, 120.5, '2025-04-01'),
  (2, 75.0, '2025-04-05'),
  (1, 200.0, '2025-04-10');
