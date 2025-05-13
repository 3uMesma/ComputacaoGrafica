from OpenGL.GL import *
from modulos.programa_shader import usar_shader
import numpy as np
from PIL import Image  # para carregar textura

def load_floor_texture(path):
    """
    Carrega uma textura 2D de chão a partir de arquivo PNG.
    Retorna o ID da textura.
    """
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    img = Image.open(path).convert("RGB")
    img_data = img.tobytes()
    width, height = img.size

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, img_data)
    glGenerateMipmap(GL_TEXTURE_2D)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    return tex_id


def init_floor(floorShader):
    """
    Inicializa VAO, VBO e textura do plano de chão em y = -1.
    Deve ser chamado uma vez na inicialização, passando o shader já compilado.
    Retorna (floorVAO, floorTexture).
    """
    usar_shader(floorShader)
    floorTexture = load_floor_texture("objetos/chao/earth-soil-ground-texture-seamless-free-thumb39.jpg")

    # Plano estendido em XZ de -size a +size, e Y fixo
    size = 1000.0
    y = -1.4
    floorVertices = np.array([
        -size, y, -size,  0.0, 0.0,
         size, y, -size,  size, 0.0,
         size, y,  size,  size, size,

         size, y,  size,  size, size,
        -size, y,  size,  0.0, size,
        -size, y, -size,  0.0, 0.0
    ], dtype=np.float32)

    floorVAO = glGenVertexArrays(1)
    floorVBO = glGenBuffers(1)
    glBindVertexArray(floorVAO)
    glBindBuffer(GL_ARRAY_BUFFER, floorVBO)
    glBufferData(GL_ARRAY_BUFFER, floorVertices.nbytes, floorVertices, GL_STATIC_DRAW)

    # position attribute
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
    # texcoord attribute
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))

    glBindVertexArray(0)
    return floorVAO, floorTexture


def update_floor(floorShader, view_matrix, projection_matrix, floorVAO, floorTexture):
    """
    Desenha o plano de chão toda frame.
    Deve ser chamado após a configuração de câmera e clear.
    """
    glDepthFunc(GL_LESS)
    usar_shader(floorShader)

    # Envia matrizes view e projection
    loc_view = glGetUniformLocation(floorShader, "view")
    loc_proj = glGetUniformLocation(floorShader, "projection")
    glUniformMatrix4fv(loc_view, 1, GL_FALSE, np.array(view_matrix, dtype=np.float32).T)
    glUniformMatrix4fv(loc_proj, 1, GL_FALSE, np.array(projection_matrix, dtype=np.float32).T)

    # Liga textura
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, floorTexture)
    glUniform1i(glGetUniformLocation(floorShader, "floorTexture"), 0)

    # Desenha plano
    glBindVertexArray(floorVAO)
    glDrawArrays(GL_TRIANGLES, 0, 6)
    glBindVertexArray(0)
