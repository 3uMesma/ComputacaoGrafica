# cena_completa.py
import glfw
from OpenGL.GL import *
import numpy as np
import glm
import math
from modulos.programa_shader import criar_shader, usar_shader
from modulos.objeto_cena_metadados import gen_scene_objects
from modulos.skybox_utils import init_skybox, skybox_update
from PIL import Image            # ADICIONADO para carregar texturas cubemap :contentReference[oaicite:0]{index=0}

# --- Configurações iniciais da cena ---
ALTURA = 700
LARGURA = 700

# --- Callbacks de input / movimento de câmera ---
firstMouse = True
lastX = LARGURA / 2
lastY = ALTURA / 2
yaw   = -90.0
pitch = 0.0

busPos = glm.vec3(0.0, 0.0, 0.0)
busYaw = 0.0
placa_escala = 1 # multiplca pelo sx da placa antes de exibir
# placa_escala muda de maneira senoidal entre 0.5 e 1.5 de acordo
# com a variacao do tempo (controlado por parametro_temporal_placa)
LIMIAR_MUL_SUP = 1.5 
LIMIAR_MUL_INF = 0.5
parametro_temporal_placa = 0
DELTA_TEMPORAL_PLACA = 0.05
# exibir malha poligonal
p_pressed = False
wireframe = False


def init_window():
    if not glfw.init():
        raise RuntimeError("Falha ao inicializar GLFW")
    # Oculta janela até chamar show_window()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(LARGURA, ALTURA, "Cena Completa", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Falha ao criar janela GLFW")
    glfw.make_context_current(window)
    return window

def mexe_onibus(fwd, yaw):
    global busPos, busYaw
    busPos += fwd
    busYaw += yaw

def process_input(window):
    global cameraPos, cameraFront, cameraUp, deltaTime, placa_escala, parametro_temporal_placa, p_pressed, wireframe
    speed = 2.5 * deltaTime
    if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        cameraPos += speed * cameraFront
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        cameraPos -= speed * cameraFront
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * speed
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * speed
    global busPos, busYaw
    speed = 2.5 * deltaTime
    # translação frente/trás (eixo local Z do ônibus)
    forward = glm.vec3(
        math.sin(glm.radians(busYaw)),
        0,
        math.cos(glm.radians(busYaw))
    )

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        mexe_onibus(forward * speed, 0)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        mexe_onibus(-forward * speed, 0)
    
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        mexe_onibus(glm.vec3(0, 0, 0), -60 * deltaTime)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        mexe_onibus(glm.vec3(0, 0, 0), 60 * deltaTime)
    
    # escalar a placa
    if glfw.get_key(window, glfw.KEY_0) == glfw.PRESS:
        parametro_temporal_placa += DELTA_TEMPORAL_PLACA
        placa_escala = (LIMIAR_MUL_SUP - LIMIAR_MUL_INF)/2 * math.sin(parametro_temporal_placa) + (LIMIAR_MUL_INF + LIMIAR_MUL_SUP)/2

    # malha poligonal
    if glfw.get_key(window, glfw.KEY_P) == glfw.PRESS:
        if not p_pressed:  # Apenas alterna na transição
            p_pressed = True
            wireframe = not wireframe
    else:
        p_pressed = False

def mouse_callback(window, xpos, ypos):
    global firstMouse, lastX, lastY, yaw, pitch, cameraFront
    if firstMouse:
        lastX, lastY = xpos, ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos
    lastX, lastY = xpos, ypos

    sensitivity = 0.1
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw   += xoffset
    pitch += yoffset
    if pitch > 89.0:
        pitch = 89.0
    if pitch < -89.0:
        pitch = -89.0

    front = glm.vec3()
    front.x = math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
    front.y = math.sin(math.radians(pitch))
    front.z = math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
    cameraFront = glm.normalize(front)

def scroll_callback(window, xoffset, yoffset):
    global fov
    fov -= yoffset
    if fov < 1.0:
        fov = 1.0
    if fov > 45.0:
        fov = 45.0

def framebuffer_size_callback(window, width, height):
    glViewport(0, 0, width, height)

# --- Matriz de modelo, view, projection ---
def model_matrix(angle, rx, ry, rz, tx, ty, tz, sx, sy, sz):
    ang = math.radians(angle)
    m = glm.mat4(1.0)
    m = glm.translate(m, glm.vec3(tx, ty, tz))
    if ang != 0:
        m = glm.rotate(m, ang, glm.vec3(rx, ry, rz))
    m = glm.scale(m, glm.vec3(sx, sy, sz))
    return np.array(m)

def view_matrix():
    return np.array(glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp))

def projection_matrix():
    return np.array(glm.perspective(glm.radians(fov), LARGURA/ALTURA, 0.1, 100.0))


# --- Execução principal ---
def main():
    global cameraPos, cameraFront, cameraUp, deltaTime, lastFrame, polygonal_mode, fov, busPos, busYaw
    window = init_window()

    # registra callbacks
    glfw.set_key_callback(window, lambda w,k,s,a,m: None)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    # carrega e usa shader principal
    program = criar_shader("shaders/vertex_shader.vs", "shaders/fragment_shader.fs")
    usar_shader(program)

    # habilita estado GL
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    polygonal_mode = False

    # inicializa parâmetros da câmera
    cameraPos   = glm.vec3(0.0, 0.0,  3.0)
    cameraFront = glm.vec3(0.0, 0.0, -1.0)
    cameraUp    = glm.vec3(0.0, 1.0,  0.0)
    fov = 45.0
    deltaTime = 0.0
    lastFrame = 0.0

    scene_objects = gen_scene_objects(program)

    ind_placa = 0 # indice da placa em scene_objects

    escala_original_placa = scene_objects[ind_placa].get_escala()

    ind_onibus = 2 # indice do onibus em scene_objects
    ind_objs_onibus = [1, 5, 6] # indices de objetos dentro do onibus
    offsets_inicais = [] # lista de offsets iniciais (posicao) desses objetos em relacao ao onibus
    offsets_atuais = [] # mesma coisa pra os atuais

    for ind_obj, ind_arr in enumerate(ind_objs_onibus):
        offsets_inicais.append(scene_objects[ind_arr].get_pos() - scene_objects[ind_onibus].get_pos())
        offsets_atuais.append(scene_objects[ind_arr].get_pos() - scene_objects[ind_onibus].get_pos())
    
    busPos = glm.vec3(-2.6, -0.99, 9.5) # reposiciona o onibus
    
    cameraPos.z += 40 # reposciona a camera

    # --- Configuração do skybox (adicionado)
    skyboxShader = criar_shader("shaders/skybox.vs", "shaders/skybox.fs")   # shader skybox
    skyboxVAO, cubemapTexture = init_skybox(skyboxShader)  # (inicializa skybox) carrega cubemap e cria VAO
    
    # vertices do chão (x, y, z, u, v)
    floor_program = criar_shader("shaders/floor_shader.vs", "shaders/floor_shader.fs")
    floor_vertices = np.array([
        # pos               texcoords
        -1000.0, -1.5, -1000.0,   0.0, 0.0,
        1000.0, -1.5, -1000.0,   5.0, 0.0,  # u=5 para repetir 5 vezes
        1000.0, -1.5,  1000.0,   5.0, 5.0,
        -1000.0, -1.5,  1000.0,   0.0, 5.0,
    ], dtype=np.float32)

    floor_indices = np.array([
        0, 1, 2,
        2, 3, 0
    ], dtype=np.uint32)

    # criar VAO/VBO/EBO
    floor_VAO = glGenVertexArrays(1)
    floor_VBO = glGenBuffers(1)
    floor_EBO = glGenBuffers(1)

    glBindVertexArray(floor_VAO)
    glBindBuffer(GL_ARRAY_BUFFER, floor_VBO)
    glBufferData(GL_ARRAY_BUFFER, floor_vertices.nbytes, floor_vertices, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, floor_EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, floor_indices.nbytes, floor_indices, GL_STATIC_DRAW)

    # posição
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
    # texcoords
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))

    glBindVertexArray(0)

    # carrega imagem
    img = Image.open("objetos/chao/gravel_floor_02_ao_1k.png")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)  # inverter y
    img_data = img.convert("RGBA").tobytes()

    # gera textura OpenGL
    floor_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, floor_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0,
                GL_RGBA, GL_UNSIGNED_BYTE, img_data)

    # parâmetros de textura
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glGenerateMipmap(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, 0)


    glfw.show_window(window)

    # loop principal
    while not glfw.window_should_close(window):
        currentFrame = glfw.get_time()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        process_input(window)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0,1.0,1.0,1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

        # ... dentro do loop de renderização, antes de desenhar seu cenário:

        # configuração skybox
        skybox_update(skyboxShader, cameraPos, cameraFront, cameraUp, projection_matrix(), skyboxVAO, cubemapTexture)
        
        # ativar shader do chão
        usar_shader(floor_program)  # criar e usar um shader separado para o chão
        # setar matrizes
        glUniformMatrix4fv(glGetUniformLocation(floor_program, "view"), 1, GL_TRUE, view_matrix())
        glUniformMatrix4fv(glGetUniformLocation(floor_program, "projection"), 1, GL_TRUE, projection_matrix())
        model = glm.mat4(1.0)  # já está no eixo Y = 0
        glUniformMatrix4fv(glGetUniformLocation(floor_program, "model"), 1, GL_FALSE, glm.value_ptr(model))

        # bind textura
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, floor_texture)
        glUniform1i(glGetUniformLocation(floor_program, "tex_diffuse"), 0)

        # desenha o VAO do chão
        glBindVertexArray(floor_VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        # restabelece depth test para o resto da cena
        glDepthFunc(GL_LESS)


        # Render sua cena normalmente
        usar_shader(program)
        loc_view2 = glGetUniformLocation(program, "view")
        glUniformMatrix4fv(loc_view2, 1, GL_TRUE, view_matrix())
        loc_proj2 = glGetUniformLocation(program, "projection")
        glUniformMatrix4fv(loc_proj2, 1, GL_TRUE, projection_matrix())

        # Transf de escala da placa
        scene_objects[ind_placa].set_escala(glm.vec3(placa_escala * escala_original_placa.x, escala_original_placa.y, escala_original_placa.z))

        # Atualiza pos do onibus
        scene_objects[ind_onibus].seta_pos(busPos)
        scene_objects[ind_onibus].transform['angle'] = busYaw

        # Atualiza pos de objetos dentros  do onibus
        rot_mat = glm.rotate(
            glm.mat4(1.0),
            glm.radians(busYaw),
            glm.vec3(0.0, 1.0, 0.0)
        )
        for ind_obj, ind_arr in enumerate(ind_objs_onibus):
            offsets_atuais[ind_obj] = glm.vec3(rot_mat * glm.vec4(offsets_inicais[ind_obj], 1.0))
            nova_pos_atual = scene_objects[ind_onibus].get_pos() + offsets_atuais[ind_obj]
            scene_objects[ind_arr].seta_pos(nova_pos_atual)
            scene_objects[ind_arr].transform['angle'] = busYaw

        for objmeta in scene_objects:
            objmeta.draw(
                model_matrix_func=model_matrix,
                **objmeta.transform
            )

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == '__main__':
    main()
