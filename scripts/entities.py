import math
import random
import pygame

from scripts.text import text, MLText

class Particle:
    def __init__(self, pos, speed, angle, size, color, lifespan, fade=0, texture=None):
        if not texture:
            self.image = pygame.Surface((size,size))
            self.color = color
            self.image.fill(self.color)
        else:
            self.image = texture
        self.opacity = 255
        self.x, self.y = pos
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

class ParticleSpawner:
    def __init__(self, pos, interval, texture=None, speed=[1,2], size=1, color=(1,1,1), lifespan=30, fade=1):
        self.texture = texture
        self.interval = interval
        self.pos = list(pos)
        self.speed = speed
        self.size = size
        self.color = color
        self.lifespan = lifespan
        self.fade = fade
        
        self.particles = []
        self.clock = -1
        
    def update(self, offset=[0, 0]):
        self.clock += 1
        if self.clock % self.interval == 0:
            self.particles.append(Particle((self.pos[0] - offset[0], self.pos[1] - offset[1]), random.uniform(self.speed[0], self.speed[1]), random.randint(0, 359), self.size, self.color, self.lifespan, self.fade, self.texture))
        
        self.temp = []
        for particle in self.particles:
            if particle.update() != -1:
                self.temp.append(particle)
        self.particles = self.temp.copy()
    
    def render(self, surf, offset=[0, 0]):
        for particle in self.particles:
            surf.blit(particle.image, (particle.px - offset[0], particle.py - offset[1]))

class PhysicsEntity:
    def __init__(self, game, asset_id, pos, size):
        self.game = game
        self.asset_id = asset_id
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        self.action = ""
        self.anim_offset = [0, 0]
        self.flip = False
        self.set_action("idle")

        self.last_movement = [0, 0]
        self.gravity = 0.1

    def rect(self):
        return pygame.Rect((self.pos[0]), (self.pos[1]), self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.asset_id + "@" + self.action][0].copy()

    def update(self, tilemap, movement=(0, 0)):
        anim_size = self.animation.img().get_size()
        size_tweak = self.animation.size_tweak
        self.size = [anim_size[0] + size_tweak[0], anim_size[1] + size_tweak[1]]

        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        frame_movement = ((movement[0] + self.velocity[0]), (movement[1] + self.velocity[1]))

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(3, self.velocity[1] + self.gravity)

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()
        self.anim_offset = self.animation.anim_offset.copy()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.jumps = 1
        self.jump_buffer = 0
        self.wall_slide = 0
        self.movement = [False, False] # running left and right

        self.jump_effect = False
        self.space_bar = False

        self.slide_counter = 0
        self.dialogue = False

    def update(self, tilemap):
        movement = (self.movement[1] - self.movement[0], 0)
        super().update(tilemap, movement=movement)

        if self.velocity[1] >= 0:
            self.jump_effect = False

        self.air_time += 1
        self.jump_buffer = max(0, self.jump_buffer - 1)

        if self.jump_buffer:
            self.jump(auto=True)

        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 1
        else:
            if self.air_time > 10:
                self.jumps = 0

        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4 and self.velocity[1] > 0:
            self.wall_slide += 1
            self.slide_counter += 1
            self.slide_counter %= 2

            if self.slide_counter == 1:
                self.velocity[1] = 1
            else:
                self.velocity[1] = 0

            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        else:
            self.wall_slide = 0

        if self.wall_slide < 1:
            self.slide_counter = 0
            if self.air_time > 4 and self.velocity[1] < 0:
                self.set_action("rising")
            elif self.air_time > 8 and self.velocity[1] > 0:
                self.set_action("falling")
            elif movement[0] != 0:
                self.set_action("run")
            else:
                self.set_action("idle")

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - (0.1), 0)
        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + (0.1), 0)

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

    def jump(self, auto=False):
        if self.wall_slide > 1:
            if self.flip and self.last_movement[0] < 0:
                if self.space_bar:
                    self.velocity[0] = 1.9
                    self.velocity[1] = -2
                    self.jump_effect = True
                else:
                    self.velocity[0] = 1
                    self.velocity[1] = -1
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                if self.space_bar:
                    self.velocity[0] = -1.9
                    self.velocity[1] = -2
                    self.jump_effect = True
                else:
                    self.velocity[0] = -1
                    self.velocity[1] = -1
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
        elif self.jumps:
            if self.space_bar:
                self.velocity[1] = -2.6
                self.jump_effect = True
            else:
                self.velocity[1] = -1.5
            self.jumps -= 1
            self.air_time = 5
            return True
        else:
            if not auto:
                self.jump_buffer = 13
    
    def vary_jump(self):
        if self.jump_effect == True:
            self.velocity[1] = max(-0.5, self.velocity[1])
            self.jump_effect = False

class InteractEntity:
    def __init__(self, game, asset_id, pos, size):
        self.game = game
        self.asset_id = asset_id
        self.pos = list(pos)
        self.size = size
        
        self.action = ""
        self.anim_offset = [0, 0]
        self.flip = False
        self.set_action("idle")
        
        self.colliding = False

    def rect(self):
        return pygame.Rect((self.pos[0]), (self.pos[1]), self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.asset_id + "@" + self.action][0].copy()

    def update(self):
        anim_size = self.animation.img().get_size()
        size_tweak = self.animation.size_tweak
        self.size = [anim_size[0] + size_tweak[0], anim_size[1] + size_tweak[1]]

        self.animation.update()
        self.anim_offset = self.animation.anim_offset.copy()
        
        if pygame.Rect.colliderect(self.game.player.rect(), self.rect()):
            self.colliding = True
        else:
            self.colliding = False

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (round(self.pos[0] - offset[0] + self.anim_offset[0]), round(self.pos[1] - offset[1] + self.anim_offset[1])))

class Door(InteractEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "door", pos, size)
        self.particles = []
        self.displayText = "[E]"
        
    def update(self):
        super().update()
        
        if self.colliding and self.game.interacting == True:
            self.game.interacting = False
            self.game.transition(text(self.game.assets["font"][0], desiredText="you left the north pole.", color=(255, 255, 255), scale=5), 2)
    
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        if self.colliding:
            text1 = text(self.game.assets["font"][0], desiredText=self.displayText, scale=4, color=(255, 255, 255))
            displayScale = (self.game.display.get_size()[0] / self.game.canvas.get_size()[0])
            renderPos = ((self.pos[0] - offset[0]) * displayScale + text1.get_size()[0]/displayScale, (self.pos[1] - offset[1] - 8) * displayScale)
            self.game.textQueue.append([text1, renderPos])
        
class Snowglobe(InteractEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "snowglobe", pos, size)
    def update(self):
        super().update()

class Sign(InteractEntity):
    def __init__(self, game, pos, size, text="placeholder"):
        super().__init__(game, "sign", pos, size)
        self.text = text
    def update(self):
        super().update()