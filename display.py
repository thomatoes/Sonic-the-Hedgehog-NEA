import pygame

#This function efficiently generates a list of integer coordinates representing points on the circumference
#of a circle with radius r using Bresenham's Circle Drawing Algorithm to optimize the calculation process
_circle_cache = {}
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


class Display:
    def __init__(self,game):
        self.game = game
        self.outline = pygame.font.Font("fonts/srb2-outline/srb2-outline.ttf",30)
        self.display_font_black = pygame.font.Font("fonts/sonic-1-hud-font/sonic-1-hud-font.ttf", 25)
        self.display_font_orange = pygame.font.Font("fonts/sonic-1-hud-font/sonic-1-hud-font.ttf", 45)
        self.display_font_white = pygame.font.Font("fonts/sonic-1-hud-font/sonic-1-hud-font.ttf", 23)
        self.display_font_large = pygame.font.Font("fonts/sonic-1-hud-font/sonic-1-hud-font.ttf", 57)
        
        #time
        self.milliseconds = 0
        self.minutes = 0
        self.seconds = 0

        #rings
        self.ring_count = 0

        #score
        self.score = 0

        #lives
        self.lives = 3
    
    def get_score(self,score):
        self.score_str = str(score).zfill(5)

    def get_rings(self, ring_count):
        self.ring_count = int(ring_count)
        self.ring_count_str = str(self.ring_count).zfill(3)
    
    def get_lives(self,lives):
        self.lives = int(lives)
    
    def get_time(self,time):
        self.milliseconds = pygame.time.get_ticks() - time
        self.seconds = int((self.milliseconds / 1000) % 60)
        self.minutes = int(self.milliseconds / 60000)

        # Format seconds to have leading zeros
        self.seconds_str = str(self.seconds).zfill(2)
    

    def ingame_display(self, screen,ring_count,score,lives,time):
        if not self.game.end_game:
            self.get_time(time=time)
        self.get_rings(ring_count)
        self.get_score(score)
        self.get_lives(lives)

        screen.blit(render(f'TIME: {self.minutes}:{self.seconds_str}', self.display_font_black), (20, 54))
        screen.blit(render(f'RINGS: {self.ring_count_str}',self.display_font_black),(20,74))
        screen.blit(render(f'SCORE:{self.score_str}',self.display_font_black),(20,34))
        screen.blit(render(f'{self.lives}',self.display_font_black),(20,94))
    
        
