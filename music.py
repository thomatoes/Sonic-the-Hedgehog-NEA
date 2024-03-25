import pygame
pygame.init()

class Music:
    def __init__(self):
        pygame.mixer.pre_init()
        pygame.mixer.init()

        #in game music files
        self.green_grove = "audio/05. Leaf Forest Zone - Act 1.mp3"

        #sound effects
        self.rings = "audio/sonic_ring_sound_effect.mp3"
        self.spring = "audio/sonic-spring.mp3"

    def play_background_music(self):
        pygame.mixer.music.load(self.green_grove)
        pygame.mixer.music.play(-1)
    
    def play_music(self,music):
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)
  
    def play_sound_effect(self,sound_file):
        sound = pygame.mixer.Sound(sound_file)
        sound.play()
    
    def stop(self):
        pygame.mixer.music.stop()