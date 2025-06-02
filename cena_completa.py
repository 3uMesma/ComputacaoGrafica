# cena_completa.py
import glfw
from OpenGL.GL import *
import numpy as np
import glm
import math
from modulos.programa_shader import criar_shader, usar_shader
from modulos.objeto_cena_metadados import gen_scene_objects
from modulos.skybox_utils import init_skybox, skybox_update
from modulos.floor_utils import init_floor, update_floor

# --- Configurações iniciais da cena ---
ALTURA = 700
LARGURA = 700

# --- Variáveis de iluminação ---
lightColor = glm.vec3(1.0, 1.0, 0.8)  # Luz amarelada
ka = 0.3  # Coeficiente de reflexão ambiente
kd = 0.7  # Coeficiente de reflexão difusa
ks = 0.5  # Coeficiente de reflexão especular
ns = 32.0  # Expoente de reflexão especular
lightPos = glm.vec3(0.0, 0.0, 0.0)

cameraPos   = glm.vec3(0.0,  0.0,  15.0)
cameraFront = glm.vec3(0.0,  0.0, -1.0)
cameraUp    = glm.vec3(0.0,  1.0,  0.0)

# --- Callbacks de input / movimento de câmera ---
firstMouse = True
lastX = LARGURA / 2
lastY = ALTURA / 2
yaw   = -90.0
pitch = 0.0
fov   =  45.0

# timing
deltaTime = 0.0
lastFrame = 0.0

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

def update_farol_position(scene_objects):
    global lightPos, busPos, busYaw
    
    farol = scene_objects[8]  # Assumindo que o farol está no índice 8
    farol.position_offset = glm.vec3(-0.5, 0.5, -1.5)
    farol.light_direction = glm.vec3(0.0, 0.0, -1.0)
    farol.light_cutoff = glm.cos(glm.radians(15.0))  # Ângulo mais estreito (15 graus)
    farol.light_power = 10.0  # Potência aumentada
    
    rot_mat = glm.rotate(glm.mat4(1.0), glm.radians(busYaw), glm.vec3(0.0, 1.0, 0.0))
    
    # Atualiza posição
    rotated_offset = glm.vec3(rot_mat * glm.vec4(farol.position_offset, 1.0))
    farol.transform['tx'] = busPos.x + rotated_offset.x
    farol.transform['ty'] = busPos.y + rotated_offset.y
    farol.transform['tz'] = busPos.z + rotated_offset.z
    lightPos = glm.vec3(farol.transform['tx'], farol.transform['ty'], farol.transform['tz'])
    
    # Atualiza direção do farol
    farol.light_direction = glm.vec3(rot_mat * glm.vec4(0.0, 0.0, -1.0, 0.0))

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

def setup_uniforms(program):
    """Configura todos os uniforms do shader"""
    global lightPos, lightColor, cameraPos, lightPower, ka, kd, ks, ns
    usar_shader(program)
    
    uniforms = {
        "lightPos": (lightPos.x, lightPos.y, lightPos.z),
        "lightColor": (lightColor.x, lightColor.y, lightColor.z),
        "lightPower": lightPower,
        "ka": ka,
        "kd": kd,
        "ks": ks,
        "ns": ns
    }
    
    print("\nUniforms disponíveis no shader:")
    num_uniforms = glGetProgramiv(program, GL_ACTIVE_UNIFORMS)
    for i in range(num_uniforms):
        name, size, type = glGetActiveUniform(program, i)
        print(f"  {name.decode('utf-8')}")
    
    for name, value in uniforms.items():
        loc = glGetUniformLocation(program, name)
        if loc == -1:
            print(f"AVISO: Uniform '{name}' não encontrado no shader!")
            continue
            
        if isinstance(value, tuple):
            glUniform3f(loc, *value)
        else:
            glUniform1f(loc, value)
        print(f"Definido uniform {name}: {value}")

# --- Execução principal ---
def main():
    global cameraPos, cameraFront, cameraUp, deltaTime, lastFrame, polygonal_mode, fov, busPos, busYaw, lightPos
    window = init_window()

    # registra callbacks
    glfw.set_key_callback(window, lambda w,k,s,a,m: None)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    # habilita recursos OpenGL primeiro
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # carrega shaders com verificação rigorosa
    program = criar_shader("shaders/vertex_shader.vs", "shaders/fragment_shader_especular.fs")
    if program == 0:
        print("ERRO: Falha ao criar shader principal!")
        glfw.terminate()
        return

    # Debug: lista todos os uniforms
    num_uniforms = glGetProgramiv(program, GL_ACTIVE_UNIFORMS)
    for i in range(num_uniforms):
        name, size, type = glGetActiveUniform(program, i)

    # carrega outros shaders
    skyboxShader = criar_shader("shaders/skybox.vs", "shaders/skybox.fs")
    floor_program = criar_shader("shaders/floor_shader.vs", "shaders/floor_shader.fs")

    lightDirection = glm.vec3(0.0, 0.0, -1.0)  # Direção padrão do farol
    lightCutoff = glm.cos(glm.radians(30.0))    # Ângulo de 30 graus

    # inicializa cena
    scene_objects = gen_scene_objects(program)
    busPos = glm.vec3(-2.6, -0.99, 9.5)
    lightPos = busPos
    cameraPos.z += 40

    # configura skybox e chão
    skyboxVAO, cubemapTexture = init_skybox(skyboxShader)
    floor_VAO, floor_texture = init_floor(floor_program)

    glfw.show_window(window)

    # loop principal
    while not glfw.window_should_close(window):
        currentFrame = glfw.get_time()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        process_input(window)
        update_farol_position(scene_objects)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

        # Debug: verifica shader ativo
        # print(f"\nFrame - Shader ativo inicial: {glGetIntegerv(GL_CURRENT_PROGRAM)}")

        # 1. Renderiza skybox
        usar_shader(skyboxShader)
        # print(f"Shader ativo skybox: {glGetIntegerv(GL_CURRENT_PROGRAM)}")
        skybox_update(skyboxShader, cameraPos, cameraFront, cameraUp, projection_matrix(), skyboxVAO, cubemapTexture)

        # 2. Renderiza chão
        usar_shader(floor_program)
        # print(f"Shader ativo chão: {glGetIntegerv(GL_CURRENT_PROGRAM)}")
        update_floor(floor_program, view_matrix(), projection_matrix(), floor_VAO, floor_texture)

        # 3. Renderiza cena principal
        usar_shader(program)  # Ativa shader principal novamente
        # print(f"Shader ativo principal: {glGetIntegerv(GL_CURRENT_PROGRAM)} (deve ser {program})")

        # Configura uniforms com verificação extra
        current_prog = glGetIntegerv(GL_CURRENT_PROGRAM)
        if current_prog != program:
            print(f"CORREÇÃO: Shader errado ativo! Ativando {program}")
            glUseProgram(program)

        farol = scene_objects[8]
        glUniform3f(glGetUniformLocation(program, "lightPos"), 
                farol.transform['tx'], 
                farol.transform['ty'], 
                farol.transform['tz'])
        glUniform3f(glGetUniformLocation(program, "lightDir"),
                farol.light_direction.x,
                farol.light_direction.y, 
                farol.light_direction.z)
        glUniform1f(glGetUniformLocation(program, "lightCutOff"), farol.light_cutoff)
        glUniform1f(glGetUniformLocation(program, "lightPower"), farol.light_power)

        # Configura todos os uniforms
        glUniform3f(glGetUniformLocation(program, "lightColor"), lightColor.x, lightColor.y, lightColor.z)
        glUniform3f(glGetUniformLocation(program, "viewPos"), cameraPos.x, cameraPos.y, cameraPos.z)
        glUniform1f(glGetUniformLocation(program, "ka"), ka)
        glUniform1f(glGetUniformLocation(program, "kd"), kd)
        glUniform1f(glGetUniformLocation(program, "ks"), ks)
        glUniform1f(glGetUniformLocation(program, "ns"), ns)
        farol.draw(model_matrix_func=model_matrix, **farol.transform)

        # Restaure os materiais padrão para outros objetos
        glUniform1f(glGetUniformLocation(program, "ka"), ka)
        glUniform1f(glGetUniformLocation(program, "kd"), kd)
        glUniform1f(glGetUniformLocation(program, "ks"), ks)

        # Configura matrizes
        glUniformMatrix4fv(glGetUniformLocation(program, "view"), 1, GL_TRUE, view_matrix())
        glUniformMatrix4fv(glGetUniformLocation(program, "projection"), 1, GL_TRUE, projection_matrix())

        # Atualiza e renderiza objetos
        for i, objmeta in enumerate(scene_objects):
            if i == 8:  # Farol
                # Configura parâmetros específicos do farol
                glUniform3f(glGetUniformLocation(program, "lightPos"), 
                        objmeta.transform['tx'], 
                        objmeta.transform['ty'], 
                        objmeta.transform['tz'])
                glUniform3f(glGetUniformLocation(program, "lightDir"),
                        objmeta.light_direction.x,
                        objmeta.light_direction.y, 
                        objmeta.light_direction.z)
                glUniform1f(glGetUniformLocation(program, "lightCutOff"), objmeta.light_cutoff)
            else:
                glUniform1f(glGetUniformLocation(program, "ka"), ka)
                glUniform1f(glGetUniformLocation(program, "kd"), kd)
                glUniform1f(glGetUniformLocation(program, "ks"), ks)
                glUniform1f(glGetUniformLocation(program, "ns"), ns)

            objmeta.draw(model_matrix_func=model_matrix, **objmeta.transform)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == '__main__':
    main()