import cv2 as cv
from PIL import ImageGrab as ig
import numpy as np

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
    'clyde': (0, 0, 255)
}

def get_screen():
    screen = ig.grab(bbox=(670, 255, 1250, 920))
    img = np.array(screen)
    img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    return img

def load_templates():
    templates = ['pacman', 'pacman-open', 'pinky', 'blinky', 'inky', 'clyde', 'power', 'cherry', 'pellet']
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