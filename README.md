# Snake Game in Python

This repository contains a small but fully functional version of the classic
Snake game written in Python using the [pygame](https://www.pygame.org)
library. The code is intentionally lightweight so that it can serve as an
educational reference or a starting point for new game mechanics.

## Requirements

- Python 3.9+
- `pygame` (install via `pip install pygame`)

## Running the game
Compile: python3 -m compileall snake_game.py
```bash
python snake_game.py
```

Use the arrow keys (or WASD) to control the snake. Eating food grows the
snake and awards 10 points. Colliding with the snake's body or the edges of the
window ends the game. After the game is over press **Enter** to restart.

## Project structure

```
.
├── README.md
└── snake_game.py
```

Feel free to fork the project and experiment with additional features such as
sound effects, difficulty levels, or alternative control schemes.
