import pygame

class GameClock:
    def __init__(self, fps: int) -> None:
        self._clock = pygame.time.Clock()
        self._fps = fps

    def tick(self) -> float:
        return self._clock.tick(self._fps) / 1000.0
