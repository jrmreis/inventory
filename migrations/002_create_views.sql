-- Useful database views for the inventory system
-- Run this in your Supabase SQL editor after running 001_create_components_table.sql

-- View: Low stock components (quantity at or below minimum)
CREATE OR REPLACE VIEW v_low_stock_components AS
SELECT
    id,
    component_type,
    name,
    part_number,
    quantity,
    minimum_quantity,
    storage_location,
    supplier,
    (quantity::DECIMAL / NULLIF(minimum_quantity, 0)) * 100 AS stock_level_percentage
FROM components
WHERE quantity <= minimum_quantity
ORDER BY stock_level_percentage ASC, component_type;

-- View: Component inventory summary by type
CREATE OR REPLACE VIEW v_inventory_summary_by_type AS
SELECT
    component_type,
    COUNT(*) AS unique_components,
    SUM(quantity) AS total_quantity,
    COUNT(CASE WHEN quantity <= minimum_quantity THEN 1 END) AS low_stock_count,
    AVG(quantity) AS avg_quantity_per_component,
    SUM(CASE WHEN unit_price IS NOT NULL THEN quantity * unit_price ELSE 0 END) AS estimated_inventory_value
FROM components
GROUP BY component_type
ORDER BY total_quantity DESC;

-- View: Component inventory summary by location
CREATE OR REPLACE VIEW v_inventory_summary_by_location AS
SELECT
    COALESCE(storage_location, 'Unassigned') AS storage_location,
    COUNT(*) AS component_count,
    SUM(quantity) AS total_items,
    array_agg(DISTINCT component_type) AS component_types
FROM components
GROUP BY storage_location
ORDER BY component_count DESC;

-- View: Recent stock movements with component details
CREATE OR REPLACE VIEW v_recent_stock_movements AS
SELECT
    sm.id,
    sm.created_at,
    sm.movement_type,
    sm.quantity_change,
    sm.quantity_before,
    sm.quantity_after,
    sm.reason,
    sm.reference,
    c.component_type,
    c.name,
    c.part_number,
    c.storage_location
FROM stock_movements sm
JOIN components c ON sm.component_id = c.id
ORDER BY sm.created_at DESC;

-- View: Component usage statistics
CREATE OR REPLACE VIEW v_component_usage_stats AS
SELECT
    c.id,
    c.component_type,
    c.name,
    c.part_number,
    COUNT(cu.id) AS usage_count,
    SUM(cu.quantity_used) AS total_quantity_used,
    MAX(cu.usage_date) AS last_used_date,
    array_agg(DISTINCT cu.project_name) FILTER (WHERE cu.project_name IS NOT NULL) AS projects_used_in
FROM components c
LEFT JOIN component_usage cu ON c.id = cu.component_id
GROUP BY c.id, c.component_type, c.name, c.part_number
ORDER BY total_quantity_used DESC NULLS LAST;

-- View: Components with full details including usage
CREATE OR REPLACE VIEW v_components_detailed AS
SELECT
    c.*,
    COALESCE(usage_stats.usage_count, 0) AS usage_count,
    COALESCE(usage_stats.total_quantity_used, 0) AS total_quantity_used,
    usage_stats.last_used_date,
    usage_stats.projects_used_in,
    CASE
        WHEN c.quantity <= 0 THEN 'OUT_OF_STOCK'
        WHEN c.quantity <= c.minimum_quantity THEN 'LOW_STOCK'
        WHEN c.quantity <= c.minimum_quantity * 2 THEN 'NORMAL'
        ELSE 'WELL_STOCKED'
    END AS stock_status
FROM components c
LEFT JOIN v_component_usage_stats usage_stats ON c.id = usage_stats.id;

-- View: Most used components (top 50)
CREATE OR REPLACE VIEW v_most_used_components AS
SELECT
    c.component_type,
    c.name,
    c.part_number,
    c.quantity AS current_stock,
    c.storage_location,
    COUNT(cu.id) AS usage_count,
    SUM(cu.quantity_used) AS total_used,
    MAX(cu.usage_date) AS last_used
FROM components c
JOIN component_usage cu ON c.id = cu.component_id
GROUP BY c.id, c.component_type, c.name, c.part_number, c.quantity, c.storage_location
ORDER BY total_used DESC
LIMIT 50;

-- View: Purchase recommendations (low stock items with supplier info)
CREATE OR REPLACE VIEW v_purchase_recommendations AS
SELECT
    c.component_type,
    c.name,
    c.part_number,
    c.quantity AS current_quantity,
    c.minimum_quantity,
    c.minimum_quantity * 3 - c.quantity AS recommended_order_quantity,
    c.supplier,
    c.unit_price,
    c.currency,
    c.datasheet_url,
    (c.minimum_quantity * 3 - c.quantity) * COALESCE(c.unit_price, 0) AS estimated_cost
FROM components c
WHERE c.quantity < c.minimum_quantity * 2
ORDER BY
    CASE WHEN c.quantity <= 0 THEN 1
         WHEN c.quantity <= c.minimum_quantity THEN 2
         ELSE 3
    END,
    c.component_type;

-- View: Inventory value by component type
CREATE OR REPLACE VIEW v_inventory_value_by_type AS
SELECT
    component_type,
    COUNT(*) AS component_count,
    SUM(quantity) AS total_quantity,
    SUM(quantity * COALESCE(unit_price, 0)) AS total_value,
    currency,
    AVG(unit_price) AS avg_unit_price
FROM components
WHERE unit_price IS NOT NULL
GROUP BY component_type, currency
ORDER BY total_value DESC;

-- Comments
COMMENT ON VIEW v_low_stock_components IS 'Components at or below minimum stock level';
COMMENT ON VIEW v_inventory_summary_by_type IS 'Inventory statistics grouped by component type';
COMMENT ON VIEW v_inventory_summary_by_location IS 'Inventory statistics grouped by storage location';
COMMENT ON VIEW v_recent_stock_movements IS 'Recent stock movements with component details';
COMMENT ON VIEW v_component_usage_stats IS 'Usage statistics for each component';
COMMENT ON VIEW v_components_detailed IS 'Components with usage stats and stock status';
COMMENT ON VIEW v_most_used_components IS 'Top 50 most frequently used components';
COMMENT ON VIEW v_purchase_recommendations IS 'Components that should be reordered';
COMMENT ON VIEW v_inventory_value_by_type IS 'Total inventory value by component type';
