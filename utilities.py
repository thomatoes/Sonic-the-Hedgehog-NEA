import pygame
import math

vertical_tile_number = 32
tile_size = 16

class Animation:
    def __init__(self,images,img_duration=5,loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_duration
        self.done = False
        self.frame = 0 #frame / animation index
    
    def copy(self):
        return Animation(self.images,self.img_duration,self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame+1) % (self.img_duration * len(self.images)) #loop animation
        else:
            self.frame = min(self.frame + 1,self.img_duration*len(self.images)-1) #go through the animation until the end
            if self.frame >= self.img_duration* len(self.images)-1:
                self.done = True #if it reaches the end, then stop

    def img(self):
        return self.images[int(self.frame/self.img_duration)] #dividing frame by how long each image is supposed to show for
    
class Spark:
    def __init__(self,pos,angle,speed):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
    
    def update(self):
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed
        
        self.speed = max(0,self.speed-0.1)
        return not self.speed
    
    def render(self,surface,offset=(0,0)):
        #Creating a small white polygon based on the angle, the speed and the camera offset
        #The vertices of the polygon are variable
        #sin --> vertical, cosine --> horizontal
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed* 6 - offset[0], self.pos[1]+ math.sin(self.angle)*self.speed*6 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5)*self.speed*0.5 -offset[0],self.pos[1]+math.sin(self.angle + math.pi * 0.5)*self.speed*0.5-offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi)*self.speed*6-offset[0],self.pos[1]+math.sin(self.angle + math.pi)*self.speed*6-offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5)*self.speed*0.5 -offset[0],self.pos[1]+math.sin(self.angle - math.pi * 0.5)*self.speed*0.5-offset[1]),
        ]

        pygame.draw.polygon(surface,(255,255,255),render_points)

#Class for leaf particles 
class Particle:
    def __init__(self,game,pos,velocity=[0,0],frame=0):
        self.game = game
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.animation = self.game.assets['particle/leaf'].copy()
        self.animation.frame = frame
    
    def update(self):
        kill = False

        #Cycle through animation until complete.
        if self.animation.done:
            kill = True
        
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        
        self.animation.update()
    
    def render(self,surface,offset=(0,0)):
        image = self.animation.img()
        surface.blit(image,(self.pos[0]-offset[0] - image.get_width()//2,self.pos[1]-offset[1]- image.get_height()//2))
