# Container Groups Setup Guide

This guide will help you set up container organization for your inventory.

## Step 1: Apply Database Migration

Since Supabase doesn't allow direct SQL execution via API, you need to apply the migration manually:

1. **Go to your Supabase Dashboard**: https://supabase.com/dashboard
2. **Navigate to SQL Editor** (left sidebar)
3. **Create a new query**
4. **Copy the contents** of `migrations/003_add_container_groups.sql`
5. **Paste and run** the SQL
6. **Verify** - You should see a success message

## Step 2: What This Adds

### New Table: `containers`
- Store physical containers like boxes, drawers, toolboxes
- Track location, capacity, and component count
- Auto-update component counts

### New Column: `components.container_id`
- Links each component to a container
- Optional - components can exist without a container

### New View: `v_container_inventory`
- Quick summary of all containers
- Shows component counts and types per container

## Step 3: Using Containers

### Create Containers (via bot commands):
```
/container_add Box 1
/container_add Arduino Toolbox
/container_add Resistor Drawer
```

### Assign Components to Containers:
```
/container_assign 5 Box 1
```
(Assigns component ID 5 to "Box 1")

### View Container Contents:
```
/container_list Box 1
```

### Move Components Between Containers:
```
/container_move 5 Box 2
```

## Step 4: Bot Commands to Add

The following commands will be added to the bot:
- `/containers` - List all containers
- `/container_add <name> [location]` - Create new container
- `/container_view <name>` - View container details
- `/container_assign <component_id> <container>` - Assign component
- `/container_move <component_id> <new_container>` - Move component

## Example Workflow

1. Create containers:
   ```
   /container_add "Box 1" "Shelf A"
   /container_add "Arduino Parts" "Workshop Drawer 2"
   ```

2. Add component to inventory (via photo):
   - Send photo of component
   - Bot identifies it
   - Enter quantity
   - ✅ Saved!

3. Assign to container:
   ```
   /container_assign 5 Box 1
   ```

4. View what's in a container:
   ```
   /container_view Box 1
   ```

   Output:
   ```
   📦 Box 1
   📍 Location: Shelf A
   📊 Components: 3 types, 15 total items

   Contents:
   • Fire TV Remote (ID: 5) - Qty: 1
   • Arduino Uno (ID: 3) - Qty: 2
   • 10kΩ Resistor (ID: 12) - Qty: 12
   ```

## Benefits

✅ **Organized Storage** - Know exactly where each component is
✅ **Quick Location** - Find components fast
✅ **Capacity Planning** - Track how full each container is
✅ **Visual Organization** - Color-code containers
✅ **Auto-tracking** - Component counts update automatically

## Next Steps

After applying the migration:
1. Run the bot update to add container commands
2. Create your first containers
3. Start organizing your inventory!
