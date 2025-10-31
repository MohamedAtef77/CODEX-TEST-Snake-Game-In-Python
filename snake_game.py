"""Simple Snake game implementation using pygame.

The game logic is intentionally kept compact and easy to read so it can be
used as a starting point for further experimentation or refactoring.  The
implementation follows the traditional Snake rules:

* Use the arrow keys (or WASD) to move the snake around the play field.
* Eating food makes the snake grow and awards points.
* Hitting the walls or the snake's own body ends the game.

Running the script launches a pygame window and starts the main game loop.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Tuple

import pygame


class Direction(Enum):
    """Cardinal directions the snake can move."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector(self) -> Tuple[int, int]:
        return self.value

    def is_opposite(self, other: "Direction") -> bool:
        dx, dy = self.vector
        ox, oy = other.vector
        return dx == -ox and dy == -oy


Coordinate = Tuple[int, int]


@dataclass
class GameConfig:
    width: int = 600
    height: int = 400
    grid_size: int = 20
    snake_speed: int = 10

    @property
    def grid_width(self) -> int:
        return self.width // self.grid_size

    @property
    def grid_height(self) -> int:
        return self.height // self.grid_size


class Snake:
    """Encapsulates the snake state."""

    def __init__(self, start: Coordinate, direction: Direction) -> None:
        self.body: List[Coordinate] = [start]
        self.direction = direction
        self._grow_segments = 0

    @property
    def head(self) -> Coordinate:
        return self.body[0]

    def queue_growth(self, amount: int = 1) -> None:
        self._grow_segments += amount

    def move(self, direction: Direction) -> None:
        if direction.is_opposite(self.direction) and len(self.body) > 1:
            direction = self.direction

        self.direction = direction
        dx, dy = direction.vector
        x, y = self.head
        new_head = (x + dx, y + dy)
        self.body.insert(0, new_head)

        if self._grow_segments > 0:
            self._grow_segments -= 1
        else:
            self.body.pop()

    def collides_with_self(self) -> bool:
        return self.head in self.body[1:]

    def collides_with(self, coordinate: Coordinate) -> bool:
        return coordinate in self.body


class FoodManager:
    """Handles spawning food within the play area."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.position: Coordinate | None = None

    def spawn(self, occupied: Iterable[Coordinate]) -> Coordinate:
        occupied_set = set(occupied)
        free_spaces = [
            (x, y)
            for x in range(self.config.grid_width)
            for y in range(self.config.grid_height)
            if (x, y) not in occupied_set
        ]
        if not free_spaces:
            raise RuntimeError("No free spaces left to spawn food.")

        self.position = random.choice(free_spaces)
        return self.position


class SnakeGame:
    """Main game controller that owns the pygame loop."""

    BACKGROUND_COLOR = pygame.Color("black")
    SNAKE_COLOR = pygame.Color(0, 200, 0)
    FOOD_COLOR = pygame.Color("red")
    GRID_COLOR = pygame.Color(40, 40, 40)
    TEXT_COLOR = pygame.Color("white")

    def __init__(self, config: GameConfig | None = None) -> None:
        self.config = config or GameConfig()
        pygame.init()
        pygame.display.set_caption("Snake")
        self.surface = pygame.display.set_mode((self.config.width, self.config.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)

        start = (
            self.config.grid_width // 2,
            self.config.grid_height // 2,
        )
        self.snake = Snake(start=start, direction=Direction.RIGHT)
        self.food = FoodManager(self.config)
        self.score = 0
        self.food.spawn(self.snake.body)

    def _draw_grid(self) -> None:
        for x in range(0, self.config.width, self.config.grid_size):
            pygame.draw.line(
                self.surface,
                self.GRID_COLOR,
                (x, 0),
                (x, self.config.height),
            )
        for y in range(0, self.config.height, self.config.grid_size):
            pygame.draw.line(
                self.surface,
                self.GRID_COLOR,
                (0, y),
                (self.config.width, y),
            )

    def _draw_snake(self) -> None:
        for x, y in self.snake.body:
            rect = pygame.Rect(
                x * self.config.grid_size,
                y * self.config.grid_size,
                self.config.grid_size,
                self.config.grid_size,
            )
            pygame.draw.rect(self.surface, self.SNAKE_COLOR, rect)

    def _draw_food(self) -> None:
        if self.food.position is None:
            return
        x, y = self.food.position
        rect = pygame.Rect(
            x * self.config.grid_size,
            y * self.config.grid_size,
            self.config.grid_size,
            self.config.grid_size,
        )
        pygame.draw.rect(self.surface, self.FOOD_COLOR, rect)

    def _draw_score(self) -> None:
        text_surface = self.font.render(f"Score: {self.score}", True, self.TEXT_COLOR)
        self.surface.blit(text_surface, (10, 10))

    def _handle_input(self, current_direction: Direction) -> Direction:
        direction = current_direction
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    direction = Direction.UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    direction = Direction.DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    direction = Direction.LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    direction = Direction.RIGHT
        return direction

    def _check_collisions(self) -> bool:
        head_x, head_y = self.snake.head
        if not (0 <= head_x < self.config.grid_width and 0 <= head_y < self.config.grid_height):
            return True
        if self.snake.collides_with_self():
            return True
        return False

    def _update_food(self) -> None:
        if self.food.position is None:
            self.food.spawn(self.snake.body)
            return

        if self.snake.head == self.food.position:
            self.snake.queue_growth()
            self.score += 10
            self.food.spawn(self.snake.body)

    def game_over(self) -> None:
        message = self.font.render("Game Over - Press Enter to play again", True, self.TEXT_COLOR)
        rect = message.get_rect(center=(self.config.width // 2, self.config.height // 2))
        self.surface.blit(message, rect)
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    waiting = False
            self.clock.tick(10)

        self.__init__(self.config)

    def run(self) -> None:
        direction = self.snake.direction
        while True:
            direction = self._handle_input(direction)
            self.snake.move(direction)

            if self._check_collisions():
                self.game_over()
                direction = self.snake.direction
                continue

            self._update_food()

            self.surface.fill(self.BACKGROUND_COLOR)
            self._draw_grid()
            self._draw_snake()
            self._draw_food()
            self._draw_score()

            pygame.display.flip()
            self.clock.tick(self.config.snake_speed)


def main() -> None:
    game = SnakeGame()
    game.run()


if __name__ == "__main__":
    main()
