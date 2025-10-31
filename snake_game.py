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

    @staticmethod
    def from_vector(vector: Tuple[int, int]) -> "Direction":
        for direction in Direction:
            if direction.vector == vector:
                return direction
        raise ValueError(f"Invalid direction vector: {vector}")


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

    BACKGROUND_COLOR = pygame.Color(18, 18, 18)
    GRID_COLOR = pygame.Color(40, 40, 40)
    SNAKE_PRIMARY_COLOR = pygame.Color(31, 117, 54)
    SNAKE_SECONDARY_COLOR = pygame.Color(68, 173, 92)
    SNAKE_BELLY_COLOR = pygame.Color(210, 186, 110)
    SNAKE_SPOT_COLOR = pygame.Color(26, 85, 47)
    SNAKE_SHADOW_COLOR = pygame.Color(12, 54, 24)
    TEXT_COLOR = pygame.Color("white")
    FOOD_GLOW_COLOR = pygame.Color(255, 82, 82)

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
        self._build_graphics_assets()

    def _build_graphics_assets(self) -> None:
        self.snake_head_images = self._create_oriented_surfaces(self._create_snake_head_surface())
        self.snake_tail_images = self._create_oriented_surfaces(self._create_snake_tail_surface())
        self.apple_image = self._create_apple_surface()

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
        if not self.snake.body:
            return

        centers = [self._cell_center(segment) for segment in self.snake.body]
        body_width = max(6, int(self.config.grid_size * 0.7))

        if len(centers) > 1:
            for start, end in zip(centers[:-1], centers[1:]):
                pygame.draw.line(
                    self.surface,
                    self.SNAKE_SHADOW_COLOR,
                    start,
                    end,
                    body_width + 4,
                )
                pygame.draw.line(
                    self.surface,
                    self.SNAKE_PRIMARY_COLOR,
                    start,
                    end,
                    body_width,
                )
                belly_offset = int(body_width * 0.25)
                pygame.draw.line(
                    self.surface,
                    self.SNAKE_BELLY_COLOR,
                    (start[0], start[1] + belly_offset),
                    (end[0], end[1] + belly_offset),
                    max(2, body_width // 4),
                )

        for center in centers[1:-1]:
            pygame.draw.circle(self.surface, self.SNAKE_PRIMARY_COLOR, center, body_width // 2)
            pygame.draw.circle(
                self.surface,
                self.SNAKE_SECONDARY_COLOR,
                center,
                max(2, body_width // 2 - 2),
                2,
            )
            pygame.draw.circle(
                self.surface,
                self.SNAKE_SPOT_COLOR,
                center,
                max(2, body_width // 5),
                0,
            )

        head_direction = self._head_direction()
        head_surface = self.snake_head_images[head_direction]
        head_rect = head_surface.get_rect(center=centers[0])
        self.surface.blit(head_surface, head_rect)

        if len(centers) > 1:
            tail_direction = self._tail_direction()
        else:
            tail_direction = head_direction
        tail_surface = self.snake_tail_images[tail_direction]
        tail_rect = tail_surface.get_rect(center=centers[-1])
        self.surface.blit(tail_surface, tail_rect)

    def _draw_food(self) -> None:
        if self.food.position is None:
            return
        x, y = self.food.position
        rect = self.apple_image.get_rect()
        rect.center = self._cell_center((x, y))
        self.surface.blit(self.apple_image, rect)

    def _cell_center(self, coordinate: Coordinate) -> Tuple[int, int]:
        x, y = coordinate
        half = self.config.grid_size // 2
        return (
            x * self.config.grid_size + half,
            y * self.config.grid_size + half,
        )

    def _head_direction(self) -> Direction:
        if len(self.snake.body) > 1:
            head_x, head_y = self.snake.body[0]
            neck_x, neck_y = self.snake.body[1]
            return Direction.from_vector((head_x - neck_x, head_y - neck_y))
        return self.snake.direction

    def _tail_direction(self) -> Direction:
        if len(self.snake.body) > 1:
            tail_x, tail_y = self.snake.body[-1]
            prev_x, prev_y = self.snake.body[-2]
            return Direction.from_vector((tail_x - prev_x, tail_y - prev_y))
        return self.snake.direction

    def _create_oriented_surfaces(self, base_surface: pygame.Surface) -> dict[Direction, pygame.Surface]:
        return {
            Direction.RIGHT: base_surface,
            Direction.DOWN: pygame.transform.rotate(base_surface, -90),
            Direction.LEFT: pygame.transform.rotate(base_surface, 180),
            Direction.UP: pygame.transform.rotate(base_surface, 90),
        }

    def _create_snake_head_surface(self) -> pygame.Surface:
        size = self.config.grid_size
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        head_rect = pygame.Rect(
            int(size * 0.05),
            int(size * 0.15),
            int(size * 0.8),
            int(size * 0.7),
        )
        pygame.draw.ellipse(surface, self.SNAKE_PRIMARY_COLOR, head_rect)

        highlight_rect = pygame.Rect(
            int(size * 0.2),
            int(size * 0.3),
            int(size * 0.6),
            int(size * 0.4),
        )
        pygame.draw.ellipse(surface, self.SNAKE_SECONDARY_COLOR, highlight_rect)

        eye_radius = max(2, size // 8)
        upper_eye = (int(size * 0.72), int(size * 0.3))
        lower_eye = (int(size * 0.72), int(size * 0.7))
        pygame.draw.circle(surface, pygame.Color("white"), upper_eye, eye_radius)
        pygame.draw.circle(surface, pygame.Color("black"), upper_eye, max(1, eye_radius // 2))
        pygame.draw.circle(surface, pygame.Color("white"), lower_eye, eye_radius)
        pygame.draw.circle(surface, pygame.Color("black"), lower_eye, max(1, eye_radius // 2))

        nostril_radius = max(1, eye_radius // 2)
        pygame.draw.circle(surface, self.SNAKE_SPOT_COLOR, (int(size * 0.82), int(size * 0.45)), nostril_radius)
        pygame.draw.circle(surface, self.SNAKE_SPOT_COLOR, (int(size * 0.82), int(size * 0.55)), nostril_radius)

        tongue_points = [
            (size - 1, size // 2),
            (int(size * 0.86), int(size * 0.44)),
            (int(size * 0.86), int(size * 0.56)),
        ]
        pygame.draw.polygon(surface, pygame.Color(220, 52, 52), tongue_points)
        pygame.draw.line(surface, pygame.Color(255, 120, 120), (size - 2, size // 2), (int(size * 0.92), int(size * 0.46)), 1)
        pygame.draw.line(surface, pygame.Color(255, 120, 120), (size - 2, size // 2), (int(size * 0.92), int(size * 0.54)), 1)

        return surface

    def _create_snake_tail_surface(self) -> pygame.Surface:
        size = self.config.grid_size
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        body_width = max(6, int(size * 0.68))
        center_y = size // 2
        half = body_width // 2

        polygon = [
            (0, center_y - half),
            (int(size * 0.62), center_y - half),
            (size - 1, center_y),
            (int(size * 0.62), center_y + half),
            (0, center_y + half),
        ]
        pygame.draw.polygon(surface, self.SNAKE_PRIMARY_COLOR, polygon)
        pygame.draw.polygon(surface, self.SNAKE_SECONDARY_COLOR, polygon, 2)
        pygame.draw.circle(surface, self.SNAKE_PRIMARY_COLOR, (int(size * 0.18), center_y), body_width // 2)
        pygame.draw.line(
            surface,
            self.SNAKE_BELLY_COLOR,
            (int(size * 0.15), center_y),
            (int(size * 0.55), center_y),
            max(2, body_width // 4),
        )
        return surface

    def _create_apple_surface(self) -> pygame.Surface:
        size = self.config.grid_size
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = max(6, int(size * 0.38))
        center = (size // 2, size // 2)

        pygame.draw.circle(surface, pygame.Color(190, 0, 0), center, radius)
        pygame.draw.circle(surface, pygame.Color(255, 120, 120), (center[0] - radius // 3, center[1] - radius // 3), radius // 2)
        pygame.draw.circle(surface, self.FOOD_GLOW_COLOR, center, radius + 2, 2)

        stem_width = max(2, radius // 4)
        stem_height = max(4, radius // 2)
        stem_rect = pygame.Rect(
            center[0] - stem_width // 2,
            max(0, center[1] - radius - stem_height // 2),
            stem_width,
            stem_height,
        )
        pygame.draw.rect(surface, pygame.Color(101, 67, 33), stem_rect)

        leaf_rect = pygame.Rect(0, 0, radius, max(4, radius // 2))
        leaf_rect.center = (center[0] + radius // 2, center[1] - radius)
        pygame.draw.ellipse(surface, pygame.Color(86, 125, 70), leaf_rect)
        pygame.draw.line(
            surface,
            pygame.Color(60, 90, 50),
            (leaf_rect.centerx - leaf_rect.width // 4, leaf_rect.centery),
            (leaf_rect.centerx + leaf_rect.width // 2, leaf_rect.centery - leaf_rect.height // 2),
            2,
        )

        return surface

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
