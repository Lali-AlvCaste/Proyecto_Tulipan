import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image
import numpy as np
import time
from enum import Enum

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

COLOR_ROJO = (1.0, 0.0, 0.0)
COLOR_NEGRO = (0.0, 0.0, 0.0)
COLOR_VERDE = (0.0, 0.7, 0.0)
COLOR_CAFE = (0.47, 0.3, 0.17)
COLOR_BLANCO = (1.0, 1.0, 1.0)

LIGHT_POS = (5.0, 10.0, 5.0, 1.0)

cam_rot_x = 45.0
cam_rot_y = 45.0
last_mouse_pos = (0, 0)
mouse_down = False
zoom = 15.0

TEXTURES = {}


class BeeState(Enum):
    CIRCULANDO = 1
    APROXIMANDOSE = 2  # se usa para el sobrevuelo tangencial
    REGRESANDO = 3


bee_state = BeeState.CIRCULANDO

bee_angle = 0.0
BEE_RADIUS = 2.5
BEE_SPEED = 1.0
BEE_Y_HEIGHT = 2.0  # Altura de vuelo normal

TULIP_X, TULIP_Y, TULIP_Z = 0.0, (4.5 * 0.5) + 0.1, 0.0  # Altura de la flor

# Parámetros ajustados
APPROACH_SPEED = 1.2  # Velocidad angular de sobrevuelo
MIN_RADIUS_SURVOL = 1.0  # Radio más cercano al tallo de la flor
RETURN_SPEED = 0.05

bee_x = 0.0
bee_y = BEE_Y_HEIGHT
bee_z = 0.0

# Parámetros para el sobrevuelo
SURVOL_ALTURA_MAX = 4.5  # Altura máxima para pasar por encima del tulipán
survol_steps = 0
MAX_SURVOL_STEPS = 120  # Número de pasos para completar la trayectoria de sobrevuelo


def load_texture(filename):
    try:
        img = Image.open(filename)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_data = np.array(list(img.getdata()), np.uint8)
        img_data = img_data.reshape(img.size[1], img.size[0], 3)
        img_data = np.flipud(img_data)

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 0,
                     GL_RGB, GL_UNSIGNED_BYTE, img_data)

        print(f"Textura '{filename}' cargada con ID: {texture_id}")
        return texture_id
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo de textura '{filename}'.")
        return None
    except Exception as e:
        print(f"Error al procesar la textura {filename}: {e}")
        return None


def draw_cube(center_x, center_y, center_z, size, color=None, texture_id=None, texture_repeat=1):
    half = size / 2.0

    vertices = [
        (center_x - half, center_y - half, center_z + half), (center_x + half, center_y - half, center_z + half),
        (center_x + half, center_y + half, center_z + half), (center_x - half, center_y + half, center_z + half),
        (center_x - half, center_y - half, center_z - half), (center_x + half, center_y - half, center_z - half),
        (center_x + half, center_y + half, center_z - half), (center_x - half, center_y + half, center_z - half)
    ]

    faces = [
        (0, 3, 2, 1), (4, 7, 6, 5), (0, 4, 5, 1),
        (3, 7, 6, 2), (1, 2, 6, 5), (0, 3, 7, 4)
    ]

    normals = [
        (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), (0.0, -1.0, 0.0),
        (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)
    ]

    scaled_tex_coords = [
        (0, 0),
        (texture_repeat, 0),
        (texture_repeat, texture_repeat),
        (0, texture_repeat)
    ]

    base_color = color if color else (1.0, 1.0, 1.0)

    for i, face in enumerate(faces):
        current_tex_id = None

        if isinstance(texture_id, dict):
            current_tex_id = texture_id.get(i, texture_id.get('default'))
        elif texture_id:
            current_tex_id = texture_id

        if current_tex_id:
            glBindTexture(GL_TEXTURE_2D, current_tex_id)
            glColor3f(1.0, 1.0, 1.0)
            use_texture = True
        else:
            glBindTexture(GL_TEXTURE_2D, 0)

            if color and len(color) == 4:
                glColor4fv(color)
            else:
                glColor3fv(base_color)

            use_texture = False

        glBegin(GL_QUADS)
        glNormal3fv(normals[i])

        for j, vertex_index in enumerate(face):
            if use_texture:
                glTexCoord2fv(scaled_tex_coords[j])
            glVertex3fv(vertices[vertex_index])
        glEnd()


def draw_minecraft_bee(s_bee=0.3):
    tex_body = TEXTURES.get('bee_body')
    tex_wings = TEXTURES.get('bee_wings')

    body_parts = [
        (0, 0, 0), (s_bee, 0, 0), (s_bee * 2, 0, 0)
    ]

    for x, y, z in body_parts:
        draw_cube(x, y, z, s_bee, COLOR_NEGRO, tex_body, 1)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glDisable(GL_LIGHTING)

    glPushMatrix()
    glTranslatef(s_bee, s_bee * 0.5, -s_bee * 0.8)

    draw_cube(0, 0, 0, s_bee * 1.5, (COLOR_BLANCO[0], COLOR_BLANCO[1], COLOR_BLANCO[2], 0.5), tex_wings, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(s_bee, s_bee * 0.5, s_bee * 0.8)
    draw_cube(0, 0, 0, s_bee * 1.5, (COLOR_BLANCO[0], COLOR_BLANCO[1], COLOR_BLANCO[2], 0.5), tex_wings, 1)
    glPopMatrix()

    glEnable(GL_LIGHTING)
    glDisable(GL_BLEND)


def draw_tulip_model():
    tex_leaves = TEXTURES.get('leaves')
    tex_wool = TEXTURES.get('red_wool')
    tex_grass_top = TEXTURES.get('grass_top')
    tex_dirt = TEXTURES.get('dirt')

    floor_textures = {
        3: tex_grass_top,
        'default': tex_dirt
    }

    s = 0.5
    soil_repeat_factor = 4

    draw_cube(0, -s * 0.5, 0, 2.0, COLOR_CAFE, floor_textures, texture_repeat=soil_repeat_factor)

    stem_blocks = [
        (0, s * 0.5, 0), (0, s * 1.5, 0), (0, s * 2.5, 0), (0, s * 3.5, 0),
        (-s, s * 1.5, 0), (s, s * 1.5, 0), (0, s * 2.5, -s), (0, s * 2.5, s),
    ]
    for x, y, z in stem_blocks:
        draw_cube(x, y, z, s, COLOR_VERDE, tex_leaves, texture_repeat=1)

    flower_center_y = s * 4.5

    flower_parts = [
        (0, flower_center_y, 0), (s, flower_center_y, 0), (-s, flower_center_y, 0),
        (0, flower_center_y, s), (0, flower_center_y, -s),
        (s, flower_center_y + s, 0), (-s, flower_center_y + s, 0),
        (0, flower_center_y + s, s), (0, flower_center_y + s, -s),
    ]
    for x, y, z in flower_parts:
        draw_cube(x, y, z, s, COLOR_ROJO, tex_wool, texture_repeat=1)

    black_centers = [
        (s * 0.5, flower_center_y + s * 0.5, 0), (-s * 0.5, flower_center_y + s * 0.5, 0),
        (0, flower_center_y + s * 0.5, s * 0.5), (0, flower_center_y + s * 0.5, -s * 0.5),
    ]
    for x, y, z in black_centers:
        draw_cube(x, y, z, s * 0.5, COLOR_NEGRO, None, texture_repeat=1)


def draw_shadow():
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_DEPTH_TEST)

    glColor4f(0.1, 0.1, 0.1, 1.0)

    s_size = 1.5
    s_y = 0.05

    glBegin(GL_QUADS)
    glVertex3f(-s_size, s_y, s_size)
    glVertex3f(s_size, s_y, s_size)
    glVertex3f(s_size, s_y, -s_size)
    glVertex3f(-s_size, s_y, -s_size)
    glEnd()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)


def init_opengl():
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    light_ambient = [0.1, 0.1, 0.1, 1.0]
    light_diffuse = [1.0, 1.0, 1.0, 1.0]
    light_specular = [1.0, 1.0, 1.0, 1.0]

    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
    glLightfv(GL_LIGHT0, GL_POSITION, LIGHT_POS)

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    glClearColor(0.53, 0.81, 0.98, 1.0)


def update_bee_movement():
    global bee_angle, bee_state, bee_x, bee_y, bee_z, survol_steps, BEE_RADIUS

    if bee_state == BeeState.CIRCULANDO:
        # Movimiento de órbita grande
        bee_angle += BEE_SPEED
        if bee_angle > 360.0:
            bee_angle -= 360.0

        BEE_RADIUS = 2.5  # Radio de órbita grande

        angle_rad = np.radians(bee_angle)
        bee_x = np.sin(angle_rad) * BEE_RADIUS
        bee_z = np.cos(angle_rad) * BEE_RADIUS
        bee_y = BEE_Y_HEIGHT
        survol_steps = 0

        # Transición al sobrevuelo
        if 350.0 < bee_angle < 360.0:
            bee_state = BeeState.APROXIMANDOSE
            # Fija el punto de inicio en la órbita grande
            bee_x = np.sin(np.radians(359.9)) * BEE_RADIUS
            bee_z = np.cos(np.radians(359.9)) * BEE_RADIUS

    elif bee_state == BeeState.APROXIMANDOSE:

        # Sobrevuelo: Mantiene la dirección de la órbita, pero ajusta radio y altura

        # 1. Aumento de ángulo (movimiento circular)
        bee_angle += APPROACH_SPEED

        # 2. Control de Altura y Radio (Trayectoria Parabólica/Senoidal)

        # Control del radio (se acerca y se aleja)
        # 0.5 para que esté en el punto más cercano (MIN_RADIUS_SURVOL) a la mitad de los pasos
        radius_factor = np.sin((survol_steps / MAX_SURVOL_STEPS) * np.pi)

        # El radio varía entre 2.5 (inicio/fin) y MIN_RADIUS_SURVOL (centro del sobrevuelo)
        BEE_RADIUS = MIN_RADIUS_SURVOL + (BEE_RADIUS - MIN_RADIUS_SURVOL) * (1 - radius_factor)

        # Control de altura (sube y baja)
        # La altura varía entre BEE_Y_HEIGHT (inicio/fin) y SURVOL_ALTURA_MAX (centro)
        height_factor = np.sin((survol_steps / MAX_SURVOL_STEPS) * np.pi)
        target_y = BEE_Y_HEIGHT + (SURVOL_ALTURA_MAX - BEE_Y_HEIGHT) * height_factor

        # Mover verticalmente de forma suave
        bee_y += (target_y - bee_y) * 0.1

        # 3. Posición 3D (Cálculo trigonométrico manteniendo la órbita)
        angle_rad = np.radians(bee_angle)
        bee_x = np.sin(angle_rad) * BEE_RADIUS
        bee_z = np.cos(angle_rad) * BEE_RADIUS

        survol_steps += 1

        # 4. Transición a REGRESANDO (cuando termina la maniobra de sobrevuelo)
        if survol_steps >= MAX_SURVOL_STEPS:
            bee_state = BeeState.REGRESANDO


    elif bee_state == BeeState.REGRESANDO:
        # Se dirige de vuelta al punto de inicio de la órbita CIRCULANDO (Z=BEE_RADIUS, X=0)

        # Establecemos el objetivo de radio y altura del estado CIRCULANDO
        target_radius = 2.5
        target_y = BEE_Y_HEIGHT

        # 1. Ajuste de Radio (para que el radio vuelva a 2.5)
        BEE_RADIUS += (target_radius - BEE_RADIUS) * 0.1

        # 2. Ajuste de Altura
        bee_y += (target_y - bee_y) * 0.1

        # 3. Movimiento Angular: Continuar la rotación para alinearse
        bee_angle += BEE_SPEED * (0.5 + 0.5 * (1.0 - abs(target_radius - BEE_RADIUS) / target_radius))

        angle_rad = np.radians(bee_angle)
        bee_x = np.sin(angle_rad) * BEE_RADIUS
        bee_z = np.cos(angle_rad) * BEE_RADIUS

        # Transición a CIRCULANDO
        if abs(BEE_RADIUS - target_radius) < 0.05 and abs(bee_y - target_y) < 0.05:
            bee_angle = 0.0  # Reiniciamos ángulo al inicio de la órbita
            bee_state = BeeState.CIRCULANDO
            BEE_RADIUS = target_radius
            bee_y = target_y


def display():
    global cam_rot_x, cam_rot_y, zoom, bee_x, bee_y, bee_z, bee_angle, bee_state

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    update_bee_movement()

    glTranslatef(0.0, 0.0, -zoom)
    glRotatef(cam_rot_x, 1, 0, 0)
    glRotatef(cam_rot_y, 0, 1, 0)

    draw_shadow()
    draw_tulip_model()

    glPushMatrix()

    glTranslatef(bee_x, bee_y, bee_z)

    rotation_angle = 0.0
    pitch_angle = 0.0  # Inclinación (para dar sensación de subida/bajada)

    if bee_state == BeeState.CIRCULANDO:
        rotation_angle = bee_angle + 90.0
    elif bee_state == BeeState.APROXIMANDOSE:
        # La rotación sigue el ángulo de órbita
        rotation_angle = bee_angle + 90.0

        # Aplicamos inclinación basada en la altura (para que parezca que sube/baja)
        # Esto es una aproximación visual de la inclinación del vector de velocidad.
        # Calculamos la posición en la trayectoria (0 a 1)
        path_progress = survol_steps / MAX_SURVOL_STEPS

        if path_progress < 0.5:  # Fase de subida y acercamiento
            pitch_angle = -30.0 * path_progress / 0.5
        else:  # Fase de descenso y alejamiento
            pitch_angle = 30.0 * (path_progress - 0.5) / 0.5


    elif bee_state == BeeState.REGRESANDO:
        rotation_angle = bee_angle + 90.0
        pitch_angle = 10.0  # Ligera inclinación mientras se estabiliza

    glRotatef(rotation_angle, 0, 1, 0)
    glRotatef(pitch_angle, 1, 0, 0)  # Aplicar inclinación

    draw_minecraft_bee(s_bee=0.3)

    glPopMatrix()

    pygame.display.flip()


def main():
    global mouse_down, last_mouse_pos, cam_rot_x, cam_rot_y, zoom, TEXTURES

    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Abejita encima de tulipan")

    init_opengl()

    glEnable(GL_TEXTURE_2D)

    TEXTURES['grass_top'] = load_texture("grass_top.png")
    TEXTURES['red_wool'] = load_texture("red-wool.png")
    TEXTURES['leaves'] = load_texture("oak-leaves.png")
    TEXTURES['dirt'] = load_texture("dirt.png")

    TEXTURES['bee_body'] = load_texture("bee_body.png")

    TEXTURES['bee_wings'] = load_texture("bee_wings.png")

    if not all(TEXTURES.values()):
        print("ADVERTENCIA: Alguna textura no se cargó. Usando color sólido o fallando.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down = True
                    last_mouse_pos = event.pos
                elif event.button == 4:
                    zoom = max(5.0, zoom - 1.0)
                elif event.button == 5:
                    zoom = min(40.0, zoom + 1.0)

            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False

            elif event.type == MOUSEMOTION:
                if mouse_down:
                    dx, dy = event.pos[0] - last_mouse_pos[0], event.pos[1] - last_mouse_pos[1]

                    cam_rot_y += dx * 0.2
                    cam_rot_x = max(-90, min(90, cam_rot_x + dy * 0.2))

                    last_mouse_pos = event.pos

        display()

        pygame.time.wait(10)

    pygame.quit()


if __name__ == "__main__":
    main()