import sys
import pygame

from scripts.utils import load_image, load_images, Animation, clip, load_spritesheet
from scripts.tilemap import Tilemap
from snowglobe_thief import game_assets

LOAD_FILE = "data/maps/0.json"
TILE_SIZE = 8

class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("editor")
        self.type = "editor"
        self.display_size = (1280,960)
        self.display = pygame.display.set_mode(self.display_size)

        self.render_scales = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.render_scale = self.render_scales[int((len(self.render_scales)-1)/2)]

        self.canvas = pygame.Surface((self.display_size[0] / self.render_scale, self.display_size[1] / self.render_scale))
        self.canvas_size = self.canvas.get_size()

        self.clock = pygame.time.Clock()
        
        self.assets = {}
        for key in game_assets.keys():
            if "tile" in game_assets[key][1]:
                self.assets[key] = game_assets[key]
        
        self.movement = [False,False,False,False]

        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)

        try:
            self.tilemap.load(LOAD_FILE)
        except:
            pass

        self.scroll = [0,0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_part = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ctrl = False
        self.ongrid = True
        self.background = False

    def run(self):
        while True:
            self.canvas.fill((0, 0, 0))

            self.scroll[0] += (self.movement[1] - self.movement[0]) / self.render_scale * 10
            self.scroll[1] += (self.movement[3] - self.movement[2]) / self.render_scale * 10
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.canvas, offset=render_scroll, alpha=255 if not self.background else 80)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][0][self.tile_part].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / self.render_scale, mpos[1] / self.render_scale)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                self.canvas.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.canvas.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid and not self.background:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {"group": self.tile_list[self.tile_group], "part": self.tile_part, "pos": tile_pos}
            if self.clicking and self.ongrid and self.background:
                self.tilemap.background_tiles[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {"group": self.tile_list[self.tile_group], "part": self.tile_part, "pos": tile_pos}
            
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if not self.background:
                    if tile_loc in self.tilemap.tilemap:
                        del self.tilemap.tilemap[tile_loc]
                else:
                    if tile_loc in self.tilemap.background_tiles:
                        del self.tilemap.background_tiles[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["group"]][0][tile["part"]]
                    tile_r = pygame.Rect(tile["pos"][0] - self.scroll[0], tile["pos"][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            #self.canvas.blit(current_tile_img, (5, 5))

            pygame.draw.polygon(self.canvas, (255,255,255), [(-1 - render_scroll[0],0 - render_scroll[1]), (0 - render_scroll[0],-1 - render_scroll[1]), (1 - render_scroll[0],0 - render_scroll[1]), (0 - render_scroll[0],1 - render_scroll[1])])

            # events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if "entity" in self.assets[self.tile_list[self.tile_group]][1]:
                            self.tilemap.entities.append({"group": self.tile_list[self.tile_group], "part": self.tile_part, "pos": (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({"group": self.tile_list[self.tile_group], "part": self.tile_part, "pos": (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    
                    if event.button == 3:
                        self.right_clicking = True

                    if self.shift:
                        if event.button == 4:
                            self.tile_part = (self.tile_part - 1) % len(self.assets[self.tile_list[self.tile_group]][0])
                        if event.button == 5:
                            self.tile_part = (self.tile_part + 1) % len(self.assets[self.tile_list[self.tile_group]][0])

                    elif self.ctrl:
                        if event.button == 4: # enlarge
                            old_size = (self.display_size[0] / self.render_scale, self.display_size[1] / self.render_scale)
                            self.render_scale = self.render_scales[min(self.render_scales.index(self.render_scale) + 1, len(self.render_scales) - 1)]
                            new_size = (self.display_size[0] / self.render_scale, self.display_size[1] / self.render_scale)
                            self.canvas = pygame.Surface(new_size)

                            mpos = pygame.mouse.get_pos()
                            self.scroll[0] += (old_size[0] - new_size[0]) / 2
                            self.scroll[1] += (old_size[1] - new_size[1]) / 2

                        if event.button == 5: # shrink
                            old_size = (self.display_size[0] / self.render_scale, self.display_size[1] / self.render_scale)
                            self.render_scale = self.render_scales[max(self.render_scales.index(self.render_scale) - 1, 0)]
                            new_size = (self.display_size[0] / self.render_scale, self.display_size[1] / self.render_scale)
                            self.canvas = pygame.Surface(new_size)

                            mpos = pygame.mouse.get_pos()
                            self.scroll[0] += (old_size[0] - new_size[0]) / 2
                            self.scroll[1] += (old_size[1] - new_size[1]) / 2

                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_part = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_part = 0

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_b:
                        self.background = not self.background
                    if event.key == pygame.K_t:
                        self.tilemap.autotile(self.tilemap.tilemap if not self.background else self.tilemap.background_tiles)
                    if event.key == pygame.K_o:
                        self.tilemap.save(LOAD_FILE)
                        print("Successfully saved file.")
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = False

            self.display.blit(pygame.transform.scale(self.canvas,self.display.get_size()),(0,0))
            pygame.display.update()
            self.clock.tick(60)

if __name__ == "__main__":
    Editor().run()
