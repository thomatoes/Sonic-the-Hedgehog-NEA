import pygame
import sys
import numpy
import math
import random
from PIL import Image

from os import path
from camera import CameraGroup
from player import Player
from level import Level
from game_data import level
from collisions import Collision
from display import Display
from music import Music
from support import load_image, load_images, import_graphics
from utilities import *
from clouds import Clouds

#Constants
highscores = "scores.txt"
_circle_cache = {}

#This function fficiently generates a list of integer coordinates representing points on the circumference
#of a circle with radius r using Bresenham's Circle Drawing Algorithm to optimize the calculation process
def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points

#Creates 2 surfaces - normal text, and text to be outlined
# then using symmetry to centre the text on top of the outline by calling the circlepoints_ function
def render(text, font, gfcolor=pygame.Color('white'), ocolor=(0, 0, 0), opx=2):
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf

#Creates a parallelogram that starts from the left, extending to the right
def parallelogram_r(x, y, width, height, color,screen):
    points = [(x, y), (x + width, y), (x + width - height, y + height), (x - height, y + height)]
    pygame.draw.polygon(screen, color, points)

#Creates a parallelogram that starts from the right, extending to the left
def parallelogram_l(x, y, width, height, color, screen):
    points = [(x, y), (x - width, y), (x - width + height, y + height), (x + height, y + height)]
    pygame.draw.polygon(screen, color, points)

class Story:
    def __init__(self,game):
        self.game = game
        self.screen = self.game.screen

        #Creates a rectangle for where the dialogue is displayed. Then accesses the lines from the file "story.txt"
        self.dialoguebox = pygame.Rect(0,350,self.screen.get_width(),150)
        self.lines = self.open()

        self.music = game.music

        #Sonic and Tails image sprites for the story
        self.sonic = {
            'normal': load_image("sprites/sonic/normal.png"),
            'determined': load_image("sprites/sonic/determined.png"),
            'resting':load_image("sprites/sonic/resting.png"),
            'dunno':load_image("sprites/sonic/dunno.png")
        }

        self.tails = {
            'normal': load_image("sprites/tails/normal.png"),
            'determined': load_image("sprites/tails/determined.png"),
            'dunno': load_image("sprites/tails/dunno.png"),
        }

        #Music and sound effect for the story
        self.assets = {
            "sonic_igotit": "audio/sonic_rush/Sonic Rush Voice Overs/sonic_igotit.wav",
            "sonic_cool": "audio/sonic_rush/Sonic Rush Voice Overs/sonic_cool.wav",
            "tails_alright" : "audio/sonic_rush/Sonic Rush Voice Overs/tails_alright.wav",
            "tails_huh": "audio/sonic_rush/Sonic Rush Voice Overs/tails_huh.wav",
            "tails_doyourbestsonic": "audio/sonic_rush/Sonic Rush Voice Overs/tails_doyourbestsonic.wav",
            "tails_nosonic": "audio/sonic_rush/Sonic Rush Voice Overs/tails_nosonic.wav",
            "tails_sonic": "audio/sonic-tails.mp3",
            "S3K_waves": "audio/S3K_waves.wav"
        }

        #initialising characters and settings
        self.character_s = self.sonic['normal']
        self.character_t = self.tails['normal']

        self.current_line = 0
        self.sound_effect = False
        self.sonic_show = True
        self.tails_show = False

    def open(self):
        #Opens the file in read mode and extracts all the lines
        file = open("story.txt","r")
        data = file.read()
        file.close()
        
        self.lines = data.split("\n")
        return  self.lines

    def s_expression(self,key):
        self.character_s = self.sonic[key]
    
    def t_expression(self,key):
        self.character_t = self.tails[key]
    
    def set_text(self,text):
        self.screen.blit(render(text,self.game.display.display_font_white,gfcolor=pygame.Color("white")),(20,365))
    
    def label(self,name,color):
        self.screen.blit(render(name,self.game.display.display_font_orange,gfcolor=pygame.Color(color)),(20,310))
    
    def next_line(self):
        self.current_line += 1

        if self.lines[self.current_line][0] == "+":
            name,color = "Miles 'Tails' Prower", "orange"
        else:
            name,color = "Sonic the Hedgehog", "skyblue"

        #represents the label of who is talking
        return name,color

    def next_check(self):
        #checks for the end of the file
        if self.current_line == 32:
            return True
    
    def check_line(self): #This is where all the story management will happen
        #Checks per line what might happen (sound effects, music, visuals)
        if self.current_line == 0 and not self.sound_effect:
            self.music.play_sound_effect(self.assets['sonic_cool'])
            self.s_expression('determined')
            return True
            #relaxed/determined
        
        if self.current_line == 2 and not self.sound_effect:
            #resting
            self.s_expression('resting')
            return True
            
        if self.current_line == 3 and not self.sound_effect:
            #normal
            self.s_expression('normal')
            self.music.play_sound_effect(self.assets['tails_sonic'])
            self.t_expression('dunno')
            #tails worried
            return True
        
        if self.current_line == 4 and not self.sound_effect:
            self.tails_show = True
            return True
            
        if self.current_line == 5 and not self.sound_effect:
            #dunno sonic
            #wprried tails
            self.s_expression('dunno')
            return True

        if self.current_line == 6 and not self.sound_effect:
            #determined sonic
            self.s_expression('determined')
            return True

        if self.current_line == 9 and not self.sound_effect:
            #determined tails
            self.t_expression('determined')
            return True

        if self.current_line == 11 and not self.sound_effect:
            #normal sonic
            self.s_expression('normal')
            self.music.play_sound_effect(self.assets['tails_huh'])
            return True

        if self.current_line == 15 and not self.sound_effect:
            #worried tails
            self.t_expression('dunno')
            return True

        if self.current_line == 20 and not self.sound_effect:
            self.music.play_sound_effect(self.assets['tails_nosonic'])
            #determind tails
            self.t_expression('dunno')
            return True

        if self.current_line == 24 and not self.sound_effect:
            self.music.play_sound_effect(self.assets['tails_huh'])
            #normal tails
            self.t_expression('dunno')
            return True

        if self.current_line == 25 and not self.sound_effect:
            self.music.play_sound_effect(self.assets['tails_nosonic'])
            #determined tails
            self.t_expression('determined')
            return True

        if self.current_line == 26 and not self.sound_effect:
            #determined sonic
            self.s_expression('determined')
            self.music.play_sound_effect(self.assets['sonic_igotit'])
            return True
            
        if self.current_line == 27 and not self.sound_effect:
            self.music.play_sound_effect(self.assets['sonic_cool'])
            return True

        if self.current_line == 30 and not self.sound_effect:
            #normal tails
            self.t_expression('normal')
            self.music.play_sound_effect(self.assets['tails_doyourbestsonic'])  
            return True    
        
        if self.current_line == 31 and not self.sound_effect:
            #determined tails
            #normal sonic
            self.t_expression('determined')
            self.s_expression('normal')
            self.music.play_sound_effect(self.assets['tails_alright'])
            return True
            

#initialising
pygame.init()
class Game:
    def __init__(self):
        #General initialising of core management of game
        self.game_screen = pygame.Surface((550,380))
        self.screen = pygame.display.set_mode((720,500))

        self.clock = pygame.time.Clock()

        #All assets the game will use; music, visuals, animation
        self.assets = {
            'player': load_image('sonic/idle/idle1.png'),
            'player/start': Animation(load_images('sonic/start_run'),img_duration=12,loop=False),
            'player/idle': Animation(load_images('sonic/idle'),img_duration=16),
            'player/walk': Animation(load_images('sonic/walk'),img_duration=6),
            'player/jog': Animation(load_images('sonic/jog'),img_duration=6),
            'player/fastjog': Animation(load_images('sonic/fastjog'),img_duration=7),
            'player/run': Animation(load_images('sonic/run'),img_duration=6),
            'player/topspeed': Animation(load_images('sonic/toprun'),img_duration=6),
            'player/jump': Animation(load_images('sonic/jump'),img_duration=6),
            'player/springjump': Animation(load_images('sonic/springjump'),img_duration=6),
            'player/lookup': Animation(load_images('sonic/look_up'),img_duration=5,loop=False),
            'player/bored': Animation(load_images('sonic/bored'),img_duration=12,loop=False),
            'player/bored1': Animation(load_images('sonic/bored2'),img_duration=10,loop=False),
            'player/crouch': Animation(load_images('sonic/crouch'),img_duration=6,loop=False), 
            'player/hurt': Animation(load_images('sonic/hurt'),img_duration=4,loop=False), 
            'player/rolling': Animation(load_images('sonic/jump'),img_duration=6),   
            'player/spindash': Animation(load_images('sonic/spindash'),img_duration=4),
            'player/die': Animation(load_images('sonic/die'),img_duration=8,loop=False),
            'spring/recoil': Animation(load_images('springs'),img_duration=5,loop=False),
            'chao/idle': Animation(load_images('chao'),img_duration=14,loop=True),
            'chao/walk': Animation(load_images('chao'),img_duration=14,loop=True),
            'enemy/idle': Animation(load_images('enemies/idle'),img_duration=6,loop=True),
            'enemy/walk':Animation(load_images('enemies/walk'),img_duration=6,loop=True),
            'ring/idle': Animation(import_graphics('levels/level_data/rings/ring'),img_duration=5,loop=True),
            'goalpost/idle': load_image('goalpost/goalpost1.png'),
            'goalpost/finish': load_image('goalpost/goalpost7.png'),
            'goalpost/spin': load_images('goalpost'),
            'projectile': load_image('enemies/shoot.png'),
            'clouds': load_image('cloud.png'),
            'sound_effect/spring':"audio/sonic-spring.mp3",
            'sound_effect/rings':"audio/sonic_ring_sound_effect.mp3",
            'sound_effect/sonic_letsdothis': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_letsdoit.wav",
            'sound_effect/sonic_herewego': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_herewego.wav",
            'sound_effect/sonic_isthatit': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_isthatit.wav",
            'sound_effect/sonic_ok': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_ok.wav",
            'sound_effect/sonic_yeah': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_yeah.wav",
            'sound_effect/sonic_yes': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_yes.wav",
            'sound_effect/sonic_yes2': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_yes2.wav",
            'sound_effect/sonic_cool': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_cool.wav",
            'sound_effect/sonic_woofeelingood':"audio/woo-feelin-good-sonic-unleashed.mp3",
            'sound_effect/jump': "audio/jump.mp3",
            'sound_effect/spindash': "audio/sonic-spindash.mp3",
            'sound_effect/sonic_ow': "audio/sonic_rush/Sonic Rush Voice Overs/sonic_ow.wav",
            'sound_effect/homingdash': "audio/sonic_homingattack.mp3",
            'sound_effect/loserings': "audio/S3K_loserings.wav",
            'sound_effect/spindashfinish': "audio/S3K_spindashfinish.wav",
            'sound_effect/sonic_tooeasy': "audio/sonic_tooeasy.mp3",
            'sound_effect/enemy_kill': "audio/enemy_kill.wav",
            'sound_effect/extra_life': "audio/sonic-extra-life.mp3",
            'sound_effect/level_finish':"audio/sonic-level-finish.mp3",
            'sound_effect/sonic_die': "audio/sonic-death-sound-effect.mp3",
            'sound_effect/gameover': "audio/level_gameover.mp3",
            'sound_effect/announcer_3': "audio/Anouncer3.wav",
            'sound_effect/announcer_2': "audio/Anouncer2.wav",
            'sound_effect/announcer_1': "audio/Anouncer1.wav",
            'sound_effect/announcer_go': "audio/AnouncerGo!.wav",
            'sound_effect/signpost': "audio/sonic-1-goal-post.mp3",
            "beach1" : "audio/05. Neo Green Hill Zone - Act 1.mp3",
            "beach2": "audio/06. Neo Green Hill Zone - Act 2.mp3",
            'background/bg':load_image('neo_green_hill_zone_background.jpg'),
            'background/asset': load_image('Leaf Forest Asset.png'),
            'menu/button': load_image('menu_ui/button.png'),
            'menu/button2': load_image('menu_ui/button2.png'),
            'menu/music': "audio/A New Day.mp3",
            'menu/bg': load_image("menu_ui/bg-leaf-storm.png"),
            'menu/bg-score': load_image("menu_ui/score-bg.png"),
            'menu/title': load_image("menu_ui/title.png"),
            'menu/sonic': load_image("sonic-model.png"),
            'menu/scoreboard_music': "audio/scoreboard.mp3",
            'wasd': load_image("wasd.png"),
            'op': load_image("op.png"),
            'so': load_image("so.png"),
            'o': load_image("o.png"),
            'particle/leaf': Animation(load_images("leaf")),
            'emerald beach': load_image("e6710a5ee862197627a7acb1145d6908.jpg")

        }
        
        self.sonic_sounds = [
                        self.assets['sound_effect/sonic_ok'],
                        self.assets['sound_effect/sonic_yeah'],
                        self.assets['sound_effect/sonic_yes'],
                        self.assets['sound_effect/sonic_yes2'],
                        self.assets['sound_effect/sonic_cool'],
                        self.assets['sound_effect/sonic_tooeasy'],
                        self.assets['sound_effect/sonic_woofeelingood'],
                    ]
        
        self.collision = Collision()

        self.substep_val = 6
        self.movement = [False,False]

        self.music = Music()

        self.bg = self.assets["background/bg"]
        # [0.25,[120+i*200,10,70,400]] for i in range(1, num_repeats)
        #Where [val, [x,y,w,h], object image.png/jpeg 
        # [x,y,w,h] --> x pos, y pos, width of rec, height of rect
        # first val , eg 0.25 - multiplier to make it move faster or slower
        self.background_objects = [
            [0.5,[50,350,400,800],self.assets['background/asset']],
            [0.5,[450,350,400,800],self.assets['background/asset']],
            [0.5,[850,350,400,800],self.assets['background/asset']],
            [0.25,[1000,450,400,800],self.assets['background/asset']],
            [0.25,[300,350,1200,1600],self.assets['background/asset']],
            [0.5,[4050,250,400,800],self.assets['background/asset']],
            [0.25,[4550,250,400,800],self.assets['background/asset']],
            ]
        
        self.level_map = Level(self,level,self.game_screen)
        #self.load_level()
        
        #Score, time, lives
        self.lives = 3
        self.display = Display(self)
        self.countdown = 3000
        self.highscores = []

        #Miscellenaeous
        self.gameover_black = render(f'GAMEOVER', self.display.display_font_black)
        self.rect1 = self.gameover_black.get_rect(center=(self.game_screen.get_width() // 2, 0))
    
    def loading(self,state):
        #Imitation of loading a level
        start_time = pygame.time.get_ticks()
        finish = False
        
        self.music.stop()

        while not finish:
            self.screen.fill((235,208,6))
            #parallelogram_l(x,y,w,h) left to right
            #parallelogram_r(x,y,w,h) right to left
            #Generates a UI

            parallelogram_l(400,200,150,400,pygame.Color(104,202,161),self.screen)
            parallelogram_l(150,150,100,700,pygame.Color(222,132,2),self.screen)
            parallelogram_l(250,300,220,600,pygame.Color(227,65,50),self.screen)
            parallelogram_l(100,0,100,650,pygame.Color(62,85,163),self.screen)

            self.screen.blit(render("LOADING...!",self.display.display_font_large,gfcolor=pygame.Color("white")),(300,300))
            
            if state == "story":
                self.screen.blit(render("[EMERALD BEACH]",self.display.display_font_large,gfcolor=pygame.Color("white")),(100,240))
            elif state == "wasd":
                self.screen.blit(self.assets['wasd'],(250,200))
                self.screen.blit(self.assets['o'],(450,200))

            time = pygame.time.get_ticks()
            if time - start_time > 5000:
                #Waits 5 seconds before continuing
                finish = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            pygame.display.update()
            self.clock.tick(60)

    def main_menu(self):
        click = False
        particles = []
    
        self.music.play_music(self.assets['menu/music'])

        while True:
            #Generating UI
            self.screen.blit(self.assets['menu/bg'],(0,0))
            parallelogram_r(20,20,330,60,pygame.Color("deeppink"),self.screen)
            parallelogram_r(20,20,300,60,pygame.Color("yellow"),self.screen)
            parallelogram_r(20,20,240,60,pygame.Color("dodgerblue"),self.screen)
            pygame.draw.line(self.screen,pygame.Color("white"),(0,90),(self.screen.get_width(),90),4)
            self.screen.blit(render("MAINMENU",self.display.display_font_large,gfcolor=pygame.Color("white")),(20,20))

            self.screen.blit(self.assets['menu/title'],(400,10))

            #Leaf particle effect (GUI)
            if random.random()*5000000 < self.screen.get_width()*self.screen.get_height():
                pos = (random.random() * self.screen.get_width(), 0)
                particles.append(Particle(self,pos,velocity=[random.random(),random.random()],frame=random.randint(0,20)))

            for particle in particles.copy():
                kill = particle.update()
                particle.render(self.screen,offset=(0,0))
                if kill:
                    particle.remove(particle)

            mx,my = pygame.mouse.get_pos()

            #Buttons 
            adventure = self.assets['menu/button']
            adventure_rect = pygame.Rect(50,200,228,33)
            scoreboard = self.assets['menu/button']
            scoreboard_rect = pygame.Rect(50,300,228,33)
            quit = self.assets['menu/button']
            quit_rect = pygame.Rect(50,400,228,33)

            #checks for mouse collision with buttons
            if adventure_rect.collidepoint((mx,my)):
                if click:
                    self.music.play_sound_effect(self.assets['sound_effect/sonic_letsdothis'])
                    self.loading("story")
                    self.story()
                    self.loading("wasd")
                    self.lives = 3 #resets lives count everytime level is accessed from main menu
                    self.load_level()
                    self.run()
                else:
                    adventure = self.assets['menu/button2']
            if scoreboard_rect.collidepoint((mx,my)):
                if click:
                    self.leaderboard()
                else:
                    scoreboard = self.assets['menu/button2']
            if quit_rect.collidepoint((mx,my)):
                if click:
                    pygame.quit()
                    sys.exit()
                else:
                    quit = self.assets['menu/button2']

            self.screen.blit(adventure,(50,200))
            self.screen.blit(scoreboard,(50,300))
            self.screen.blit(quit,(50,400))
            self.screen.blit(render("ADVENTURE",self.display.display_font_black,gfcolor=pygame.Color("yellow")),(100,190))
            self.screen.blit(render("SCOREBOARD",self.display.display_font_black,gfcolor=pygame.Color("yellow")),(100,290))
            self.screen.blit(render("QUIT",self.display.display_font_black,gfcolor=pygame.Color("yellow")),(140,390))
            
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True
                    if event.button == 2:
                        click = True
                    if event.button == 3:
                        click = True
            
            pygame.display.update()
            self.clock.tick(60)
    
    def leaderboard(self):
        running = True
        particles = []
        self.music.play_music(self.assets['menu/scoreboard_music'])

        #Loads any saved scores before the leaderboard.
        self.load_score()

        while running:
            #creates UI
            self.screen.blit(self.assets['menu/bg-score'],(0,0))
            parallelogram_r(20,20,330,60,pygame.Color("deeppink"),self.screen)
            parallelogram_r(20,20,300,60,pygame.Color("yellow"),self.screen)
            parallelogram_r(20,20,240,60,pygame.Color("dodgerblue"),self.screen)
            pygame.draw.line(self.screen,pygame.Color("white"),(0,90),(self.screen.get_width(),90),4)
            self.screen.blit(render("SCOREBOARD",self.display.display_font_large,gfcolor=pygame.Color("white")),(20,20))

            #Leaf particle effect (GUI) - creates leaves to fall from the top of the screen
            if random.random()*5000000 < self.screen.get_width()*self.screen.get_height():
                pos = (random.random() * self.screen.get_width(), 0)
                particles.append(Particle(self,pos,velocity=[random.random(),random.random()],frame=random.randint(0,20)))

            for particle in particles.copy():
                kill = particle.update()
                particle.render(self.screen,offset=(0,0))
                if kill:
                    particle.remove(particle)
            
            self.screen.blit(self.assets['menu/sonic'], (350,30))

            mx,my = pygame.mouse.get_pos() 

            menu = self.assets['menu/button']
            menu_rect = pygame.Rect(50,400,228,33)

            x_pos,y_pos= 50,120
            for score in self.highscores:
                #rendering text onto screen from file "highscores.txt"
                #does this 5 times as there are 5 scores in highscores 
                score_text = render(f"{str(score)}",self.display.display_font_black,gfcolor=pygame.Color("white"))
                score_rect = pygame.Rect(x_pos,y_pos,228,33)
                parallelogram_r(x_pos,y_pos,220,30,"deeppink",self.screen)
                parallelogram_r(x_pos,y_pos,190,30,"yellow",self.screen)
                self.screen.blit(score_text,score_rect)

                y_pos += 55

            #check collision with back button to go back to menu
            if menu_rect.collidepoint((mx,my)):
                if click:
                    running = False
                else:
                    menu = self.assets['menu/button2']

            self.screen.blit(menu,(50,400))
            self.screen.blit(render("BACK",self.display.display_font_black,gfcolor=pygame.Color("white")),(140,390))

            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True
                
            pygame.display.update()
            self.clock.tick(60)
        
        self.music.play_music(self.assets['menu/music'])

    def save_score(self, score):
        # Read existing high scores
        with open(highscores, "r") as f:
            existing_scores = [int(line.strip()) for line in f]


        print(existing_scores)
        # Add the new score
        existing_scores.append(int(score))

        # Sort the scores in descending order
        existing_scores.sort(reverse=True)
        print (existing_scores)

        # Keep only the top 5 scores
        top_scores = existing_scores[:5]

        # Save the updated scores back to the file
        with open(highscores, "w") as f:
            for top_score in top_scores:
                f.write(f"{top_score}\n")
        
    def load_score(self):
        self.highscores = []
        with open(highscores,"r") as f:
            try:
                for line in f:
                    # Loads the scores into highscores
                    self.highscores.append(line)
            except:
                # Should be 5 empty lines in the score txt 
                # So replace with 0 if there is a blank space
                self.highscores.append(0)

    def load_level(self):
        #Resetting flags, variables, entities
        self.music.play_background_music()
        self.level_map.reset_entity()
        self.start_game = True
        self.end_game = False

        self.chao_interact = False

        self.projectiles = []
        self.sparks = []
        self.rings = []
        self.particles = []

        self.player = Player((32,600),self)
        self.camera_group = CameraGroup(self.game_screen)
        
        self.clouds = Clouds(self.assets['clouds'], count=10)

        self.camera_group.add(self.player)
        self.last_frame_time = pygame.time.get_ticks()
        self.elapsed_time = 0

        self.level_start_x = 0
        self.level_end_x = 5328

        self.s_key_hold = False

        self.countdown = 3000

        self.hurt_time = 0
        self.hurt_frames = 0
        self.dead_frames = 0
        self.end_frames = 0

        self.player.is_dead = False

        self.player.start_level() #resets their score, time, rings and plays start animation
        self.player.start = True

        for sprite in self.level_map.goalpost_sprite:
            sprite.idle = True
            sprite.finish = False
            sprite.spin = False
    
    def gameover(self):
        # the text starts at the top of the screen and keeps moving downwards until it reaches the middle of the screen
        if self.rect1.centery < self.game_screen.get_height() // 2:
            self.game_screen.blit(self.gameover_black, (self.rect1[0],self.rect1[1]))

            self.rect1.centery += 1
        else:
            self.game_screen.blit(self.gameover_black, (self.rect1[0],self.rect1[1]))
    
    def calc_score(self):
        # Depending on the time threshold <30 seconds gets 50k, 30<time<60 seconds gets 25k and >60 seconds gets 5k in score
        if self.display.milliseconds < 30000:
            time = 50000
        elif self.display.milliseconds > 30000 and self.display.milliseconds < 60000:
            time = 25000
        else:
            time = 5000

        # Calculates ring, time and total score
        # Creates text and rects so they can be put onto the screen
        ring_bonus = render(f'RING BONUS:..................{str(int(self.display.ring_count)*100)} ',self.display.display_font_black,gfcolor=pygame.Color("orange"))
        time_bonus = render(f'TIME BONUS:..................{str(time)}' , self.display.display_font_black,gfcolor=pygame.Color("orange"))
        total = render(f'TOTAL:..................{str(int(self.display.ring_count *100) + int(time) + int(self.display.score))}',self.display.display_font_black,gfcolor=pygame.Color("orange"))
        score = (self.display.ring_count * 100) + time + self.display.score
        
        rect1 = ring_bonus.get_rect(center=(self.game_screen.get_width()-self.game_screen.get_width(), self.game_screen.get_height()//2 - 50))
        rect2 = time_bonus.get_rect(center=(0, self.game_screen.get_height()//2 - 80))
        rect3 = total.get_rect(center=(0, self.game_screen.get_height()//2 - 30))

        return ring_bonus,rect1,time_bonus,rect2,total,rect3,score

    def display_score(self,ring_bonus,rect1,time_bonus,rect2,total,rect3):
        # the text starts at the left part of the screen and keeps moving right until it reaches the middle of the screen
        finished = False
        if rect1.centerx < self.game_screen.get_width()//2:
            self.game_screen.blit(ring_bonus,(rect1[0],rect1[1]))
            self.game_screen.blit(time_bonus,(rect2[0],rect2[1]))
            
            rect1.centerx += 4
            rect2.centerx += 4
        else:
            self.game_screen.blit(ring_bonus,(rect1[0],rect1[1]))
            self.game_screen.blit(time_bonus,(rect2[0],rect2[1]))
            finished = True

        # Total displayed after the time and ring bonus
        if finished:
            if rect3.centerx < self.game_screen.get_width()//2:
                self.game_screen.blit(total,(rect3[0],rect3[1]))
                rect3.centerx += 5
            else:
                self.game_screen.blit(total,(rect3[0],rect3[1]))
    
    def story(self):
        story = Story(self)
        running = True
        click = False

        self.music.play_music(self.assets['beach2'])

        # Starting label is Sonic
        name,color = "Sonic the Hegdehog", "skyblue"
        while running:
            self.screen.blit(self.assets['emerald beach'],(0,0))

            pygame.draw.line(self.screen,pygame.Color("white"),(0,330),(self.screen.get_width(),330),10)
            pygame.draw.rect(self.screen,(0,0,0),story.dialoguebox)
            mx,my = pygame.mouse.get_pos() 

            # The characters might pop up/disappear at different points of the story, hence why the need for sonic/tails_show
            # Only blits the characters if their flag is triggered
            if story.sonic_show:
                self.screen.blit(story.character_s,(0,170))
            if story.tails_show:
                self.screen.blit(story.character_t, (500,170))
                
            story.label(name,color)

            if story.check_line():
                story.sound_effect = True

            if name == "Miles 'Tails' Prower":
                #The dialogue is seperated by the first character of the line
                #+ indicates Tails is speaking, so display characters after that character
                story.set_text(story.set_text(story.lines[story.current_line][1:]))
            else:
                story.set_text(story.set_text(story.lines[story.current_line]))

            if story.dialoguebox.collidepoint((mx,my)):
                if click:
                    story.sound_effect = False #Resets the sound effect each time a dialogue is shown so sound effects are only played once
                    if story.next_check():
                        running = False
                    else:
                        name, color = story.next_line()  
            
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True

            pygame.display.update()
            self.clock.tick(60)

    def run(self):
        running = True
        num_repeats = math.ceil((self.game_screen.get_width() / self.bg.get_width()) + 10) #to work out how many times the bg can fit in one screen before needing to be repeated
        while running:
            game_over = False

            #creates scrolling effect with the background
            self.game_screen.fill((0, 152, 248))
            for i in range(-num_repeats,num_repeats):
                self.game_screen.blit(self.bg,(i*self.bg.get_width() + (self.camera_group.offset.x//4),150))

            #Paradox scrolling, clouds and level tiles are updated to move along with the camera of the player
            self.camera_group.parallax_scroll(self.background_objects)
            self.clouds.update()
            self.clouds.render(self.game_screen, offset=(self.camera_group.offset.x, self.camera_group.offset.y))
            self.level_map.update(self.camera_group)

            #Calculating in-game real time
            current_time = pygame.time.get_ticks()
            time_passed = current_time - self.last_frame_time
            self.elapsed_time += time_passed
            self.last_frame_time = current_time

            if self.start_game: #if the level just starts, displays  3..2..1..go!
                start_time = pygame.time.get_ticks()
                if self.countdown == 3000:
                    self.music.play_sound_effect(self.assets['sound_effect/sonic_letsdothis'])
                    self.music.play_sound_effect(self.assets['sound_effect/announcer_3'])
                if self.countdown == 2000:
                    self.music.play_sound_effect(self.assets['sound_effect/announcer_2'])
                if self.countdown == 1000:
                    self.music.play_sound_effect(self.assets['sound_effect/announcer_1'])
                
                self.countdown -= time_passed

                if self.countdown >= 0:
                    # Blit the countdown text at the center of the screen
                    self.text = self.game_screen.blit(render(f'{(self.countdown // 1000)+1}',self.display.display_font_black),(self.game_screen.get_width()//2,self.game_screen.get_height()//2))
                elif self.countdown < 0: 
                    self.text = self.game_screen.blit(render("GO!!!",self.display.display_font_orange,gfcolor=pygame.Color("orange")),(self.game_screen.get_width()//2,self.game_screen.get_height()//2))
                    self.player.start = False
                    if self.countdown < -800:
                        self.text = self.game_screen.blit(render("GO!!!",self.display.display_font_orange,gfcolor=pygame.Color("orange")),(self.game_screen.get_width()//2,self.game_screen.get_height()//2))
                        self.music.play_sound_effect(self.assets['sound_effect/sonic_herewego'])
                        self.music.play_sound_effect(self.assets['sound_effect/announcer_go'])
                        self.start_game = False
                
            #die animation of player
            if self.player.is_dead:
                self.player.fall = True
                self.player.die()

            # the frames following the player's death
            if self.dead_frames>0:
                self.dead_frames += 1
                if self.dead_frames > 360 and self.lives != 0:
                    self.display.seconds = 0 #resets time and entities if player can restart
                    self.display.minutes = 0
                    self.load_level()
                elif self.lives == 0:
                    if self.dead_frames == 160:
                        game_over = True
                    #stop game
                    if self.dead_frames > 160:
                        self.gameover()
                    if self.dead_frames > 1080:
                        running = False
                
            if game_over:
                game_over = False
                pygame.mixer.music.stop()
                self.music.play_sound_effect(self.assets['sound_effect/gameover'])

            #the frame after the player has reached the end of the level
            if self.end_game:
                self.end_frames += 1
                if self.end_frames == 20:
                    self.music.play_sound_effect(self.assets['sound_effect/signpost'])
                if self.end_frames == 60:
                    self.player.control_lock(15000) #freeze player input
                if self.end_frames == 360:
                    for sprite in self.level_map.goalpost_sprite:
                        pygame.mixer.music.stop()
                        self.music.play_sound_effect(self.assets['sound_effect/level_finish'])
                        sprite.spin = False
                        sprite.finish = True
                        ring_bonus,rect1,time_bonus,rect2,total,rect3,score = self.calc_score()

                #display scores, save and go back to the main menu
                if self.end_frames > 360:
                    self.display_score(ring_bonus,rect1,time_bonus,rect2,total,rect3)
                if self.end_frames == 360:
                    self.save_score(score)
                if self.end_frames == 720:
                    self.music.play_sound_effect(random.choice(self.sonic_sounds))
                if self.end_frames == 1080:
                    running = False #breaks out of the running loop so player can go back to the main menu

            #Creates leaf particles that fall from the top of the screen at random positions 
            if random.random()*5000000 < self.game_screen.get_width()*self.game_screen.get_height():
                pos = (random.random() * self.game_screen.get_width(), 0)
                self.particles.append(Particle(self,pos,velocity=[random.random(),random.random()],frame=random.randint(0,20)))

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.game_screen,offset=(0,0))
                if kill:
                    particle.remove(particle) #removes them after they cycled through their animation

            # Checks and updates chao entities
            for chao in self.level_map.chao_sprites:
                chao_pos = (self.camera_group.offset.x,self.camera_group.offset.y)
                chao.update(self.level_map,(0,0))
                chao.render(self.game_screen,offset =chao_pos)

                if self.chao_interact:
                    if self.player.rect.x < 700:
                        self.game_screen.blit(self.assets['op'],(256,230)) #displays tutorial prompt
                    else:
                        self.game_screen.blit(self.assets['so'],(400,150)) #displays tutorial prompt

            # Checks and updates enemy entities
            for enemy in self.level_map.enemy_sprites.copy():
                enemy_pos = (self.camera_group.offset.x,self.camera_group.offset.y+16)
                kill = enemy.update(self.level_map,(0,0))
                enemy.render(self.game_screen,offset =enemy_pos)

                # Checks for player-enemy collision
                if self.player.rect.collidepoint((enemy.rect()[0],enemy.rect()[1])) and not self.player.is_dead:
                    if not(self.player.is_jumping or self.player.is_rolling or self.player.is_homingdash) and not self.player.is_hurt:
                        if self.player.ring_count != 0: #If player has rings, player gets hurt
                            self.player.is_hurt = True

                            self.hurt_time = pygame.time.get_ticks()
                            self.player.hurt()
                            self.hurt_frames += 1
                            self.player.ring_count = 0
                        
                        elif self.player.ring_count == 0: #Else player loses a life and restarts the level/quits the game depending on life count
                            self.player.speed_y = 0
                            self.music.play_sound_effect(self.assets['sound_effect/sonic_die'])
                            self.player.die_anim()
                            self.player.is_dead = True
                            self.lives -= 1
                            self.dead_frames += 1
                        
                    if (self.player.is_jumping or self.player.is_homingdash):
                        self.player.rebound() #Go back up into the air as if the player is bouncing off of the enemy

                if kill: #Removes the enemy off of the screen
                    self.player.score += 1000
                    self.music.play_sound_effect(random.choice(self.sonic_sounds))
                    self.music.play_sound_effect(self.assets['sound_effect/enemy_kill'])
                    self.level_map.enemy_sprites.remove(enemy)
            
            #projectile array --> [[x,y],direction,timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.game_screen.blit(img,(projectile[0][0] - img.get_width()/2 - self.camera_group.offset.x, projectile[0][1] - img.get_height()/2-self.camera_group.offset.y))
                if projectile[2] > 240: #if exceeds the frame time they exist for, destroy the projectile and make them hit against the air
                    for i in range(4):
                        self.sparks.append(Spark(self.projectiles[0][0],random.random()- 0.5 + (math.pi if projectile[1] > 0 else 0), 2+random.random()))
                    self.projectiles.remove(projectile)
                elif not self.player.is_hurt and not self.player.is_dead:
                    if self.player.rect.collidepoint(projectile[0]): #if player collides with the projectile 
                        if self.player.ring_count != 0: # if player has rings, get hurt
                            self.player.is_hurt = True

                            self.hurt_time = pygame.time.get_ticks()
                            self.player.hurt()
                            self.hurt_frames += 1
                            self.player.ring_count = 0
                        
                        elif self.player.ring_count == 0: # else lose a life from the player and restart level/quit back to main menu
                            self.player.speed_y = 0
                            self.player.die_anim()
                            self.music.play_sound_effect(self.assets['sound_effect/sonic_die'])
                            self.player.is_dead = True
                            self.lives -= 1
                            self.dead_frames += 1

                        self.projectiles.remove(projectile)
                        for i in range(30):
                            angle = random.random() *math.pi *2
                            self.sparks.append(Spark(self.player.rect.center,angle,2+random.random())) #player sparks blow up
            
            for spark in self.sparks.copy(): #any sparks generated from enemy or projectile collision is destroyed after set frame period after being created
                pos = (self.camera_group.offset.x, self.camera_group.offset.y)
                kill = spark.update()
                spark.render(self.game_screen,offset=pos)
                if kill:
                    self.sparks.remove(spark)

            # Checks and updates ring entities
            for ring in self.rings.copy():
                pos = (self.camera_group.offset.x, self.camera_group.offset.y)
                kill = ring.update(self.level_map) #remove the ring from the screen
                ring.render(self.game_screen,offset=pos)
                if kill:
                    self.rings.remove(ring)

            # Checks and updates goal post
            for sprite in self.level_map.goalpost_sprite:
                goalpost_pos = (sprite.rect.x - self.camera_group.offset.x, sprite.rect.y - self.camera_group.offset.y)
                self.game_screen.blit(sprite.image, goalpost_pos)

                #Check if player collides with the goal post signifying the end of the level
                if self.player.rect.colliderect(sprite.rect):
                    sprite.spin = True

                sprite.animation()
            
                if sprite.spin:
                    self.end_game = True #Level completes
                    self.end_frames += 1

            #If player gets hurt, generate some sparks 
            if self.hurt_frames>0:
                for i in range(4):
                    angle = random.random() *math.pi *2
                    self.sparks.append(Spark(self.player.rect.center,angle,2+random.random()))
                self.hurt_frames += 1
            if self.hurt_frames == 120: #After 3 seconds, stop hurt aimation
                for i in range(4):
                    angle = random.random() *math.pi *2
                    self.sparks.append(Spark(self.player.rect.center,angle,2+random.random()))

                self.hurt_frames = 0
                self.player.is_hurt = False

            #Substep values to make smaller incremental movements per frame rather than one large movement
            subspeed_x = self.player.speed /self.substep_val
            subspeed_y = self.player.speed_y/self.substep_val
            
            if not self.player.is_dead:
                for i in range(self.substep_val): #Goes through each substep value 60x in a frame
                    #Performs smaller movements and add to the player position
                    substep_movement = subspeed_x / self.substep_val
                
                    if self.player.rect.left < self.level_start_x:
                        self.player.rect.x = self.level_start_x + 2
                        self.player.speed_y = 0
                    if self.player.rect.right >self.level_end_x:
                        self.player.rect.x = self.level_end_x - 32
                        self.player.speed_y = 0

                    self.player.rect.x += substep_movement
                    self.player.detect_wall(self.level_map) #Check for collision after smaller movement

                    substep_movement_y = subspeed_y / self.substep_val

                    # Move the player vertically and check for ground collisions
                    self.player.rect.y += substep_movement_y
                    self.player.detect_ground(self.level_map)


            # Call the player-entity(springs, rings) collision methods
            if not self.player.is_dead:
                self.player.spring_collision(self.level_map, self.music, self.screen)
                self.player.ring_collision(self.level_map,self.music,coll_type=None)
            
                if current_time - self.hurt_time > 2500:
                    self.player.ring_collision(self.level_map,self.music,coll_type=True)

                if self.player.ring_count != 0:
                    if self.player.ring_count % 100 ==0:
                        self.player.add_life()
                        self.music.play_sound_effect(random.choice(self.sonic_sounds))
                
                if self.player.score != 0:
                    if self.player.score % 10000 == 0: #For every 10,000 in score, Sonic audio is played to let player know they are progressing
                        self.music.play_sound_effect(random.choice(self.sonic_sounds))
            
            # Displays relevant game information
            self.display.ingame_display(self.game_screen,self.player.ring_count,self.player.score,self.lives,start_time)

            # Idle animation timers
            if self.player.idle or self.player.bored or self.player.bored1:
                if self.elapsed_time >= 4000:
                    self.player.bored = True
                    self.player.bored1 = False
                if self.elapsed_time >= 16000:
                    self.player.bored = False
                    self.player.bored1 = True
                if self.player.bored1 and not self.player.idle:
                    self.player.bored1 = False
            else:
                self.elapsed_time = 0
                self.player.bored = False
                self.player.bored1 = False

            # Movement handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and not self.player.lock_controls:
                    if event.key == pygame.K_w:
                        if self.player.is_grounded:
                            self.player.is_lookup = True
                    if event.key == pygame.K_s:
                        if self.player.is_grounded:
                            if not self.player.is_crouching and self.player.is_grounded:
                                #Crouch
                                self.player.is_crouching = True
                                self.s_key_hold = True

                                #Roll if moving in a direction/crouching while moving    
                                if (self.player.direction.x != 0 or self.player.speed !=0) and self.player.is_crouching:
                                    self.player.rolling()
                            else:
                                self.player.is_crouching = False
                                self.player.is_rolling = False
                                
                    if event.key == pygame.K_o: # Spindash if player is pressing s, and hasn't moved
                        if self.s_key_hold and self.player.direction.x == 0 and self.player.speed == 0:
                            self.player.is_crouching = False
                            self.player.is_rolling = False
                            self.player.is_charging_spindash = True
                            self.music.play_sound_effect(self.assets['sound_effect/spindash'])

                        if not self.player.is_jumping and self.player.is_grounded and not self.player.is_charging_spindash: #Make player jump
                            self.player.direction.y = -1
                            self.player.is_jumping = True
                            self.player.is_springjump = False
                            self.player.is_grounded = False
                            self.player.is_crouching = False

                            #to reset the homing dash
                            self.player.is_homingdash = False
                            self.player.jump()
                
                if event.type == pygame.KEYUP and not self.player.lock_controls:
                    if event.key == pygame.K_w:
                        if self.player.is_grounded:
                            self.player.is_lookup = False
                        
                    if event.key == pygame.K_s: #No longer crouching while spindashing accelerates player forward as spindash is executed
                        self.s_key_hold = False
                        if self.player.is_grounded and self.player.is_charging_spindash and self.player.direction.x == 0 and self.player.speed == 0:
                          self.music.play_sound_effect(self.assets['sound_effect/spindashfinish'])
                          self.player.is_charging_spindash = False 
                          self.player.is_spindashing = True
                        else:
                            self.player.is_charging_spindash = False

                        self.player.is_rolling = False
                        self.player.is_crouching = False                         
            
            self.camera_group.update()  #Update player camera + display
            if not self.player.is_dead:  
                self.camera_group.custom_draw(self.player)  
            else:
                self.game_screen.blit(pygame.transform.rotate(pygame.transform.flip(self.player.animation.img(),self.player.flip,False),self.player.angle),(self.player.rect.x - self.camera_group.offset.x, self.player.rect.y - self.camera_group.offset.y))   

            self.screen.blit(pygame.transform.scale(self.game_screen, self.screen.get_size()), (0,0)) 
            pygame.display.update()
            self.clock.tick(60)
        
        if not running:
            self.loading("adventure")
            self.music.play_music(self.assets['menu/music'])

#Instantiate the game
game = Game()
game.main_menu()
