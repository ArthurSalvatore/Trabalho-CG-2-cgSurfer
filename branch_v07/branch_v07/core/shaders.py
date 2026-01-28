from OpenGL.GL import *
import OpenGL.GL.shaders as gls
import os

def load_shader_program(vs_path, fs_path):
    with open(vs_path, 'r') as file:
        vertex_src = file.read()
    with open(fs_path, 'r') as file:
        fragment_src = file.read()

    vertex_shader = gls.compileShader(vertex_src, GL_VERTEX_SHADER)
    fragment_shader = gls.compileShader(fragment_src, GL_FRAGMENT_SHADER)
    program = gls.compileProgram(vertex_shader, fragment_shader)

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program
