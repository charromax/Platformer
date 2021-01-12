import pygame
from pygame.locals import *
import os
import random
import sys
from config import *

pygame.mixer.pre_init()
pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption(GAME_TITLE)

screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
scale_screen = pygame.Surface((SCALE_W, SCALE_H))
running = True

# player_image = pygame.image.load(os.path.join("assets", "p1_stand.png"))
# player_image.set_colorkey(COLOR_WHITE)
grass_top = pygame.image.load(os.path.join("assets", "grass.png"))
dirt = pygame.image.load(os.path.join("assets", "dirt.png"))
background = pygame.image.load(os.path.join("assets", "background.png"))

jump = pygame.mixer.Sound(os.path.join("assets", "jump.wav"))
grass_sounds = [pygame.mixer.Sound(os.path.join("assets", "grass_0.flac")), pygame.mixer.Sound(os.path.join("assets", "grass_1.flac"))]
jump.set_volume(SOUND_FX_VOL)
grass_sounds[0].set_volume(SOUND_FX_VOL)
grass_sounds[1].set_volume(SOUND_FX_VOL)
pygame.mixer.set_num_channels(64)
pygame.mixer.music.load(os.path.join("assets", "music_1.ogg"))
pygame.mixer.music.set_volume(MUSIC_VOL)
pygame.mixer.music.play(-1)

player_width = 16
player_x = SCALE_W / 2 - player_width / 2
player_height = 22
player_y = SCALE_H / 2 - player_height / 2
player_y_momentum = 0 #jump acceleration
player_rect = pygame.Rect(player_x, player_y, player_width, player_height) 

moving_right = False #flags to determine direction of movement
moving_left = False

true_scroll = [0,0]
global animation_frames
animation_frames = {}


#BUILD LEVEL  - COORDS ARE IN REVERSE FORMAT [Y,X]
def read_map_file():
    file = open(os.path.join("assets", "level1.txt"), 'r')
    level = file.read()
    file.close()
    level = level.split('\n')
    game_map=[]
    for row in level:
        game_map.append(row)
    return game_map

def draw_map():
    y = 0
    for row in game_map:
        x = 0
        for tile in row:
            if tile == '1':
                scale_screen.blit(dirt, (x*dirt.get_width() - scroll[0], y*dirt.get_height() - scroll[1]))
            if tile == '2':
                scale_screen.blit(grass_top, (x*dirt.get_width() - scroll[0], y*dirt.get_height() - scroll[1]))
            
            if tile != '0':
                tile_rects.append(pygame.Rect(x*16, y*16, 16, 16))   #tiles are 16px x 16px in size

            x+=1
        y+=1

def draw_background_objects(objects, scroll):
    for object in objects:
        object_rect = pygame.Rect(object[1][0] - scroll[0] * object[0],     # X
                                    object[1][1] - scroll[1] * object[0],   # Y
                                    object[1][2],                           # WIDTH
                                    object[1][3])                           # HEIGHT
        if object[0] == 0.8:
            pygame.draw.rect(scale_screen, COLOR_BLUE_DARK, object_rect)
        elif object[0] == 0.25:
            pygame.draw.rect(scale_screen, COLOR_BLUE_LIGHT, object_rect)

def load_animations(path, frame_duration):
    global animation_frames
    anim_name = path.split('/')[-1]
    anim_frames_data = []
    n = 0
    for frame in frame_duration:
        anim_frame_id = anim_name + '_' + str(n)
        anim_location = f"{path}/{anim_frame_id}.png"
        anim_image = pygame.image.load(anim_location).convert()
        anim_image.set_colorkey(COLOR_WHITE)
        animation_frames[anim_frame_id] = anim_image.copy()
        for i in range(frame):
            anim_frames_data.append(anim_frame_id)
        n+= 1
    return anim_frames_data

def collision_test(obj, tiles):
    """checks for collision between an object ie. the player

    Args:
        object (rect): rect corresponding to the object that needs colliding
    and the tiles in the map
        tiles (list[rect]): tiles in the map that are susceptible of collision

    Returns:
        List of tiles that collided with object
    """
    hit_list= []
    for tile in tiles:
        if obj.colliderect(tile):
            hit_list.append(tile)
    return hit_list

def move(obj, path, tiles):
    """moves object provided as rect, checks for collisions
    and updates screen 

    Args:
        obj (rect): object to move
        path (tuple): direction of movement as [x,y]
        tiles (list[rect]): list of tiles that the object can collide with

    Returns:
        collision_types: Map indicating where the collision was produced
        object: The object being moved
    """
    collision_types = {'top':False,'bottom':False,'left':False,'right':False}

    #CHECK HORIZONTAL MOVEMENT
    obj.x += path[0]
    hit_list = collision_test(obj, tiles)
    for tile in hit_list:

        if path[0] > 0:         #if moving right
            obj.right = tile.left
            collision_types['right'] = True         #object collided with left side of tile
        elif path[0] < 0:
            obj.left = tile.right
            collision_types['left'] = True          #object collided with right side of tile

    #CHECK VERTICAL MOVEMENT
    obj.y += path[1]
    hit_list = collision_test(obj, tiles)

    for tile in hit_list:

        if path[1] > 0:         #if moving right
            obj.bottom = tile.top
            collision_types['bottom'] = True         #object collided with top side of tile
        elif path[1] < 0:
            obj.top = tile.bottom
            collision_types['top'] = True          #object collided with bottom side of tile
    
    return obj, collision_types

def change_action(action_var, frame, new_value):
    if action_var != new_value:
         action_var = new_value
         frame = 0
    return action_var, frame

#LOAD ANIMATIONS FOR PLAYER
animation_database = {}
animation_database['run'] = load_animations('assets/player/run', [7,7,7,7])
animation_database['idle'] = load_animations('assets/player/idle', [7])

player_action = 'idle'
player_frame = 0
player_flip = False

grass_sound_timer = 0

game_map = read_map_file()
background_objects = [[0.8, [120, 10, 70, 400]], [0.8, [370, 50, 200, 50]], [0.25, [50, 180, 70, 150]],[0.25, [250, 15, 170, 40]]]

while running:
    scale_screen.blit(background, (0,0))
    
    clock.tick(FPS)
    true_scroll[0] += (player_rect.x - true_scroll[0] - (SCALE_W/2) - (player_width/2)) / 20
    true_scroll[1] += (player_rect.y - true_scroll[1] - (SCALE_H/2) - (player_height/2)) / 20
    scroll = true_scroll.copy()
    scroll[0] = int(true_scroll[0])
    scroll[1] = int(true_scroll[1])
    draw_background_objects(background_objects, scroll)
    tile_rects= []    #keeps track of tiles in the map to collide with

    draw_map()

    if grass_sound_timer > 0:
        grass_sound_timer -= 1
    
    player_y_momentum += PLAYER_MOMENTUM_RATE

    player_movement = [0,0]
    

    if moving_right:
        player_movement[0] += PLAYER_SPEED
        
    if moving_left: 
        player_movement[0] -= PLAYER_SPEED
        
    player_movement[1] += player_y_momentum
    if player_y_momentum > 5:
        player_y_momentum = 5     

    if player_movement[0] == 0:
        player_action, player_frame = change_action(player_action, player_frame, 'idle')
    
    if player_movement[0] < 0:
        player_action, player_frame = change_action(player_action, player_frame, 'run')
        player_flip = True

    if player_movement[0] > 0:
        player_action, player_frame = change_action(player_action, player_frame, 'run')
        player_flip = False
    player_rect, collision_directions = move(player_rect, player_movement, tile_rects)


    if collision_directions['bottom']:        #makes the player fall slower after having hit the ground or a platform
        player_y_momentum = 0
        if player_movement[0] != 0 and grass_sound_timer == 0:
            grass_sound_timer = 30
            random.choice(grass_sounds).play()

    if collision_directions['top']:
        player_y_momentum = -player_y_momentum   #this is so that the head of the character doesnt stick to the bottom of tiles
    
    player_frame += 1

    #RESET LOOP IF ANIMATION IS AT THE LAST FRAME
    if player_frame >= len(animation_database[player_action]):
        player_frame = 0

    player_image_id = animation_database[player_action][player_frame]
    player_image = animation_frames[player_image_id]

    scale_screen.blit(pygame.transform.flip(player_image, player_flip, False), (player_rect.x - scroll[0], player_rect.y - scroll[1])) #draw player

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:

            if event.key == K_LEFT:
                moving_left = True

            if event.key == K_RIGHT:
                moving_right = True

            if event.key == K_SPACE:
                player_y_momentum = -5
                jump.play()

        if event.type == pygame.KEYUP:
            if event.key == K_LEFT:
                moving_left = False
            if event.key == K_RIGHT:
                moving_right = False

    # if keys[pygame.K_DOWN]:
    #     player_y -= PLAYER_SPEED 
    #     player_y += PLAYER_SPEED

    screen.blit(pygame.transform.scale(scale_screen, (GAME_WIDTH,GAME_HEIGHT)), (0,0))
    pygame.display.update()


