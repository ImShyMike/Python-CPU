"""Display module"""

import numpy as np

pygame = None  # pylint: disable=invalid-name


def init_pygame() -> None:
    """Import and initialize pygame"""

    global pygame  # pylint: disable=global-statement

    import pygame  # pylint: disable=import-outside-toplevel, redefined-outer-name

    if not pygame.get_init():
        pygame.init()

    return True


class Display:
    """Display"""

    def __init__(self, width: int, height: int, scale: int = 2) -> None:
        self.pixel_size = scale
        self.screen = pygame.display.set_mode(
            (width * self.pixel_size, height * self.pixel_size)
        )
        self.surface = pygame.Surface(
            (width * self.pixel_size, height * self.pixel_size)
        )
        self.clock = pygame.time.Clock()

        # Initialize with uint16 dtype for 32-bit color values
        self.image = np.zeros((width, height), dtype=np.uint32)
        self.buffer = np.zeros((width, height), dtype=np.uint32)
        self.width = width
        self.height = height
        self.is_drawing_to_buffer = False
        self.color = 0
        self.needs_update = False

    def swap_buffer(self) -> None:
        """Swap the display buffer with the image"""

        self.image, self.buffer = self.buffer, self.image
        self.needs_update = True

    def clear_image(self) -> None:
        """Clear the image"""

        self.image = np.zeros((self.width, self.height), dtype=np.uint32)
        self.needs_update = True

    def clear_buffer(self) -> None:
        """Clear the buffer"""

        self.buffer = np.zeros((self.width, self.height), dtype=np.uint32)
        self.needs_update = True

    def set_color(self, color: int) -> None:
        """Set the color"""

        self.color = color

    def set_pixel(self, x: int, y: int) -> None:
        """Set a pixel"""

        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return

        # Ensure color is a valid 32-bit value
        color = self.color & 0xFFFFFFFF

        if self.is_drawing_to_buffer:
            self.buffer[x, y] = color
        else:
            self.image[x, y] = color

        self.needs_update = True

    def draw(self) -> None:
        """Draw the display"""
        # Extract RGB components from the 24-bit color values
        r = (self.image >> 16) & 0xFF
        g = (self.image >> 8) & 0xFF
        b = self.image & 0xFF

        # Stack the RGB components into a 3D array
        rgb_array = np.stack([r, g, b], axis=2).astype(np.uint8)

        # Create surface and scale
        array = pygame.surfarray.make_surface(rgb_array)
        scaled_surface = pygame.transform.scale(
            array, (self.width * self.pixel_size, self.height * self.pixel_size)
        )
        self.screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()

    def update(self) -> None:
        """Update the display"""

        if self.needs_update:
            self.draw()
            self.needs_update = False

    def set_drawing_to_buffer(self, value: int) -> None:
        """Set drawing to buffer (using ints for booleans)"""

        self.is_drawing_to_buffer = bool(value)

    def clear(self) -> None:
        """Clear all display data"""

        self.clear_image()
        self.clear_buffer()
