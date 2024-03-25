import pygame


class CameraGroup(pygame.sprite.Group):
    def __init__(self, displaySurface):
        super().__init__()
        self.display_surface = displaySurface

        #offset
        self.offset = pygame.math.Vector2()

        #box setup
        self.camera_borders = {'left': 100,
                               'right': 100,
                               'top': 100,
                               'bottom': 100}
        l = self.camera_borders['left']
        t = self.camera_borders['top']
        w = self.display_surface.get_size()[0] - (self.camera_borders['left'] + self.camera_borders['right'])
        h = self.display_surface.get_size()[1] - (self.camera_borders['top'] + self.camera_borders['bottom'])
        self.camera_rect = pygame.Rect(l,t,w,h)

    def box_camera(self,target):

        if target.rect.left < self.camera_rect.left:
            self.camera_rect.left = target.rect.left
        if target.rect.right > self.camera_rect.right:
            self.camera_rect.right = target.rect.right
        if target.rect.top < self.camera_rect.top:
            self.camera_rect.top = target.rect.top
        if target.rect.bottom > self.camera_rect.bottom:
            self.camera_rect.bottom = target.rect.bottom
            
        self.offset.x = self.camera_rect.left - self.camera_borders['left']
        self.offset.y = self.camera_rect.top - self.camera_borders['top']

    def center_camera(self,target):
        self.offset.x = target.rect.centerx - (self.display_surface.get_size()[0]//2)
        self.offset.y = target.rect.centery - (self.display_surface.get_size()[1]//2)
        
    def parallax_scroll(self,background_objects):
        for background_object in background_objects:
            obj_image = background_object[2]
            obj_rect = pygame.Rect(
                background_object[1][0] - self.offset.x*background_object[0],
                background_object[1][1] - self.offset.y*background_object[0],
                background_object[1][2],
                background_object[1][3]
                )
            if background_object[0] == 0.5:
                #pygame.draw.rect(self.display_surface,(14,222,150), obj_rect) 
                self.display_surface.blit(obj_image, obj_rect)
                #Use this when using images
            else:
                #pygame.draw.rect(self.display_surface,(9,91,85),obj_rect)
                self.display_surface.blit(obj_image, obj_rect)
                
    def custom_draw(self,player):
        self.box_camera(player)
        #self.center_camera(player)
        
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(pygame.transform.rotate(pygame.transform.flip(sprite.animation.img(),sprite.flip,False),sprite.angle),offset_pos)
        
        
        #player.draw_sensors(self.display_surface,offset_pos)
        #pygame.draw.rect(self.display_surface,'yellow',self.camera_rect,5)
