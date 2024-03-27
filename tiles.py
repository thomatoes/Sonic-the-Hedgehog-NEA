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
        #Taking the pixels from the image
        # pixels where the alpha (transparency) value is not 0, this means that there is no pixel there and it is transparent
        bitmap = numpy.array(self.image_png)

        bitmap = bitmap[:,:,-1] > 20 #If alpha value > 20 append the pixel to the numpy array
        self.height_map = numpy.zeros(bitmap.shape[1], dtype=int)

        for x, col in enumerate(bitmap.T): #Go through through the array
            for y, is_ground in enumerate(col): 
                if is_ground:
                    self.height_map[x] = int(y)
                    break

        #An array of the heights of the pixel value in each 64x64 px square is returned. This goes from top to bottom
        #Reverse the array so the height is from bottom to top instead
        for i in range(len(self.height_map)):
            self.height_map[i] = 64 - self.height_map[i]
            
    
    def set_angle_array(self,angle_dict):
        # Get angle of terraformed platforms
        #With respect to image path name

        self.angle_array = angle_dict.get(self.image_name, [0]*64) #If not terraformed pad with 0s
    
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
    
    def animate(self): #Loops through the frames of the images for each animated tile
        self.frame_index += 0.15
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames [int(self.frame_index)]

#class for ring entities placed on the map
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
        
#class for spring entities placed on map
class Spring(Tile):
    def __init__(self, size, x, y, display_surface,image):
        super().__init__(size, x, y, display_surface)

        #Image and surface
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

        #General
        self.game = game 
        self.type = "goalpost"

        #Image set up
        self.image= image
        self.rect = self.image.get_rect(topleft=(x,y))
        self.mask = pygame.mask.from_surface(self.image)

        #Animation
        self.frame_index = 0
        self.spin = False
        self.finish = False
        self.animation_offset = (-3,-3) #to account for padding in different images
        self.flip = False

        self.images = game.assets['goalpost/spin'].copy()

    def animation(self):
        #going through the animation of the goal post until completed after a set timeframe
        if self.spin:
            self.frame_index += 0.45
            if self.frame_index>= len(self.images):
                self.frame_index = 0
            self.image = self.images[int(self.frame_index)]
        
        if self.finish:
            self.image = self.game.assets['goalpost/finish'].copy()

class PalmtreeAnimated(AnimatedTile):
    def __init__(self,size,x,y,display_surface,path):
        super().__init__(size,x,y,display_surface,path) #inheriting from animated tile
    
    def animate_slower(self):
        self.frame_index += 0.09
        if self.frame_index >= len(self.frames):
            self.frame_index=0
        self.image = self.frames[int(self.frame_index)]
