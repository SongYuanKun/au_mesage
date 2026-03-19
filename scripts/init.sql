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
  source VARCHAR(30) DEFAULT 'playwright' COMMENT '数据来源: gold_api/exchange_rate/fawazahmed0/playwright',
  currency VARCHAR(10) DEFAULT 'CNY' COMMENT '计价币种: CNY/USD',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type_created (data_type, created_at DESC),
  INDEX idx_date_type_recycle (trade_date, data_type, recycle_price),
  INDEX idx_type_date_created (data_type, trade_date, created_at),
  INDEX idx_source (source, data_type, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS exchange_rate (
  id INT AUTO_INCREMENT PRIMARY KEY,
  base_currency VARCHAR(10) NOT NULL,
  target_currency VARCHAR(10) NOT NULL,
  rate DECIMAL(12, 6) NOT NULL,
  source VARCHAR(30) NOT NULL DEFAULT 'exchange_rate_api',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_pair_time (base_currency, target_currency, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS daily_ohlc (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trade_date DATE NOT NULL,
  data_type VARCHAR(50) NOT NULL,
  source VARCHAR(30) NOT NULL,
  currency VARCHAR(10) DEFAULT 'USD',
  open_price DECIMAL(12, 4),
  high_price DECIMAL(12, 4),
  low_price DECIMAL(12, 4),
  close_price DECIMAL(12, 4),
  volume DECIMAL(20, 4) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_date_type_source (trade_date, data_type, source),
  INDEX idx_type_date (data_type, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
