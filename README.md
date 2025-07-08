# Crystal Caverns - Glitch Adventure

A 2D platformer game with procedurally generated caves, combat, and exploration.

## Project Structure

```
ClassicGame/
├── assets/
│   ├── audio/       # Sound effects and music
│   └── images/      # Game textures and sprites
├── src/
│   ├── core/        # Core game functionality
│   │   ├── config.py    # Game constants and configuration
│   │   └── main.py      # Main game loop and mechanics
│   ├── entities/    # Game entities and objects
│   │   ├── entities.py  # Player, enemies, items, etc.
│   │   └── room.py      # Room generation and management
│   ├── generators/  # Procedural generation
│   │   └── cave_generator.py  # Cave generation algorithms
│   └── ui/          # User interface components
│       └── audio.py     # Audio management
```

## Features

- Procedurally generated caves with multiple algorithms
- Combat system with directional attacks
- Inventory and equipment system
- Crystal-based abilities (teleport, phase)
- Enemy AI with different behaviors
- Boss battles
- Textured environments

## Controls

- **WASD/Arrow Keys**: Move
- **Space**: Jump
- **Left Click**: Attack in cursor direction
- **Right Click**: Teleport toward cursor
- **Q**: Phase (pass through walls)
- **I**: Open inventory
- **R**: Enter door (when near unlocked door)

## Setup

1. Ensure you have Python 3.x and Pygame installed
2. Place image assets in `assets/images/` directory
3. Place audio assets in `assets/audio/` directory
4. Run the game with `python main.py`

## Required Assets

- `stone.jpg`: Wall texture
- `crystal.png`: Crystal collectible
- `glitch_crystal.png`: Special crystal
- `beatle.png`: Enemy sprite
- `bg.png`: Background image
- Audio files: `jump.wav`, `crystal.wav`, `glitch.wav`, `beat.wav`, `bg_sound.wav`

## Cave Generation Types

- **Cellular**: Organic, bubble-like caves
- **Perlin**: Flowing, natural caves
- **Tunnels**: Connected tunnel networks
- **Cavern**: Large open spaces
- **Mixed**: Combination of techniques