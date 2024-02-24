import pygame
import os

from pygame.locals import *

BASE_IMG_PATH = 'data/images/'

def load_image(path, colorkey=(0, 0, 0)):
    path = BASE_IMG_PATH + path if not path.startswith("*") else path.replace("*", "")
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img

def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

def clip(surf,x,y,x_size,y_size):
    handle_surf = surf.copy()
    clipR = pygame.Rect(x,y,x_size,y_size)
    handle_surf.set_clip(clipR)
    image = surf.subsurface(handle_surf.get_clip())
    return image.copy()

def swap_color(img,old_c,new_c):
    img.set_colorkey(old_c)
    surf = img.copy()
    surf.fill(new_c)
    surf.blit(img,(0,0))
    return surf

class Animation:
    def __init__(self, images, img_dur=5, anim_offset=[0, 0], size_tweak = [0, 0], loop=True):
        self.images = images
        self.img_duration = img_dur
        self.loop = loop
        self.done = False
        self.frame = 0
        self.anim_offset = anim_offset
        self.size_tweak = size_tweak

    def copy(self):
        return Animation(self.images, self.img_duration, self.anim_offset, self.size_tweak, self.loop)

    def update(self, dt=1):
        if self.loop:
            self.frame = (self.frame + 1 * dt) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1 * dt, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self, dt=1):
        cf = self.frame / self.img_duration
        cf = int(cf % (len(self.images)))
        return self.images[cf]

def load_spritesheet(spritesheet, colorkey=(0, 0, 0), two_d=False):
    rows = []
    sprites = []
    for y in range(spritesheet.get_height()):
        c = spritesheet.get_at((0,y))
        c = (c[0],c[1],c[2])
        if c == (255, 255, 0):
            rows.append(y)
    for row in rows:
        row_content = []
        for x in range(spritesheet.get_width()):
            c = spritesheet.get_at((x,row))
            c = (c[0],c[1],c[2])
            if c == (255,0,255):
                x2 = 0
                while True:
                    x2 += 1
                    c = spritesheet.get_at((x+x2,row))
                    c = (c[0],c[1],c[2])
                    if c == (0,255,255):
                        break
                y2 = 0
                while True:
                    y2 += 1
                    c = spritesheet.get_at((x,row+y2))
                    c = (c[0],c[1],c[2])
                    if c == (0,255,255):
                        break
                img = clip(spritesheet,x+1,row+1,x2-1,y2-1)
                img.set_colorkey(colorkey)
                row_content.append(img)
        sprites.append(row_content)
    if not two_d:
        one_d = []
        for row in sprites:
            for sprite in row:
                one_d.append(sprite)
        return one_d
    return sprites
