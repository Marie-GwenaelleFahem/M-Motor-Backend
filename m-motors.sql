CREATE TYPE order_type AS ENUM ('purchase', 'rental');
CREATE TYPE status_type AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
  id SERIAL PRIMARY KEY,
  model VARCHAR(255) NOT NULL,
  purchase_price INT DEFAULT NULL,
  rental_price INT DEFAULT NULL,
  is_sold BOOLEAN
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  vehicle_id INT NOT NULL,
  order_type order_type NOT NULL,
  status status_type DEFAULT 'pending',
  subscription BOOLEAN DEFAULT FALSE,
  options JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  start_date TIMESTAMP,
  return_date TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);
