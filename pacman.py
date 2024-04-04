class Game:
    def __init__(self):
        self.entities = []
        self.pacman = None

    def reset_entities(self):
        self.entities_last = self.entities
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)
        entity.game = self
        if entity.type == 'pacman':
            self.pacman = entity

    def get_ghost(self, name):
        for entity in self.entities:
            if entity.type == 'ghost' and entity.name == name:
                return entity
        return None


class Entity:
    def __init__(self, pos):
        self.pos = pos
        self.value = 1
        self.game = None

    def distance(self, entity):
        return abs(entity.pos[0] - self.pos[0]) + abs(entity.pos[1] - self.pos[1])

    def get_neighbours(self, radius = 50):
        neighbours = []
        while len(neighbours) == 0:
            for entity in self.game.entities:
                if entity != self:
                    distance = self.distance(entity)
                    if distance < radius:
                        neighbours.append((entity, distance))
            radius += 50
        return neighbours
    
class Pacman(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'pacman'

    def move(self):
        neighbours = self.get_neighbours()
        # sort by dist
        neighbours.sort(key=lambda x: x[1])

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
    def __init__(self, pos, name):
        super().__init__(pos)
        self.name = name
        self.type = 'ghost'
        self.value = -1

class VulnerableGhost(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = 'vuln_ghost'
        self.value = 5