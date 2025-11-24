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
  INDEX idx_type_date (data_type, trade_date),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify table creation
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'price_data' AND TABLE_SCHEMA = DATABASE();
