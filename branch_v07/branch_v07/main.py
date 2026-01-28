from core.window import create_window, should_close, update_inputs
from core.renderer import load_shader_program, load_obj, load_texture, create_vao, render_scene, GROUND_VERTICES
from core.renderer import load_ui_shader, create_screen_quad, create_empty_texture, update_texture, render_ui
from OpenGL.GL import *
import glfw
import glm
import numpy as np
import itertools
import math
import random
from PIL import Image, ImageDraw, ImageFont

#CONFIG
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
FOV_DEFAULT = 60.0
FOV, NEAR, FAR = FOV_DEFAULT, 0.1, 150.0 

#Consts do jogo
GAME_SPEED_INITIAL = 20.0
GAME_SPEED = GAME_SPEED_INITIAL
TARGET_GAME_SPEED = GAME_SPEED_INITIAL
MAX_GAME_SPEED = 50.0
SPEED_INCREMENT_PER_COIN = 0.5
OBSTACLE_BOOST_SPEED = 40.0 
OBS_BOOST_SPEED_CHANCE = 0.25
PLANE_LENGTH = 50.0  
TRACK_SEGMENT_LEN = 1.0 
CULL_DISTANCE = 80.0 

#Consts de base
GROUND_Y = -1.05 
TRACK_Y = -1.0
PLAYER_BASE_Y = -1.0 
PLAYER_DEPTH = -3.0

TRILHOS = [-1.5, 0.0, 1.5] 
LATERAL_SPEED = 12.0 

SPACING_Z = 20.0 
MAX_OBSTACLES = 25 
MAX_ROCKS = 15     

#Física
PLAYER_SCALE = 1.0 
GRAVITY = -60.0 
JUMP_VELOCITY = 18.0 
RAMP_BOOST_Y = 20.0 

SUN_ORBIT_RADIUS = 60.0
TIME_SPEED = 0.2 

#Camera
CAMERA_DIST_DEFAULT = 6.0
CAMERA_DIST_MIN = 3.5  
CAMERA_DIST_MAX = 12.0 
ZOOM_SPEED = 5.0 

#Estados
STATE_WAITING = 0
STATE_RUNNING = 1
STATE_PAUSED = 2
STATE_GAMEOVER = 3
game_state = STATE_WAITING

#Tipos de Objetos
TYPE_TRAIN_A = "train_a" 
TYPE_TRAIN_B = "train_b" 
TYPE_TRAIN_C = "train_c" 
TYPE_WALL    = "wall"
TYPE_RAMP    = "ramp"
TYPE_PLANET  = "planet"
TYPE_COIN    = "coin"

#Buffs e nerfs
PLAYER_STATE_NORMAL = 0
PLAYER_STATE_BUFF_GOLD = 1 
PLAYER_STATE_NERF_QUAKE = 2 
STATE_DURATION = 10.0

player = {
    "y": PLAYER_BASE_Y,
    "vy": 0.0,
    "on_ground": True,
    "standing_on": None, 
    "run_time": 0.0,
    "score": 0,
    "state": PLAYER_STATE_NORMAL,
    "state_timer": 0.0
}

#Para controlar
z_offset = 0.0
trilho_atual_index = 1
target_x_position = TRILHOS[trilho_atual_index]
current_x_position = TRILHOS[trilho_atual_index]
key_pressed_left = False
key_pressed_right = False
esc_pressed = False 
game_time_accumulator = 0.0

obstacles = [] 
rocks = [] 
coins = []
_obj_id_counter = itertools.count(1)

meshes = {}
textures = {}

#UI
ui_shader = None
ui_vao = None
ui_texture_id = None
ui_image_pil = None
last_score = -1
ui_dirty = True

def init_ui():
    global ui_shader, ui_vao, ui_texture_id, ui_image_pil
    ui_shader = load_ui_shader()
    ui_vao = create_screen_quad()
    ui_texture_id = create_empty_texture(WINDOW_WIDTH, WINDOW_HEIGHT)
    ui_image_pil = Image.new("RGBA", (WINDOW_WIDTH, WINDOW_HEIGHT), (0,0,0,0))

def update_ui_texture():
    global ui_dirty, last_score, ui_image_pil
    
    if not ui_dirty and player['score'] == last_score and game_state == STATE_RUNNING:
        return

    last_score = player['score']
    ui_dirty = False
    
    ui_image_pil.paste((0,0,0,0), [0,0,ui_image_pil.size[0], ui_image_pil.size[1]])
    draw = ImageDraw.Draw(ui_image_pil)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    if game_state == STATE_WAITING:
        draw.rectangle([0, 0, WINDOW_WIDTH, WINDOW_HEIGHT], fill=(0, 0, 0, 150))
        
        text = "Pressione a tecla SPACE para Iniciar"
        bbox = draw.textbbox((0,0), text, font=font_large)
        w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text(((WINDOW_WIDTH - w)/2, (WINDOW_HEIGHT - h)/2 + 100), text, font=font_large, fill=(255, 255, 255, 255))
        
        title = "CG SURFERS"
        bbox2 = draw.textbbox((0,0), title, font=font_large)
        w2 = bbox2[2]-bbox2[0]
        draw.text(((WINDOW_WIDTH - w2)/2, 100), title, font=font_large, fill=(255, 215, 0, 255))

    elif game_state == STATE_GAMEOVER:
        draw.rectangle([0, 0, WINDOW_WIDTH, WINDOW_HEIGHT], fill=(50, 0, 0, 180))
        
        text1 = "GAME OVER"
        text2 = f"Pontuação Final: {player['score']}"
        text3 = "Pressione SPACE para Reiniciar"
        
        for i, (txt, color) in enumerate([(text1, (255,0,0)), (text2, (255,255,255)), (text3, (200,200,200))]):
            bbox = draw.textbbox((0,0), txt, font=font_large)
            w = bbox[2]-bbox[0]
            draw.text(((WINDOW_WIDTH - w)/2, 200 + i*60), txt, font=font_large, fill=color)

    elif game_state == STATE_RUNNING or game_state == STATE_PAUSED:
        #Contador de Moedas
        coin_text = f"Moedas: {player['score']}"
        bbox = draw.textbbox((0,0), coin_text, font=font_small)
        w = bbox[2]-bbox[0]

        draw.rectangle([WINDOW_WIDTH - w - 30, 10, WINDOW_WIDTH - 10, 50], fill=(0,0,0,100))
        draw.text((WINDOW_WIDTH - w - 20, 20), coin_text, font=font_small, fill=(255, 215, 0))

        if game_state == STATE_PAUSED:
            draw.rectangle([0, 0, WINDOW_WIDTH, WINDOW_HEIGHT], fill=(0, 0, 0, 100))
            draw.text((WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2), "PAUSADO", font=font_large, fill=(255,255,255))

    update_texture(ui_texture_id, ui_image_pil)


def reset_game():
    global GAME_SPEED, TARGET_GAME_SPEED, z_offset, trilho_atual_index, target_x_position, current_x_position
    global obstacles, rocks, coins, game_time_accumulator, game_state, ui_dirty
    
    player["y"] = PLAYER_BASE_Y
    player["vy"] = 0.0
    player["on_ground"] = True
    player["standing_on"] = None
    player["score"] = 0
    player["state"] = PLAYER_STATE_NORMAL
    player["state_timer"] = 0.0

    GAME_SPEED = GAME_SPEED_INITIAL
    TARGET_GAME_SPEED = GAME_SPEED_INITIAL
    z_offset = 0.0
    trilho_atual_index = 1
    target_x_position = TRILHOS[trilho_atual_index]
    current_x_position = TRILHOS[trilho_atual_index]
    game_time_accumulator = 0.0 
    
    obstacles.clear()
    rocks.clear()
    coins.clear()
    
    spawn_game_object(-30) 
    for _ in range(10): spawn_rock(random.uniform(-10, -50))
    
    game_state = STATE_RUNNING
    ui_dirty = True
    print("=== JOGO INICIADO ===")

#Ambiente
def get_sky_color(sun_y):
    if sun_y > 15.0: return glm.vec3(0.53, 0.81, 0.92) 
    elif sun_y > -5.0:
        t = (sun_y + 5.0) / 20.0 
        return glm.mix(glm.vec3(0.1, 0.1, 0.15), glm.vec3(0.8, 0.5, 0.2), t)
    else: return glm.vec3(0.05, 0.05, 0.08)

def spawn_rock(z_pos):
    side = random.choice([-1, 1])
    dist = random.uniform(4.0, 15.0)
    x_pos = side * dist
    rocks.append({
        "x": x_pos, "z": z_pos,
        "scale": random.uniform(0.8, 2.0), "rot": random.uniform(0, 360)
    })

def update_rocks(delta_time):
    for rock in rocks: rock["z"] += GAME_SPEED * delta_time
    rocks[:] = [r for r in rocks if r["z"] < 20.0] 
    while len(rocks) < MAX_ROCKS:
        furthest_z = min(r["z"] for r in rocks) if rocks else -50
        spawn_rock(furthest_z - random.uniform(5.0, 15.0))

#SPAWN
def create_obj_entry(otype, trilho, z, mesh_key, speed=GAME_SPEED, height=1.0, length=2.0, y_offset=0.0):
    return {
        "id": next(_obj_id_counter), "type": otype, "trilho": trilho, "z": float(z),
        "mesh": mesh_key, "speed": float(speed), "height": height, "length": length, 
        "y_offset": y_offset, "is_collided": False, "collected": False 
    }

def spawn_coin_pattern(start_z):
    trilho = random.randint(0, 2)
    for i in range(5):
        coins.append({"id": next(_obj_id_counter), "trilho": trilho, "z": start_z - (i * 1.5), "y": 0.5, "active": True})

def spawn_game_object(z_position):
    r = random.random()
    trilho = random.randint(0, 2)
    speed = GAME_SPEED
    
    same_track_obs = [o for o in obstacles if o['trilho'] == trilho]
    if not same_track_obs or min(same_track_obs, key=lambda o: o['z'])['speed'] > GAME_SPEED + 1.0:
        if random.random() < OBS_BOOST_SPEED_CHANCE: speed = OBSTACLE_BOOST_SPEED

    new_obs_list = []
    
    if r < 0.60: # Trens
        ttype = random.choice([TYPE_TRAIN_A, TYPE_TRAIN_B, TYPE_TRAIN_C])
        if ttype == TYPE_TRAIN_A: 
            new_obs_list.append(create_obj_entry(TYPE_TRAIN_A, trilho, z_position, "train_a_head", speed, length=1.5))
            new_obs_list.append(create_obj_entry(TYPE_TRAIN_A, trilho, z_position-2.8, "train_a_mid", speed, length=1.5))
            new_obs_list.append(create_obj_entry(TYPE_TRAIN_A, trilho, z_position-5.6, "train_a_mid", speed, length=1.5))
        elif ttype == TYPE_TRAIN_B:
            new_obs_list.append(create_obj_entry(TYPE_TRAIN_B, trilho, z_position, "train_b_head", speed, length=1.4))
            new_obs_list.append(create_obj_entry(TYPE_TRAIN_B, trilho, z_position-2.4, "train_b_wag", speed, length=1.4))
        elif ttype == TYPE_TRAIN_C:
            new_obs_list.append(create_obj_entry(TYPE_TRAIN_C, trilho, z_position, "train_c", speed, length=1.5))
    elif r < 0.70: # Parede
        new_obs_list.append(create_obj_entry(TYPE_WALL, trilho, z_position, "wall_door", GAME_SPEED, height=2.5, length=0.2))
    elif r < 0.80: # Rampa
        new_obs_list.append(create_obj_entry(TYPE_RAMP, trilho, z_position, "ramp", GAME_SPEED, height=0.5, length=1.2))
        spawn_coin_pattern(z_position - 5.0)
    elif r < 0.85: # Planeta
        obs = create_obj_entry(TYPE_PLANET, trilho, z_position, "planet", GAME_SPEED, height=1.0, length=0.5)
        obs['y_offset'] = 0.5 
        new_obs_list.append(obs)
    else: spawn_coin_pattern(z_position)
    obstacles.extend(new_obs_list)

def update_objects(delta_time):
    for obs in obstacles: obs["z"] += obs["speed"] * delta_time
    obstacles[:] = [obs for obs in obstacles if obs["z"] < 10.0]
    for c in coins: c["z"] += GAME_SPEED * delta_time
    coins[:] = [c for c in coins if c["z"] < 10.0]
    while len(obstacles) < MAX_OBSTACLES:
        last_z = min((obs["z"] for obs in obstacles), default=-40.0)
        spawn_game_object(last_z - SPACING_Z - random.uniform(0, 5))

#COLISÃO
def get_obstacle_aabb(obs):
    x, z, y = TRILHOS[obs["trilho"]], obs["z"], TRACK_Y + obs.get('y_offset', 0.0)
    w, h, l = 0.5, obs['height'], obs['length']
    return {
        "min_x": x-w, "max_x": x+w, 
        "min_y": y,   "max_y": y+h, 
        "min_z": z-l, "max_z": z+l, 
        "top_y": y+h
    }

def check_collisions(delta_time):
    global GAME_SPEED, TARGET_GAME_SPEED, game_state, ui_dirty
    px, py, pz = current_x_position, player["y"], PLAYER_DEPTH
    pw = 0.25

    for obs in obstacles:
        if obs['is_collided']: continue
        if player["standing_on"] and player["standing_on"]["id"] == obs["id"]: continue
        if abs(obs['z'] - pz) > 5.0: continue

        box = get_obstacle_aabb(obs)
        cx = (px + pw > box["min_x"]) and (px - pw < box["max_x"])
        cy = (py < box["max_y"]) and (py + 1.0 > box["min_y"]) 
        cz = (pz + 0.3 > box["min_z"]) and (pz - 0.3 < box["max_z"])
        
        if cx and cz:
            if obs['type'] == TYPE_RAMP and cy:
                player['vy'] = RAMP_BOOST_Y; player['on_ground'] = False; player['standing_on'] = None; obs['is_collided'] = True
            elif obs['type'] == TYPE_PLANET and cy:
                if random.random() < 0.5:
                    player['state'], player['state_timer'] = PLAYER_STATE_BUFF_GOLD, STATE_DURATION
                else:
                    player['state'], player['state_timer'] = PLAYER_STATE_NERF_QUAKE, STATE_DURATION
                obs['is_collided'] = True; obs['z'] = 100
            elif obs['type'] == TYPE_WALL and py > box['max_y'] - 0.5:
                game_state = STATE_GAMEOVER
                ui_dirty = True
                print("MORTE: Parede")
            elif "train" in obs['type']:
                if player['vy'] <= 0 and py >= box['max_y'] - 0.2:
                     player["y"] = box["top_y"] + 0.6
                     player["vy"] = 0.0
                     player["on_ground"] = False
                     player["standing_on"] = obs
                elif cy:
                    game_state = STATE_GAMEOVER
                    ui_dirty = True
                    print("MORTE: Trem")

    for c in coins:
        if not c['active']: continue
        if abs(c['z'] - pz) > 2.0: continue 

        hit_z = abs(pz - c['z']) < 1.0 
        hit_x = abs(px - TRILHOS[c['trilho']]) < 0.6
        hit_y = (py < c['y'] + 0.5) and (py + 1.8 > c['y'] - 0.2)

        if hit_x and hit_z and hit_y:
            c['active'] = False
            player['score'] += 2 if player['state'] == PLAYER_STATE_BUFF_GOLD else 1
            if TARGET_GAME_SPEED < MAX_GAME_SPEED: TARGET_GAME_SPEED += SPEED_INCREMENT_PER_COIN
            ui_dirty = True

def update_player_state(delta_time):
    if player['state'] != PLAYER_STATE_NORMAL:
        player['state_timer'] -= delta_time
        if player['state_timer'] <= 0: player['state'] = PLAYER_STATE_NORMAL

def get_input(window):
    return update_inputs(window)




def main():
    global z_offset, trilho_atual_index, target_x_position, current_x_position
    global key_pressed_left, key_pressed_right, GAME_SPEED, TARGET_GAME_SPEED
    global game_state, esc_pressed, game_time_accumulator, ui_dirty

    window = create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "CG Surfers - Final")
    shader = load_shader_program("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    
    init_ui()

    tex_rock = load_texture("assets/colormap-rocks.png")
    tex_char = load_texture("assets/colormap-character-male-e.png")
    tex_track = load_texture("assets/colormap-track-detailed.png")
    tex_ground = load_texture("assets/ground-texture.png")
    textures.update({"rock": tex_rock, "char": tex_char, "track": tex_track, "ground": tex_ground})

    def load_mesh(key, path):
        try: meshes[key] = create_vao(load_obj(path))
        except: meshes[key] = meshes.get("track_rail", create_vao(load_obj("assets/track-detailed.obj")))

    meshes["ground"] = create_vao(np.array(GROUND_VERTICES, dtype=np.float32))
    meshes["player"] = create_vao(load_obj("assets/character-male-e.obj"))
    meshes["track_rail"] = create_vao(load_obj("assets/track-detailed.obj"))
    meshes["rock"] = create_vao(load_obj("assets/rocks.obj"))
    
    for k, p in [("train_a_head", "assets/train-electric-bullet-a.obj"), ("train_a_mid", "assets/train-electric-bullet-b.obj"),
                 ("train_b_head", "assets/train-electric-subway-a.obj"), ("train_b_wag", "assets/train-electric-subway-b.obj"),
                 ("train_c", "assets/train-carriage-container-green.obj"), ("wall_door", "assets/wall-door-wide.obj"),
                 ("ramp", "assets/stairs-ramp.obj"), ("planet", "assets/table-display-planet.obj"),
                 ("coin_silver", "assets/item-coin-silver.obj"), ("coin_gold", "assets/item-coin-gold.obj")]:
        load_mesh(k, p)

    glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    game_state = STATE_WAITING 
    ui_dirty = True
    last_time = glfw.get_time()
    current_camera_dist = CAMERA_DIST_DEFAULT

    while not should_close(window):
        current_time = glfw.get_time()
        delta_time = current_time - last_time
        last_time = current_time

        if game_state == STATE_WAITING:
            delta_time = 0 
            game_time_accumulator += 0.01
            if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS or glfw.get_key(window, glfw.KEY_ENTER) == glfw.PRESS:
                reset_game()
                game_state = STATE_RUNNING
                ui_dirty = True
        
        elif game_state == STATE_PAUSED:
            delta_time = 0
            if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
                if not esc_pressed: 
                    game_state = STATE_RUNNING; esc_pressed = True; ui_dirty = True
            else: esc_pressed = False
            
        elif game_state == STATE_RUNNING:
            game_time_accumulator += delta_time
            if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
                if not esc_pressed: 
                    game_state = STATE_PAUSED; esc_pressed = True; ui_dirty = True
            else: esc_pressed = False
            
            if GAME_SPEED < TARGET_GAME_SPEED: GAME_SPEED += delta_time * 0.5
            z_offset += GAME_SPEED * delta_time
            if z_offset >= PLANE_LENGTH: z_offset -= PLANE_LENGTH
            
            update_objects(delta_time)
            update_rocks(delta_time)
            
            move_dir = get_input(window)
            if move_dir == -1 and not key_pressed_left and trilho_atual_index > 0: trilho_atual_index -= 1
            elif move_dir == 1 and not key_pressed_right and trilho_atual_index < 2: trilho_atual_index += 1
            target_x_position = TRILHOS[trilho_atual_index]
            key_pressed_left, key_pressed_right = (move_dir == -1), (move_dir == 1)

            if (glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS or glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS) \
            and abs(player["vy"]) < 0.001:
                player['vy'] = JUMP_VELOCITY; player['on_ground'] = False; player['standing_on'] = None

            if player['standing_on']:
                box = get_obstacle_aabb(player['standing_on'])
                in_x = (current_x_position > box["min_x"] - 0.2) and (current_x_position < box["max_x"] + 0.2)
                in_z = (PLAYER_DEPTH > box["min_z"]) and (PLAYER_DEPTH < box["max_z"])
                if not in_x or not in_z:
                    player['standing_on'] = None; player['on_ground'] = False

            if not player["on_ground"] and player["standing_on"] is None: 
                player["vy"] += GRAVITY * delta_time
            
            player["y"] += player["vy"] * delta_time
            
            if player["y"] <= PLAYER_BASE_Y:
                player["y"] = PLAYER_BASE_Y; player["vy"] = 0.0; player["on_ground"] = True; player['standing_on'] = None
                
            if current_x_position != target_x_position:
                diff = target_x_position - current_x_position
                step = LATERAL_SPEED * delta_time
                if abs(diff) <= step: current_x_position = target_x_position
                else: current_x_position += np.sign(diff) * step

            check_collisions(delta_time)
            update_player_state(delta_time)
            if player['on_ground'] or player['standing_on']: player['run_time'] += delta_time * GAME_SPEED * 0.8
            else: player['run_time'] = 0.5
        
        elif game_state == STATE_GAMEOVER:
            delta_time = 0
            if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS: 
                reset_game()
                ui_dirty = True

        sun_angle = game_time_accumulator * TIME_SPEED
        sun_pos = glm.vec3(math.cos(sun_angle) * SUN_ORBIT_RADIUS, math.sin(sun_angle) * SUN_ORBIT_RADIUS, 20.0)
        night_factor = min(max(-sun_pos.y / 10.0, 0.0), 1.0)

        sky = get_sky_color(sun_pos.y)
        glClearColor(sky.x, sky.y, sky.z, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS:
            current_camera_dist = min(CAMERA_DIST_MAX, current_camera_dist + ZOOM_SPEED * 0.016)
        if glfw.get_key(window, glfw.KEY_LEFT_ALT) == glfw.PRESS:
            current_camera_dist = max(CAMERA_DIST_MIN, current_camera_dist - ZOOM_SPEED * 0.016)

        win_w, win_h = glfw.get_framebuffer_size(window)
        glViewport(0, 0, win_w, win_h)
        projection = glm.perspective(glm.radians(FOV_DEFAULT), win_w / max(win_h, 1), NEAR, FAR)

        cam_y = glm.mix(3.5, 1.2, night_factor) + (player["y"] * 0.5)
        
        #Camera de inicio
        if game_state == STATE_WAITING:
            cam_pos = glm.vec3(2.0, 1.0, PLAYER_DEPTH + 3.0)
            target_pos = glm.vec3(0.0, PLAYER_BASE_Y + 1.0, PLAYER_DEPTH)
        else:
            cam_pos = glm.vec3(current_x_position * 0.7, cam_y, PLAYER_DEPTH + current_camera_dist)
            target_pos = glm.vec3(current_x_position * 0.4, (player["y"] * 0.1) + glm.mix(0.0, 2.0, night_factor), PLAYER_DEPTH - 10.0)
        
        view = glm.lookAt(cam_pos, target_pos, glm.vec3(0.0, 1.0, 0.0))

        if player['state'] == PLAYER_STATE_NERF_QUAKE and game_state == STATE_RUNNING:
             view = glm.rotate(view, (random.random()-0.5)*0.1, glm.vec3(0,0,1))

        flash_dir = glm.normalize(target_pos - cam_pos)
        light_data = {"sun_pos": sun_pos, "sun_color": glm.vec3(1.0, 0.9, 0.8), "flash_pos": cam_pos, "flash_dir": flash_dir, "flash_on": 1.0 if night_factor > 0.2 else 0.0}

        for i in range(-1, 3): 
            plane_z = -PLANE_LENGTH * i + z_offset
            if plane_z - cam_pos.z > CULL_DISTANCE + PLANE_LENGTH: continue
            if plane_z - cam_pos.z < -CULL_DISTANCE - PLANE_LENGTH: continue

            model = glm.translate(glm.mat4(1.0), glm.vec3(0.0, GROUND_Y, plane_z))
            render_scene(shader, meshes['ground'][0], meshes['ground'][1], textures['ground'], model, view, projection, **light_data)
            
            segs = int(PLANE_LENGTH / TRACK_SEGMENT_LEN)
            for tx in TRILHOS:
                for seg in range(segs):
                    fz = plane_z - seg * TRACK_SEGMENT_LEN
                    dist = fz - cam_pos.z
                    if dist > 5.0 or dist < -CULL_DISTANCE: continue 
                    model = glm.translate(glm.mat4(1.0), glm.vec3(tx, TRACK_Y, fz))
                    render_scene(shader, meshes['track_rail'][0], meshes['track_rail'][1], textures['track'], model, view, projection, **light_data)

        for r in rocks:
            if r['z'] - cam_pos.z > 5.0 or r['z'] - cam_pos.z < -CULL_DISTANCE: continue
            model = glm.translate(glm.mat4(1.0), glm.vec3(r['x'], GROUND_Y, r['z']))
            model = glm.rotate(model, glm.radians(r['rot']), glm.vec3(0,1,0))
            model = glm.scale(model, glm.vec3(r['scale']))
            render_scene(shader, meshes['rock'][0], meshes['rock'][1], textures['rock'], model, view, projection, **light_data)

        for obs in obstacles:
            if obs['z'] - cam_pos.z > 5.0 or obs['z'] - cam_pos.z < -CULL_DISTANCE: continue
            model = glm.translate(glm.mat4(1.0), glm.vec3(TRILHOS[obs['trilho']], TRACK_Y + obs.get('y_offset',0), obs['z']))
            tint = glm.vec3(1.0)
            if obs['type'] == TYPE_PLANET:
                model = glm.rotate(model, game_time_accumulator, glm.vec3(0,1,0))
                model = glm.scale(model, glm.vec3(2.0))
                tint = glm.vec3(0.2, 1.0, 0.2) if math.sin(game_time_accumulator * 15) > 0 else glm.vec3(1.0, 0.2, 0.2)
            elif obs['type'] == TYPE_WALL: model = glm.scale(model, glm.vec3(1.5, 1.5, 1.0))
            if obs['is_collided'] and "train" in obs['type']: tint = glm.vec3(1.0, 0.0, 0.0)
            
            vao, count = meshes[obs['mesh']]
            tex = textures["track"] if "train" in obs['type'] else textures["rock"]
            render_scene(shader, vao, count, tex, model, view, projection, tint=tint, **light_data)

        for c in coins:
            if not c['active'] or c['z'] - cam_pos.z > 5.0 or c['z'] - cam_pos.z < -CULL_DISTANCE: continue
            model = glm.translate(glm.mat4(1.0), glm.vec3(TRILHOS[c['trilho']], TRACK_Y + c['y'], c['z']))
            model = glm.rotate(model, game_time_accumulator * 3.0, glm.vec3(0,1,0))
            k = "coin_gold" if player['state'] == PLAYER_STATE_BUFF_GOLD else "coin_silver"
            render_scene(shader, meshes[k][0], meshes[k][1], textures['track'], model, view, projection, **light_data)

        model = glm.translate(glm.mat4(1.0), glm.vec3(current_x_position, player["y"], PLAYER_DEPTH))
        
        if game_state == STATE_WAITING:
            model = glm.rotate(model, game_time_accumulator, glm.vec3(0, 1, 0))
            ptint = glm.vec3(2.0, 2.0, 1.0)
        else:
            model = glm.rotate(model, glm.radians(180), glm.vec3(0, 1, 0))
            if player['on_ground']: 
                model = glm.rotate(model, glm.radians(math.sin(player["run_time"]) * 5.0), glm.vec3(0, 0, 1))
            ptint = glm.vec3(1.5, 1.2, 0.5) if player['state'] == PLAYER_STATE_BUFF_GOLD else glm.vec3(1.0)
        
        model = glm.scale(model, glm.vec3(PLAYER_SCALE))
        render_scene(shader, meshes['player'][0], meshes['player'][1], textures['char'], model, view, projection, tint=ptint, **light_data)

        update_ui_texture()
        render_ui(ui_shader, ui_vao, ui_texture_id)

        glfw.swap_buffers(window)
        glfw.poll_events()
    glfw.terminate()

if __name__ == "__main__":
    main()