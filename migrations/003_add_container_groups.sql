-- Container Groups Migration
-- Adds support for organizing components into physical containers/groups

-- Create containers table
CREATE TABLE IF NOT EXISTS containers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE, -- e.g., "Box 1", "Toolbox", "Drawer A3"
    description TEXT,
    location VARCHAR(255), -- Physical location: "Shelf 2", "Workshop", "Garage"
    color VARCHAR(50), -- Optional color coding for visual organization

    -- Capacity tracking (optional)
    max_capacity INTEGER, -- Maximum number of component types
    current_count INTEGER DEFAULT 0, -- Automatically updated

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by BIGINT -- Telegram user ID
);

-- Add container_id to components table
ALTER TABLE components
ADD COLUMN IF NOT EXISTS container_id BIGINT REFERENCES containers(id) ON DELETE SET NULL;

-- Create index for faster container lookups
CREATE INDEX IF NOT EXISTS idx_components_container ON components(container_id);

-- Function to update container count automatically
CREATE OR REPLACE FUNCTION update_container_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update old container count (if component was moved)
    IF OLD.container_id IS NOT NULL AND OLD.container_id != NEW.container_id THEN
        UPDATE containers
        SET current_count = (
            SELECT COUNT(*) FROM components WHERE container_id = OLD.container_id
        )
        WHERE id = OLD.container_id;
    END IF;

    -- Update new container count
    IF NEW.container_id IS NOT NULL THEN
        UPDATE containers
        SET current_count = (
            SELECT COUNT(*) FROM components WHERE container_id = NEW.container_id
        )
        WHERE id = NEW.container_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update container counts on INSERT
CREATE TRIGGER update_container_count_on_insert
    AFTER INSERT ON components
    FOR EACH ROW
    WHEN (NEW.container_id IS NOT NULL)
    EXECUTE FUNCTION update_container_count();

-- Trigger to update container counts on UPDATE
CREATE TRIGGER update_container_count_on_update
    AFTER UPDATE ON components
    FOR EACH ROW
    WHEN (OLD.container_id IS DISTINCT FROM NEW.container_id)
    EXECUTE FUNCTION update_container_count();

-- Trigger to update container counts on DELETE
CREATE OR REPLACE FUNCTION update_container_count_on_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.container_id IS NOT NULL THEN
        UPDATE containers
        SET current_count = (
            SELECT COUNT(*) FROM components WHERE container_id = OLD.container_id
        )
        WHERE id = OLD.container_id;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_container_count_on_delete
    AFTER DELETE ON components
    FOR EACH ROW
    WHEN (OLD.container_id IS NOT NULL)
    EXECUTE FUNCTION update_container_count_on_delete();

-- Trigger for container updated_at
CREATE TRIGGER update_containers_updated_at
    BEFORE UPDATE ON containers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for container inventory summary
CREATE OR REPLACE VIEW v_container_inventory AS
SELECT
    c.id,
    c.name,
    c.description,
    c.location,
    c.color,
    c.current_count,
    c.max_capacity,
    COUNT(comp.id) as actual_count,
    SUM(comp.quantity) as total_items,
    ARRAY_AGG(DISTINCT comp.component_type) FILTER (WHERE comp.component_type IS NOT NULL) as component_types,
    c.created_at,
    c.updated_at
FROM containers c
LEFT JOIN components comp ON comp.container_id = c.id
GROUP BY c.id, c.name, c.description, c.location, c.color, c.current_count, c.max_capacity, c.created_at, c.updated_at
ORDER BY c.name;

-- Comments
COMMENT ON TABLE containers IS 'Physical containers/groups for organizing components (boxes, drawers, toolboxes, etc.)';
COMMENT ON COLUMN containers.name IS 'Unique container name (e.g., "Box 1", "Arduino Toolbox")';
COMMENT ON COLUMN containers.location IS 'Physical location of the container (e.g., "Shelf 2-A", "Workshop Drawer")';
COMMENT ON COLUMN containers.current_count IS 'Number of different component types in container (auto-updated)';
COMMENT ON VIEW v_container_inventory IS 'Summary view of all containers with their component counts';
