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
ALTURA = 1000
LARGURA = 1000

# --- Variáveis de iluminação ---
lightColor = glm.vec3(1.0, 1.0, 0.8)  # Luz amarelada
ka_farol = 1  # Coeficiente de reflexão ambiente do farol
kd_farol = 0.7  # Coeficiente de reflexão difusa do farol
ks_farol = 0.5  # Coeficiente de reflexão especular do farol
constant_farol = 1.0  # Atenuação constante do farol
linear_farol = 0.02  # Atenuação linear do farol
quadratic_farol = 0.002  # Atenuação quadrática do farol

ka_fone = 0.7  # Coeficiente de reflexão ambiente do fone
kd_fone = 0.3  # Coeficiente de reflexão difusa do fone
ks_fone = 0.2  # Coeficiente de reflexão especular do fone
constant_fone = 0.5  # Atenuação constante do fone
linear_fone = 1.3 # Atenuação linear do fone
quadratic_fone = 1.2  # Atenuação quadrática do fone

ka_lampada = 1.0  # Coeficiente de reflexão ambiente da lâmpada
kd_lampada = 1.0  # Coeficiente de reflexão difusa da lâmpada
ks_lampada = 1.0  # Coeficiente de reflexão especular da lâmpada
constant_lampada = 1.0  # Atenuação constante da lâmpada
linear_lampada = 0.009  # Atenuação linear da lâmpada
quadratic_lampada = 0.0032  # Atenuação quadrática da lâmpada

ka_celular = 1  # Coeficiente de reflexão ambiente do celular
kd_celular = 0.7  # Coeficiente de reflexão difusa do celular
ks_celular = 0.5  # Coeficiente de reflexão especular do celular
constant_celular = 1.0  # Atenuação constante do celular
linear_celular = 0.7  # Atenuação linear do celular
quadratic_celular = 0.5  # Atenuação quadrática do celular

luz_ambiente_ligada = True
luz_ambiente_power = 0.8
luz_farol_ligada = True
luzCelularCor = glm.vec3(1.0, 0.0, 0.0)  # Cor da luz do celular
luzCelularPos = glm.vec3(0.0, 10.0, 0.0)  # Posição da luz do celular
luzCelularLigada = True
luzFoneCor = glm.vec3(0.5, 0.0, 0.5)  # Cor da luz do fone de ouvido
luzFonePos = glm.vec3(0.0, 10.0, 0.0)  # Posição da luz do fone de ouvido
luzFoneLigada = True
luzLampadaCor = glm.vec3(1.0, 1.0, 0.5)  # Cor da luz da lâmpada do ônibus
luzLampadaPos = glm.vec3(0.0, 10.0, 0.0)  # Posição da luz da lâmpada do ônibus
luzLampadaLigada = True

cameraPos   = glm.vec3(0.0,  1.0,  15.0)
cameraFront = glm.vec3(0.0,  0.0, -1.0)
cameraUp    = glm.vec3(0.0,  1.0,  0.0)
cameraSpeedFactor = 3

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

def update_bus_position(scene_objects, offsets_iniciais):
    global busPos, busYaw
    
    # --- Atualiza o ônibus principal ---
    onibus = scene_objects[2]
    onibus.transform['tx'] = float(busPos.x)
    onibus.transform['ty'] = float(busPos.y)
    onibus.transform['tz'] = float(busPos.z)
    onibus.transform['angle'] = float(busYaw)  # Atualiza rotação
    
    # Atualiza os faróis
    farol_direito = scene_objects[8]
    farol_esquerdo = scene_objects[9]
    
    for farol in [farol_direito, farol_esquerdo]:
        farol.light_direction = glm.vec3(0.0, 0.0, 1.0)
        farol.light_cutoff = glm.cos(glm.radians(15.0))
        farol.light_outer_cutoff = glm.cos(glm.radians(20.0))
        farol.light_power = 1.0
    
    farol_direito.position_offset = glm.vec3(-1.25, 1.30, 6.0)
    farol_esquerdo.position_offset = glm.vec3(1.25, 1.30, 6.0)
    
    rot_mat = glm.rotate(glm.mat4(1.0), glm.radians(busYaw), glm.vec3(0.0, 1.0, 0.0))
    
    for farol in [farol_direito, farol_esquerdo]:
        rotated_offset = glm.vec3(rot_mat * glm.vec4(farol.position_offset, 1.0))
        farol.transform['tx'] = float(busPos.x + rotated_offset.x)
        farol.transform['ty'] = float(busPos.y + rotated_offset.y)
        farol.transform['tz'] = float(busPos.z + rotated_offset.z)
        farol.light_direction = glm.vec3(rot_mat * glm.vec4(0.0, 0.0, 1.0, 0.0))

    # atualiza os objetos dentro do ônibus
    ind_objs_onibus = [1, 5, 6, 10, 11]  # Índices dos objetos dentro do ônibus (pessoa, mochila, mala, luz_onibus, fone) 
    scene_objects[2].seta_pos(busPos)
    scene_objects[2].transform['angle'] = busYaw

    # Atualiza objetos dentro do ônibus
    rot_mat = glm.rotate(glm.mat4(1.0), glm.radians(busYaw), glm.vec3(0.0, 1.0, 0.0))
    for ind_obj, ind_arr in enumerate(ind_objs_onibus):
        # Posição relativa (com rotação aplicada)
        pos_relativa = glm.vec3(rot_mat * glm.vec4(offsets_iniciais[ind_obj], 1.0))
        
        # Nova posição absoluta (ônibus + posição relativa)
        nova_pos = busPos + pos_relativa
        
        # Atualiza o objeto
        scene_objects[ind_arr].seta_pos(nova_pos)
        scene_objects[ind_arr].transform['angle'] = busYaw

        # Ajuste adicional só para o headset
        if ind_arr == 11:  # fone_ouvido
            # Levemente abaixo do pescoço
            scene_objects[ind_arr].transform['ty'] += 0.10
            scene_objects[ind_arr].transform['tz'] += 0.05
            # Pequena rotação para parecer pendurado
            scene_objects[ind_arr].transform['angle'] -= 90
            scene_objects[ind_arr].transform['rx'] = 1
            scene_objects[ind_arr].transform['ry'] = 0
            scene_objects[ind_arr].transform['rz'] = 0

        if ind_arr == 10: # lampada_onibus
            scene_objects[ind_arr].transform['angle'] -= 180
            scene_objects[ind_arr].transform['rx'] = 1

def mexe_onibus(fwd, yaw):
    global busPos, busYaw
    busPos += fwd
    busYaw += yaw

def get_bbox(obj_pos, offset):
    """Retorna uma bounding box baseada na posição do objeto + offset"""
    return {
        'min_x': obj_pos.x - offset,
        'max_x': obj_pos.x + offset,
        'min_y': obj_pos.y - offset,
        'max_y': obj_pos.y + offset,
        'min_z': obj_pos.z - offset,
        'max_z': obj_pos.z + offset
    }

def process_input(window, obstaculos):
    global cameraPos, cameraFront, cameraUp, deltaTime, placa_escala, parametro_temporal_placa, p_pressed, wireframe
    speed = 2.5 * deltaTime
    global luz_ambiente_ligada, luz_ambiente_power, luz_farol_ligada, luzCelularLigada, luzFoneLigada, luzLampadaLigada
    global busPos, busYaw
    global ks_farol, ks_celular, ks_fone, ks_lampada
    global kd_farol, kd_celular, kd_fone, kd_lampada
    global ka_farol, ka_celular, ka_fone, ka_lampada

    speed = 2.5 * deltaTime
    # translação frente/trás (eixo local Z do ônibus)
    forward = glm.vec3(
        math.sin(glm.radians(busYaw)),
        0,
        math.cos(glm.radians(busYaw))
    )
    
    # Movimento proposto
    new_pos = busPos
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        new_pos = busPos + forward * speed
    elif glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        new_pos = busPos - forward * speed
    
    # Verifica colisão com cada obstáculo
    colisao = False
    hitbox_margin = 2.0
    for bbox in obstaculos:
        if (bbox['min_x'] - hitbox_margin <= new_pos.x <= bbox['max_x'] + hitbox_margin and
            bbox['min_y'] <= new_pos.y <= bbox['max_y'] and
            bbox['min_z'] <= new_pos.z <= bbox['max_z']):
            colisao = True
            # print(f"Colisão com objeto em {bbox}!")
            break

    if not colisao:
        busPos = new_pos


    if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(window, True)

    # Limites da câmera
    max_x = 10.0
    min_x = -10.0
    max_y = 30.0
    min_y = 0.0
    min_z = -50.0
    max_z = 50.0

    # movimentando a camera
    new_pos = cameraPos
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        new_pos = cameraPos + speed * cameraFront * cameraSpeedFactor
            
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        new_pos = cameraPos - speed * cameraFront * cameraSpeedFactor
            
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        new_pos = cameraPos - glm.normalize(glm.cross(cameraFront, cameraUp)) * speed * cameraSpeedFactor
            
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        new_pos = cameraPos + glm.normalize(glm.cross(cameraFront, cameraUp)) * speed * cameraSpeedFactor

    # verificando se ele ultrapasosu o limite da cena
    if not (
        new_pos.x > max_x or 
        new_pos.x < min_x or
        new_pos.y > max_y or
        new_pos.y < min_y or
        new_pos.z > max_z or
        new_pos.z < min_z
    ):
        cameraPos = new_pos

    if not colisao:
        if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
            mexe_onibus(forward * speed, 0)
        if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
            mexe_onibus(-forward * speed, 0)
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

    # Controle da luz ambiente (tecla L)
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        luz_ambiente_ligada = not luz_ambiente_ligada
        print(f"Luz ambiente {'ligada' if luz_ambiente_ligada else 'desligada'}")
        while glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:  # Espera soltar a tecla
            glfw.poll_events()

    # Controle da luz do farol (tecla F)
    if glfw.get_key(window, glfw.KEY_F) == glfw.PRESS:
        luz_farol_ligada = not luz_farol_ligada
        print(f"Luz farol {'ligada' if luz_farol_ligada else 'desligada'}")
        while glfw.get_key(window, glfw.KEY_F) == glfw.PRESS:  # Espera soltar a tecla
            glfw.poll_events()
    
    # Potencia da luz ambiente (tecla 0 e 9)
    if glfw.get_key(window, glfw.KEY_9) == glfw.PRESS:
        luz_ambiente_power += 0.05
        if luz_ambiente_power > 2.0:
            luz_ambiente_power = 2.0
        print(f"Potência da luz ambiente aumentada para {luz_ambiente_power:.1f}")
        while glfw.get_key(window, glfw.KEY_0) == glfw.PRESS:
            glfw.poll_events()
    elif glfw.get_key(window, glfw.KEY_0) == glfw.PRESS:
        luz_ambiente_power -= 0.05
        if luz_ambiente_power < 0.1:
            luz_ambiente_power = 0.1
        print(f"Potência da luz ambiente reduzida para {luz_ambiente_power:.1f}")
        while glfw.get_key(window, glfw.KEY_9) == glfw.PRESS:
            glfw.poll_events()
    
    if glfw.get_key(window, glfw.KEY_U) == glfw.PRESS:
        luzCelularLigada = not luzCelularLigada
        print(f"Luz do celular {'ligada' if luzCelularLigada else 'desligada'}")
        while glfw.get_key(window, glfw.KEY_U) == glfw.PRESS:  # Espera soltar a tecla
            glfw.poll_events()
    if glfw.get_key(window, glfw.KEY_O) == glfw.PRESS:
        luzFoneLigada = not luzFoneLigada
        print(f"Luz do fone {'ligada' if luzFoneLigada else 'desligada'}")
        while glfw.get_key(window, glfw.KEY_O) == glfw.PRESS:  # Espera soltar a tecla
            glfw.poll_events()
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        luzLampadaLigada = not luzLampadaLigada
        print(f"Luz da lâmpada {'ligada' if luzLampadaLigada else 'desligada'}")
        while glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:  # Espera soltar a tecla
            glfw.poll_events()
    if glfw.get_key(window, glfw.KEY_1) == glfw.PRESS:
        if ks_farol > 0.1 and ks_celular > 0.1 and ks_fone > 0.1 and ks_lampada > 0.1:
            ks_farol -= 0.1
            ks_celular -= 0.1
            ks_fone -= 0.1
            ks_lampada -= 0.1
            print(f"Reduzindo ks de todas as luzes para {ks_farol:.2f} {ks_celular:.2f} {ks_fone:.2f} {ks_lampada:.2f}")
    elif glfw.get_key(window, glfw.KEY_2) == glfw.PRESS:
        if ks_farol < 10.0 and ks_celular < 10.0 and ks_fone < 10.0 and ks_lampada < 10.0:
            ks_farol += 0.1
            ks_celular += 0.1
            ks_fone += 0.1
            ks_lampada += 0.1
            print(f"Aumentando ks de todas as luzes para {ks_farol:.2f} {ks_celular:.2f} {ks_fone:.2f} {ks_lampada:.2f}")
    
    if glfw.get_key(window, glfw.KEY_3) == glfw.PRESS:
        if kd_farol > 0.1 and kd_celular > 0.1 and kd_fone > 0.1 and kd_lampada > 0.1:
            kd_farol -= 0.1
            kd_celular -= 0.1
            kd_fone -= 0.1
            kd_lampada -= 0.1
            print(f"Reduzindo kd de todas as luzes para {kd_farol:.2f} {kd_celular:.2f} {kd_fone:.2f} {kd_lampada:.2f}")
            #while glfw.get_key(window, glfw.KEY_3) == glfw.PRESS:
            #    glfw.poll_events()
    elif glfw.get_key(window, glfw.KEY_4) == glfw.PRESS:
        if kd_farol < 10.0 and kd_celular < 10.0 and kd_fone < 10.0 and kd_lampada < 10.0:
            kd_farol += 0.1
            kd_celular += 0.1
            kd_fone += 0.1
            kd_lampada += 0.1
            print(f"Aumentando kd de todas as luzes para {kd_farol:.2f} {kd_celular:.2f} {kd_fone:.2f} {kd_lampada:.2f}")
            #while glfw.get_key(window, glfw.KEY_4) == glfw.PRESS:
            #    glfw.poll_events()
    
    if glfw.get_key(window, glfw.KEY_5) == glfw.PRESS:
        if ka_farol > 0.1 and ka_celular > 0.1 and ka_fone > 0.1 and ka_lampada > 0.1:
            ka_farol -= 0.1
            ka_celular -= 0.1
            ka_fone -= 0.1
            ka_lampada -= 0.1
            print(f"Reduzindo ka de todas as luzes para {ka_farol:.2f} {ka_celular:.2f} {ka_fone:.2f} {ka_lampada:.2f}")
    elif glfw.get_key(window, glfw.KEY_6) == glfw.PRESS:
        if ka_farol < 10.0 and ka_celular < 10.0 and ka_fone < 10.0 and ka_lampada < 10.0:
            ka_farol += 0.1
            ka_celular += 0.1
            ka_fone += 0.1
            ka_lampada += 0.1
            print(f"Aumentando ka de todas as luzes para {ka_farol:.2f} {ka_celular:.2f} {ka_fone:.2f} {ka_lampada:.2f}")


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

    # carrega outros shaders
    skyboxShader = criar_shader("shaders/skybox.vs", "shaders/skybox.fs")
    floor_program = criar_shader("shaders/floor_shader.vs", "shaders/floor_shader.fs")

    # inicializa cena
    scene_objects = gen_scene_objects(program)
    busPos = glm.vec3(-2.6, -0.99, 9.5)
    cameraPos.z += 35

    # Definindo as posições
    placa_pos = scene_objects[0].get_pos()
    ponto_onibus_pos = scene_objects[3].get_pos()
    pessoa_telefone_pos = scene_objects[4].get_pos()

    # Definindo as hitboxes individualmente
    placa_bbox = get_bbox(placa_pos, offset=2.0)
    ponto_onibus_bbox = get_bbox(ponto_onibus_pos, offset=2.0)
    pessoa_telefone_bbox = get_bbox(pessoa_telefone_pos, offset=2.0)

    # Colocando em uma lista
    obstaculos = [
        placa_bbox,
        ponto_onibus_bbox,
        pessoa_telefone_bbox
    ]

    ind_objs_onibus = [1, 5, 6, 10, 11]  # Índices dos objetos dentro do ônibus (pessoa, mochila, mala, luz_onibus, fone)
    offsets_inicais = []

    # Calcula a posição relativa inicial de cada objeto em relação ao ônibus
    for ind_obj in ind_objs_onibus:
        pos_obj = scene_objects[ind_obj].get_pos()
        pos_onibus = scene_objects[2].get_pos() # 2 é a posição do onibus no vetor
        offset = pos_obj - pos_onibus
        offsets_inicais.append(offset)



    # configura skybox e chão
    skyboxVAO, cubemapTexture = init_skybox(skyboxShader)
    floor_VAO, floor_texture = init_floor(floor_program)

    glfw.show_window(window)

    # loop principal
    while not glfw.window_should_close(window):
        currentFrame = glfw.get_time()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        process_input(window, obstaculos)
        update_bus_position(scene_objects, offsets_inicais)

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

        farol_direito = scene_objects[8]
        farol_esquerdo = scene_objects[9]

        # set de on/off luz do farol
        glUniform1i(glGetUniformLocation(program, "luzFarolLigada"), luz_farol_ligada)

        for i, farol in enumerate([farol_direito, farol_esquerdo], start=1):
            # Define os uniforms para cada farol
            glUniform3f(glGetUniformLocation(program, f"lightPos{i}"), 
                        farol.transform['tx'], 
                        farol.transform['ty'], 
                        farol.transform['tz'])
            
            glUniform3f(glGetUniformLocation(program, f"lightDir{i}"),
                        farol.light_direction.x,
                        farol.light_direction.y, 
                        farol.light_direction.z)
            
            # Parâmetros comuns
            glUniform1f(glGetUniformLocation(program, "lightCutOff"), farol.light_cutoff)
            glUniform1f(glGetUniformLocation(program, "lightOuterCutOff"), farol.light_outer_cutoff)
            glUniform1f(glGetUniformLocation(program, "lightPower"), farol.light_power)
            
            # farol.draw(model_matrix_func=model_matrix, **farol.transform)

        # Configura todos os uniforms
        glUniform3f(glGetUniformLocation(program, "viewPos"), cameraPos.x, cameraPos.y, cameraPos.z)

        # Configura uniforms de iluminação
        usar_shader(program)
        
        luzCelularPos = scene_objects[4].get_pos()  # Posição da luz do celular
        luzCelularPos.y += 4.0
        luzCelularPos.x += 1.0
        luzFonePos = scene_objects[11].get_pos()  # Posição da luz do fone de ouvido
        luzLampadaPos = scene_objects[10].get_pos()  # Posição da luz da lâmpada do ônibus

        # Calcula os limites do ônibus
        onibus_min_bounds = glm.vec3(busPos.x - 1.5, busPos.y + 1.0, busPos.z - 6.6)
        onibus_max_bounds = glm.vec3(busPos.x + 1.5, busPos.y + 3.6, busPos.z + 6.15)

        # Envia para o shader
        glUniform3f(glGetUniformLocation(program, "onibusMinBounds"), 
                    onibus_min_bounds.x, onibus_min_bounds.y, onibus_min_bounds.z)
        glUniform3f(glGetUniformLocation(program, "onibusMaxBounds"), 
                    onibus_max_bounds.x, onibus_max_bounds.y, onibus_max_bounds.z)

        # Aplica o poder da luz ambiente
        glUniform1f(glGetUniformLocation(program, "luzAmbientePower"), luz_ambiente_power)
        glUniform1i(glGetUniformLocation(program, "luzAmbienteLigada"), luz_ambiente_ligada)
        glUniform3f(glGetUniformLocation(program, "posFone"),
                    luzFonePos.x, luzFonePos.y, luzFonePos.z)
        glUniform3f(glGetUniformLocation(program, "corFone"),
                    luzFoneCor.x, luzFoneCor.y, luzFoneCor.z)
        glUniform3f(glGetUniformLocation(program, "posCelular"),
                    luzCelularPos.x, luzCelularPos.y, luzCelularPos.z)
        glUniform3f(glGetUniformLocation(program, "corCelular"),
                    luzCelularCor.x, luzCelularCor.y, luzCelularCor.z)
        glUniform3f(glGetUniformLocation(program, "posLampada"),
                    luzLampadaPos.x, luzLampadaPos.y, luzLampadaPos.z)
        glUniform3f(glGetUniformLocation(program, "corLampada"),
                    luzLampadaCor.x, luzLampadaCor.y, luzLampadaCor.z)
        glUniform1i(glGetUniformLocation(program, "luzCelularLigada"), luzCelularLigada)
        glUniform1i(glGetUniformLocation(program, "luzFoneLigada"), luzFoneLigada)
        glUniform1i(glGetUniformLocation(program, "luzLampadaLigada"), luzLampadaLigada)
        glUniform1f(glGetUniformLocation(program, "ka_farol"), ka_farol)
        glUniform1f(glGetUniformLocation(program, "kd_farol"), kd_farol)
        glUniform1f(glGetUniformLocation(program, "ks_farol"), ks_farol)
        glUniform1f(glGetUniformLocation(program, "constant_farol"), constant_farol)
        glUniform1f(glGetUniformLocation(program, "linear_farol"), linear_farol)
        glUniform1f(glGetUniformLocation(program, "quadratic_farol"), quadratic_farol)
        glUniform1f(glGetUniformLocation(program, "ka_fone"), ka_fone)
        glUniform1f(glGetUniformLocation(program, "kd_fone"), kd_fone)
        glUniform1f(glGetUniformLocation(program, "ks_fone"), ks_fone)
        glUniform1f(glGetUniformLocation(program, "constant_fone"), constant_fone)
        glUniform1f(glGetUniformLocation(program, "linear_fone"), linear_fone)
        glUniform1f(glGetUniformLocation(program, "quadratic_fone"), quadratic_fone)
        glUniform1f(glGetUniformLocation(program, "ka_lampada"), ka_lampada)
        glUniform1f(glGetUniformLocation(program, "kd_lampada"), kd_lampada)
        glUniform1f(glGetUniformLocation(program, "ks_lampada"), ks_lampada)
        glUniform1f(glGetUniformLocation(program, "constant_lampada"), constant_lampada)
        glUniform1f(glGetUniformLocation(program, "linear_lampada"), linear_lampada)
        glUniform1f(glGetUniformLocation(program, "quadratic_lampada"), quadratic_lampada)
        glUniform1f(glGetUniformLocation(program, "ka_celular"), ka_celular)
        glUniform1f(glGetUniformLocation(program, "kd_celular"), kd_celular)
        glUniform1f(glGetUniformLocation(program, "ks_celular"), ks_celular)
        glUniform1f(glGetUniformLocation(program, "constant_celular"), constant_celular)
        glUniform1f(glGetUniformLocation(program, "linear_celular"), linear_celular)
        glUniform1f(glGetUniformLocation(program, "quadratic_celular"), quadratic_celular)
        
        # Configura outros parâmetros de iluminação
        glUniform3f(glGetUniformLocation(program, "lightColorFarol"), lightColor.x, lightColor.y, lightColor.z)
        glUniform3f(glGetUniformLocation(program, "viewPos"), cameraPos.x, cameraPos.y, cameraPos.z)

        # Configura matrizes
        glUniformMatrix4fv(glGetUniformLocation(program, "view"), 1, GL_TRUE, view_matrix())
        glUniformMatrix4fv(glGetUniformLocation(program, "projection"), 1, GL_TRUE, projection_matrix())

        for i, objmeta in enumerate(scene_objects):      
            # Desenha o objeto
            objmeta.draw(model_matrix_func=model_matrix, **objmeta.transform)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == '__main__':
    main()