import pygame
import sys

# --- CONFIGURATION ---
# The size of the window you draw in
WINDOW_SIZE = 800 
# The size of the actual game world (from your racing game code)
GAME_MAP_SIZE = 20000 

# Scale factor: 1 pixel on screen = 7.5 pixels in the game
SCALE = GAME_MAP_SIZE / WINDOW_SIZE

pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Track Designer - Draw with Mouse!")
font = pygame.font.SysFont("Arial", 18)
clock = pygame.time.Clock()

points = [] # Stores the raw coordinates
closed_loop = False

def get_game_coords(screen_pos):
    """Converts screen (800x800) click to game (6000x6000) coord"""
    return (int(screen_pos[0] * SCALE), int(screen_pos[1] * SCALE))

def get_screen_coords(game_pos):
    """Converts game (6000x6000) coord back to screen for drawing"""
    return (int(game_pos[0] / SCALE), int(game_pos[1] / SCALE))

running = True
print("--- TRACK DESIGNER STARTED ---")
print("LEFT CLICK: Add Point | RIGHT CLICK: Undo | SPACE: Close Loop | ENTER: Print Code")

while running:
    screen.fill((30, 30, 30)) # Dark background
    
    # Draw Grid (Optional, helps with alignment)
    for i in range(0, WINDOW_SIZE, 100):
        pygame.draw.line(screen, (50, 50, 50), (i, 0), (i, WINDOW_SIZE))
        pygame.draw.line(screen, (50, 50, 50), (0, i), (WINDOW_SIZE, i))

    mx, my = pygame.mouse.get_pos()

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                if not closed_loop:
                    points.append(get_game_coords((mx, my)))
            elif event.button == 3: # Right Click
                if len(points) > 0:
                    points.pop()
                    closed_loop = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: # Close Loop
                if len(points) > 2:
                    # Make sure the last point is exactly the start point
                    if points[-1] != points[0]:
                        points.append(points[0])
                    closed_loop = True
            
            if event.key == pygame.K_RETURN: # Print Code
                print("\n" + "="*40)
                print("COPY THIS LIST INTO YOUR GAME CODE:")
                print("="*40)
                print("points = [")
                for p in points:
                    print(f"    {p},")
                print("]")
                print("="*40 + "\n")

    # --- DRAWING ---
    
    # Draw the lines connecting your clicks
    if len(points) > 0:
        # Draw points
        for i, p in enumerate(points):
            sp = get_screen_coords(p)
            color = (0, 255, 0) if i == 0 else (255, 255, 255) # Start point is Green
            pygame.draw.circle(screen, color, sp, 5)
            
        # Draw lines
        if len(points) > 1:
            screen_points = [get_screen_coords(p) for p in points]
            pygame.draw.lines(screen, (255, 255, 0), False, screen_points, 2)
            
        # Draw "Rubber band" line to mouse cursor (preview)
        if not closed_loop:
            last_sp = get_screen_coords(points[-1])
            pygame.draw.line(screen, (100, 100, 100), last_sp, (mx, my), 1)

    # UI Text
    coord_text = f"Mouse Game Coords: {get_game_coords((mx, my))}"
    instr_text = "L-Click: Add | R-Click: Undo | SPACE: Close Loop | ENTER: Generate Code"
    
    screen.blit(font.render(coord_text, True, (0, 255, 255)), (10, 10))
    screen.blit(font.render(instr_text, True, (200, 200, 200)), (10, WINDOW_SIZE - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()