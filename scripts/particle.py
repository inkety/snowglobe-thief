class Particle:
    def __init__(self, x, y, speed, angle, size, color, lifespan, fade=0, texture=None):
        if not texture:
            self.image = pygame.Surface((size,size))
            self.color = color
            self.image.fill(self.color)
        else:
            self.image = texture
        self.opacity = 255
        self.x, self.y = x, y
        self.px, self.py = int(self.x), int(self.y)
        self.size = size
        self.speed = speed
        self.angle = angle
        self.age = 0
        self.lifespan = lifespan
        self.fade = fade

    def update(self):
        self.age += 1

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.px, self.py = int(self.x), int(self.y)

        self.opacity -= self.fade
        if self.opacity <= 0:
            return -1
        self.image.set_alpha(self.opacity)

        if self.age > self.lifespan:
            return -1

    def render(self, surf):
        surf.blit(self.image, (self.px, self.py))
