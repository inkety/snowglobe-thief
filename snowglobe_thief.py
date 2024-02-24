import sys
import random
import time

import pygame

from scripts.text import text
from scripts.utils import load_image, load_images, Animation, load_spritesheet
from scripts.entities import Player, Door, Snowglobe, Sign
from scripts.tilemap import Tilemap

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Snowglobe Thief")
        self.type = "game"

        self.display_size = (1000, 750)
        self.canvas_size = (160, 120)

        self.display = pygame.display.set_mode(self.display_size)
        self.canvas = pygame.Surface(self.canvas_size)

        self.fps = 60
        self.clock = pygame.time.Clock()
        self.last_time = time.time()

        self.assets = {
            "snow": (load_spritesheet(load_image("tiles/fg/snow.png")), ["tile", "autotile", "physics"]),
            "stone": (load_spritesheet(load_image("tiles/fg/stone.png")), ["tile", "autotile", "physics"]),
            "cobblestone": (load_spritesheet(load_image("tiles/fg/cobblestone.png")), ["tile", "autotile", "physics"]),
            "brick": (load_spritesheet(load_image("tiles/fg/brick.png")), ["tile", "autotile", "physics"]),
            
            "barrier": ([pygame.Surface((8, 8))],["tile", "physics"]),

            "snow_bg": (load_spritesheet(load_image("tiles/bg/snow_bg.png")), ["tile", "autotile"]),

            "resize": (load_images("tiles/resize"), ["tile", "physics"]),
            "decor": (load_images("tiles/decor"), ["tile"]),

            "spawners": (load_images("tiles/spawners"), ["tile", "entity"]),

            "player@idle": (Animation(load_images("entities/player/idle"), img_dur=6, anim_offset=[-1, -2], size_tweak=[-2, -2]), ["animation"]),
            "player@run": (Animation(load_images("entities/player/run"), img_dur=4, anim_offset=[-1, -2], size_tweak=[-2, -2]), ["animation"]),
            "player@rising": (Animation(load_images("entities/player/rising"), img_dur=6, anim_offset=[-1, -2], size_tweak=[-2, -2]), ["animation"]),
            "player@falling": (Animation(load_images("entities/player/falling"), img_dur=6, anim_offset=[-1, -2], size_tweak=[-2, -2]), ["animation"]),
            "player@wall_slide": (Animation(load_images("entities/player/wall_cling"), img_dur=15, anim_offset=[0, -2], size_tweak=[0, -1]), ["animation"]),

            "door@idle": (Animation(load_images("entities/door/idle")), ["animation"]),
            "snowglobe@idle": (Animation(load_images("entities/snow_globe/idle")), ["animation"]),
            "sign@idle": (Animation(load_images("entities/sign/idle")), ["animation"]),

            "particle.warning": (load_image("particle/warning.png"), ["particle"]),

            "background": (load_image("background.png"), ["background"]),

            "font": (load_image("pixel_font.png"), ["font"])
        }

        self.player = Player(self, (0,0), [6,14])
        self.particles = []
        self.exits = []
        self.snowglobes = []
        self.signs = []
        
        self.cam_speed = 13 # LOWER = FASTER

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        try:
            self.load_level(self.level)
        except FileNotFoundError:
            print(f"Level {self.level} not found.")

        self.screenshake = 0

        self.scroll = [0, 0]
        self.scroll[0] += (self.player.rect().centerx - self.canvas.get_width()/2 - self.scroll[0])
        self.scroll[1] += (self.player.rect().centery - self.canvas.get_height()/2 - self.scroll[1])

        self.cur_fps = 0
        self.frame_counter = 0
        self.textQueue = []
        self.fadeTextQueue = []
        self.interacting = False
        #self.testSpawner = ParticleSpawner((0,0), 3, color=(255,255,255), speed=[0.5,0.7], lifespan=15)

    def load_level(self, map_id):
        self.player.air_time = 0
        self.player.jumps = 1
        self.player.wall_cling = 0

        self.tilemap.load("data/maps/" + str(map_id) + ".json")

        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1), ("spawners", 2)]):
            if spawner["part"] == 0:
                self.player.pos = spawner["pos"]
            if spawner["part"] == 1:
                self.exits.append(Door(self, spawner["pos"], [9, 19]))
            if spawner["part"] == 2:
                self.snowglobes.append(Snowglobe(self, spawner["pos"], [8, 10]))
            if spawner["part"] == 3:
                self.signs.append(Sign(self, spawner["pos"], [10, 10]))

        self.particles = []
        
    def transition(self, showText, waitTime):
        displayTextSurf = showText
        ds = self.display.get_size()
        dtss = displayTextSurf.get_size()
        
        transitionSurf = pygame.Surface(self.display.get_size())
        transitionSurf.fill((1, 1, 1))
        pointAltitude = 250
        y = -ds[1] - pointAltitude
        stage = 1
        self.player.movement = [0, 0]
        
        while True:
            self.canvas.blit(self.assets["background"][0], (0, 0))
            self.screenshake = max(0, self.screenshake - 1)

            self.scroll[0] += (self.player.rect().centerx - self.canvas.get_width()/2 - self.scroll[0]) / self.cam_speed 
            self.scroll[1] += (self.player.rect().centery - self.canvas.get_height()/2 - self.scroll[1]) / self.cam_speed
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.canvas, offset=render_scroll)

            for group in [self.snowglobes, self.exits, self.signs]:
                for entity in group:
                    entity.update()
                    entity.render(self.canvas, render_scroll)

            self.player.update(self.tilemap)
            self.player.render(self.canvas, offset=render_scroll)
            
            now = time.time()
            
            if stage == 1:
                y += ds[1]/10
                if y >= 0:
                    stage = 2
                    begin = time.time()
            if stage == 2:
                if now - begin > waitTime:
                    stage = 3
            if stage == 3:
                y += ds[1]/10
                if y >= ds[1]:
                    self.textQueue.clear()
                    return
                
            self.display.blit(pygame.transform.scale(self.canvas, self.display.get_size()), (0, 0))
            pPoints = [(0, y - pointAltitude - 50), (ds[0]/2, y - 50),(ds[0], y - pointAltitude - 50), (ds[0], ds[1] + y + 50), (ds[0]/2, ds[1] + y + pointAltitude + 50), (0, ds[1] + y + 50)]
            pygame.draw.polygon(self.display, (0, 0, 0), pPoints)
            self.display.blit(displayTextSurf, (ds[0]/2 - dtss[0]/2, ds[1]/2 + y - dtss[1]/2 - 50))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            pygame.display.update()
            self.clock.tick(self.fps)
            
    def run(self):
        while True:
            self.canvas.blit(self.assets["background"][0], (0, 0))
            self.screenshake = max(0, self.screenshake - 1)

            self.scroll[0] += (self.player.rect().centerx - self.canvas.get_width()/2 - self.scroll[0]) / self.cam_speed 
            self.scroll[1] += (self.player.rect().centery - self.canvas.get_height()/2 - self.scroll[1]) / self.cam_speed
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.canvas, offset=render_scroll)

            for group in [self.snowglobes, self.exits, self.signs]:
                for entity in group:
                    entity.update()
                    entity.render(self.canvas, render_scroll)

            self.player.update(self.tilemap)
            self.player.render(self.canvas, offset=render_scroll)

            # PLAYER HITBOX
            #pygame.draw.rect(self.canvas, (255, 255, 0), (self.player.pos[0] - render_scroll[0], self.player.pos[1] - render_scroll[1], self.player.size[0], self.player.size[1]))

            #print(pygame.Rect.colliderect(self.player.rect(), self.exits[0].rect()))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    # Movement
                    if event.key in [pygame.K_a, pygame.K_LEFT]:
                        self.player.movement[0] = True
                    if event.key in [pygame.K_d, pygame.K_RIGHT]:
                        self.player.movement[1] = True
                    if event.key in [pygame.K_SPACE]:
                        self.player.space_bar = True
                        self.player.jump()

                    # Other
                    if event.key in [pygame.K_e]:
                        self.interacting = True
                    if event.key in [pygame.K_t]:
                        self.transition(text(self.assets["font"][0], desiredText="you have pressed T.", color=(255, 255, 255), scale=5), 2)
                    
                if event.type == pygame.KEYUP:
                    # Movement
                    if event.key in [pygame.K_a, pygame.K_LEFT]:
                        self.player.movement[0] = False
                    if event.key in [pygame.K_d, pygame.K_RIGHT]:
                        self.player.movement[1] = False
                    if event.key in [pygame.K_SPACE]:
                        self.player.space_bar = False
                        self.player.vary_jump()

                    # Other
                    if event.key in [pygame.K_e]:
                        self.interacting = False

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.display.blit(pygame.transform.scale(self.canvas,self.display.get_size()), screenshake_offset)
            
            for toShow in self.textQueue:
                self.display.blit(toShow[0], toShow[1])
            self.textQueue.clear()
            
            pygame.display.update()
            self.clock.tick(self.fps)

if __name__ == "__main__":
    Game().run()
else:
    game_assets = Game().assets