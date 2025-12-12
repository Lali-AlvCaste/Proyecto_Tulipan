import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image
import numpy as np


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

COLOR_ROJO = (1.0, 0.0, 0.0)
COLOR_NEGRO = (0.0, 0.0, 0.0)
COLOR_VERDE = (0.0, 0.7, 0.0)  # Verde brillante para el tallo
COLOR_CAFE = (0.47, 0.3, 0.17) # Color café para la tierra

LIGHT_POS = (5.0, 10.0, 5.0, 1.0)

cam_rot_x = 45.0
cam_rot_y = 45.0
last_mouse_pos = (0, 0)
mouse_down = False
zoom = 15.0

TEXTURES = {}


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


def draw_cube(center_x, center_y, center_z, size, color=None, texture_id=None):
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

    tex_coords = [(0, 0), (1, 0), (1, 1), (0, 1)]

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
            glColor3fv(base_color)
            use_texture = False

        
        glBegin(GL_QUADS)
        glNormal3fv(normals[i])

        for j, vertex_index in enumerate(face):
            if use_texture:
                glTexCoord2fv(tex_coords[j])
            glVertex3fv(vertices[vertex_index])
        glEnd()


def draw_tulip_model():
    

    s = 0.5

    
    draw_cube(0, -s * 0.5, 0, 2.0, COLOR_CAFE, None)

    stem_blocks = [
        (0, s * 0.5, 0), (0, s * 1.5, 0), (0, s * 2.5, 0), (0, s * 3.5, 0),
        (-s, s * 1.5, 0), (s, s * 1.5, 0), (0, s * 2.5, -s), (0, s * 2.5, s),
    ]
    for x, y, z in stem_blocks:
        draw_cube(x, y, z, s, COLOR_VERDE, None)

    
    flower_center_y = s * 4.5

    flower_parts = [
        (0, flower_center_y, 0), (s, flower_center_y, 0), (-s, flower_center_y, 0),
        (0, flower_center_y, s), (0, flower_center_y, -s),
        (s, flower_center_y + s, 0), (-s, flower_center_y + s, 0),
        (0, flower_center_y + s, s), (0, flower_center_y + s, -s),
    ]
    for x, y, z in flower_parts:
        draw_cube(x, y, z, s, COLOR_ROJO, None)

    
    black_centers = [
        (s * 0.5, flower_center_y + s * 0.5, 0), (-s * 0.5, flower_center_y + s * 0.5, 0),
        (0, flower_center_y + s * 0.5, s * 0.5), (0, flower_center_y + s * 0.5, -s * 0.5),
    ]
    for x, y, z in black_centers:
        draw_cube(x, y, z, s * 0.5, COLOR_NEGRO, None)


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


def display():
    global cam_rot_x, cam_rot_y, zoom

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glTranslatef(0.0, 0.0, -zoom)
    glRotatef(cam_rot_x, 1, 0, 0)
    glRotatef(cam_rot_y, 0, 1, 0)

    draw_shadow()
    draw_tulip_model()

    pygame.display.flip()


def main():
    global mouse_down, last_mouse_pos, cam_rot_x, cam_rot_y, zoom, TEXTURES

    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Tulipán 3D Voxel (Color Sólido)")

    init_opengl()

   
    glEnable(GL_TEXTURE_2D)

    
    TEXTURES['grass_top'] = load_texture("grass_top.png")
    TEXTURES['red_wool'] = load_texture("red_wool.png")
    TEXTURES['leaves'] = load_texture("leaves.png")

    if not all(TEXTURES.values()):
        print("ADVERTENCIA: Alguna textura no se cargó. Usando color sólido.")

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
