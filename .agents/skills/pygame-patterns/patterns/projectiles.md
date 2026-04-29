# Projectile Patterns

Verified patterns for implementing projectile entities (bullets, missiles, arrows, etc.) in pygame.

## Pattern 1: Spawning Projectiles

### Spawn at Entity Position with Direction

```python
import math

def spawn_projectile(x: float, y: float, angle: float, config: ProjectileConfig):
    """
    Spawn a projectile at entity position facing a direction.

    Args:
        x: Spawn X position (entity center)
        y: Spawn Y position (entity center)
        angle: Direction in degrees (0° = right, 90° = up, 180° = left, 270° = down)
        config: ProjectileConfig from config.py

    Returns:
        Projectile instance
    """
    # Convert angle to radians
    angle_rad = math.radians(angle)

    # Calculate velocity vector (accounting for pygame Y-axis inversion)
    velocity_x = math.cos(angle_rad) * config.speed
    velocity_y = -math.sin(angle_rad) * config.speed  # Negative because pygame Y is inverted

    return Projectile(x, y, velocity_x, velocity_y, config)
```

**Key points:**
- Angle in degrees (0° = right, follows pygame/trig convention)
- Use `math.radians()` to convert to radians for trig functions
- **Velocity Y is negative** (`-math.sin()`) because pygame Y-axis points down
- Spawn at entity center (x, y)

---

## Pattern 2: Projectile Movement

### Frame-Independent Velocity-Based Movement

```python
class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, config: ProjectileConfig):
        self.x = x
        self.y = y
        self.velocity_x = vx  # Pixels per second
        self.velocity_y = vy  # Pixels per second
        self.age = 0.0        # Seconds since spawn
        self.config = config
        self.alive = True

    def update(self, delta_time: float) -> None:
        """Update projectile position and lifetime.

        Args:
            delta_time: Time since last frame (seconds)
        """
        if not self.alive:
            return

        # Frame-independent movement
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time

        # Track lifetime
        self.age += delta_time
        if self.age >= self.config.lifetime:
            self.alive = False
```

**Key points:**
- Store velocity (pixels/second), not direction
- Multiply velocity by `delta_time` for frame-independence
- Track age for lifetime management
- Set `alive = False` instead of deleting (caller removes dead projectiles)

---

## Pattern 3: Circle Collision Detection

### Check Collision with Entities

```python
def check_collision(self, entity_x: float, entity_y: float, entity_radius: int) -> bool:
    """
    Check if projectile collides with an entity using circle collision.

    Args:
        entity_x: Entity center X
        entity_y: Entity center Y
        entity_radius: Entity collision radius

    Returns:
        True if collision detected
    """
    import math

    # Calculate distance between centers
    dx = self.x - entity_x
    dy = self.y - entity_y
    distance = math.sqrt(dx * dx + dy * dy)

    # Collision if distance < sum of radii
    return distance < (self.config.radius + entity_radius)
```

**Key points:**
- Use Pythagorean theorem: `distance = sqrt(dx² + dy²)`
- Collision when `distance < radius1 + radius2`
- Both entities treated as circles
- Fast and suitable for most projectile games

---

## Pattern 4: Lifetime Management

### Despawn After Lifetime or Collision

```python
class Projectile:
    def mark_for_removal(self) -> None:
        """Mark projectile as dead (hit target or expired)."""
        self.alive = False
        logger.debug(f"Projectile despawned at ({int(self.x)}, {int(self.y)})")

    def is_alive(self) -> bool:
        """Check if projectile should remain in game."""
        return self.alive

# In game loop:
for projectile in projectiles[:]:  # Iterate over copy
    if not projectile.is_alive():
        projectiles.remove(projectile)
```

**Key points:**
- Use `alive` flag instead of immediate removal
- Caller iterates over copy (`projectiles[:]`) to safely remove during iteration
- Log despawn events for debugging
- Remove after update/collision checks, not during

---

## Pattern 5: Config-Driven Projectile

### Use Centralized Config (Never Hardcode)

```python
# In src/config.py
@dataclass
class ProjectileConfig:
    """Projectile/bullet settings"""
    speed: float = 500.0         # Pixels per second
    radius: int = 4              # Collision radius
    color: tuple = (255, 255, 0) # Yellow
    lifetime: float = 2.0        # Seconds before despawn
    damage: int = 10

# Global instance
projectile_config = ProjectileConfig()

# In src/entities/projectile.py
from config import projectile_config

class Projectile:
    def __init__(self, x, y, vx, vy):
        self.config = projectile_config  # Reference global config
        self.speed = self.config.speed   # NOT hardcoded!
```

**Key points:**
- All values in `config.py` dataclass
- No magic numbers in entity code
- Easy to balance/tune from one location
- Follows project convention (see PlayerConfig, ZombieConfig, etc.)

---

## Pattern 6: Rendering Projectiles

### Simple Circle Rendering

```python
def render(self, screen) -> None:
    """Draw projectile on screen."""
    if not self.alive:
        return

    pygame.draw.circle(
        screen,
        self.config.color,
        (int(self.x), int(self.y)),
        self.config.radius
    )
```

**Key points:**
- Convert float positions to int for drawing
- Use config color (not hardcoded)
- Skip rendering if not alive
- Can replace with sprite later (use `load_sprite()` from utils.py)

---

## Complete Example

```python
# src/entities/projectile.py
import math
import pygame
from logger import get_logger
from config import projectile_config

logger = get_logger(__name__)


class Projectile:
    """A projectile entity (bullet, arrow, etc.)"""

    def __init__(self, x: float, y: float, angle: float):
        """Spawn projectile at position with direction.

        Args:
            x: Spawn X position
            y: Spawn Y position
            angle: Direction in degrees (0° = right)
        """
        self.x = x
        self.y = y
        self.config = projectile_config

        # Convert angle to velocity
        angle_rad = math.radians(angle)
        self.velocity_x = math.cos(angle_rad) * self.config.speed
        self.velocity_y = -math.sin(angle_rad) * self.config.speed

        self.age = 0.0
        self.alive = True

        logger.debug(f"Projectile spawned at ({int(x)}, {int(y)}) angle={angle}°")

    def update(self, delta_time: float) -> None:
        """Update position and lifetime."""
        if not self.alive:
            return

        # Move
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time

        # Age
        self.age += delta_time
        if self.age >= self.config.lifetime:
            self.alive = False
            logger.debug(f"Projectile expired at ({int(self.x)}, {int(self.y)})")

    def check_collision(self, entity_x: float, entity_y: float, entity_radius: int) -> bool:
        """Check circle collision with entity."""
        dx = self.x - entity_x
        dy = self.y - entity_y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (self.config.radius + entity_radius)

    def render(self, screen) -> None:
        """Draw projectile."""
        if not self.alive:
            return
        pygame.draw.circle(screen, self.config.color, (int(self.x), int(self.y)), self.config.radius)
```

---

## Testing Patterns

Use with **python-testing** skill:

```python
# tests/entities/test_projectile.py
def test_projectile_spawns_with_correct_velocity():
    """Test angle-to-velocity conversion."""
    # 0° = right
    p = Projectile(100, 100, angle=0)
    assert p.velocity_x > 0
    assert abs(p.velocity_y) < 0.01  # Nearly zero

    # 90° = up (negative Y in pygame)
    p = Projectile(100, 100, angle=90)
    assert abs(p.velocity_x) < 0.01
    assert p.velocity_y < 0  # Negative = upward

def test_projectile_moves_frame_independently():
    """Test movement with different delta_time."""
    p = Projectile(0, 0, angle=0)
    initial_x = p.x

    # Large timestep
    p.update(delta_time=1.0)
    distance_1sec = p.x - initial_x

    # Should travel at config.speed px/sec
    assert abs(distance_1sec - p.config.speed) < 1.0
```

---

## Angle Convention Reference

**Pygame coordinate system:**
- X-axis: Left (0) → Right (positive)
- Y-axis: Top (0) → Down (positive) ← **INVERTED**

**Angle directions:**
- 0° = Right (→)
- 90° = Up (↑)
- 180° = Left (←)
- 270° = Down (↓)

**Velocity conversion:**
```python
velocity_x = math.cos(radians) * speed   # Positive = right
velocity_y = -math.sin(radians) * speed  # Negative = up (inverted!)
```

---

## Common Pitfalls

❌ **Forgetting Y-axis inversion:**
```python
velocity_y = math.sin(angle_rad) * speed  # WRONG - projectile goes down when aiming up
```

✅ **Correct Y-axis handling:**
```python
velocity_y = -math.sin(angle_rad) * speed  # CORRECT - negative Y = upward
```

❌ **Hardcoded values:**
```python
self.speed = 500  # WRONG - not configurable
```

✅ **Config-driven:**
```python
self.speed = self.config.speed  # CORRECT - from config.py
```

❌ **Removing during iteration:**
```python
for proj in projectiles:
    if not proj.alive:
        projectiles.remove(proj)  # WRONG - modifies list during iteration
```

✅ **Iterate over copy:**
```python
for proj in projectiles[:]:  # CORRECT - iterate over copy
    if not proj.alive:
        projectiles.remove(proj)
```
