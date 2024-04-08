import cv2 as cv
import numpy as np
from PIL import ImageGrab as ig
from pynput import mouse
import pacman
import time
import threading

game = pacman.Game()
ideal_bounds = [(670, 255), (1250, 920)]
game_bounds = [(0, 0), (0, 0)]
template_images = {}
debug_mode = False
draw_nodes_flag = False
draw_neighbours_flag = False
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

    print('Please click and drag over the game bounds in 3...')
    time.sleep(1)
    print('2...')
    time.sleep(1)
    print('1...')
    time.sleep(1)

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
    templates = ['pacman', 'pacman_open', 'pacman_open_2', 'pinky', 'blinky', 'inky', 'clyde', 'power', 'cherry','vuln_ghost', 'vuln_ghost_2', 'pellet']
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
        'vuln_ghost_2': pacman.VulnerableGhost,
        'cherry': pacman.Cherry
    }

    threads = []

    for template_name, template_image in template_images.items():
        def match_template(template_name, template_image):
            t_start = time.time()
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

                    if debug_mode:
                        cv.rectangle(screen, top_left, bottom_right, colors[template_name], 2)

            else: # multiple objects
                loc = np.where(result < 0.15)
                for pt in zip(*loc[::-1]):
                    top_left = pt
                    bottom_right = (top_left[0] + w, top_left[1] + h)
                    center = (top_left[0] + w // 2, top_left[1] + h // 2)

                    # Add the entity to the game
                    game.add_entity(entity_classes[template_name](center))

                    if debug_mode:
                        cv.rectangle(screen, top_left, bottom_right, colors[template_name], 2)
            t_end = time.time()
            #print(f'{template_name} took {t_end - t_start} seconds')
        thread = threading.Thread(target=match_template, args=(template_name, template_image))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if load_board:
        for e in game.entities:
            if e.type == 'pellet' or e.type == 'power' or e.type == 'pacman':
                node = game.add_node(e.pos)

                n = e.get_neighbours(50, 10)
                for (entity, dist) in n:
                    if entity.type == 'pellet' or entity.type == 'power' or entity.type == 'pacman':
                        if abs(entity.pos[0] - e.pos[0]) < 1 or abs(entity.pos[1] - e.pos[1] < 1):
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

def move_pacman(screen):
    if (game.pacman is None):
        return
    new_pos = get_new_position(get_screen(), game.pacman.template)
    if new_pos is None:
        new_pos = game.pacman.pos
    return game.pacman.move(new_pos, game.pacman.pos)

def draw_neighbours(screen):
    if (game.pacman is None):
        return
    
    close = game.pacman.get_neighbours()
    for (entity, dist) in close:
        # draw on screen
        cv.circle(screen, entity.pos, 10, (0, 255, 255), -1)

def draw_nodes(screen):
    for node in game.board:
        cv.circle(screen, node.pos, 5, (0, 255, 255), -1)
        if node.neighbour_U is not None:
            cv.line(screen, node.pos, node.neighbour_U.pos, (0, 255, 255), 2)
        if node.neighbour_D is not None:
            cv.line(screen, node.pos, node.neighbour_D.pos, (0, 255, 255), 2)
        if node.neighbour_L is not None:
            cv.line(screen, node.pos, node.neighbour_L.pos, (0, 255, 255), 2)
        if node.neighbour_R is not None:
            cv.line(screen, node.pos, node.neighbour_R.pos, (0, 255, 255), 2)

def get_new_position(screen, template):
    result = cv.matchTemplate(screen, game.pacman.template, cv.TM_SQDIFF_NORMED)
    h, w = template.shape[:2]
    if result.min() < 0.3:
                _, _, min_loc, _ = cv.minMaxLoc(result)
                top_left = min_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                center = (top_left[0] + w // 2, top_left[1] + h // 2)
                
                cv.rectangle(screen, top_left, bottom_right, (255, 0, 0), 2)
    
                return center

def main():
    global debug_mode
    global draw_nodes_flag
    global draw_neighbours_flag
    
    init_game_bounds()
    load_templates()
    load_board()

    while True:
        screen = get_screen()
        detect_objects(screen)
        path = move_pacman(screen)
        if draw_nodes_flag:
            draw_nodes(screen)
        if draw_neighbours_flag:
            draw_neighbours(screen)

        if path is not None:
            for i in range(len(path) - 1):
                cv.line(screen, path[i].pos, path[i + 1].pos, (0, 255, 255), 2)
        
        cv.imshow('screen', screen)
        key = cv.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            debug_mode = not debug_mode
        elif key == ord('b'):
            draw_nodes_flag = not draw_nodes_flag
        elif key == ord('n'):
            draw_neighbours_flag = not draw_neighbours_flag
        
    cv.destroyAllWindows()
      
if __name__ == '__main__':
    main()