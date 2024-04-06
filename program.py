import cv2 as cv
import numpy as np
from PIL import ImageGrab as ig
from pynput import mouse
import pacman
import time

game = pacman.Game()
ideal_bounds = [(670, 255), (1250, 920)]
game_bounds = [(0, 0), (0, 0)]
template_images = {}
colors = {
    'pellet': (255, 255, 255),
    'power': (0, 255, 255),
    'cherry': (255, 0, 0),
    'pacman': (0, 255, 0),
    'pacman_open': (0, 255, 0),
    'pacman_open_2': (0, 255, 0),
    'pinky': (0, 0, 255),
    'blinky': (0, 0, 255),
    'inky': (0, 0, 255),
    'clyde': (0, 0, 255),
    'vuln_ghost': (255, 0, 255),
    'vuln_ghost_2': (255, 0, 255)
}

def init_game_bounds():
    def on_click(x, y, button, pressed):
        if pressed:
            # mouse down
            game_bounds[0] = (x, y)
        else:
            # mouse up
            game_bounds[1] = (x, y)
            game.bounds = game_bounds
            return False

    print('Please click and drag over the game bounds.')

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

def get_screen():
    screen = ig.grab(bbox=(game_bounds[0][0], game_bounds[0][1], game_bounds[1][0], game_bounds[1][1]))
    arr = np.array(screen)
    img = cv.cvtColor(arr, cv.COLOR_RGB2BGR)
    # resize to ideal bounds
    img = cv.resize(img, (ideal_bounds[1][0] - ideal_bounds[0][0], ideal_bounds[1][1] - ideal_bounds[0][1]))
    return img

def load_templates():
    templates = ['pacman', 'pacman_open', 'pacman_open_2', 'pinky', 'blinky', 'inky', 'clyde', 'power', 'cherry', 'pellet', 'vuln_ghost', 'vuln_ghost_2']
    global template_images
    template_images = {}
    for template in templates:
        template_images[template] = cv.imread(f'templates/{template}.png', cv.IMREAD_UNCHANGED)
        if template_images[template] is None:
            print(f'Error: Could not load template {template}.png')
            exit(1)

def load_board():
    board = cv.imread('board.png')
    detect_objects(board, load_board=True)

def detect_objects(screen, load_board = False):
    game.reset_entities()

    for template_name, template_image in template_images.items():
        result = cv.matchTemplate(screen, template_image, cv.TM_SQDIFF_NORMED)
        if template_name in ['pacman', 'pacman_open', 'cherry', 'inky', 'blinky', 'pinky', 'clyde']: # single object
            if result.min() < 0.3:
                _, _, min_loc, _ = cv.minMaxLoc(result)
                top_left = min_loc
                h, w = template_image.shape[:2]
                bottom_right = (top_left[0] + w, top_left[1] + h)
                center = (top_left[0] + w // 2, top_left[1] + h // 2)
                
                if template_name in ['inky', 'blinky', 'pinky', 'clyde']:
                    game.add_entity(pacman.Ghost(center, template_name))
                elif template_name in ['pacman', 'pacman_open', 'pacman_open_2']:
                    game.add_entity(pacman.Pacman(center))

                #cv.rectangle(screen, top_left, bottom_right, colors[template_name], 1)
                #cv.putText(screen, template_name, top_left, cv.FONT_HERSHEY_SIMPLEX, 0.5, colors[template_name], 1)
        else: # multiple objects
            loc = np.where(result < 0.15)
            for pt in zip(*loc[::-1]):
                top_left = pt
                h, w = template_image.shape[:2]
                bottom_right = (top_left[0] + w, top_left[1] + h)
                center = (top_left[0] + w // 2, top_left[1] + h // 2)

                if template_name == 'pellet':
                    game.add_entity(pacman.Pellet(center))
                elif template_name == 'power': # FIX: PowerUps being detected multiple times for some reason
                    game.add_entity(pacman.PowerUp(center))
                elif template_name == 'vuln_ghost' or template_name == 'vuln_ghost_2':
                    game.add_entity(pacman.VulnerableGhost(center))
                
                #cv.rectangle(screen, top_left, bottom_right, colors[template_name], 1)
    if load_board:
        for e in game.entities:
            if e.type == 'pellet' or e.type == 'power' or e.type == 'pacman':
                node = game.add_node(e.pos)

                n = e.get_neighbours(50, 10)
                for (entity, dist) in n:
                    if entity.type == 'pellet' or entity.type == 'power' or entity.type == 'pacman':
                        if abs(entity.pos[0] - e.pos[0]) < 10 or abs(entity.pos[1] - e.pos[1] < 10):
                            node2 = game.add_node(entity.pos)
                            if node == node2:
                                continue

                            if entity.pos[0] == e.pos[0]:
                                if entity.pos[1] < e.pos[1]:
                                    node.neighbour_U = node2
                                else:
                                    node.neighbour_D = node2
                            else:
                                if entity.pos[0] < e.pos[0]:
                                    node.neighbour_L = node2
                                else:
                                    node.neighbour_R = node2

def detect_objects_optimized(screen, load_board = False):
    game.reset_entities()

    # Map template names to entity classes
    entity_classes = {
        'inky': pacman.Ghost,
        'blinky': pacman.Ghost,
        'pinky': pacman.Ghost,
        'clyde': pacman.Ghost,
        'pacman': pacman.Pacman,
        'pacman_open': pacman.Pacman,
        'pacman_open_2': pacman.Pacman,
        'pellet': pacman.Pellet,
        'power': pacman.PowerUp,
        'vuln_ghost': pacman.VulnerableGhost,
        'vuln_ghost_2': pacman.VulnerableGhost
    }

    for template_name, template_image in template_images.items():
        result = cv.matchTemplate(screen, template_image, cv.TM_SQDIFF_NORMED)
        h, w = template_image.shape[:2]

        if template_name in ['pacman', 'pacman_open', 'cherry', 'inky', 'blinky', 'pinky', 'clyde']: # single object
            if result.min() < 0.3:
                _, _, min_loc, _ = cv.minMaxLoc(result)
                top_left = min_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                center = (top_left[0] + w // 2, top_left[1] + h // 2)
                
                # Add the entity to the game
                game.add_entity(entity_classes[template_name](center))

        else: # multiple objects
            loc = np.where(result < 0.15)
            for pt in zip(*loc[::-1]):
                top_left = pt
                bottom_right = (top_left[0] + w, top_left[1] + h)
                center = (top_left[0] + w // 2, top_left[1] + h // 2)

                # Add the entity to the game
                game.add_entity(entity_classes[template_name](center))

def move_pacman():
    if (game.pacman is None):
        return
    
    return game.pacman.move()

def draw_neighbours(screen):
    if (game.pacman is None):
        return
    
    close = game.pacman.get_neighbours()
    for (entity, dist) in close:
        # draw on screen
        cv.circle(screen, entity.pos, 10, (0, 255, 255), -1)

def main():
    init_game_bounds()
    load_templates()
    load_board()

    while True:
        stime = time.time()
        atime = time.time()
        screen = get_screen()
        print(f'Get screen: {time.time() - stime}')
        stime = time.time()
        detect_objects_optimized(screen)
        print(f'Detect objects: {time.time() - stime}')
        stime = time.time()
        print(f'Draw neighbours: {time.time() - stime}')
        stime = time.time()
        path = move_pacman()
        stime = time.time()
        print(f'Move pacman: {time.time() - stime}')
        if path is not None:
            for i in range(len(path) - 1):
                cv.line(screen, path[i].pos, path[i + 1].pos, (0, 255, 255), 2)
        #print(f'Move pacman: {time.time() - stime}')
        #print(f'Total time: {time.time() - atime}')
        
        cv.imshow('screen', screen)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
        
    cv.destroyAllWindows()
      
if __name__ == '__main__':
    main()