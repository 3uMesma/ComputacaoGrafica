from OpenGL.GL import *
from modulos.programa_shader import usar_shader
import numpy as np
from PIL import Image            # ADICIONADO para carregar texturas cubemap :contentReference[oaicite:0]{index=0}
import glm

# --- Skybox helper: carrega as 6 faces em um cubemap :contentReference[oaicite:1]{index=1}
def load_cubemap(faces):
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, tex_id)
    for i, face in enumerate(faces):
        img = Image.open(face)
        img_data = img.convert("RGB").tobytes()
        glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i,
                     0, GL_RGB, img.width, img.height, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, img_data)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
    return tex_id


def init_skybox(skyboxShader):
    """
    Initialize the skybox by setting up the necessary environment and resources.
    This function is called at the start of the program to ensure that the skybox
    is ready for use.
    """
    usar_shader(skyboxShader)
    faces = [
        "objetos/skybox/miramar_ft.tga",  # POSITIVE_Z (front)
        "objetos/skybox/miramar_bk.tga",  # NEGATIVE_Z (back)
        "objetos/skybox/miramar_up.tga",  # POSITIVE_Y (top)
        "objetos/skybox/miramar_dn.tga",  # NEGATIVE_Y (bottom)
        "objetos/skybox/miramar_rt.tga",  # POSITIVE_X (right)
        "objetos/skybox/miramar_lf.tga",  # NEGATIVE_X (left)
    ]
    cubemapTexture = load_cubemap(faces)                   # carrega cubemap :contentReference[oaicite:3]{index=3}

    # Skybox VAO/VBO (36 vértices de cube) :contentReference[oaicite:4]{index=4}
    skyboxVertices = np.array([
        -1.0,  1.0, -1.0,  -1.0, -1.0, -1.0,   1.0, -1.0, -1.0,
         1.0, -1.0, -1.0,   1.0,  1.0, -1.0,  -1.0,  1.0, -1.0,
        -1.0, -1.0,  1.0,  -1.0, -1.0, -1.0,  -1.0,  1.0, -1.0,
        -1.0,  1.0, -1.0,  -1.0,  1.0,  1.0,  -1.0, -1.0,  1.0,
         1.0, -1.0, -1.0,   1.0, -1.0,  1.0,   1.0,  1.0,  1.0,
         1.0,  1.0,  1.0,   1.0,  1.0, -1.0,   1.0, -1.0, -1.0,
        -1.0, -1.0,  1.0,  -1.0,  1.0,  1.0,   1.0,  1.0,  1.0,
         1.0,  1.0,  1.0,   1.0, -1.0,  1.0,  -1.0, -1.0,  1.0,
        -1.0,  1.0, -1.0,   1.0,  1.0, -1.0,   1.0,  1.0,  1.0,
         1.0,  1.0,  1.0,  -1.0,  1.0,  1.0,  -1.0,  1.0, -1.0,
        -1.0, -1.0, -1.0,  -1.0, -1.0,  1.0,   1.0, -1.0, -1.0,
         1.0, -1.0, -1.0,  -1.0, -1.0,  1.0,   1.0, -1.0,  1.0
    ], dtype=np.float32)
    skyboxVAO = glGenVertexArrays(1)
    skyboxVBO = glGenBuffers(1)
    glBindVertexArray(skyboxVAO)
    glBindBuffer(GL_ARRAY_BUFFER, skyboxVBO)
    glBufferData(GL_ARRAY_BUFFER, skyboxVertices.nbytes, skyboxVertices, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))

    return skyboxVAO, cubemapTexture


def skybox_update(skyboxShader, cameraPos, cameraFront, cameraUp, dummy_projection_matrix, skyboxVAO, cubemapTexture):
    """
    Update the skybox shader with the current camera position.
    This function is called every frame to ensure that the skybox
    is rendered correctly based on the camera's position.
    """
    glDepthFunc(GL_LEQUAL)
    usar_shader(skyboxShader)

    # view sem translação, sem inversões
    raw_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp)
    view_no_trans = glm.mat4(glm.mat3(raw_view))
    view_data = np.array(view_no_trans, dtype=np.float32).T
    loc_view = glGetUniformLocation(skyboxShader, "view")
    glUniformMatrix4fv(loc_view, 1, GL_FALSE, view_data)

    loc_proj = glGetUniformLocation(skyboxShader, "projection")
    proj_data = np.array(dummy_projection_matrix, dtype=np.float32).T
    glUniformMatrix4fv(loc_proj, 1, GL_FALSE, proj_data)

    glBindVertexArray(skyboxVAO)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_CUBE_MAP, cubemapTexture)
    glDrawArrays(GL_TRIANGLES, 0, 36)