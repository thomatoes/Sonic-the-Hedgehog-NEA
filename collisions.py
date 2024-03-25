import pygame

class Collision:
    def detect_ground(self,level):
        #Calls the appropriate collision function depending on if the player
        #is on the ground or in the air
        if not self.fall:
            self.grounded(level)
        else:
            self.airbourne(level)
        
        self.reset_wall_floor_rects()
    
    def grounded(self,level):
        change = None
        pads_on = [False,False]
        for i,floor in enumerate(self.floor_detect_rects):
            #iterates over the elements in the player.floor_detect_rects, 
            # and i is the index, and floor is the value at that index

            collide,pads_on = self.check_floor_initial(pads_on,(i,floor),level)
            #collide,pads_on = self.check_floor_initial_mask(pads_on,(i,floor),level)

            #It passes pads_on, a tuple (i, floor), and level as arguments
            # The result is unpacked into collide and pads_on
            if collide:
                change = self.check_floor_final(collide,(i,floor),change,level)
        
        if pads_on[0]^pads_on[1]:
            change = self.detect_glitch_fix(pads_on,change,level)

        if change != None:
            self.rect.y = int(change -  self.rect.height)+66 #amend coordinates - changed to add 64 too
        else:
           self.fall = True
           self.is_grounded = False
           self.airborne = True
           self.direction.y = 0

    def check_floor_initial(self,pads_on,pads_details,level):
        i,floor = pads_details #get sensor details / sensor rects and coordinates
        collide = []

        for cell in level.rect_dict:  #iterate through dictionary to see if colliding with cell
            if floor.colliderect(level.rect_dict[cell]): # if rect overlap
                collide.append(cell)
                pads_on[i] = True
                self.is_grounded=True
        return collide,pads_on #add to collision array and return positive for collision


    def check_floor_final(self,collide, pad_details,change,level):
        #Get exact ground value from a colliding detector
        i,floor = pad_details
        for key in collide:
            rect = level.rect_dict[key]
            
            coord = (rect.x,rect.y) #topleft is the coordinates
            cell_heights = level.height_dict.get(coord)#, [0]*level.cell_size[0]) #level.height_dict.get[coord]
            x_loc_in_cell = floor.x- key[0] #*64 #level.cell_size[0]
            offset = cell_heights[x_loc_in_cell] #cell_heights[min(x_loc_in_cell, len(cell_heights) - 1)]
            
            angle_array = level.angle_dict.get(coord)
            self.angle = angle_array[x_loc_in_cell]

            if change == None:
                change = (key[1]+1)-offset # find the change in offsets and coordinates for thesensros
            else:
                change = min((key[1]+1)-offset,change) #(key[1]+1*level.cell_size[1])-offset,change
        
        return change #y_coordinate 

    def detect_glitch_fix(self,pads,change,level):
        #Fixes a glitch with the blit location that occurs on up-slopes when
        #one detection bar hits a solid cell and the other doesn't
        inc,index = ((1,0) if not pads[0] else (-1,1))
        detector = self.floor_detect_rects[index].copy()
        pad_details = (index,detector) #sensor details (floor sensors, there are 2)
        old_change = change
        
        while detector.x != self.floor_detect_rects[not index].x:
            detector.x += inc
            collide = self.check_floor_initial([0,0],pad_details,level)[0]
            change = self.check_floor_final(collide,pad_details,change,level)
            if change < old_change:
                return change
        return old_change

    def airbourne(self,level):
        #Search for the ground via mask detection while in the air.
        mask = self.floor_detect_mask
        check = (pygame.Rect(self.rect.x+1,self.rect.y,self.rect.width-1,1),
                 pygame.Rect(self.rect.x+1,self.rect.bottom-1,self.rect.width-2,1))
        stop_fall = False
        
        for rect in check:
            if self.collide_with(level,rect,mask,[0,int(self.speed_y)]):
                offset = [0,int(self.speed_y)]

                self.speed_y = self.adjust_pos(level,rect,mask,offset,1,)

                stop_fall = True
        
        if stop_fall:
            self.fall = False
            self.direction.y = 0
            self.is_grounded = True
            self.airborne = False
            self.is_jumping = False
            self.is_springjump = False
            self.is_hurt = False
            self.ishoming_dash = False
        
        self.angle = 0

    def detect_wall(self,level):
        #Detects collisions with walls.
        if self.is_grounded:
            rect,mask = self.wall_detect_rects,self.wall_detect_mask
        else:
            rect,mask = self.rect,self.rect_mask

        if self.collide_with(level,rect,mask,(int(self.speed),0)):
            self.speed = self.adjust_pos(level,rect,mask,[int(self.speed),0],0)
        
        self.reset_wall_floor_rects()

    def adjust_pos(self,level,rect,mask,offset,off_ind):
        #Continuously calls the collide_with method, decrementing the players
        #rect position until no collision is detected.
        offset[off_ind] += (1 if offset[off_ind]<0 else -1)
        while 1:
            if any(self.collide_with(level,rect,mask,offset)):
                offset[off_ind] += (1 if offset[off_ind]<0 else -1)
                if not offset[off_ind]:
                    return 0
            else:
                return offset[off_ind]
    
    def collide_with(self,level,rect,mask,offset):
       #The real collision detection occurs here. Initial tests are done with
        #rect collision and if positive further tests are done with masks."""
        test = pygame.Rect((rect.x+offset[0],rect.y+offset[1]),rect.size)
        self.collide_ls = []
        for cell,rec in level.rect_dict.items(): #Rect collision first - player rect and tile rect
            if test.colliderect(rec):  #If rect collision positive, test masks.
                coord_of_rect = (cell[0],cell[1])
                level_rect = level.rect_dict[cell] #get rect of the colliding tile
                mask_test = test.x-level_rect[0],test.y-level_rect[1]
                level_mask = level.mask_dict[coord_of_rect]
                if level_mask.overlap_area(mask,mask_test):
                    self.collide_ls.append(cell)
        return self.collide_ls
    
    def ring_collision(self, level, music,coll_type=None):
        if coll_type != None:
            for ring in self.game.rings.copy():
                if ring.rect().colliderect(self.rect):
                    music.play_sound_effect(music.rings)
                    self.ring_count+=1
                    self.score += 100

                    self.game.rings.remove(ring)
        else:
            for sprite in level.rings_sprites.sprites(): #access the sprite group of rings
                if sprite.rect.colliderect(self.rect): #check rect collision
                    music.play_sound_effect(music.rings)

                    self.ring_count += 1
                    self.score += 100
                    pygame.sprite.spritecollide(self,level.rings_sprites,True) #check overlap and remove
            
    def spring_collision(self,level,music,surface):
        
        for sprite in level.springs_sprites.sprites():
            if sprite.rect.colliderect(self.rect):
                if sprite.mask.overlap(self.mask,(self.rect.x-sprite.rect.x,self.rect.y-sprite.rect.y)):
                    music.play_sound_effect(music.spring)
                    
                    self.spring_jump()   
                    sprite.play_animation(self.game)     
                    sprite.render(surface)            
                    


        

            
        


