# Container Organization - Quick Start

## Step 1: Apply Database Migration

**IMPORTANT:** Before using container commands, you must apply the database migration.

1. Open Supabase Dashboard: https://supabase.com/dashboard
2. Go to **SQL Editor** (left sidebar)
3. Click "New Query"
4. Copy ALL contents from `migrations/003_add_container_groups.sql`
5. Paste and click "Run"
6. ✅ You should see "Success. No rows returned"

## Step 2: Restart the Bot

```bash
./restart_bot.sh
```

## Step 3: Start Organizing!

### Create Your First Container
```
/container_add "Box 1" "Shelf A"
```

### List All Containers
```
/containers
```

### Assign a Component to a Container
```
/container_assign 5 "Box 1"
```
(This assigns component ID 5 to Box 1)

### View Container Contents
```
/container_view "Box 1"
```

## Complete Workflow Example

1. **Create containers for your workspace:**
   ```
   /container_add "Resistors Box" "Drawer 1"
   /container_add "Arduino Parts" "Shelf B"
   /container_add "Capacitors" "Drawer 2"
   ```

2. **Add a component via photo:**
   - Send photo of component
   - Bot identifies it (e.g., "Fire TV Remote")
   - Enter quantity: `1`
   - ✅ Component saved with ID 5

3. **Organize the component:**
   ```
   /container_assign 5 "Arduino Parts"
   ```

4. **Check what's in the container:**
   ```
   /container_view "Arduino Parts"
   ```

   Output:
   ```
   📦 Arduino Parts
   📍 Location: Shelf B
   📊 Components: 1 types
   📈 Total items: 1

   Contents:
   • Fire TV Remote (ID: 5)
     Type: remote_control
     Qty: 1
   ```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/containers` | List all containers | `/containers` |
| `/container_add` | Create new container | `/container_add "Box 1" "Shelf A"` |
| `/container_view` | View container details | `/container_view "Box 1"` |
| `/container_assign` | Assign component | `/container_assign 5 "Box 1"` |

## Tips

- Use descriptive container names: "Resistors Box", "Arduino Toolbox"
- Set locations for easy finding: "Shelf A", "Drawer 2", "Workshop"
- The bot automatically tracks component counts per container
- Components can be reassigned to different containers anytime

## Benefits

✅ **Know Exactly Where Things Are** - No more searching!
✅ **Quick Location** - `/container_view` shows all contents
✅ **Auto-Tracking** - Component counts update automatically
✅ **Flexible Organization** - Move components between containers easily
