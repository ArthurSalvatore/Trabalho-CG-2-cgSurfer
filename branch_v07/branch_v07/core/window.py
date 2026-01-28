import glfw


def create_window(width, height, title):
    if not glfw.init():
        raise Exception("Erro GLFW")

    #glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    #glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    #glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(width, height, title, None, None)
    if not window:
        glfw.terminate()
        raise Exception("Erro window")

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    
    glfw.set_framebuffer_size_callback(window, _framebuffer_size_callback)
    
    return window

def _framebuffer_size_callback(window, width, height):
    from OpenGL.GL import glViewport
    glViewport(0, 0, width, height)

def should_close(window):
    return glfw.window_should_close(window)

def update_inputs(window):
    move = 0
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        move = -1
    elif glfw.get_key(window, glfw.KEY_D) == glfw.PRESS or \
         glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        move = 1
    
    return move