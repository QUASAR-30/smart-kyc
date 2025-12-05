-- ============================================
-- SmartKYC Database Schema
-- MySQL 8.0
-- ============================================

USE smartkyc_db;

-- ============================================
-- TABLE: merchants
-- ============================================
CREATE TABLE IF NOT EXISTS merchants (
    id VARCHAR(36) PRIMARY KEY,
    genuka_merchant_id VARCHAR(100) UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    business_name VARCHAR(255) NOT NULL,
    
    -- OAuth tokens
    access_token TEXT,
    token_expires_at DATETIME,
    
    -- Subscription
    subscription_tier ENUM('FREE', 'BASIC', 'PRO', 'ENTERPRISE') DEFAULT 'FREE',
    subscription_ends_at DATETIME,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_genuka_id (genuka_merchant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: trustscores
-- ============================================
CREATE TABLE IF NOT EXISTS trustscores (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL,
    
    -- Score
    trustscore INT NOT NULL,
    badge ENUM('NONE', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM') NOT NULL,
    
    -- Metrics (JSON)
    metrics JSON NOT NULL,
    
    -- Metadata
    calculation_mode ENUM('COLD_START', 'NORMAL') NOT NULL,
    valid_until DATETIME NOT NULL,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
    INDEX idx_merchant_id (merchant_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: documents
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL,
    
    -- Type
    document_type ENUM('RCCM', 'CNI', 'NIF', 'BANK_STATEMENT', 'ADDRESS_PROOF') NOT NULL,
    
    -- File
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    
    -- Verification
    verification_status ENUM('PENDING', 'VERIFIED', 'REJECTED') DEFAULT 'PENDING',
    verified_at DATETIME,
    
    -- OCR data (JSON)
    extracted_data JSON,
    
    -- Timestamps
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
    INDEX idx_merchant_id (merchant_id),
    INDEX idx_doc_type (document_type),
    UNIQUE KEY unique_merchant_doc (merchant_id, document_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: badges
-- ============================================
CREATE TABLE IF NOT EXISTS badges (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL UNIQUE,
    
    -- Badge
    badge_level ENUM('BRONZE', 'SILVER', 'GOLD', 'PLATINUM') NOT NULL,
    badge_image_path VARCHAR(500),
    
    -- QR Code
    qr_code_data TEXT NOT NULL,
    qr_code_image_path VARCHAR(500),
    verification_code VARCHAR(100) UNIQUE NOT NULL,
    
    -- Validity
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
    INDEX idx_verification_code (verification_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: verifications
-- ============================================
CREATE TABLE IF NOT EXISTS verifications (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL,
    
    -- Viewer info
    viewer_email VARCHAR(255),
    viewer_ip VARCHAR(45),
    
    -- Timestamp
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- User agent
    user_agent TEXT,
    
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
    INDEX idx_merchant_id (merchant_id),
    INDEX idx_viewed_at (viewed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: mock_genuka_data
-- ============================================
CREATE TABLE IF NOT EXISTS mock_genuka_data (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL,
    
    -- Mock data (JSON)
    orders JSON NOT NULL,
    customers JSON NOT NULL,
    products JSON NOT NULL,
    
    -- Metadata
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
    INDEX idx_merchant_id (merchant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- DONE
-- ============================================
SELECT 'SmartKYC Database Schema Created Successfully!' AS status;
