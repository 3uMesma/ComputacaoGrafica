import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import ctypes
import math
import random

# -------------------------------------
# Função utilitária para multiplicar matrizes 4x4 (usando NumPy)
def multiplica_matriz(a, b):
    m_a = a.reshape(4, 4)
    m_b = b.reshape(4, 4)
    m_c = np.dot(m_a, m_b)
    return m_c.reshape(1, 16)

# -------------------------------------
# Funções de construção manual de matrizes 4x4

def identidade():
    return np.identity(4, dtype=np.float32).reshape(1, 16)

def translacao(tx, ty, tz):
    m = np.identity(4, dtype=np.float32)
    m[0, 3] = tx
    m[1, 3] = ty
    m[2, 3] = tz
    return m.reshape(1, 16)

def escala(sx, sy, sz):
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m.reshape(1, 16)

def rotacao_x(theta):  # theta em radianos
    c = math.cos(theta)
    s = math.sin(theta)
    m = np.identity(4, dtype=np.float32)
    m[1, 1] = c
    m[1, 2] = -s
    m[2, 1] = s
    m[2, 2] = c
    return m.reshape(1, 16)

def rotacao_y(theta):
    c = math.cos(theta)
    s = math.sin(theta)
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    return m.reshape(1, 16)

def rotacao_z(theta):
    c = math.cos(theta)
    s = math.sin(theta)
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 1] = -s
    m[1, 0] = s
    m[1, 1] = c
    return m.reshape(1, 16)

def rotacao_arbitraria(theta, ax, ay, az):
    # Normaliza o eixo
    norm = math.sqrt(ax*ax + ay*ay + az*az)
    ax /= norm; ay /= norm; az /= norm
    c = math.cos(theta)
    s = math.sin(theta)
    t = 1 - c
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = t * ax * ax + c
    m[0, 1] = t * ax * ay - s * az
    m[0, 2] = t * ax * az + s * ay
    m[1, 0] = t * ax * ay + s * az
    m[1, 1] = t * ay * ay + c
    m[1, 2] = t * ay * az - s * ax
    m[2, 0] = t * ax * az - s * ay
    m[2, 1] = t * ay * az + s * ax
    m[2, 2] = t * az * az + c
    return m.reshape(1, 16)

def ortho(left, right, bottom, top, near, far):
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = 2 / (right - left)
    m[1, 1] = 2 / (top - bottom)
    m[2, 2] = -2 / (far - near)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = -(far + near) / (far - near)
    m[3, 3] = 1.0
    return m.reshape(1, 16)

# -------------------------------------
# Inicialização do GLFW e da janela
if not glfw.init():
    raise Exception("GLFW initialization failed")

window = glfw.create_window(800, 600, "Cena: Avião, Nuvem, Oceano, Sol e Pássaros", None, None)
if not window:
    glfw.terminate()
    raise Exception("GLFW window creation failed")
glfw.make_context_current(window)

glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glClearColor(0.53, 0.81, 0.92, 1.0)  # Céu

# -------------------------------------
# Shaders simples: transforma os vértices e colore
vertex_src = """
#version 330 core
layout(location = 0) in vec3 aPos;
uniform mat4 mat_transformation;
void main(){
    gl_Position = mat_transformation * vec4(aPos, 1.0);
}
"""
fragment_src = """
#version 330 core
uniform vec4 color;
out vec4 FragColor;
void main(){
    FragColor = color;
}
"""

program = OpenGL.GL.shaders.compileProgram(
    OpenGL.GL.shaders.compileShader(vertex_src, GL_VERTEX_SHADER),
    OpenGL.GL.shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
)
glUseProgram(program)
loc_transform = glGetUniformLocation(program, "mat_transformation")
loc_color = glGetUniformLocation(program, "color")

# -------------------------------------
# 1. AVIÃO
# Vértices e índices do avião
airplane_vertices = np.array([
    # Fuselagem (retangular)
     0.75,  0.2,  0.2,   # 0
    -0.75,  0.2,  0.2,   # 1
    -0.75, -0.2,  0.2,   # 2 
     0.75, -0.2,  0.2,   # 3
     0.75,  0.2, -0.2,   # 4
    -0.75,  0.2, -0.2,   # 5
    -0.75, -0.2, -0.2,   # 6
     0.75, -0.2, -0.2,   # 7
    # Asa direita
    -0.25,  0.025, 1.2,  # 8
    -0.25,  0.025, 0.2,  # 9
     0.25,  0.025, 0.2,  # 10
    -0.25, -0.025, 1.2,  # 11
    -0.25, -0.025, 0.2,  # 12
     0.25, -0.025, 0.2,  # 13
    # Asa esquerda
    -0.25,  0.025, -1.2, # 14
    -0.25,  0.025, -0.2, # 15
     0.25,  0.025, -0.2, # 16
    -0.25, -0.025, -1.2, # 17
    -0.25, -0.025, -0.2, # 18
     0.25, -0.025, -0.2, # 19
    # Nariz
     0.95,  0.1,  0.1,   # 20 
     0.95, -0.1,  0.1,   # 21
     0.95,  0.1, -0.1,   # 22
     0.95, -0.1, -0.1,   # 23
     1.2,  0.0,  0.0,    # 24
    # Traseira
    -1.2,  0.2,  0.0,    # 25
    # Barbatana
    -0.8,  0.2,  0.025,  # 26
    -0.8,  0.2, -0.025,  # 27
    -1.0,  0.2,  0.025,  # 28
    -1.0,  0.2, -0.025,  # 29
    -1.0,  0.6,  0.025,  # 30
    -1.0,  0.6, -0.025,  # 31
    -0.95, 0.6,  0.025,  # 32
    -0.95, 0.6, -0.025,  # 33
    # Estabilizador Direito
    -0.95,  0.025, 0.4,  # 34
    -0.95,  0.025, 0.05, # 35
    -0.80,  0.025, 0.15, # 36
    -0.95, -0.025, 0.4,  # 37
    -0.95, -0.025, 0.05, # 38
    -0.80, -0.025, 0.15, # 39
    # Estabilizador Esquerdo
    -0.95,  0.025, -0.4, # 40
    -0.95,  0.025, -0.05,# 41
    -0.80,  0.025, -0.15,# 42
    -0.95, -0.025, -0.4, # 43
    -0.95, -0.025, -0.05,# 44
    -0.80, -0.025, -0.15,# 45
], dtype=np.float32)

airplane_indices = np.array([
    # Fuselagem (24 índices)
     0,  1,  2,   0,  2,  3,
     4,  6,  5,   4,  7,  6,
     0,  4,  5,   0,  5,  1,
     2,  6,  7,   2,  7,  3,
    # Asa Direita (18 índices)
     8,  9, 10,
    11, 13, 12,
     8,  9, 12,   8, 12, 11,
     8, 10, 13,   8, 13, 11,
    # Asa Esquerda (18 índices)
    14, 15, 16,
    17, 19, 18,
    14, 15, 18,  14, 18, 17,
    14, 16, 19,  14, 19, 17,
    # Nariz parte branca (24 índices)
     0,  3, 20,   3, 20, 21,
     0,  4, 20,   4, 20, 22,
     4,  7, 22,   7, 22, 23,
     3,  7, 23,   3, 21, 23,
    # Nariz parte roxa (12 índices)
    20, 22, 24,
    20, 21, 24,
    21, 23, 24,
    22, 23, 24,
    # Traseira (12 índices)
     1,  2, 25,
     2,  5, 25,
     5,  6, 25,
     1,  5, 25,
    # Barbatana (30 índices)
    26, 28, 30,   26, 30, 32,
    27, 29, 31,   27, 31, 33,
    26, 27, 32,   27, 32, 33,
    31, 32, 33,   30, 31, 32,
    28, 29, 30,   29, 30, 31,
    # Estabilizador Direito (18 índices)
    34, 35, 36,
    37, 39, 38,
    34, 35, 38,   34, 38, 37,
    34, 36, 39,   34, 39, 37,
    # Estabilizador Esquerdo (18 índices)
    40, 41, 42,
    43, 45, 44,
    40, 41, 44,   40, 44, 43,
    40, 42, 45,   40, 45, 43,
], dtype=np.uint32)

# Cria VAO/VBO/EBO para o avião
VAO_airplane = glGenVertexArrays(1)
VBO_airplane = glGenBuffers(1)
EBO_airplane = glGenBuffers(1)
glBindVertexArray(VAO_airplane)
glBindBuffer(GL_ARRAY_BUFFER, VBO_airplane)
glBufferData(GL_ARRAY_BUFFER, airplane_vertices.nbytes, airplane_vertices, GL_STATIC_DRAW)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_airplane)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, airplane_indices.nbytes, airplane_indices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# -------------------------------------
# 2. NUVEM
def geraPoligono3D(n_lados, tamanhos, espessura, deslocamento_z, rotacao):
    pontos = []
    offset_angulo = rotacao
    for i in range(n_lados):
        x = tamanhos[i] * math.cos(offset_angulo)
        y = tamanhos[i] * math.sin(offset_angulo)
        pontos.append([x, y, deslocamento_z])
        offset_angulo += 2 * math.pi / n_lados
    copia_pontos = [[x, y, espessura + deslocamento_z] for x, y, _ in pontos]
    vertices = np.array(pontos + copia_pontos, dtype=np.float32)
    indices = []
    for i in range(n_lados):
        prox = (i + 1) % n_lados
        indices.extend([i, prox, n_lados + prox, n_lados + i])
    indices = np.array(indices, dtype=np.uint32)
    return vertices, indices

NUM_POLIGONOS = 5
poligonos_vertices_list = []
poligonos_indices_list = []
deslocamento_z = 0.0
indice_offset = 0
for _ in range(NUM_POLIGONOS):
    n_lados = random.randint(12, 20)
    tamanhos = np.random.uniform(1.5, 2.5, n_lados)
    rotacao_inicial = random.uniform(0, 2 * math.pi)
    v, ind = geraPoligono3D(n_lados, tamanhos, 0.5, deslocamento_z, rotacao_inicial)
    ind = ind + indice_offset
    poligonos_vertices_list.append(v)
    poligonos_indices_list.append(ind)
    indice_offset += len(v)
    deslocamento_z -= 0.3
poligonos_vertices = np.vstack(poligonos_vertices_list)
poligonos_indices = np.hstack(poligonos_indices_list)

# Cria VAO/VBO/EBO para a nuvem
VAO_cloud = glGenVertexArrays(1)
VBO_cloud = glGenBuffers(1)
EBO_cloud = glGenBuffers(1)
glBindVertexArray(VAO_cloud)
glBindBuffer(GL_ARRAY_BUFFER, VBO_cloud)
glBufferData(GL_ARRAY_BUFFER, poligonos_vertices.nbytes, poligonos_vertices, GL_STATIC_DRAW)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_cloud)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, poligonos_indices.nbytes, poligonos_indices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# -------------------------------------
# 3. OCEANO
ocean_vertices = np.array([
    # Retângulo principal
    -1.0, -0.5, 0.0,   # 0 
     1.0, -0.5, 0.0,   # 1
    -1.0,  0.0, 0.0,   # 2
     1.0,  0.0, 0.0,   # 3,
    # Ondinhas
    -0.9, 0.0, 0.0,    # 4
    -0.8, 0.0, 0.0,    # 5
    -0.7, 0.0, 0.0,    # 6
    -0.6, 0.0, 0.0,    # 7
    -0.5, 0.0, 0.0,    # 8
    -0.4, 0.0, 0.0,    # 9
    -0.3, 0.0, 0.0,    # 10
    -0.2, 0.0, 0.0,    # 11
    -0.1, 0.0, 0.0,    # 12
     0.0, 0.0, 0.0,    # 13
     0.1, 0.0, 0.0,    # 14
     0.2, 0.0, 0.0,    # 15
     0.3, 0.0, 0.0,    # 16
     0.4, 0.0, 0.0,    # 17
     0.5, 0.0, 0.0,    # 18
     0.6, 0.0, 0.0,    # 19
     0.7, 0.0, 0.0,    # 20
     0.8, 0.0, 0.0,    # 21
     0.9, 0.0, 0.0,    # 22
    # Ondinhas azuis padrão
    -0.95, 0.03, 0.0,  # 23
    -0.75, 0.03, 0.0,  # 24
    -0.55, 0.03, 0.0,  # 25
    -0.35, 0.03, 0.0,  # 26
    -0.15, 0.03, 0.0,  # 27
     0.05, 0.03, 0.0,  # 28
     0.25, 0.03, 0.0,  # 29
     0.45, 0.03, 0.0,  # 30
     0.65, 0.03, 0.0,  # 31
     0.85, 0.03, 0.0,  # 32
    # Ondinhas azuis claro
    -0.85, 0.03, 0.0,  # 33
    -0.65, 0.03, 0.0,  # 34
    -0.45, 0.03, 0.0,  # 35
    -0.25, 0.03, 0.0,  # 36
    -0.05, 0.03, 0.0,  # 37
     0.15, 0.03, 0.0,  # 38
     0.35, 0.03, 0.0,  # 39
     0.55, 0.03, 0.0,  # 40
     0.75, 0.03, 0.0,  # 41
     0.95, 0.03, 0.0   # 42
], dtype=np.float32)

ocean_indices = np.array([
    # Retângulo principal
     0, 1, 2,
     1, 2, 3,
    # Ondinhas padrão
     2, 23, 4,
     5, 24, 6,
     7, 25, 8,
     9, 26, 10,
     11, 27, 12,
     13, 28, 14,
     15, 29, 16,
     17, 30, 18,
     19, 31, 20,
     21, 32, 22,
    # Ondinhas mais claras
     4, 33, 5,
     6, 34, 7,
     8, 35, 9,
    10, 36, 11,
    12, 37, 13,
    14, 38, 15,
    16, 39, 17,
    18, 40, 19,
    20, 41, 21,
    22, 42, 3,
], dtype=np.uint32)

# Cria VAO/VBO/EBO para o oceano
VAO_ocean = glGenVertexArrays(1)
VBO_ocean = glGenBuffers(1)
EBO_ocean = glGenBuffers(1)
glBindVertexArray(VAO_ocean)
glBindBuffer(GL_ARRAY_BUFFER, VBO_ocean)
glBufferData(GL_ARRAY_BUFFER, ocean_vertices.nbytes, ocean_vertices, GL_STATIC_DRAW)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_ocean)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, ocean_indices.nbytes, ocean_indices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# -------------------------------------
# 4. SOL
n_lados = 4
angles = np.linspace(0, 2 * math.pi, n_lados, endpoint=False)
sun_vertices = [(math.cos(a), math.sin(a), 0.0) for a in angles]
sun_vertices.insert(0, (0.0, 0.0, 0.0))  # centro
sun_vertices = np.array(sun_vertices, dtype=np.float32)
sun_indices = np.array([0] + list(range(1, n_lados + 1)) + [1], dtype=np.uint32)

VAO_sun = glGenVertexArrays(1)
VBO_sun = glGenBuffers(1)
EBO_sun = glGenBuffers(1)
glBindVertexArray(VAO_sun)
glBindBuffer(GL_ARRAY_BUFFER, VBO_sun)
glBufferData(GL_ARRAY_BUFFER, sun_vertices.nbytes, sun_vertices, GL_STATIC_DRAW)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_sun)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, sun_indices.nbytes, sun_indices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# -------------------------------------
# 5. PÁSSARO
bird_vertices = np.array([
    # Cabeça
     0.5,  0.2, 0.0,   # 0 
     0.0, -0.8, 0.0,   # 1
    -0.5,  0.2, 0.0,   # 2
    # Corpo
     0.5, -0.5, 0.0,   # 3
    -0.5, -0.5, 0.0,   # 4
     0.3, -1.5, 0.0,   # 5
    -0.3, -1.5, 0.0,   # 6
     0.3, -2.0, 0.0,   # 7
    -0.3, -2.0, 0.0,   # 8
    # Asas
     2.0, -0.6, 0.0,   # 9
    -2.0, -0.6, 0.0,   # 10
     0.0, -1.5, 0.0,   # 11
     2.5, -2.0, 0.0,   # 12
    -2.5, -2.0, 0.0,   # 13
     0.5, -0.6, 0.0,   # 14
    -0.5, -0.6, 0.0,   # 15
    # Rabo
     0.7, -2.8, 0.0,   # 16
    -0.7, -2.8, 0.0    # 17
], dtype=np.float32)

bird_indices = np.array([
    # Cabeça
    0, 1, 2,
    # Corpo
    3, 4, 5,
    4, 5, 6,
    5, 6, 7,
    6, 7, 8,
    # Asas
    9, 10, 11,
    12, 9, 14,
    13, 10, 15,
    # Rabo
    7, 8, 16,
    16, 17, 8,
], dtype=np.uint32)

VAO_bird = glGenVertexArrays(1)
VBO_bird = glGenBuffers(1)
EBO_bird = glGenBuffers(1)
glBindVertexArray(VAO_bird)
glBindBuffer(GL_ARRAY_BUFFER, VBO_bird)
glBufferData(GL_ARRAY_BUFFER, bird_vertices.nbytes, bird_vertices, GL_STATIC_DRAW)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_bird)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, bird_indices.nbytes, bird_indices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# -------------------------------------
# Projeção ortográfica (sem view) para posicionar os objetos diretamente
proj = ortho(-4.0, 4.0, -3.0, 3.0, -10, 10)

# -------------------------------------
# Posições e escalas dos objetos – usando listas para permitir atualizações
airplane_pos = [0.0, 0.5, 0.0]
airplane_scale = [1.0, 1.0, 1.0]
airplane_speed = 0.001
airplane_rotational_speed = 0.001
airplane_angle_x = 0.0
airplane_angle_y = 0.0
airplane_angle_z = 0.0

cloud_pos = (-3.0, 1.5, 0.0)
cloud_scale = (0.2, 0.2, 0.2)
cloud_angle = 0.0

ocean_pos = [0.0, -2.0, 0.0]
ocean_scale = [10.0, 10.0, 1.0]

sun_pos = (3.0, 2.0, 0.0)
sun_scale = (0.5, 0.5, 0.5)

birds_positions = [
    (-2.0, 1.0, 0.0),
    (-1.5, 1.2, 0.0),
    (-2.5, 0.8, 0.0)
]
bird_scale = (0.1, 0.1, 0.1)

wireframe = False
p_pressed = False

# -------------------------------------
# Loop principal
while not glfw.window_should_close(window):
    glfw.poll_events()

    # Verifica a tecla 'P' para alternar o modo de renderização:
    if glfw.get_key(window, glfw.KEY_P) == glfw.PRESS:
        if not p_pressed:  # Apenas alterna na transição
            p_pressed = True
            wireframe = not wireframe
            if wireframe:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        p_pressed = False

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # --- Desenha o OCEANO ---
    # Atualiza a escala e posição via teclado
    if glfw.get_key(window, glfw.KEY_G) == glfw.PRESS:
        ocean_scale[0] += 0.001
        ocean_scale[1] += 0.001
        ocean_pos[0] += 0.001
        ocean_pos[1] += 0.001
    if glfw.get_key(window, glfw.KEY_H) == glfw.PRESS:
        ocean_scale[0] -= 0.001
        ocean_scale[1] -= 0.001
        ocean_pos[0] -= 0.001
        ocean_pos[1] -= 0.001

    T_ocean = translacao(ocean_pos[0], ocean_pos[1], ocean_pos[2])
    S_ocean = escala(ocean_scale[0], ocean_scale[1], ocean_scale[2])
    model_ocean = multiplica_matriz(T_ocean, S_ocean)
    mvp_ocean = multiplica_matriz(proj, model_ocean)
    glUniformMatrix4fv(loc_transform, 1, GL_TRUE, mvp_ocean)
    glBindVertexArray(VAO_ocean)
    # Retângulo principal
    glUniform4f(loc_color, 0.0, 0.0, 1.0, 1.0)
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
    # Ondinhas padrão
    glDrawElements(GL_TRIANGLES, 30, GL_UNSIGNED_INT, ctypes.c_void_p(6 * 4))
    # Ondinhas mais claras
    glUniform4f(loc_color, 0.678, 0.847, 0.902, 1.0)
    glDrawElements(GL_TRIANGLES, 30, GL_UNSIGNED_INT, ctypes.c_void_p(36 * 4))

    # --- Desenha o AVIÃO ---
    # Controle via teclado para rotação
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        airplane_angle_y += airplane_rotational_speed
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        airplane_angle_y -= airplane_rotational_speed
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        airplane_angle_x += airplane_rotational_speed
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        airplane_angle_x -= airplane_rotational_speed
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        airplane_angle_z += airplane_rotational_speed
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        airplane_angle_z -= airplane_rotational_speed

    # Movimento "para frente" com a tecla W
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        # Constrói a matriz de rotação completa
        rX = rotacao_x(airplane_angle_x)
        rY = rotacao_y(airplane_angle_y)
        rZ = rotacao_z(airplane_angle_z)
        rotationMatrix = multiplica_matriz(rZ, multiplica_matriz(rY, rX))
        # Calcula a direção para frente (vetor (1, 0, 0) transformado)
        rotMat = rotationMatrix.reshape(4, 4)
        forward = np.dot(rotMat, np.array([1, 0, 0, 0], dtype=np.float32))
        norm = np.linalg.norm(forward[:3])
        if norm != 0:
            forward = forward / norm
        airplane_pos[0] += airplane_speed * forward[0]
        airplane_pos[1] += airplane_speed * forward[1]
        airplane_pos[2] += airplane_speed * forward[2]

    # Monta a model matrix para o avião: T * R * S
    T_airplane = translacao(airplane_pos[0], airplane_pos[1], airplane_pos[2])
    rX = rotacao_x(airplane_angle_x)
    rY = rotacao_y(airplane_angle_y)
    rZ = rotacao_z(airplane_angle_z)
    R_airplane = multiplica_matriz(rZ, multiplica_matriz(rY, rX))
    S_airplane = escala(airplane_scale[0], airplane_scale[1], airplane_scale[2])
    model_airplane = multiplica_matriz(T_airplane, multiplica_matriz(R_airplane, S_airplane))
    mvp_airplane = multiplica_matriz(proj, model_airplane)
    glUniformMatrix4fv(loc_transform, 1, GL_TRUE, mvp_airplane)
    glBindVertexArray(VAO_airplane)
    # Fuselagem – branco
    glUniform4f(loc_color, 1.0, 1.0, 1.0, 1.0)
    glDrawElements(GL_TRIANGLES, 24, GL_UNSIGNED_INT, None)
    # Asa Direita – roxo
    glUniform4f(loc_color, 0.4, 0.1, 0.8, 1.0)
    glDrawElements(GL_TRIANGLES, 18, GL_UNSIGNED_INT, ctypes.c_void_p(24 * 4))
    # Asa Esquerda – roxo
    glDrawElements(GL_TRIANGLES, 18, GL_UNSIGNED_INT, ctypes.c_void_p((24+18) * 4))
    # Nariz parte branca – branco
    glUniform4f(loc_color, 1.0, 1.0, 1.0, 1.0)
    glDrawElements(GL_TRIANGLES, 24, GL_UNSIGNED_INT, ctypes.c_void_p((24+18+18) * 4))
    # Nariz parte roxa – roxo
    glUniform4f(loc_color, 0.4, 0.1, 0.8, 1.0)
    glDrawElements(GL_TRIANGLES, 12, GL_UNSIGNED_INT, ctypes.c_void_p((24+18+18+24) * 4))
    # Traseira – branco
    glUniform4f(loc_color, 1.0, 1.0, 1.0, 1.0)
    glDrawElements(GL_TRIANGLES, 12, GL_UNSIGNED_INT, ctypes.c_void_p((24+18+18+24+12) * 4))
    # Barbatana – roxo
    glUniform4f(loc_color, 0.4, 0.1, 0.8, 1.0)
    glDrawElements(GL_TRIANGLES, 30, GL_UNSIGNED_INT, ctypes.c_void_p((24+18+18+24+12+12) * 4))
    # Estabilizador Direito – roxo
    glDrawElements(GL_TRIANGLES, 18, GL_UNSIGNED_INT, ctypes.c_void_p((24+18+18+24+12+12+30) * 4))
    # Estabilizador Esquerdo – roxo
    glDrawElements(GL_TRIANGLES, 18, GL_UNSIGNED_INT, ctypes.c_void_p((24+18+18+24+12+12+30+18) * 4))

    # --- Desenha a NUVEM ---
    cloud_angle += 0.001
    T_cloud = translacao(cloud_pos[0], cloud_pos[1], cloud_pos[2])
    R_cloud = rotacao_arbitraria(cloud_angle, 1, 1, 1)
    S_cloud = escala(cloud_scale[0], cloud_scale[1], cloud_scale[2])
    model_cloud = multiplica_matriz(T_cloud, multiplica_matriz(R_cloud, S_cloud))
    mvp_cloud = multiplica_matriz(proj, model_cloud)
    glUniformMatrix4fv(loc_transform, 1, GL_TRUE, mvp_cloud)
    glBindVertexArray(VAO_cloud)
    glUniform4f(loc_color, 1.0, 1.0, 1.0, 0.75)
    glDrawElements(GL_TRIANGLE_FAN, len(poligonos_indices), GL_UNSIGNED_INT, None)

    # --- Desenha o SOL ---
    T_sun = translacao(sun_pos[0], sun_pos[1], sun_pos[2])
    S_sun = escala(sun_scale[0], sun_scale[1], sun_scale[2])
    model_sun = multiplica_matriz(T_sun, S_sun)
    mvp_sun = multiplica_matriz(proj, model_sun)
    glUniformMatrix4fv(loc_transform, 1, GL_TRUE, mvp_sun)
    glBindVertexArray(VAO_sun)
    glUniform4f(loc_color, 1.0, 0.85, 0.3, 1.0)
    glDrawElements(GL_TRIANGLE_FAN, len(sun_indices), GL_UNSIGNED_INT, None)

    # --- Desenha os PÁSSAROS ---
    glBindVertexArray(VAO_bird)
    glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)  # cor preta
    for pos in birds_positions:
        T_bird = translacao(pos[0], pos[1], pos[2])
        R_bird = rotacao_z(math.radians(-90.0))
        S_bird = escala(bird_scale[0], bird_scale[1], bird_scale[2])
        model_bird = multiplica_matriz(T_bird, multiplica_matriz(R_bird, S_bird))
        mvp_bird = multiplica_matriz(proj, model_bird)
        glUniformMatrix4fv(loc_transform, 1, GL_TRUE, mvp_bird)
        glDrawElements(GL_TRIANGLES, len(bird_indices), GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)

glfw.terminate()
