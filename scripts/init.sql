-- Price Data Table Initialization Script
-- Execute this SQL in your MySQL database before running the application

CREATE TABLE IF NOT EXISTS price_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trade_date DATE NOT NULL,
  trade_time TIME NOT NULL,
  data_type VARCHAR(50) NOT NULL,
  real_time_price DECIMAL(10, 4) DEFAULT 0,
  recycle_price DECIMAL(10, 4) DEFAULT 0,
  high_price DECIMAL(10, 4) DEFAULT 0,
  low_price DECIMAL(10, 4) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type_created (data_type, created_at DESC),
  INDEX idx_date_type_recycle (trade_date, data_type, recycle_price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
