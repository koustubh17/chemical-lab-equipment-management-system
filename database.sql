-- ====================================================================
-- Chemistry Lab Equipment & Chemical Management System
-- Institution: Vivekanand College, Kolhapur
-- Database Schema: backend/database.sql
-- Description: Standard SQL DDL for database setup with separate
--              Equipment and Chemicals tables.
-- ====================================================================

-- 1. Admin Table
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    role VARCHAR(50) DEFAULT 'Administrator'
);

-- 2. Users Table (Students, Teachers, Lab Assistants)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'Student', 'Teacher', 'Lab Assistant'
    department VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- 4. Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(150) NOT NULL,
    address TEXT NOT NULL
);

-- 5. Equipment Table (Physical Apparatus, Instruments, Glassware, Safety Gear)
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    category_id INTEGER NOT NULL,
    supplier_id INTEGER,
    total_qty REAL NOT NULL DEFAULT 1.0,
    available_qty REAL NOT NULL DEFAULT 1.0,
    damaged_qty REAL NOT NULL DEFAULT 0.0,
    unit_type VARCHAR(20) DEFAULT 'Units', -- 'Units', 'Pieces', 'Sets', 'Boxes'
    unit_price REAL DEFAULT 0.0,
    location VARCHAR(150) NOT NULL,
    status VARCHAR(50) DEFAULT 'Available', -- 'Available', 'In Use', 'Maintenance', 'Damaged'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
);

-- 6. Chemicals Table (Chemical Reagents, Solvents, Acids, Bases, Indicators)
CREATE TABLE IF NOT EXISTS chemicals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chemical_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    formula VARCHAR(100),                      -- Chemical formula e.g., HCl, C2H5OH, NaOH
    cas_number VARCHAR(50),                   -- CAS registry number e.g., 7647-01-0
    category_id INTEGER NOT NULL,
    supplier_id INTEGER,
    total_qty REAL NOT NULL DEFAULT 0.0,
    available_qty REAL NOT NULL DEFAULT 0.0,
    unit_type VARCHAR(20) DEFAULT 'mL',       -- 'mL', 'Liters', 'Grams', 'Kg', 'Bottles'
    unit_price REAL DEFAULT 0.0,
    purity_grade VARCHAR(50) DEFAULT 'AR',    -- 'AR Grade', 'LR Grade', 'HPLC Grade', 'Technical'
    hazard_class VARCHAR(50) DEFAULT 'None',  -- 'Corrosive', 'Flammable', 'Toxic', 'Oxidizer', 'None'
    expiry_date VARCHAR(50),
    location VARCHAR(150) NOT NULL,
    status VARCHAR(50) DEFAULT 'Available',   -- 'Available', 'Low Stock', 'Out of Stock', 'Expired'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
);

-- 7. Equipment Issue Table
CREATE TABLE IF NOT EXISTS equipment_issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_code VARCHAR(50) UNIQUE NOT NULL,
    equipment_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    issue_qty REAL DEFAULT 1.0,
    issue_date VARCHAR(50) NOT NULL,
    expected_return_date VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Issued', -- 'Issued', 'Returned', 'Overdue'
    notes TEXT,
    issued_by VARCHAR(150) NOT NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- 8. Chemical Issue Table
CREATE TABLE IF NOT EXISTS chemical_issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_code VARCHAR(50) UNIQUE NOT NULL,
    chemical_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    issue_qty REAL DEFAULT 1.0,
    issue_unit VARCHAR(20) DEFAULT 'mL',
    issue_date VARCHAR(50) NOT NULL,
    notes TEXT,
    issued_by VARCHAR(150) NOT NULL,
    FOREIGN KEY (chemical_id) REFERENCES chemicals (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- 9. Equipment Return Table (with Online QR & Offline Cash fine payment collection)
CREATE TABLE IF NOT EXISTS equipment_return (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER UNIQUE NOT NULL,
    actual_return_date VARCHAR(50) NOT NULL,
    fine_amount REAL DEFAULT 0.0,
    payment_mode VARCHAR(50) DEFAULT 'Offline Cash', -- 'Offline Cash', 'Online UPI QR'
    payment_txn_id VARCHAR(100) DEFAULT 'N/A',
    payment_status VARCHAR(50) DEFAULT 'Paid', -- 'Paid', 'Pending'
    damage_status VARCHAR(50) DEFAULT 'No Damage', -- 'No Damage', 'Minor Damage', 'Broken'
    remarks TEXT,
    received_by VARCHAR(150) NOT NULL,
    FOREIGN KEY (issue_id) REFERENCES equipment_issue (id)
);

-- 10. Maintenance Table
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    service_date VARCHAR(50) NOT NULL,
    completion_date VARCHAR(50),
    issue_description TEXT NOT NULL,
    cost REAL DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'Under Repair',
    technician VARCHAR(150) NOT NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment (id)
);

-- 11. Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- Initial Seed Data
-- ====================================================================

-- Default Administrator
INSERT OR IGNORE INTO admin (username, password, name, email, role)
VALUES ('admin', 'admin123', 'Vivekanand Admin', 'admin@vivekanandcollege.ac.in', 'Administrator');

-- Default Users (Assistants, Teachers, Students)
INSERT OR IGNORE INTO users (user_code, name, email, phone, role, department, password) VALUES
('LAB-101', 'Prof. Suresh Patil', 'suresh.patil@vivekanandcollege.ac.in', '9822012345', 'Lab Assistant', 'Chemistry Dept', 'tech123'),
('TCH-201', 'Dr. Sunita Deshmukh', 'sunita.deshmukh@vivekanandcollege.ac.in', '9822054321', 'Teacher', 'Organic Chemistry', 'teacher123'),
('STU-301', 'Rohan Kulkarni', 'rohan.kulkarni@student.ac.in', '9822099999', 'Student', 'B.Sc Chemistry 3rd Year', 'student123'),
('STU-302', 'Neha Jadhav', 'neha.jadhav@student.ac.in', '9822088888', 'Student', 'B.Sc Chemistry 2nd Year', 'student123');

-- Categories
INSERT OR IGNORE INTO categories (id, name, description) VALUES
(1, 'Glassware', 'Beakers, flasks, burettes, pipettes, and test tubes.'),
(2, 'Chemicals & Reagents', 'Solvents, acids, bases, indicators, and organic reagents.'),
(3, 'Instruments', 'Spectrophotometers, centrifuges, pH meters, balances, and refractometers.'),
(4, 'Safety Equipment', 'Fume hoods, eyewash kits, fire extinguishers, and safety goggles.');

-- Suppliers
INSERT OR IGNORE INTO suppliers (id, name, contact_person, phone, email, address) VALUES
(1, 'Borosil Scientific Ltd', 'Vikram Malhotra', '022-24930123', 'sales@borosil.com', 'Mumbai, Maharashtra'),
(2, 'Thermo Fisher Scientific India', 'Sanjay Kumar', '080-67123000', 'info.india@thermofisher.com', 'Bengaluru, Karnataka'),
(3, 'Kolhapur Chemical Suppliers', 'Milind Kulkarni', '0231-2654321', 'orders@kolhapurchem.com', 'Kolhapur, Maharashtra');

-- Equipment Table Seed Data (Physical Lab Items)
INSERT OR IGNORE INTO equipment (equipment_code, name, category_id, supplier_id, total_qty, available_qty, damaged_qty, unit_type, unit_price, location, status) VALUES
('EQ-GLA-001', 'Pyrex Volumetric Flask 1000mL', 1, 1, 25.0, 20.0, 1.0, 'Units', 450.0, 'Glassware Cabinet A-02', 'Available'),
('EQ-INS-002', 'Digital Analytical Balance (0.1mg)', 3, 2, 4.0, 3.0, 0.0, 'Units', 35000.0, 'Instrument Room Bench 1', 'Available'),
('EQ-GLA-003', 'Burette 50mL Class A Precision', 1, 1, 30.0, 28.0, 2.0, 'Units', 320.0, 'Glassware Drawer G-01', 'Available'),
('EQ-SAF-004', 'Safety Eyewash Station & Fume Hood', 4, 2, 2.0, 2.0, 0.0, 'Units', 125000.0, 'Organic Lab Fume Zone 1', 'Available');

-- Chemicals Table Seed Data (Reagents, Solvents, Acids, Bases, Indicators)
INSERT OR IGNORE INTO chemicals (chemical_code, name, formula, cas_number, category_id, supplier_id, total_qty, available_qty, unit_type, unit_price, purity_grade, hazard_class, expiry_date, location, status) VALUES
('CHM-ACD-001', 'Hydrochloric Acid 37% (Concentrated)', 'HCl', '7647-01-0', 2, 3, 5000.0, 4200.0, 'mL', 1.5, 'AR Grade', 'Corrosive', '2028-12-31', 'Acid Storage Safe', 'Available'),
('CHM-SOL-002', 'Ethanol 99.9% Absolute Alcohol', 'C2H5OH', '64-17-5', 2, 3, 10.0, 7.5, 'Liters', 650.0, 'AR Grade', 'Flammable', '2027-06-30', 'Solvent Cabinet B-01', 'Available'),
('CHM-BAS-003', 'Sodium Hydroxide Pellets (NaOH)', 'NaOH', '1310-73-2', 2, 3, 2500.0, 1800.0, 'Grams', 0.8, 'LR Grade', 'Corrosive', '2029-01-15', 'Chemical Shelf C-04', 'Available'),
('CHM-IND-004', 'Phenolphthalein Indicator Solution 1%', 'C20H14O4', '77-09-8', 2, 3, 500.0, 450.0, 'mL', 2.5, 'AR Grade', 'None', '2028-05-20', 'Indicator Rack I-01', 'Available');

-- Equipment Issues Seed Data
INSERT OR IGNORE INTO equipment_issue (issue_code, equipment_id, user_id, issue_qty, issue_date, expected_return_date, status, notes, issued_by) VALUES
('ISS-1001', 1, 3, 1.0, '2026-07-20', '2026-07-27', 'Issued', 'Titration experiment lab session', 'Prof. Suresh Patil'),
('ISS-1002', 2, 2, 1.0, '2026-07-25', '2026-08-01', 'Issued', 'UV Spectroscopy practical', 'Prof. Suresh Patil');

-- Chemical Issues Seed Data
INSERT OR IGNORE INTO chemical_issue (issue_code, chemical_id, user_id, issue_qty, issue_unit, issue_date, notes, issued_by) VALUES
('CHM-ISS-101', 1, 3, 250.0, 'mL', '2026-07-20', 'Organic synthesis experiment', 'Prof. Suresh Patil');

-- Maintenance Seed Data
INSERT OR IGNORE INTO maintenance (id, equipment_id, service_date, completion_date, issue_description, cost, status, technician) VALUES
(1, 2, '2026-07-15', '2026-07-18', 'Digital balance calibration & sensor alignment', 1500.0, 'Completed', 'TechCare Instruments Kolhapur'),
(2, 4, '2026-07-22', NULL, 'Safety eyewash nozzle cleaning & fume hood exhaust belt replacement', 3500.0, 'Under Repair', 'Apex Lab Maintenance Services');