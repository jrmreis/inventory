-- Electronic Components Inventory Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Components table
CREATE TABLE IF NOT EXISTS components (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,

    -- Basic Information
    component_type VARCHAR(100) NOT NULL, -- resistor, capacitor, arduino, connector, ic, led, sensor, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    manufacturer VARCHAR(255),
    part_number VARCHAR(255),

    -- Technical Specifications (stored as JSONB for flexibility)
    specifications JSONB DEFAULT '{}',
    -- Example for resistor: {"resistance": "10k", "tolerance": "5%", "power_rating": "0.25W", "package": "0805"}
    -- Example for capacitor: {"capacitance": "100uF", "voltage_rating": "25V", "type": "electrolytic"}
    -- Example for arduino: {"model": "Uno R3", "voltage": "5V", "pins": "14 digital, 6 analog"}

    -- Inventory Management
    quantity INTEGER NOT NULL DEFAULT 0,
    minimum_quantity INTEGER DEFAULT 5, -- Alert threshold
    storage_location VARCHAR(255), -- e.g., "Drawer A3", "Box 12", "Shelf 2-B"
    bin_number VARCHAR(50),

    -- Image and Recognition
    image_url TEXT,
    ocr_text TEXT, -- Extracted text from component image
    recognition_confidence DECIMAL(5,2), -- AI confidence score (0-100)

    -- Metadata
    notes TEXT,
    tags TEXT[], -- Array of tags for searching: ["smd", "through-hole", "5v-compatible"]

    -- Purchase Information (optional)
    supplier VARCHAR(255),
    unit_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    last_purchase_date DATE,
    datasheet_url TEXT,

    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by BIGINT, -- Telegram user ID
    last_modified_by BIGINT
);

-- Component usage history (track when components are used in projects)
CREATE TABLE IF NOT EXISTS component_usage (
    id BIGSERIAL PRIMARY KEY,
    component_id BIGINT REFERENCES components(id) ON DELETE CASCADE,

    project_name VARCHAR(255),
    quantity_used INTEGER NOT NULL,
    usage_date DATE DEFAULT CURRENT_DATE,
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by BIGINT -- Telegram user ID
);

-- Stock movements (detailed tracking of additions/removals)
CREATE TABLE IF NOT EXISTS stock_movements (
    id BIGSERIAL PRIMARY KEY,
    component_id BIGINT REFERENCES components(id) ON DELETE CASCADE,

    movement_type VARCHAR(20) NOT NULL, -- 'add', 'remove', 'adjust', 'transfer'
    quantity_change INTEGER NOT NULL, -- Positive for additions, negative for removals
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,

    reason VARCHAR(255), -- 'purchase', 'project_use', 'inventory_correction', etc.
    reference TEXT, -- Invoice number, project name, etc.
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by BIGINT -- Telegram user ID
);

-- Indexes for performance
CREATE INDEX idx_components_type ON components(component_type);
CREATE INDEX idx_components_location ON components(storage_location);
CREATE INDEX idx_components_part_number ON components(part_number);
CREATE INDEX idx_components_tags ON components USING GIN(tags);
CREATE INDEX idx_components_created_at ON components(created_at DESC);
CREATE INDEX idx_component_usage_component_id ON component_usage(component_id);
CREATE INDEX idx_component_usage_date ON component_usage(usage_date DESC);
CREATE INDEX idx_stock_movements_component_id ON stock_movements(component_id);
CREATE INDEX idx_stock_movements_created_at ON stock_movements(created_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at
CREATE TRIGGER update_components_updated_at
    BEFORE UPDATE ON components
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to track stock movements automatically
CREATE OR REPLACE FUNCTION track_stock_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- Only track if quantity changed
    IF OLD.quantity != NEW.quantity THEN
        INSERT INTO stock_movements (
            component_id,
            movement_type,
            quantity_change,
            quantity_before,
            quantity_after,
            reason,
            created_by
        ) VALUES (
            NEW.id,
            CASE
                WHEN NEW.quantity > OLD.quantity THEN 'add'
                WHEN NEW.quantity < OLD.quantity THEN 'remove'
                ELSE 'adjust'
            END,
            NEW.quantity - OLD.quantity,
            OLD.quantity,
            NEW.quantity,
            'quantity_update',
            NEW.last_modified_by
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic stock movement tracking
CREATE TRIGGER track_component_stock_changes
    AFTER UPDATE ON components
    FOR EACH ROW
    EXECUTE FUNCTION track_stock_movement();

-- Comments for documentation
COMMENT ON TABLE components IS 'Main inventory table for electronic components';
COMMENT ON TABLE component_usage IS 'History of component usage in projects';
COMMENT ON TABLE stock_movements IS 'Detailed log of all stock quantity changes';
COMMENT ON COLUMN components.specifications IS 'Component technical specifications in JSON format (flexible schema)';
COMMENT ON COLUMN components.tags IS 'Searchable tags for categorization and filtering';
