import cv2 as cv
import numpy as np
from PIL import ImageGrab as ig
from pynput import mouse

ideal_bounds = [(670, 255), (1250, 920)]
game_bounds = [(0, 0), (0, 0)]
template_images = {}
colors = {
    'pellet': (255, 255, 255),
    'power': (0, 255, 255),
    'cherry': (255, 0, 0),
    'pacman': (0, 255, 0),
    'pacman-open': (0, 255, 0),
    'pinky': (0, 0, 255),
    'blinky': (0, 0, 255),
    'inky': (0, 0, 255),
    'clyde': (0, 0, 255),
    'vuln_ghost': (255, 0, 255)
}

def init_game_bounds():
    def on_click(x, y, button, pressed):
        if pressed:
            # mouse down
            game_bounds[0] = (x, y)
        else:
            # mouse up
            game_bounds[1] = (x, y)
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
    templates = ['pacman', 'pacman-open', 'pinky', 'blinky', 'inky', 'clyde', 'power', 'cherry', 'pellet', 'vuln_ghost']
    global template_images
    template_images = {}
    for template in templates:
        template_images[template] = cv.imread(f'templates/{template}.png', cv.IMREAD_UNCHANGED)
        if template_images[template] is None:
            print(f'Error: Could not load template {template}.png')
            exit(1)

def detect_objects(screen):
    for template_name, template_image in template_images.items():
        result = cv.matchTemplate(screen, template_image, cv.TM_SQDIFF_NORMED)
        if template_name in ['pacman', 'pacman-open', 'cherry', 'inky', 'blinky', 'pinky', 'clyde']: # single object
            if result.min() < 0.3:
                _, _, min_loc, _ = cv.minMaxLoc(result)
                top_left = min_loc
                h, w = template_image.shape[:2]
                bottom_right = (top_left[0] + w, top_left[1] + h)
                
                cv.rectangle(screen, top_left, bottom_right, colors[template_name], 1)
                cv.putText(screen, template_name, top_left, cv.FONT_HERSHEY_SIMPLEX, 0.5, colors[template_name], 1)
        else: # multiple objects
            loc = np.where(result < 0.15)
            for pt in zip(*loc[::-1]):
                top_left = pt
                h, w = template_image.shape[:2]
                bottom_right = (top_left[0] + w, top_left[1] + h)
                
                cv.rectangle(screen, top_left, bottom_right, colors[template_name], 1)

def main():
    init_game_bounds()
    load_templates()

    while True:
        screen = get_screen()
        detect_objects(screen)
        cv.imshow('screen', screen)
        if cv.waitKey(10) & 0xFF == ord('q'):
            break
        
    cv.destroyAllWindows()
      
if __name__ == '__main__':
    main()