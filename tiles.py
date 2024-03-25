import pygame
import numpy
from PIL import Image
from camera import *
from utilities import *
from support import import_graphics
from game_data import tile_angles

class Tile(pygame.sprite.Sprite):
    def __init__(self,size,x,y,display_surface):
        #pos for where, size for how large
        super().__init__() #Inherit from pygame Sprite class
        
        self.tile_size = size
        self.display_surface = display_surface
        self.offset = pygame.math.Vector2()
    
        self.image = pygame.Surface((size,size))
        self.rect = self.image.get_rect(topleft = (x,y)) #To position tiles using pygame coordinate axes
          
    def update(self):
        self.offset = self.rect.topleft - self.offset #To move it with the camera
        self.display_surface.blit(self.image,self.offset)

class TerrainTile(pygame.sprite.Sprite):
    def __init__(self,size,x,y,tile_surface,tile_filename):
        super().__init__()

        #General
        self.tile_size = size

        #Image setup
        self.image = tile_surface #For pygame surface
        self.image_name = tile_filename #For reference
        self.image_path = 'levels/level_data/tiles/'+tile_filename #To get path
        self.image_png = Image.open(self.image_path)

        #Coordinate positioning
        self.rect_img = pygame.Surface((size,size))
        self.rect = self.rect_img.get_rect(topleft = (x,y)) #Positioning of tiles

        self.set_angle_array(tile_angles)
        self.image_to_height_array()
    
    def image_to_height_array(self):
        bitmap = numpy.array(self.image_png)

        bitmap = bitmap[:,:,-1] > 20
        self.height_map = numpy.zeros(bitmap.shape[1], dtype=int)

        for x, col in enumerate(bitmap.T):
            for y, is_ground in enumerate(col): # 
                if is_ground:
                    self.height_map[x] = int(y)
                    break
        
        for i in range(len(self.height_map)):
            self.height_map[i] = 64 - self.height_map[i]
            
    
    def set_angle_array(self,angle_dict):
        # Get image path
        #With respect to angle dict

        self.angle_array = angle_dict.get(self.image_name, [0]*64)
    
    def get_angle_array(self):
        return (self.angle_array)

    def get_height_map(self):
        return (self.height_map)
    
    def get_rect(self):
        return (self.rect)

    def get_tile_id(self):
        angles = self.get_angle_array()
        height_map = self.get_height_map()
        rect = self.get_rect()

        return ((rect), height_map, angles)
    
class StaticTile(Tile):
    def __init__(self,size,x,y,display_surface,surface):
        super().__init__(size,x,y,display_surface) #Inherit from initial Tile class
        self.image = surface #Add image attribute
    
    def get_size(self):
        return self.image.get_size()

class AnimatedTile(Tile):
    def __init__(self,size,x,y,display_surface,path):
        super().__init__(size,x,y,display_surface)
        self.frames = import_graphics(path)
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
    
    def animate(self):
        self.frame_index += 0.15
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames [int(self.frame_index)]

class Rings(AnimatedTile):
    def __init__(self,size,x,y,display_surface,path):
        super().__init__(size,x,y,display_surface,path)
        self.mask = pygame.mask.from_surface(self.image)
    
        self.after_frames = [
            pygame.image.load('levels/level_data/rings/collect/collect1.png').convert_alpha(),
            pygame.image.load('levels/level_data/rings/collect/collect2.png').convert_alpha(),
        ]
    
    def collect_ring(self):
        self.frames = []
        self.frames = self.collect_images #play collect ring animation
        self.frame_index = 0
        self.frame_index += 0.3

        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
        

class Spring(Tile):
    def __init__(self, size, x, y, display_surface,image):
        super().__init__(size, x, y, display_surface)

        self.image = image
        self.rect = self.image.get_rect(topleft = (x,y))
        self.mask = pygame.mask.from_surface(self.image)    
    
    def play_animation(self,game):
        self.animation = game.assets['spring/recoil'].copy()
    
    def render(self,surface):
        surface.blit(self.animation.img(), self.rect.topleft)

class GoalPost(Tile,Animation):
    def __init__(self,size,x,y,display_surface,image,game):
        super().__init__(size,x,y,display_surface)

        self.game = game 
        self.type = "goalpost"
        
        self.image= image
        self.rect = self.image.get_rect(topleft=(x,y))
        self.mask = pygame.mask.from_surface(self.image)

        self.frame_index = 0
        self.spin = False
        self.finish = False

        #animation
        self.animation_offset = (-3,-3) #to account for padding in different images
        self.flip = False

        self.images = game.assets['goalpost/spin'].copy()

    def animation(self):
        if self.spin:
            self.frame_index += 0.45
            if self.frame_index>= len(self.images):
                self.frame_index = 0
            self.image = self.images[int(self.frame_index)]
        
        if self.finish:
            self.image = self.game.assets['goalpost/finish'].copy()

class PalmtreeAnimated(AnimatedTile):
    def __init__(self,size,x,y,display_surface,path):
        super().__init__(size,x,y,display_surface,path)
    
    def animate_slower(self):
        self.frame_index += 0.09
        if self.frame_index >= len(self.frames):
            self.frame_index=0
        self.image = self.frames[int(self.frame_index)]