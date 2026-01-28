from OpenGL.GL import *
import OpenGL.GL.shaders as gl_shaders
import glm
import ctypes
import numpy as np
from PIL import Image

GROUND_VERTICES = np.array([
    # X,    Y,      Z,       U,     V,      NX,  NY,  NZ
    -40.0, 0.0,   0.0,     0.0,  25.0,   0.0, 1.0, 0.0,
     40.0, 0.0,   0.0,    20.0,  25.0,   0.0, 1.0, 0.0,
     40.0, 0.0, -50.0,    20.0,   0.0,   0.0, 1.0, 0.0,
    -40.0, 0.0,   0.0,     0.0,  25.0,   0.0, 1.0, 0.0,
    -40.0, 0.0, -50.0,     0.0,   0.0,   0.0, 1.0, 0.0,
     40.0, 0.0, -50.0,    20.0,   0.0,   0.0, 1.0, 0.0
], dtype=np.float32)


def load_shader_program(vs_path: str, fs_path: str):

    with open(vs_path, 'r', encoding='utf-8') as file: 
        vertex_src = file.read()
    with open(fs_path, 'r', encoding='utf-8') as file: 
        fragment_src = file.read()

    vs = gl_shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
    fs = gl_shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
    
    program = gl_shaders.compileProgram(vs, fs)
    
    glDeleteShader(vs)
    glDeleteShader(fs)
    
    return program

def load_ui_shader():
    return load_shader_program("shaders/ui_vertex_shader.glsl", "shaders/ui_fragment_shader.glsl")


def load_texture(path: str):
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    #Repetição e filtragem
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    try:
        image = Image.open(path)
        image = image.transpose(Image.FLIP_TOP_BOTTOM) 
        if image.mode != 'RGBA':
            image = image.convert("RGBA")
            
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 
                     0, GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
        glGenerateMipmap(GL_TEXTURE_2D)
        
    except Exception as e:
        print(f"Falha ao carregar textura {path}: {e}")

        error_color = bytes([255, 0, 255, 255])
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, error_color)
    
    return texture_id

def create_empty_texture(width: int, height: int):
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    return texture_id

def update_texture(texture_id: int, image: Image.Image):
    if image.mode != 'RGBA':
        image = image.convert("RGBA")
    
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, image.width, image.height, 
                    GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())


#.objs
def load_obj(filename: str):
    positions, uvs, normals = [], [], []
    buffer_data = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                prefix = parts[0]
                
                if prefix == 'v':
                    positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif prefix == 'vt':
                    uvs.append([float(parts[1]), float(parts[2])])
                elif prefix == 'vn':
                    normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif prefix == 'f':
                    for i in range(1, 4):
                        if i >= len(parts): break
                        
                        indices = parts[i].split('/')
                        
                        idx_pos = int(indices[0]) - 1
                        buffer_data.extend(positions[idx_pos])
                        
                        if len(indices) > 1 and indices[1]:
                            idx_uv = int(indices[1]) - 1
                            buffer_data.extend(uvs[idx_uv])
                        else:
                            buffer_data.extend([0.0, 0.0])
                            
                        if len(indices) > 2 and indices[2]:
                            idx_norm = int(indices[2]) - 1
                            buffer_data.extend(normals[idx_norm])
                        else:
                            buffer_data.extend([0.0, 1.0, 0.0])
                        
    except Exception as e:
        print(f"Falha ao carregar {filename}: {e}")
        return np.array([], dtype=np.float32)

    return np.array(buffer_data, dtype=np.float32)

def create_vao(vertices):
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    stride = 32 # 8 floats * 4 bytes
    
    #Layout 0: Posição
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    
    #Layout 1: Textura
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
    glEnableVertexAttribArray(1)
    
    #Layout 2: Normal
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(20))
    glEnableVertexAttribArray(2)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    
    vertex_count = len(vertices) // 8
    return vao, vertex_count

def create_screen_quad():
    quad_vertices = np.array([
        -1.0,  1.0,  0.0, 0.0,
        -1.0, -1.0,  0.0, 1.0,
         1.0, -1.0,  1.0, 1.0,

        -1.0,  1.0,  0.0, 0.0,
         1.0, -1.0,  1.0, 1.0,
         1.0,  1.0,  1.0, 0.0
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
    
    stride = 16 # 4 floats * 4 bytes
 
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
    glEnableVertexAttribArray(1)
    
    return vao


def render_scene(shader, vao, vertex_count, texture_id, model_matrix, view_matrix, proj_matrix, 
                 tint=None, sun_pos=None, sun_color=None, 
                 flash_pos=None, flash_dir=None, flash_on=0.0):

    if tint is None: tint = glm.vec3(1.0)
    if sun_pos is None: sun_pos = glm.vec3(0, 50, 0)
    if sun_color is None: sun_color = glm.vec3(1.0)
    if flash_pos is None: flash_pos = glm.vec3(0)
    if flash_dir is None: flash_dir = glm.vec3(0, 0, -1)

    glUseProgram(shader)
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glUniform1i(glGetUniformLocation(shader, "mainTexture"), 0)

    #Matrizes
    glUniformMatrix4fv(glGetUniformLocation(shader, "model"), 1, GL_FALSE, glm.value_ptr(model_matrix))
    glUniformMatrix4fv(glGetUniformLocation(shader, "view"), 1, GL_FALSE, glm.value_ptr(view_matrix))
    glUniformMatrix4fv(glGetUniformLocation(shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj_matrix))
    
    #Iluminação
    glUniform3fv(glGetUniformLocation(shader, "objectTint"), 1, glm.value_ptr(tint))
    glUniform3fv(glGetUniformLocation(shader, "sunPos"), 1, glm.value_ptr(sun_pos))
    glUniform3fv(glGetUniformLocation(shader, "sunColor"), 1, glm.value_ptr(sun_color))
    glUniform3fv(glGetUniformLocation(shader, "flashPos"), 1, glm.value_ptr(flash_pos))
    glUniform3fv(glGetUniformLocation(shader, "flashDir"), 1, glm.value_ptr(flash_dir))
    glUniform1f(glGetUniformLocation(shader, "flashOn"), flash_on)
    glUniform3fv(glGetUniformLocation(shader, "viewPos"), 1, glm.value_ptr(flash_pos))

    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLES, 0, vertex_count)
    glBindVertexArray(0)
    glUseProgram(0)

def render_ui(shader, vao, texture_id):
    glDisable(GL_DEPTH_TEST) 
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glUseProgram(shader)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glUniform1i(glGetUniformLocation(shader, "uiTexture"), 0)

    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLES, 0, 6)
    glBindVertexArray(0)
    
    glEnable(GL_DEPTH_TEST) 
    glUseProgram(0)