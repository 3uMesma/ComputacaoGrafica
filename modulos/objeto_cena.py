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
        """
        obj_path: caminho para o arquivo .obj
        textures_folder: pasta base onde estão as texturas
        material_texture_map: mapeia nome do material -> arquivo de textura
        shader_program: ID do programa de shader já compilado e ativo
        """
        self.shader_program = shader_program
        self.vertices = []          # lista de posições X,Y,Z
        self.texcoords = []         # lista de coordenadas UV
        self.material_groups = {}   # grupos de faces por material
        self.texture_ids = {}       # map material -> ID de textura OpenGL

        # 1. Carrega geometria do .obj
        self._load_obj(obj_path)
        # 2. Prepara buffers de vértices e UVs na GPU
        self._setup_buffers()
        # 3. Carrega e configura texturas para cada material
        self._load_textures(textures_folder, material_texture_map)

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
        """
        Carrega texturas dos arquivos e gera texturas OpenGL.
        Usa uma textura preta padrão para materiais sem imagem.
        """
        self.texture_ids = {}
        glEnable(GL_TEXTURE_2D)

        self.first_default_texture = None
        for mat, tex_file in mat_map.items():
            path = os.path.join(folder, tex_file)
            print(f"Carregando textura '{path}' para material '{mat}'")
            tex_handle = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_handle)
            img = Image.open(path)
            img = img.convert('RGB')
            w, h = img.size
            fmt = GL_RGB
            data = img.tobytes('raw', img.mode, 0, -1)
            # parâmetros de wrap/filter
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt, GL_UNSIGNED_BYTE, data)

            self.texture_ids[mat] = tex_handle
            if self.first_default_texture is None:
                self.first_default_texture = tex_handle

        # limpa bind para não afetar chamadas seguintes
        glBindTexture(GL_TEXTURE_2D, 0)

    def draw(self, model_matrix_func, **model_kwargs):
        """
        Renderiza o objeto: aplica a matriz-modelo, faz bind das texturas e desenha cada grupo.
        model_matrix_func: função que retorna matriz-modelo (4x4)
        model_kwargs: parâmetros para model_matrix_func
        """
        # envia matriz-modelo para o shader
        loc_model = glGetUniformLocation(self.shader_program, "model")
        model_mat = model_matrix_func(**model_kwargs)
        glUniformMatrix4fv(loc_model, 1, GL_TRUE, model_mat)

        # bind do VAO para restaurar estados de VBO/atributos
        glBindVertexArray(self.vao)

        for mat_name, grp in self.material_groups.items():
            # seleciona textura do material ou fallback
            tex_id = self.texture_ids.get(mat_name, self.first_default_texture)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            uni = glGetUniformLocation(self.shader_program, "texture_diffuse1")
            glUniform1i(uni, 0)
            glDrawArrays(GL_TRIANGLES, grp['start'], grp['count'])

        # limpa estado após desenhar
        # limpa isso
        glBindVertexArray(0)
        glBindTexture(GL_TEXTURE_2D, 0)
