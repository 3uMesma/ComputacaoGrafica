import glfw
from OpenGL.GL import *
import numpy as np
import glm
import math
from numpy import random
from PIL import Image
import sys
import os

sys.path.append(os.path.abspath('..'))
from shader_s import Shader

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

altura = 700
largura = 700

window = glfw.create_window(largura, altura, "Programa", None, None)

if (window == None):
    print("Failed to create GLFW window")
    glfwTerminate()
    
glfw.make_context_current(window)

ourShader = Shader("../vertex_shader.vs", "../fragment_shader.fs")
ourShader.use()

program = ourShader.getProgram()

glEnable(GL_TEXTURE_2D)
glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
glEnable( GL_BLEND )
glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
glEnable(GL_LINE_SMOOTH)


global vertices_list
vertices_list = []    
global textures_coord_list
textures_coord_list = []


def load_model_from_file(filename):
    """Loads a Wavefront OBJ file. """
    objects = {}
    vertices = []
    texture_coords = []
    faces = []

    material = None

    # abre o arquivo obj para leitura
    for line in open(filename, "r"): ## para cada linha do arquivo .obj
        if line.startswith('#'): continue ## ignora comentarios
        values = line.split() # quebra a linha por espaço
        if not values: continue

        ### recuperando vertices
        if values[0] == 'v':
            vertices.append(values[1:4])

        ### recuperando coordenadas de textura
        elif values[0] == 'vt':
            texture_coords.append(values[1:3])

        ### recuperando faces 
        elif values[0] in ('usemtl', 'usemat'):
            material = values[1]
        elif values[0] == 'f':
            face = []
            face_texture = []
            for v in values[1:]:
                w = v.split('/')
                face.append(int(w[0]))
                if len(w) >= 2 and len(w[1]) > 0:
                    face_texture.append(int(w[1]))
                else:
                    face_texture.append(0)

            faces.append((face, face_texture, material))

    model = {}
    model['vertices'] = vertices
    model['texture'] = texture_coords
    model['faces'] = faces

    return model


def load_texture_from_file(texture_id, img_textura):
    print(f"Carregando textura: {img_textura}")
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    img = Image.open(img_textura)
    
    # Converte para RGB se necessário
    if img.mode in ('L', 'LA', 'P'):
        img = img.convert('RGB')
    
    img_width = img.size[0]
    img_height = img.size[1]
    
    # Usa o formato correto baseado no modo da imagem
    if img.mode == 'RGB':
        format = GL_RGB
    elif img.mode == 'RGBA':
        format = GL_RGBA
    else:
        format = GL_RGB  # Fallback
        
    image_data = img.tobytes("raw", img.mode, 0, -1)
    glTexImage2D(GL_TEXTURE_2D, 0, format, img_width, img_height, 0, format, GL_UNSIGNED_BYTE, image_data)



'''
É possível encontrar, na Internet, modelos .obj cujas faces não sejam triângulos. Nesses casos, precisamos gerar triângulos a partir dos vértices da face.
A função abaixo retorna a sequência de vértices que permite isso. Créditos: Hélio Nogueira Cardoso e Danielle Modesti (SCC0650 - 2024/2).
'''
def circular_sliding_window_of_three(arr):
    if len(arr) == 3:
        return arr
    circular_arr = arr + [arr[0]]
    result = []
    for i in range(len(circular_arr) - 2):
        result.extend(circular_arr[i:i+3])
    return result
    
global numberTextures
numberTextures = 0

def load_obj_and_texture(objFile, textures_path):
    modelo = load_model_from_file(objFile)
    
    global vertices_list, textures_coord_list, numberTextures
    vertices_list = []
    textures_coord_list = []
    numberTextures = 0
    
    # Mapeamento de materiais para texturas (baseado no seu MTL)
    material_to_texture = {
        'CRN_Material__258': 'ASPHALT3.JPG',
        'CRN_Material__259': 'bd636add7b95.jpg',
        'CRN_black_and_white_pavement_25_69_diffuse': 'conrete_pavement_pathway_25_94_diffuse.jpg',
        'CRN_V_N_Grass_36': 'GRASSHR1.jpg',
        'CRN_sfiubccb_2K_Albedo': 'sfiubccb_2K_Albedo.jpg',
        # Adicione outros mapeamentos conforme necessário
    }
    
    # Organiza faces por material
    material_data = {}
    for face in modelo['faces']:
        material = face[2]
        if material not in material_data:
            material_data[material] = {'verts': [], 'tex_coords': []}
        
        verts = circular_sliding_window_of_three(face[0])
        tex_coords = circular_sliding_window_of_three(face[1])
        
        for v_idx, t_idx in zip(verts, tex_coords):
            material_data[material]['verts'].append(modelo['vertices'][v_idx-1])
            material_data[material]['tex_coords'].append(modelo['texture'][t_idx-1] if t_idx > 0 else [0.0, 0.0])

    # Concatena vértices e prepara material_groups
    material_groups = {}
    start = 0
    for material, data in material_data.items():
        count = len(data['verts'])
        material_groups[material] = {
            'start': start,
            'count': count,
            'texture': material_to_texture.get(material, 'ASPHALT3.JPG')  # Default
        }
        vertices_list.extend(data['verts'])
        textures_coord_list.extend(data['tex_coords'])
        start += count
    
    # Carrega texturas
    texture_ids = {}
    loaded_textures = set()  # Para evitar carregar a mesma textura múltiplas vezes
    
    for material, group in material_groups.items():
        texture_file = group['texture']
        if texture_file not in loaded_textures:
            try:
                load_texture_from_file(numberTextures, textures_path + texture_file)
                texture_ids[texture_file] = numberTextures
                loaded_textures.add(texture_file)
                numberTextures += 1
            except Exception as e:
                print(f"Erro ao carregar textura {texture_file}: {str(e)}")
                texture_ids[texture_file] = 0
    
    return material_groups, texture_ids

# carrega caixa (modelo e texturas)
material_groups, texture_ids = load_obj_and_texture(
    'uploads_files_2748108_radtypesremastered.obj',
    'texturas/'
)


def desenha_rua(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z, material_groups, texture_ids):
    mat_model = model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
    
    # Desenha cada parte com sua textura apropriada
    for material, group in material_groups.items():
        texture_file = group['texture']
        if texture_file in texture_ids:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, texture_ids[texture_file])
            glUniform1i(glGetUniformLocation(program, "texture_diffuse1"), 0)
        
        glDrawArrays(GL_TRIANGLES, group['start'], group['count'])


#verticeInicial_spider_man, quantosVertices_spider_man = load_obj_and_texture('objetos/spiderman/spiderman.obj', ['objetos/spiderman/spiderman.png'])

buffer_VBO = glGenBuffers(2)

# Configuração dos buffers (apenas uma vez!)
vertices = np.array(vertices_list, dtype=np.float32)
textures = np.array(textures_coord_list, dtype=np.float32)

# Gera e configura os buffers
buffer_VBO = glGenBuffers(2)

# Buffer de vértices
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[0])
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# Buffer de texturas
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[1])
glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(1)

# Verifique se os atributos estão corretamente vinculados
print("\nAtributos do shader:")
print(f"position: {glGetAttribLocation(program, 'position')}")
print(f"texture_coord: {glGetAttribLocation(program, 'texture_coord')}")

# Verifique as texturas carregadas
print("\nTexturas carregadas:")
for name, tex_id in texture_ids.items():
    print(f"{name}: ID {tex_id}")

#cameraPos   = glm.vec3(0.0,  0.0,  1.0);
#cameraFront = glm.vec3(0.0,  0.0, -1.0);
#cameraUp    = glm.vec3(0.0,  1.0,  0.0);

# camera
cameraPos   = glm.vec3(0.0, 0.0, 3.0)
cameraFront = glm.vec3(0.0, 0.0, -1.0)
cameraUp    = glm.vec3(0.0, 1.0, 0.0)

firstMouse = True
yaw   = -90.0	# yaw is initialized to -90.0 degrees since a yaw of 0.0 results in a direction vector pointing to the right so we initially rotate a bit to the left.
pitch =  0.0
lastX =  largura / 2.0
lastY =  altura / 2.0
fov   =  45.0

# timing
deltaTime = 0.0	# time between current frame and last frame
lastFrame = 0.0


firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  largura/2
lastY =  altura/2


def key_event(window,key,scancode,action,mods):
    global cameraPos, cameraFront, cameraUp, polygonal_mode

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    
    cameraSpeed = 50 * deltaTime
    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += cameraSpeed * cameraFront
    
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= cameraSpeed * cameraFront
    
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
        
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed

    if key == glfw.KEY_P and action == glfw.PRESS:
        polygonal_mode = not polygonal_mode
        

def framebuffer_size_callback(window, largura, altura):

    # make sure the viewport matches the new window dimensions note that width and 
    # height will be significantly larger than specified on retina displays.
    glViewport(0, 0, largura, altura)

# glfw: whenever the mouse moves, this callback is called
# -------------------------------------------------------
def mouse_callback(window, xpos, ypos):
    global cameraFront, lastX, lastY, firstMouse, yaw, pitch
   
    if (firstMouse):

        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos # reversed since y-coordinates go from bottom to top
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1 # change this value to your liking
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # make sure that when pitch is out of bounds, screen doesn't get flipped
    if (pitch > 89.0):
        pitch = 89.0
    if (pitch < -89.0):
        pitch = -89.0

    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)

# glfw: whenever the mouse scroll wheel scrolls, this callback is called
# ----------------------------------------------------------------------
def scroll_callback(window, xoffset, yoffset):
    global fov

    fov -= yoffset
    if (fov < 1.0):
        fov = 1.0
    if (fov > 45.0):
        fov = 45.0
    
glfw.set_key_callback(window,key_event)
glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
glfw.set_cursor_pos_callback(window, mouse_callback)
glfw.set_scroll_callback(window, scroll_callback)

# tell GLFW to capture our mouse
glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

def model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    
    angle = math.radians(angle)
    
    matrix_transform = glm.mat4(1.0) # instanciando uma matriz identidade
       
    # aplicando translacao (terceira operação a ser executada)
    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))    
    
    # aplicando rotacao (segunda operação a ser executada)
    if angle!=0:
        matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(r_x, r_y, r_z))
    
    # aplicando escala (primeira operação a ser executada)
    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))
    
    matrix_transform = np.array(matrix_transform)
    
    return matrix_transform

def view():
    global cameraPos, cameraFront, cameraUp
    mat_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
    mat_view = np.array(mat_view)
    return mat_view

def projection():
    global altura, largura
    # perspective parameters: fovy, aspect, near, far
    mat_projection = glm.perspective(glm.radians(fov), largura/altura, 0.1, 100.0)

    
    mat_projection = np.array(mat_projection)    
    return mat_projection

glfw.show_window(window)

glEnable(GL_DEPTH_TEST) ### importante para 3D
polygonal_mode = False 

# Após compilar o programa do shader:
baseColor_loc = glGetUniformLocation(program, "AsphaltTexture")
normal_loc = glGetUniformLocation(program, "AsphaltCloseTexture")
metallic_loc = glGetUniformLocation(program, "CementTexture")

if baseColor_loc == -1 or normal_loc == -1 or metallic_loc == -1:
    print("ERRO: Uniforms do shader não encontrados! Verifique os nomes no shader")
    
while not glfw.window_should_close(window):

    currentFrame = glfw.get_time()
    deltaTime = currentFrame - lastFrame
    lastFrame = currentFrame

    glfw.poll_events() 
       
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glClearColor(1.0, 1.0, 1.0, 1.0)
    
    if polygonal_mode:
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

    
    desenha_rua(0.0, 0, 1, 0, 0, -10, -10, 0.01, 0.01, 0.01, material_groups, texture_ids)
    
    mat_view = view()
    loc_view = glGetUniformLocation(program, "view")
    glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

    mat_projection = projection()
    loc_projection = glGetUniformLocation(program, "projection")
    glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    
    
    glfw.swap_buffers(window)

glfw.terminate()