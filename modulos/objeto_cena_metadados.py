import glm
from modulos.objeto_cena import GenericObj

# Essa classe contém uma instância de Generic
class ObjectMetadata(GenericObj):
    def __init__(self, name, obj_file, textures_map, shader_program, **transform):
        super().__init__(obj_file, f"objetos/{name}/texturas/", textures_map, shader_program)
        self.transform = transform
    def get_pos(self):
        return glm.vec3(self.transform['tx'], self.transform['ty'], self.transform['tz'])
    def seta_pos(self, pos):
        self.transform['tx'] = pos.x
        self.transform['ty'] = pos.y
        self.transform['tz'] = pos.z
    def get_escala(self):
        return glm.vec3(self.transform['sx'], self.transform['sy'], self.transform['sz'])
    def set_escala(self, esc):
        self.transform['sx'] = esc.x
        self.transform['sy'] = esc.y
        self.transform['sz'] = esc.z

def gen_scene_objects(shader_program):
    """
    Gera objetos da cena com metadados.
    shader_program: programa de shader a ser usado para todos os objetos
    """
    # aqui você pode adicionar mais objetos, se quiser
    # ou mesmo criar uma função que gere os objetos a partir de um arquivo de configuração
    return [
            ObjectMetadata(
                name="placa",
                obj_file="objetos/placa/uploads_files_2585599_Road+Sign+-+Pare.obj",
                textures_map={
                    'Holder': 'Holder_color.png',
                    'Road_Sign_-_Pare': 'Road Sign - Pare_color.png'
                },
                shader_program=shader_program,
                # agora passam direto os args:
                angle=0, rx=0, ry=1, rz=0,
                tx=-7, ty=-1, tz=30,
                sx=1.8, sy=1.8, sz=1.8
            ),
            ObjectMetadata(
                name="pessoa_sentada",
                obj_file="objetos/pessoa_sentada/Humano_02Casual_18_30K.obj",
                textures_map={
                    'Humano_02Casual_18': 'Humano_02Casual_18_Diffuse01.jpg'
                },
                shader_program=shader_program,
                angle=0, rx=0, ry=1, rz=0,
                tx=-3.2, ty=1, tz=-6.9,
                sx=0.01, sy=0.01, sz=0.01
            ),
            ObjectMetadata(
                name="onibus",
                obj_file="objetos/onibus/onibus.obj",
                textures_map={
                    'bus':   'bus_BaseColor.png',
                    'base2': 'base2_BaseColor.png',
                    'glass': 'glass_op.png'
                },
                shader_program=shader_program,
                angle=0,  rx=0, ry=1, rz=0,
                tx=-2,    ty=-1, tz=-5,
                sx=1.5,   sy=1.5, sz=1.5
            ),
            ObjectMetadata(
                name='ponto_onibus',
                obj_file='objetos/ponto_onibus/uploads_files_4596518_Bus_Stand.obj',
                textures_map={
                    'dark_wood': 'dark_wood_diff_1k.jpg',
                    'denim_fabric': 'denim_fabric_diff_1k.jpg',
                    'denmin_fabric_02': 'denim_fabric_diff_1k.jpg',
                    'fabric_leather_02': 'fabric_leather_02_diff_1k.jpg',
                    'green_rough_planks': 'green_rough_planks_diff_1k.jpg',
                },
                shader_program=shader_program,
                angle=0, rx=0, ry=1, rz=0,
                tx=-8, ty=-0.9, tz=35,
                sx=1.5, sy=1.5, sz=1.5
            ),
            ObjectMetadata(
                name='pessoa_telefone',
                obj_file='objetos/pessoa_telefone/pessoa_telefone.obj',
                textures_map={
                    'diff': 'diff.jpg',
                    'phone': 'phone.jpg'
                },
                shader_program=shader_program,
                angle=180, rx=0, ry=1, rz=0,
                tx=-7, ty=-1, tz=35,
                sx=0.0013, sy=0.0013, sz=0.0013
            ),
            ObjectMetadata(
                name='mochila',
                obj_file='objetos/mochila/backpack.obj',
                textures_map={
                    'BaseColor': 'backpack_backpack_BaseColor.png',
                    'Normal': 'backpack_backpack_Normal.png',
                    'Metallic': 'backpack_backpack_Metallic.png',
                    'Height': 'backpack_backpack_Height.png'
                },
                shader_program=shader_program,
                angle=180, rx=0, ry=1, rz=0,
                tx=-2.7, ty=1.4, tz=-7.2,
                sx=0.2, sy=0.2, sz=0.2
            ),
            ObjectMetadata(
                name='mala',
                obj_file='objetos/mala/Suitcase_Grey_London.obj',
                textures_map={
                    'BaseColor': '2_MIRORAPPLY_UV_Material.003_BaseColor.png',
                    'Normal': '2_MIRORAPPLY_UV_Material.003_Normal.png',
                    'Metallic': '2_MIRORAPPLY_UV_Material.003_Metallic.png',
                    'Height': '2_MIRORAPPLY_UV_Material.003_Height.png'
                },
                shader_program=shader_program,
                angle=0, rx=0, ry=1, rz=0,
                tx=-2.7, ty=0.91, tz=-6.7,
                sx=1, sy=1, sz=1
            ),
            ObjectMetadata(
                name='rua',
                obj_file='objetos/rua/uploads_files_2748108_radtypesremastered.obj',
                textures_map={
                    'CRN_Material__258': 'ASPHALT3.JPG',
                    'CRN_Material__259': 'bd636add7b95.jpg',
                    'CRN_black_and_white_pavement_25_69_diffuse': 'conrete_pavement_pathway_25_94_diffuse.jpg',
                    'CRN_V_N_Grass_36': 'GrassHR1.jpg',
                    'CRN_sfiubccb_2K_Albedo': 'sfiubccb_2K_Albedo.jpg'
                },
                shader_program=shader_program,
                angle=0, rx=0, ry=1, rz=0,
                tx=0, ty=-1, tz=0,
                sx=0.01, sy=0.01, sz=0.01
            )
        ]