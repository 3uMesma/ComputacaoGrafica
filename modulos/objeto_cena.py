import os
from OpenGL.GL import *
import numpy as np
from PIL import Image

"""
Fornece a função 'draw' para desenhar objetos 3D a partir de arquivos .obj 
, texturas associadas e a matriz-modelo.
"""
class GenericObj:
    def __init__(self, obj_path: str, textures_folder: str, material_texture_map: dict, shader_program: int):
        self.shader_program = shader_program
        self.vertices = []
        self.texcoords = []
        self.material_groups = {}
        self.texture_ids = {}
        self.first_default_texture = None

        # Inicializa um cubo padrão se não houver arquivo .obj
        if not obj_path:
            self._init_default_cube()
        else:
            self._load_obj(obj_path)
            self._setup_buffers()
        
        # Carrega texturas se houver mapa de materiais
        if material_texture_map:
            self._load_textures(textures_folder, material_texture_map)
        else:
            self._create_default_texture()
            self.material_groups = {'default': {'start': 0, 'count': len(self.vertices)//3}}
            self.texture_ids = {'default': self.first_default_texture}

    def _init_default_cube(self, size=1.0):
        """Inicializa um cubo padrão como geometria"""
        self.create_cube(size)
        self._setup_buffers()

    def _load_obj(self, path: str):
        """
        Lê arquivo .obj e extrai vértices, texcoords e faces agrupadas por material.
        Gera buffers em listas self.vertices e self.texcoords já triangulados.
        """
        verts, texs = [], []
        faces_by_mat = {}  # material -> lista de tuplas (indices de v, indices de vt)
        current_mat = None

        with open(path, 'r') as f:
            for line in f:
                if line.startswith('#') or not (vals := line.split()):
                    continue  # ignora comentários e linhas vazias
                tag = vals[0]
                if tag == 'v':
                    verts.append(list(map(float, vals[1:4])))
                elif tag == 'vt':
                    texs.append(list(map(float, vals[1:3])))
                elif tag in ('usemtl', 'usemat'):
                    current_mat = vals[1]
                    faces_by_mat.setdefault(current_mat, [])
                elif tag == 'f':
                    vi, ti = [], []
                    for v in vals[1:]:
                        p = v.split('/')
                        vi.append(int(p[0]))
                        ti.append(int(p[1]) if len(p) > 1 and p[1] else 0)
                    faces_by_mat.setdefault(current_mat, []).append((vi, ti))

        # Triangula e popula listas de dados finais para GPU
        offset = 0
        for mat, face_list in faces_by_mat.items():
            self.material_groups[mat] = {'start': offset, 'count': 0}
            for vi, ti in face_list:
                idxs = self._triangulate(vi)
                tex_idxs = self._triangulate(ti)
                for v_idx, t_idx in zip(idxs, tex_idxs):
                    # ajusta índice -1 (OBJ é 1-based)
                    self.vertices.append(verts[v_idx-1])
                    # se não houver UV, usa UV padrão [0,0]
                    self.texcoords.append(texs[t_idx-1] if t_idx > 0 else [0.0, 0.0])
                    self.material_groups[mat]['count'] += 1
                    offset += 1

    def _triangulate(self, arr: list) -> list:
        """
        Converte lista de índices de polígono (>=3) em lista de triângulos.
        Retorna sequência de índices já organizada em triângulos.
        """
        if len(arr) == 3:
            return arr
        circ = arr + [arr[0]]
        out = []
        for i in range(len(circ)-2):
            out.extend(circ[i:i+3])
        return out

    def _setup_buffers(self):
        """
        Cria e configura VAO e VBOs para posições e UVs na GPU.
        Define atributos de vértice conforme shader ativo.
        """
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Buffer de posições
        self.vbo_vertices = glGenBuffers(1)
        verts = np.array(self.vertices, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_STATIC_DRAW)
        pos_loc = glGetAttribLocation(self.shader_program, "position")
        glEnableVertexAttribArray(pos_loc)
        glVertexAttribPointer(pos_loc, 3, GL_FLOAT, GL_FALSE, 0, None)

        # Buffer de coordenadas UV
        self.vbo_texcoords = glGenBuffers(1)
        texs = np.array(self.texcoords, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_texcoords)
        glBufferData(GL_ARRAY_BUFFER, texs.nbytes, texs, GL_STATIC_DRAW)
        uv_loc = glGetAttribLocation(self.shader_program, "texture_coord")
        glEnableVertexAttribArray(uv_loc)
        glVertexAttribPointer(uv_loc, 2, GL_FLOAT, GL_FALSE, 0, None)

        # limpa bindings para evitar efeitos colaterais
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def _load_textures(self, folder: str, mat_map: dict):
        self.texture_ids = {}
        glEnable(GL_TEXTURE_2D)

        # Textura padrão preta
        self._create_default_texture()
        
        for mat_name, tex_file in mat_map.items():
            if not tex_file:
                self.texture_ids[mat_name] = self.first_default_texture
                continue
                
            try:
                # Usa o caminho da pasta que já foi passado
                full_path = os.path.join(folder, tex_file)
                print(f"Carregando textura: {full_path}")  # Debug
                
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"Caminho não existe: {full_path}")
                
                tex_handle = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, tex_handle)
                
                with Image.open(full_path) as img:
                    img = img.convert('RGB')
                    w, h = img.size
                    data = img.tobytes('raw', 'RGB', 0, -1)
                    
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
                    glGenerateMipmap(GL_TEXTURE_2D)
                
                self.texture_ids[mat_name] = tex_handle
                
            except Exception as e:
                print(f"Erro ao carregar textura {tex_file}: {str(e)}")
                self.texture_ids[mat_name] = self.first_default_texture

        glBindTexture(GL_TEXTURE_2D, 0)

    def _create_default_texture(self):
        """Cria uma textura preta padrão 1x1"""
        self.first_default_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.first_default_texture)
        
        # Pixel preto
        black_pixel = np.array([0, 0, 0], dtype=np.uint8)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 1, 1, 0, GL_RGB, GL_UNSIGNED_BYTE, black_pixel)
        
        # Configurações básicas
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glBindTexture(GL_TEXTURE_2D, 0)

    def create_cube(self, size=1.0):
        """Cria a geometria de um cubo centrado na origem"""
        s = size / 2.0
        vertices = [
            # Face 1
            -s, -s,  s,   s, -s,  s,   s,  s,  s,  -s,  s,  s,
            # Face 2
            -s, -s, -s,   s, -s, -s,   s,  s, -s,  -s,  s, -s,
            # Face 3
            -s,  s, -s,   s,  s, -s,   s,  s,  s,  -s,  s,  s,
            # Face 4
            -s, -s, -s,   s, -s, -s,   s, -s,  s,  -s, -s,  s,
            # Face 5
             s, -s, -s,   s,  s, -s,   s,  s,  s,   s, -s,  s,
            # Face 6
            -s, -s, -s,  -s,  s, -s,  -s,  s,  s,  -s, -s,  s
        ]
        
        texcoords = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0] * 6
        
        indices = [
            0, 1, 2,  0, 2, 3,    # Face 1
            4, 5, 6,  4, 6, 7,     # Face 2
            8, 9, 10, 8, 10, 11,   # Face 3
            12,13,14, 12,14,15,    # Face 4
            16,17,18, 16,18,19,    # Face 5
            20,21,22, 20,22,23     # Face 6
        ]
        
        final_vertices = []
        final_texcoords = []
        
        for i in indices:
            final_vertices.extend(vertices[i*3:i*3+3])
            final_texcoords.extend(texcoords[i*2:i*2+2])
        
        self.vertices = final_vertices
        self.texcoords = final_texcoords
        self._setup_buffers()

        # Cria um grupo material padrão para o cubo
        self.material_groups = {'default': {'start': 0, 'count': len(final_vertices)//3}}
        self.texture_ids = {'default': 0}  # Textura padrão

    def draw(self, model_matrix_func, **model_kwargs):
        # 1. Filtra apenas os parâmetros que model_matrix() espera
        base_params = ['angle', 'rx', 'ry', 'rz', 'tx', 'ty', 'tz', 'sx', 'sy', 'sz']
        transform_params = {k: model_kwargs[k] for k in base_params if k in model_kwargs}
        
        # 2. Matriz modelo
        model_mat = model_matrix_func(**transform_params)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_TRUE, model_mat)
        
        # 3. Configurações especiais para objetos emissivos
        if getattr(self, 'emissive', False):
            glUniform1i(glGetUniformLocation(self.shader_program, "isEmissive"), 1)
            glUniform3f(glGetUniformLocation(self.shader_program, "emissiveColor"),
                    *getattr(self, 'emissive_color', [1,1,0]))  # Amarelo padrão
            glUniform1f(glGetUniformLocation(self.shader_program, "emissivePower"),
                    getattr(self, 'emissive_power', 1.0))
        else:
            glUniform1i(glGetUniformLocation(self.shader_program, "isEmissive"), 0)
        
        # 4. Renderização normal
        glBindVertexArray(self.vao)
        for mat_name, grp in self.material_groups.items():
            tex_id = self.texture_ids.get(mat_name, self.first_default_texture)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glDrawArrays(GL_TRIANGLES, grp['start'], grp['count'])
        glBindVertexArray(0)