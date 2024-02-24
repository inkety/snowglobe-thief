import pygame
import json
import math

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 7,
    tuple(sorted([(-1, 0), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = []
for x in range(-2, 3):
    for y in range(-2, 3):
        NEIGHBOR_OFFSETS.append((x, y))

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.background_tiles = {}
        self.offgrid_tiles = []
        self.entities = []
        self.PHYSICS_TILES = set()
        self.AUTOTILE_GROUPS = set()

        for key in self.game.assets.keys():
            if self.game.assets[key][1].count("physics"):
                self.PHYSICS_TILES.add(key)
        for key in self.game.assets.keys():
            if self.game.assets[key][1].count("autotile"):
                self.AUTOTILE_GROUPS.add(key)

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile["group"], tile["part"]) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap.copy():
            tile = self.tilemap[loc]
            if (tile["group"], tile["part"]) in id_pairs:
                matches.append(tile.copy())
                matches[-1]["pos"] = matches[-1]["pos"].copy()
                matches[-1]["pos"][0] *= self.tile_size
                matches[-1]["pos"][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def save(self, path):
        f = open(path, "w")
        json.dump({"tilemap": self.tilemap, "tile_size": self.tile_size, "offgrid": self.offgrid_tiles, "background": self.background_tiles, "entities": self.entities}, f)
        f.close()

    def load(self, path):
        f = open(path, "r")
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data["tilemap"]
        self.tile_size = map_data["tile_size"]
        self.offgrid_tiles = map_data["offgrid"]
        self.background_tiles = map_data["background"]
        self.entities = map_data["entities"]

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ";" + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]["group"] in self.PHYSICS_TILES:
                return self.tilemap[tile_loc]
            
    def tiles_around(self, pos):
        # return a list of locations of the tiles around the position
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def offgrid_tiles_around(self, pos):
        tiles = []
        for tile in self.offgrid_tiles:
            if math.sqrt((tile["pos"][0] - pos[0])**2 + (tile["pos"][1] - pos[1])**2) < 75 and tile["group"] in self.PHYSICS_TILES:
                size = self.game.assets[tile["group"]][0][tile["part"]].get_size()
                tiles.append([tile["pos"], size])
        return tiles

    def physics_rects_around(self, pos):
        # return a list of rects of the tiles around the position
        rects = []
        for tile in self.tiles_around(pos):
            if tile["group"] in self.PHYSICS_TILES:
                rects.append(pygame.Rect(tile["pos"][0] * self.tile_size, tile["pos"][1] * self.tile_size, self.tile_size, self.tile_size))
        for tile in self.offgrid_tiles_around(pos):
            rects.append(pygame.Rect(tile[0][0], tile[0][1], tile[1][0], tile[1][1]))
        return rects

    def autotile(self, tilemap=None):
        tiles = tilemap if tilemap else self.tilemap
        for loc in tiles:
            tile = tiles[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile["pos"][0] + shift[0]) + ";" + str(tile["pos"][1] + shift[1])
                if check_loc in tiles:
                    if tiles[check_loc]["group"] == tile["group"]:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile["group"] in self.AUTOTILE_GROUPS) and (neighbors in AUTOTILE_MAP):
                tile["part"] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0,0), alpha=255):
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.background_tiles:
                    tile = self.background_tiles[loc]
                    img = self.game.assets[tile["group"]][0][tile["part"]]
                    render_pos = (tile["pos"][0] * self.tile_size - offset[0], tile["pos"][1] * self.tile_size - offset[1])
                    if self.game.type == "editor":
                        surf.blit(img, render_pos)
                    elif -self.tile_size <= render_pos[0] <= self.game.canvas_size[0] and -self.tile_size <= render_pos[1] <= self.game.canvas_size[1]:
                        surf.blit(img, render_pos)

        for tile in self.offgrid_tiles:
            img = self.game.assets[tile["group"]][0][tile["part"]].copy()
            img.set_alpha(alpha)
            render_pos = (tile["pos"][0] - offset[0], tile["pos"][1] - offset[1])
            if self.game.type == "editor":
                        surf.blit(img, render_pos)
            elif -self.tile_size <= render_pos[0] <= self.game.canvas_size[0] and -self.tile_size <= render_pos[1] <= self.game.canvas_size[1]:
                surf.blit(img, render_pos)

        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    img = self.game.assets[tile["group"]][0][tile["part"]].copy()
                    img.set_alpha(alpha)
                    render_pos = (tile["pos"][0] * self.tile_size - offset[0], tile["pos"][1] * self.tile_size - offset[1])
                    if self.game.type == "editor":
                        surf.blit(img, render_pos)
                    elif -self.tile_size <= render_pos[0] <= self.game.canvas_size[0] and -self.tile_size <= render_pos[1] <= self.game.canvas_size[1]:
                        surf.blit(img, render_pos)
