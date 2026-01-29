import pygame
from pathlib import Path
import sys
def resource_path(relative_path: str | Path) -> Path:
    relative_path = Path(relative_path)
    if getattr(sys, "frozen", False) and hasattr(sys, "#_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent
    return str(base_path / relative_path)
pygame.init()
pygame.display.set_caption("VidGet: Lỗi hệ thống")
message = "Lỗi không xác định đã xảy ra."
if len(sys.argv) >= 2:
    message += "\nThông tin chi tiết:\n" + " ".join(sys.argv[1:])

screen = pygame.display.set_mode((400, int(len(message) * 2.3) - int(29*0.2)))
font = pygame.font.Font(resource_path("./fonts/roboto_regular.ttf"), 15)
s_render = font.render(message, True, "#000000", wraplength=400)
running = 1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = 0
            break
    screen.fill("#ffffff")
    screen.blit(s_render, (10, 10))
    pygame.display.flip()
pygame.quit()