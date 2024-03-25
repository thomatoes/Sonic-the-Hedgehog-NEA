import pygame
import random
import math
from collisions import Collision
from utilities import Spark

class PhysicsEntity(pygame.sprite.Sprite):
    def __init__(self,game,e_type,pos,size,image):
        super().__init__()
        self.game = game
        self.type = e_type
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        self.velocity = pygame.math.Vector2(0,0)
        self.image = image
        
        #animation
        self.action = ''
        self.animation_offset = (-3,-3) #to account for padding in different images
        self.flip = False
        self.set_action('idle')
    
    def rect(self):
        return pygame.Rect(self.pos[0],self.pos[1],self.size[0],self.size[1])
    
    def update(self,level_map,movement=(0,0)):
        self.collisions = {
            "left": False,
            "right": False,
            "up": False,
            "down": False
        }
        frame_movement = (movement[0]+self.velocity[0],movement[1]+self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()

        for rect in level_map.rect_dict:
            if entity_rect.colliderect(level_map.rect_dict[rect]):
                if frame_movement[0]>0:
                    entity_rect.right = level_map.rect_dict[rect].left
                    self.collisions['right'] = True
                if frame_movement[0]<0:
                    entity_rect.left = level_map.rect_dict[rect].right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1]+= frame_movement[1]
        entity_rect = self.rect()

        for rect in level_map.rect_dict:
            if entity_rect.colliderect(level_map.rect_dict[rect]):
                if frame_movement[1]>0:
                    entity_rect.bottom = level_map.rect_dict[rect].top
                    self.collisions['down']=True
                if frame_movement[1]<0:
                    entity_rect.top = level_map.rect_dict[rect].bottom
                    self.collisions['up']=True
                self.pos[1] = entity_rect.y
        
        
        if movement[0] >0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
        
        self.last_movement = movement
        self.velocity[1] = min(2,self.velocity[1]+0.1)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1]=0
        self.animation.update()
    
    def render(self,surface,offset=(0,0)):
        surface.blit(pygame.transform.flip(self.animation.img(),self.flip,False) ,(self.pos[0]-offset[0]+self.animation_offset[0],self.pos[1]-offset[1]+self.animation_offset[1]))
    
    def set_action(self,action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type +'/'+self.action].copy()

class Chao(PhysicsEntity):
    def __init__(self,game,pos,size,image):
        super().__init__(game,'chao',pos,size,image)
        self.initial_pos = list(pos)

        self.walking = 0
        self.static_bounding_box = pygame.Rect(self.initial_pos[0] - 20, self.initial_pos[1] - 20, self.size[0] + 20, self.size[1] + 20)

    def update(self,level_map,movement=(0,0)):
        self.check_dist()

        if self.walking:
            new_x = self.pos[0] + movement[0]
            if new_x < self.static_bounding_box.left:
                self.flip = False
            elif new_x + self.size[0] > self.static_bounding_box.right:
                self.flip = True
            else:
                self.pos[0] = new_x
            
            movement = (movement[0]-0.5 if self.flip else 0.5,movement[1])
            self.walking = max(0, self.walking - 1)
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        super().update(level_map,movement=movement)
    
    def check_dist(self):
        if self.static_bounding_box.colliderect(self.game.player.rect):
            self.game.chao_interact = True
        else:
            self.game.chao_interact = False

class Enemy(PhysicsEntity):
    def __init__(self,game,pos,size,image):
        super().__init__(game,'enemy',pos,size,image)

        self.walking = 0
        self.cooldown = 0
    
    def update(self,level_map,movement=(0,0)):
        if self.walking:
            if level_map.solid_check((self.rect().x+(-8 if self.flip else 8), self.pos[1]+20)):
                movement = (movement[0]-0.5 if self.flip else 0.5,movement[1])
            else:
                self.flip = not self.flip

            self.walking = max(0,self.walking-1)
            
            if self.cooldown > 0:
                self.cooldown += -1

            distance = (self.game.player.rect.centerx - self.pos[0],self.game.player.rect.centery - (self.pos[1]))
            if distance[1]<5:
                if (self.flip and distance[0]< 0): #if player is to the left
                    if self.cooldown == 0:
                        self.game.projectiles.append([[self.rect().centerx,self.rect().centery],-1.5,0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() -0.5 + math.pi, 2+random.random()))
                        self.cooldown = 60

                if (not self.flip and distance[0]>0): #player is to the right and looking right
                    if self.cooldown == 0:
                        self.game.projectiles.append([[self.rect().centerx,self.rect().centery],1.5,0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0],random.random() -0.5, 2+random.random()))
                        self.cooldown = 60


        elif random.random()<0.01:
            self.walking = random.randint(30,120)
        super().update(level_map,movement=movement)

        if movement[0] != 0:
            self.set_action('walk')
        else:
            self.set_action('idle')
        
        if (self.game.player.is_jumping or self.game.player.is_rolling or self.game.player.is_homingdash) and not self.game.player.is_hurt and not self.game.player.is_dead:
            if self.rect().colliderect(self.game.player.rect):
                for i in range(20):
                    angle = random.random() *math.pi *2
                    self.game.sparks.append(Spark(self.rect().center,angle,2+random.random()))
                
                self.game.sparks.append(Spark(self.rect().center,0,5+random.random()))
                self.game.sparks.append(Spark(self.rect().center,math.pi,5+random.random()))
                return True
    
    def render(self,surface,offset=(0,0)):
        super().render(surface,offset=offset)

class RingObject():
    def __init__(self,game,e_type,pos,size,image):
        super().__init__()
        self.game = game
        self.type = e_type
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        self.velocity = pygame.math.Vector2(0,0)
        self.angle = 0
        self.image = image

        #timer
        self.timer = 5000  # Time in milliseconds
        self.timer_started = False
        self.timer_start_time = 0
        
        #animation
        self.action = ''
        self.animation_offset = (-3,-3) #to account for padding in different images
        self.flip = False
        self.set_action('idle')
    
    def set(self,speed,angle):
        # Modify the X component of the velocity based on the angle
        self.velocity[0] = speed * math.cos(self.angle + angle)
        self.velocity[1] = speed * math.sin(self.angle + angle)

    def rect(self):
        return pygame.Rect(self.pos[0],self.pos[1],self.size[0],self.size[1])
    

    def update(self,level_map,movement=(0,0)):
        self.collisions = {
            "left": False,
            "right": False,
            "up": False,
            "down": False
        }
         # Adjust the decrement value as needed
        frame_movement = (movement[0]+self.velocity[0],movement[1]+self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()

        for rect in level_map.rect_dict:
            if entity_rect.colliderect(level_map.rect_dict[rect]):
                if frame_movement[0]>0:
                    entity_rect.right = level_map.rect_dict[rect].left
                    self.collisions['right'] = True
                if frame_movement[0]<0:
                    entity_rect.left = level_map.rect_dict[rect].right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1]+= frame_movement[1]
        entity_rect = self.rect()

        for rect in level_map.rect_dict:
            if entity_rect.colliderect(level_map.rect_dict[rect]):
                if frame_movement[1]>0:
                    entity_rect.bottom = level_map.rect_dict[rect].top
                    self.collisions['down']=True
                if frame_movement[1]<0:
                    entity_rect.top = level_map.rect_dict[rect].bottom
                    self.collisions['up']=True
                self.pos[1] = entity_rect.y
        
        self.last_movement = movement
        self.velocity[1] = min(2,self.velocity[1]+0.1)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1]=0
        
        self.velocity[0] *= 0.99
        self.animation.update()

        if not self.timer_started:
            self.timer_start_time = pygame.time.get_ticks()
            self.timer_started = True

        # Check if the timer duration has passed, and if so, indicate that the ring should be removed
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.timer_start_time
        if elapsed_time >= self.timer:
            return True 
        

    def render(self,surface,offset=(0,0)):
        surface.blit(pygame.transform.flip(self.animation.img(),self.flip,False) ,(self.pos[0]-offset[0]+self.animation_offset[0],self.pos[1]-offset[1]+self.animation_offset[1]))
    
    def set_action(self,action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type +'/'+self.action].copy()

class Player(pygame.sprite.Sprite, Collision):
    def __init__(self,pos,game):
        super().__init__()
        self.game = game
        self.image = self.game.assets['player'] #change

        self.rect = self.image.get_frect(center = pos) #pygame.Rect(32,64,32,40)
        self.height = self.image.get_height()
        self.angle = 0

        #Animation
        self.action = ''
        self.animation_offset = (-3,-3) #to account for padding in different images
        self.flip = False
        self.set_action('idle')

        #Player values
        self.ring_count = 0
        self.score = 0

        #Boolean values
        self.fall = False
        self.idle = False
        self.is_jumping = False
        self.is_crouching = False
        self.is_rolling = False
        self.is_grounded = True
        self.is_charging_spindash = False
        self.is_homingdash = False
        self.is_springjump = False
        self.is_lookup = False
        self.is_hurt = False
        self.bored = False
        self.bored1 = False
        self.is_spindashing = False
        self.is_dead = False
        self.start = False

        #player collisions
        #Collision detection bar rects based on player position, reset every frame
        self.setup_collision_bars()

        #masks
        self.mask = pygame.mask.from_surface(self.image)

        #Player vectors
        self.direction = pygame.math.Vector2(0,0)
        self.friction_direction = 0

        #Player movement
        self.speed = 0  # Initial speed in x direction
        self.speed_y = 0

        self.friction_speed = 0.125 #0.046875 #
        self.top_speed = 7.5
        self.acceleration_speed = 0.046875 #0.0625 
        self.deceleration_speed = 0.625 #0.5
        
        self.gravity_force = 0.21875
        self.jump_force = -6
        self.max_jump_speed = -6.5

        #Player rolling and spindash
        self.spinrev = 0
        self.top_spindash_speed = 8
        self.roll_friction_speed = 0.0234375
        self.roll_deceleration_speed = 0.125
        self.slope_factor_rollup = 0.078125
        self.slope_factor_rolldown = 0.078125

        #Player homing dash
        self.is_homingdash = False
        self.counter = 0
        self.homing_acceleration = 0
        self.air_drag = 0.0234735

        #Miscellaneous constants
        self.spring_constant = -7

        #hurt
        self.hurt_x_force = 2
        self.hurt_y_force = -4 
        
        #Control locks
        self.lock_controls = False
        self.lock_duration = 1000  # Lock duration in milliseconds (1 second in this case)
        self.lock_timer = 0

    def control_lock(self, time):
        self.lock_controls = True
        self.lock_timer = pygame.time.get_ticks() + time  # Set the timer to the current time + lock duration

    def update_control_lock(self):
        if self.lock_controls:
            current_time = pygame.time.get_ticks()
            if current_time >= self.lock_timer:
                self.lock_controls = False

    def set_action(self,action):
        if action == "idle":
            self.idle = True
        else:
            self.idle = False
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['player'+'/'+self.action].copy()

    def setup_collision_bars(self):
        self.reset_wall_floor_rects()

        #Create masks for collision checks
        self.rect_mask = pygame.Mask(self.rect.size)
        self.rect_mask.fill()
        self.wall_detect_mask = pygame.Mask(self.wall_detect_rects.size)
        self.wall_detect_mask.fill()
        self.floor_detect_mask = pygame.Mask(self.wall_detect_rects.size)
        self.floor_detect_mask.fill()
        self.collisions =[] #Store all possible collisions in an array so it is easier to resolve

    def reset_wall_floor_rects(self):
        floor = (pygame.Rect((self.rect.x+1,self.rect.y),(1,self.rect.height+8)),
               pygame.Rect((self.rect.right-2,self.rect.y),(1,self.rect.height+8)))
        #Creates 2 thin strips which are positioned near the bounding box of the entity
        #Acts as sensors
        wall = pygame.Rect(self.rect.x,self.rect.bottom-16,self.rect.width,1) #Sensor to detect wall - full tiles

        self.floor_detect_rects = floor
        self.wall_detect_rects = wall
        #set as variables 
        
        #create 1 thin strip which is center of player radius to detect walls
        wall = pygame.Rect(self.rect.x,self.rect.bottom-5,self.rect.width,1)
    
    def draw_sensors(self,surface, shift):
        for rect in self.floor_detect_rects:
           surface.fill((255,0,0),rect.move(shift.x - self.rect.x ,shift.y - self.rect.y))
        surface.fill((255,0,0),self.wall_detect_rects.move(shift.x - self.rect.x ,shift.y - self.rect.y ))
            
    def get_input(self):
        keys = pygame.key.get_pressed()
        
        #Moving left/right
        if keys[pygame.K_d] and not self.lock_controls:
            if self.is_charging_spindash or self.is_spindashing:
                self.direction.x = 0
            else:
                self.direction.x = 1
        elif keys[pygame.K_a] and not self.lock_controls:
            if self.is_charging_spindash or self.is_spindashing:
                self.direction.x = 0
            else:
                self.direction.x = -1
        else:
            #dont do anything
            self.direction.x = 0


        #Homing dash
        if  keys[pygame.K_p] and not self.lock_controls:
            if self.is_jumping and not self.is_homingdash:
                #Want homing dash to happen once in the air
                self.is_homingdash = True
                self.speed = 0
                self.homingdash()
                    
    def apply_gravity(self):
        if self.fall:
            self.direction.y += self.gravity_force
        
        self.rect.y += self.direction.y

    def jump(self):
        #check if jumping
        if self.is_jumping and not self.fall: #add IsOnGround later
            self.game.music.play_sound_effect(self.game.assets['sound_effect/jump'])
            self.speed_y += self.jump_force

        # Apply air drag
            if self.speed_y < 0 and self.speed_y > -4.0:
                self.speed_y -= (self.speed_y // 0.125) / 256

            if self.speed_y > self.max_jump_speed:
                self.speed_y = self.max_jump_speed
            
            self.fall = True
        self.direction.y += self.speed_y

    def spring_jump(self):
        self.speed_y += self.spring_constant
        if self.speed_y <0 and self.speed_y > -6.5:
            self.speed_y -= (self.speed_y //0.125)/256
        
        if self.speed_y < -7.5:
            self.speed_y = -7.5 
            
        self.direction.y += self.speed_y
        self.fall = True
        self.is_grounded = False
        self.airborne = True
        
        self.is_springjump = True

    def spindash(self):
        self.direction.y = 0
        self.spinrev -= (self.direction.x // 0.125) /256
        self.spinrev = 8 + (self.spinrev//2)
        # Apply spin rev and friction based on the player's direction
        if not self.flip:
            self.speed = max(self.spinrev - self.roll_friction_speed - self.roll_deceleration_speed, 0)
        elif self.flip:
            self.speed = min(-self.spinrev + self.roll_friction_speed + self.roll_deceleration_speed, 0)

        # Update the player's direction (optional, depending on your requirements)
        self.is_spindashing = False

    def homingdash(self):
        if self.is_homingdash:
            self.homing_acceleration -= (self.direction.x // 0.125)/256
            if self.direction.x > 0:
                self.game.music.play_sound_effect(self.game.assets['sound_effect/homingdash'])
                self.speed = 8 + (self.homing_acceleration//2)
                self.speed = max(self.speed - self.air_drag, 0)
            elif self.direction.x < 0:
                self.game.music.play_sound_effect(self.game.assets['sound_effect/homingdash'])
                self.speed = -8 - (self.homing_acceleration//2)
                self.speed = min(self.speed + self.air_drag, 0)
        
   
        self.direction.x += self.speed

    def rolling(self):
        if self.angle == 0 and (self.direction.x >0 or self.speed >0):
            self.speed -= self.roll_deceleration_speed + self.roll_friction_speed
            if self.speed < 0:
                self.speed = 0
        if  self.angle == 0 and (self.direction.x <0 or self.speed <0):
            self.speed += self.roll_deceleration_speed + self.roll_friction_speed
            if self.speed >0:
                self.speed = 0
       
        if self.angle > 0:
            self.speed -= self.slope_factor_rollup
            if self.speed < -self.top_speed:
                self.speed = -self.top_speed
        if self.angle < 0:
            self.speed += self.slope_factor_rolldown
            if self.speed > self.top_speed:
                self.speed = self.top_speed   
        
        self.is_rolling = abs(self.speed)>0 or self.angle != 0
        
        #self.rect.x += self.speed
    
    def rebound(self):
        if not self.is_grounded and self.fall:
            self.speed_y += self.jump_force*2
            if self.speed_y < 0 and self.speed_y > -4.0:
                self.speed_y -= (self.speed_y // 0.125) / 256

            if self.speed_y < self.max_jump_speed:
                self.speed_y = self.max_jump_speed
            
            self.fall = True
        self.direction.y += self.speed_y
    
    def hurt(self):
        if self.is_hurt:
            self.game.music.play_sound_effect(self.game.assets['sound_effect/sonic_ow'])
            a = 1 if self.flip else -1

            self.speed = 0
            self.speed_y = 0

            self.speed_y = -self.hurt_y_force * a
            self.speed = -self.hurt_x_force  if self.flip else self.hurt_x_force
            self.drop_rings()
            self.game.music.play_sound_effect(self.game.assets['sound_effect/loserings'])
            self.control_lock(2000)
        
        self.direction.y += self.speed_y
    
    def drop_rings(self):
        if self.ring_count>20:
            for i in range(20):
                rand_speed = random.uniform(-4, 4)  # Adjust the range as needed
                angle_variation = random.uniform(-0.5, 0.5)  # Adjust the range as needed
                ring = RingObject(self.game,"ring",self.rect.center,(16,16),'levels/level_data/rings/ring/ring1.png')
                ring.set(rand_speed,angle_variation)
                self.game.rings.append(ring)
        else:
            for i in range(self.ring_count):
                rand_speed = random.uniform(-4, 4)  # Adjust the range as needed
                angle_variation = random.uniform(-0.5, 0.5)  # Adjust the range as needed
                ring = RingObject(self.game,"ring",self.rect.center,(16,16),'levels/level_data/rings/ring/ring1.png')
                ring.set(rand_speed,angle_variation)
                self.game.rings.append(ring)

    def die(self):
        if self.game.lives > 0 and self.is_dead:
            self.control_lock(4000)
            self.speed = 0
            self.direction.x = 0

    
    def die_anim(self):
        self.speed_y = -5

        # Apply air drag
        if self.speed_y < 0 and self.speed_y > -4.0:
            self.speed_y -= (self.speed_y // 0.125) / 256

        if self.speed_y < self.max_jump_speed:
            self.speed_y = self.max_jump_speed
            
        self.direction.y += self.speed_y
    
    def start_level(self):
        self.control_lock(4000)

    def add_life(self):
        self.game.lives += 1
        self.game.music.play_sound_effect(self.game.assets['sound_effect/extra_life'])

    def update(self):
        self.update_control_lock()
        self.get_input()
        
        if not self.is_crouching and not self.is_rolling and not self.is_dead:
            #Adjust speed based on direction + acceleration
            if self.direction.x != 0: #If going left, direction =-1 and if right direction
                self.speed += self.direction.x * self.acceleration_speed

            #Apply friction
            if self.direction.x == 0 and self.speed != 0: #If not pressing key but still moving, slow down
                self.friction_direction = 1 if self.speed<0 else -1
                self.speed += self.friction_direction * self.friction_speed

            #When not moving completely
            if self.direction.x ==0:
                if abs(self.speed)<self.friction_speed:
                    self.speed = 0

            #Going faster than at top speed
            if self.speed >= self.top_speed:
                self.speed = self.top_speed
            elif self.speed <= -(self.top_speed):
                self.speed = -(self.top_speed)
        
        elif self.is_rolling and not self.is_dead:
            self.rolling()

        if self.is_spindashing and not self.is_dead:
            self.spindash()
            self.is_rolling = True

        if self.direction.x > 0:
            self.flip = False
        elif self.direction.x < 0:
            self.flip = True

        self.rect.x += self.speed
        self.apply_gravity()

        self.animation.update()
        if self.start:
            self.set_action('start')
        elif self.is_dead:
            self.set_action('die')
        elif self.is_hurt:
            self.set_action('hurt')
        elif self.is_jumping:
            self.set_action('jump')
        elif self.is_crouching and not self.is_rolling:
            self.set_action('crouch')
        elif self.is_rolling:
            self.set_action('rolling')
        elif self.is_charging_spindash:
            self.set_action('spindash')
        elif self.is_lookup and self.direction.x == 0 and abs(self.speed) <= 0.48675:
            self.set_action('lookup')
        elif self.is_springjump or self.is_jumping and self.is_springjump:
            self.set_action('springjump')
        elif abs(self.speed) > 0 and abs(self.speed) <=2:
            self.set_action('walk')
        elif abs(self.speed)>2 and abs(self.speed)<= 3.5:
            self.set_action('jog')
        elif abs(self.speed)>3.5 and abs(self.speed)<=4.5:
            self.set_action('fastjog')
        elif abs(self.speed)>4.5 and abs(self.speed)<=6.5:
            self.set_action('run')
        elif abs(self.speed)>6.5:
            self.set_action('topspeed')
        elif self.bored:
            self.set_action('bored')
            self.idle = True
        elif self.bored1:
            self.set_action('bored1')
            self.idle = True
        else:
            self.set_action('idle')

        print ("player speed: ",self.speed)
        print ("player angle: ",self.angle)

            
