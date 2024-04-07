from pydirectinput import press
import random
import cv2 as cv

class Game:
    def __init__(self):
        self.entities = []
        self.board = []
        self.pacman = None
        self.pac_goal = None
        self.bounds = None

    def reset_entities(self):
        self.entities_last = self.entities
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)
        entity.game = self
        if entity.type == 'pacman':
            self.pacman = entity

    def add_node(self, pos):
        node = self.get_node(pos)

        if node is None:
            node = Map_Node(pos)
            self.board.append(node)
        return node
    
    def get_node(self, pos):
        for node in self.board:
            if abs(node.pos[0] - pos[0]) < 20 and abs(node.pos[1] - pos[1]) < 20:
                return node
        return None
    
    def get_closest_node(self, pos):
        closest = None
        closest_dist = 1000000
        for node in self.board:
            dist = abs(node.pos[0] - pos[0]) + abs(node.pos[1] - pos[1])
            if dist < closest_dist:
                closest = node
                closest_dist = dist
        return closest

    def plot_path(self, entity_start, entity_end):
        if entity_start is None or entity_end is None:
            return None
        start = self.get_closest_node(entity_start.pos)
        end = self.get_closest_node(entity_end.pos)
        path = self.a_star(start, end)
        return path
    
    def a_star(self, start, end):
        open_list = []
        closed_list = []
        open_list.append(start)
        start.g = 0
        start.h = start.distance(end)
        start.f = start.h
        bad_nodes = [self.get_closest_node(entity.pos) for entity in self.entities_last if entity.type == 'ghost']
        temp = []
        for bad_node in bad_nodes:
            temp.extend(bad_node.get_bad_node_neighbours(2))
        bad_nodes.extend(temp)

        while len(open_list) > 0:
            current = open_list[0]
            for node in open_list:
                if node.f < current.f:
                    current = node
            open_list.remove(current)
            closed_list.append(current)

            if current == end:
                path = []
                while current != start:
                    path.append(current)
                    current = current.parent
                path.append(start)
                path.reverse()
                return path

            for neighbour in current.get_neighbours():
                if neighbour in closed_list or neighbour in bad_nodes:
                    continue
                if neighbour not in open_list:
                    open_list.append(neighbour)
                    neighbour.g = current.g + 1
                    neighbour.h = neighbour.distance(end)
                    neighbour.f = neighbour.g + neighbour.h
                    neighbour.parent = current
                else:
                    if current.g + 1 < neighbour.g:
                        neighbour.g = current.g + 1
                        neighbour.f = neighbour.g + neighbour.h
                        neighbour.parent = current
        return None
    
    
class Entity:
    def __init__(self, pos):
        self.pos = pos
        self.value = 1
        self.game = None

    def distance(self, entity):
        return abs(entity.pos[0] - self.pos[0]) + abs(entity.pos[1] - self.pos[1])

    def get_neighbours(self, radius = 120, increment = 50):
        neighbours = []
        while len(neighbours) == 0:
            for entity in self.game.entities:
                if entity != self:
                    distance = self.distance(entity)
                    if distance < radius:
                        neighbours.append((entity, distance))
            radius += increment
            if radius > (self.game.bounds[1][1] - self.game.bounds[0][1]):
                break
        return neighbours
    
    # for getting the nearby nodes of ghosts to avoid those nodes as well
    def get_bad_node_neighbours(self, depth=2):
        bad_nodes = []
        for _ in range(depth):
            for neighbor in self.get_neighbours():
                if neighbor not in bad_nodes:
                    bad_nodes.append(neighbor)
            for neighbor in bad_nodes[:]:
                for n in neighbor.get_neighbours():
                    if n not in bad_nodes:
                        bad_nodes.append(n)
        return bad_nodes


class Map_Node(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'node'
        self.neighbour_L = None
        self.neighbour_R = None
        self.neighbour_U = None
        self.neighbour_D = None
        self.g = float('inf')
        self.h = 0
        self.f = 0
        self.parent = None

    def get_neighbours(self):
        neighbours = []
        if self.neighbour_L is not None:
            neighbours.append(self.neighbour_L)
        if self.neighbour_R is not None:
            neighbours.append(self.neighbour_R)
        if self.neighbour_U is not None:
            neighbours.append(self.neighbour_U)
        if self.neighbour_D is not None:
            neighbours.append(self.neighbour_D)
        return neighbours

class Pacman(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'pacman'
        self.template = cv.imread('templates/pacman.png')
        self.old_pos = (0, 0)
        self.last_keystroke = None

    def move(self, new_pos, old_pos):
        self.old_pos = old_pos
        self.pos = new_pos
        
        my_node = self.game.get_closest_node(self.pos)
        if self.game.pac_goal is None or my_node == self.game.pac_goal:
            neighbours = self.get_neighbours()
            neighbours.sort(key = lambda x: x[0].value, reverse = True)
            if len(neighbours) == 0:
                return None
            self.game.pac_goal = neighbours[0][0]

        path = self.game.plot_path(self, self.game.pac_goal)
        if path is not None:
            if len(path) == 1:
                return None
            next_node = path[1]
            if next_node.pos[0] < my_node.pos[0]:
                press('left')
                # print('LEFT')
                self.last_keystroke = 'left'
            elif next_node.pos[0] > my_node.pos[0]:
                press('right')
                # print('RIGHT')
                self.last_keystroke = 'right'
            elif next_node.pos[1] < my_node.pos[1]:
                press('up')
                # print('UP')
                self.last_keystroke = 'up'
            elif next_node.pos[1] > my_node.pos[1]:
                press('down')
                # print('DOWN')
                self.last_keystroke = 'down'
                
        if not self.is_moving() or path is None:
            valid_keys = []
            if self.last_keystroke in ['left', 'right']:
                valid_keys = ['up', 'down']
            elif self.last_keystroke in ['up', 'down']:
                valid_keys = ['left', 'right']
            
            if valid_keys:
                random_key = random.choice(valid_keys)
                press(random_key)
                # print("Pressing {} to attempt to reposition.".format(random_key))
                self.current_keystroke = random_key


        return path
        
    def is_moving(self):
        if self.pos != self.old_pos:
            return True
        else:
            return False
        
class Pellet(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'pellet'

class PowerUp(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'power'
        self.value = 3

class Ghost(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'ghost'
        self.value = -1

class VulnerableGhost(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'vuln_ghost'
        self.value = 5

class Cherry(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'cherry'
        self.value = 4