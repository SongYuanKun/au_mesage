-- Admin: data source config, config history, audit log
-- Run after scripts/init.sql

CREATE TABLE IF NOT EXISTS data_source_config (
  source_id VARCHAR(30) PRIMARY KEY,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  priority INT NOT NULL DEFAULT 100,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  updated_by VARCHAR(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS data_source_config_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_id VARCHAR(30) NOT NULL,
  enabled TINYINT(1) NOT NULL,
  priority INT NOT NULL,
  changed_by VARCHAR(128) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_source_created (source_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  actor VARCHAR(128) NOT NULL,
  action VARCHAR(64) NOT NULL,
  target VARCHAR(128) DEFAULT NULL,
  before_value JSON DEFAULT NULL,
  after_value JSON DEFAULT NULL,
  ip VARCHAR(45) DEFAULT NULL,
  user_agent VARCHAR(512) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_created (created_at DESC),
  INDEX idx_action_created (action, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO data_source_config (source_id, enabled, priority, updated_by) VALUES
  ('gold_api', 1, 10, 'system'),
  ('fawazahmed0', 1, 20, 'system'),
  ('exchange_rate', 1, 30, 'system'),
  ('playwright', 1, 40, 'system');
