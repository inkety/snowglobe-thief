import pygame
from scripts.utils import load_image, clip, swap_color

def text(font_img, desiredText="placeholder",color=(220,220,250),font_specs=[(255,255,255),(0,0,0),(0,0,255),10],font_order=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
    '1','2','3','4','5','6','7','8','9','0',',','.','!','?','+','-','=','\'',
    '"','_','~','<','>','*','|','#','$','&','/','\\','%',':',';','(',')','[',']','{','}',' '], scale=1): 
    lastX = -1
    chars = []
    for x in range(font_img.get_width()):
        if font_img.get_at((x,0)) == font_specs[2]:
            chars.append(clip(font_img,lastX+1,0,x-lastX-1,font_specs[3]))
            lastX = x
    total_length = 0
    final = []

    for char in desiredText:
        if char in font_order:
            final.append(chars[font_order.index(char)])
            total_length += final[-1].get_width()+1
    surf = pygame.Surface((total_length,font_specs[3]))
    x = 0
    for char in final:
        surf.blit(char,(x,0))
        x += char.get_width() + 1
    surf = swap_color(surf,font_specs[0],color)
    surf.set_colorkey((0,0,0))
    surf = pygame.transform.scale(surf, (surf.get_size()[0] * scale, surf.get_size()[1] * scale))
    return surf

def MLText(font_img, glines=["placeholder","second line placeholder","third line placeholder"],color=(220,220,250), spacing=0, scale=1): # multiple lines text
    fontHeight = font_img.get_height()
    lines = []
    for line in glines:
        lines.append(text(line,color,font_img))
    lengths = []
    for line in lines:
        lengths.append(line.get_width())
    surf = pygame.Surface((max(lengths),len(lines)*fontHeight+(len(lines)-1)*spacing))
    for i in range(len(lines)):
        surf.blit(lines[i],(0,i*spacing+i*fontHeight))
    surf.set_colorkey((0,0,0))
    surf = pygame.transform.scale(surf, (surf.get_size()[0] * scale, surf.get_size()[1] * scale))
    return surf