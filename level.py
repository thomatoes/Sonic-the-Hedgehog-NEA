import pygame

from tiles import  StaticTile, Rings, PalmtreeAnimated, TerrainTile,Spring, GoalPost
from utilities import tile_size
from game_data import tile_angles
from camera import *
from player import PhysicsEntity, Chao, Enemy
from support import import_csv_layout, import_cut_graphics, import_graphics, import_file_names, load_image

class Level:
    def __init__(self,game,level_data,surface):
        #general setup
        self.display_surface = surface
        self.cell_size = (tile_size, tile_size)
        self.game = game
        self.level_data = level_data

        self.terrain_filename_list = []

        #terrain setup - layer number 6
        #rect/mask dictionary
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.terrain_sprites = self.create_tile_group(terrain_layout,'terrain')
        self.rect_dict = self.create_rect_dictionary()
        self.height_dict = self.create_height_dictionary()
        self.mask_dict = self.create_mask_dictionary()
        self.angle_dict = self.create_angle_dictionary()

        #grass setup - layer number 4
        grass_layout = import_csv_layout(level_data['grass fg'])
        self.grass_sprites = self.create_tile_group(grass_layout, 'grass')

        #background tiles - layer number 11
        background_tiles_layout = import_csv_layout(level_data['background tiles'])
        self.background_tile_sprites = self.create_tile_group(background_tiles_layout, 'background tiles')

        #background sand tiles - layer number 23
        background_sand_tiles_layout = import_csv_layout(level_data['background sand'])
        self.background_sand_sprites = self.create_tile_group(background_sand_tiles_layout,'background sand')

        #assets tiles - layer number 8
        assets_layout = import_csv_layout(level_data['assets'])
        self.assets_sprites = self.create_tile_group(assets_layout, 'assets')

        #rings tiles
        rings_layout = import_csv_layout(level_data['rings'])
        self.rings_sprites = self.create_tile_group(rings_layout, 'rings')
        #self.setup_level(level_data)

        #springs
        springs_layout = import_csv_layout(level_data['springs'])
        self.springs_sprites = self.create_tile_group(springs_layout,'spring')

        #chao
        chao_layout = import_csv_layout(level_data['chao'])
        self.chao_sprites = self.create_tile_group(chao_layout,'chao')

        #goalpost
        goalpost_layout = import_csv_layout(level_data['setup'])
        self.goalpost_sprite = self.create_tile_group(goalpost_layout,'goalpost')

        #enemy
        enemy_layout = import_csv_layout(level_data['enemies'])
        self.enemy_sprites = self.create_tile_group(enemy_layout,'enemy')

        #palmtrees - seperated into static and animated 
        palmtrees_bg_static_layout = import_csv_layout(level_data['palmtrees bg static'])
        self.palmtrees_bg_static_sprites = self.create_tile_group(palmtrees_bg_static_layout, 'palmtrees static')
        palmtrees_bg_animated_layout = import_csv_layout(level_data['palmtrees bg animated'])
        self.palmtrees_bg_animated_sprites = self.create_tile_group(palmtrees_bg_animated_layout, 'palmtrees animated')

    def create_tile_group(self,layout,type):
        sprite_group = pygame.sprite.Group()

        for row_index,row in enumerate(layout):
            for col_index,val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    if type == 'terrain':
                        terrain_tile_list_image = import_graphics('levels/level_data/tiles') 
                        terrain_image_list_names = import_file_names('levels/level_data/tiles')
                        
                        tile_surface = terrain_tile_list_image[int(val)]
                        tile_filename = terrain_image_list_names[int(val)]
                        
                        #For reference only -----
                        self.terrain_filename_list.append((tile_filename, (x,y)))
                        #----------------------------------------
                         
                        sprite = TerrainTile(64,x,y-48,tile_surface,tile_filename)
                    
                    if type == 'grass':
                        grass_tile_list = import_graphics('levels/level_data/deco/grass_deco')
                        tile_surface = grass_tile_list[int(val)]
                        sprite = StaticTile(64,x,y-48,self.display_surface,tile_surface)
                    
                    if type == 'assets':
                        assets_tile_list = import_graphics('levels/level_data/deco/assets')
                        tile_surface = assets_tile_list[int(val)]
                        sprite = StaticTile(64,x,y-48,self.display_surface,tile_surface)
                    
                    if type == 'background tiles':
                        background_tile_list = import_cut_graphics('levels/level_data/tiles/13grass04.png', tile_size)
                        tile_surface = background_tile_list[int(val)]
                        sprite = StaticTile(tile_size,x,y,self.display_surface,tile_surface)
                    
                    if type == 'background sand':
                        background_sand_list = import_graphics('levels/level_data/tiles')
                        tile_surface =background_sand_list[int(val)]
                        sprite = StaticTile(tile_size,x,y-48,self.display_surface,tile_surface)
                    
                    if type == 'rings':
                        sprite = Rings(tile_size, x,y, self.display_surface, 'levels/level_data/rings/ring')
                    
                    if type == 'palmtrees static':
                        palmtree_tile_list = import_graphics('levels/level_data/deco/palmtrees/images')
                        tile_surface = palmtree_tile_list[int(val)]
                        sprite = StaticTile(tile_size,x,y-48,self.display_surface, tile_surface)
                    
                    if type == 'palmtrees animated':
                        if int(val)==0:
                            sprite = PalmtreeAnimated(tile_size,x,y-48,self.display_surface,'levels/level_data/deco/palmtrees/animated/palmtree1')
                        elif int(val)==3:
                            sprite = PalmtreeAnimated(tile_size,x,y-48,self.display_surface,'levels/level_data/deco/palmtrees/animated/palmtree4')
                    
                    if type == 'spring':
                        image = load_image('springs/spring1.png')
                        sprite = Spring(tile_size,x,y-48,self.display_surface,image)
                    
                    if type == 'chao':
                        image = load_image('chao/w_chao01.png')
                        sprite = Chao(self.game,(x,y-32),(13,21),image)
                    
                    if type == 'goalpost':
                        image = load_image('goalpost/goalpost1.png')
                        sprite = GoalPost(tile_size,x,y-48,self.display_surface,image, self.game)

                    if type == 'enemy':
                        image = load_image('enemies/idle/left_stand1.png')
                        sprite = Enemy(self.game,(x,y),(20,20),image)
                    sprite_group.add(sprite)
        
        return sprite_group
    
    def reset_entity(self):
        #rings tiles
        rings_layout = import_csv_layout(self.level_data['rings'])
        self.rings_sprites = self.create_tile_group(rings_layout, 'rings')
        
        #enemy
        enemy_layout = import_csv_layout(self.level_data['enemies'])
        self.enemy_sprites = self.create_tile_group(enemy_layout,'enemy')
    
    def reset_entity_pos(self,layout,type):
        sprite_group = pygame.sprite.Group()

        for row_index,row in enumerate(layout):
            for col_index,val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    if type == 'rings':
                        sprite = Rings(tile_size, x,y, self.display_surface, 'levels/level_data/rings/ring')
                    
                    if type == 'enemy':
                        image = load_image('enemies/idle/left_stand1.png')
                        sprite = Enemy(self.game,(x,y),(20,20),image)
            
            sprite_group.add(sprite)
        
        return sprite_group
    
    
    def create_rect_dictionary(self):
        rect_dict = {}
        for tile in self.terrain_sprites:
            x,y = tile.get_tile_id()[0][0], tile.get_tile_id()[0][1]
            rect_dict[(x,y)] = tile.get_tile_id()[0] #Rect val
        
        return rect_dict
    
    def create_height_dictionary(self):
        height_dict = {}
        for tile in self.terrain_sprites:
            x,y = tile.get_tile_id()[0][0], tile.get_tile_id()[0][1]
            height_dict[(x,y)] = tile.get_tile_id()[1] #Height val
        
        return height_dict
        
    def create_mask_dictionary(self):
        mask_dict = {}
        for tile in self.terrain_sprites:
            x,y = tile.get_tile_id()[0][0], tile.get_tile_id()[0][1]
            mask_dict[(x,y)] = pygame.mask.from_surface(tile.image) #Ripping mask from image
        
        return mask_dict
    
    def create_angle_dictionary(self):
        angle_dict = {}
        for tile in self.terrain_sprites:
            x,y = tile.get_tile_id()[0][0], tile.get_tile_id()[0][1]
            angle_dict[(x,y)] = tile.get_tile_id()[2] # angle array

        return angle_dict

    def solid_check(self,pos):
        for rect_key, rect_value in self.rect_dict.items():
            if rect_value.collidepoint(pos):
                return True
        return False

    def update(self, camera):
        for tile in self.background_tile_sprites:
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)
        
        for tile in self.background_sand_sprites:
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)

        for tile in self.palmtrees_bg_animated_sprites:
            tile.animate_slower()
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)
                
        for tile in self.palmtrees_bg_static_sprites:
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)

        for tile in self.terrain_sprites:
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)

        for tile in self.grass_sprites:
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)
            
        for tile in self.assets_sprites:
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)

        for tile in self.rings_sprites:
            tile.animate()
            tile_position = (tile.rect.x - camera.offset.x, tile.rect.y - camera.offset.y)
            self.display_surface.blit(tile.image, tile_position)
        
        for spring in self.springs_sprites:
            tile_position = (spring.rect.x - camera.offset.x, spring.rect.y - camera.offset.y)
            self.display_surface.blit(spring.image, tile_position)
        
