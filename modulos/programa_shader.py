from OpenGL.GL import *

# Carrega o código fonte de um arquivo
# caminho: caminho do arquivo a ser lido
# retorna: string com o conteúdo do arquivo
# Lança IOError em falha de leitura

def carregar_codigo(caminho: str) -> str:
    with open(caminho, 'r') as arquivo:
        return arquivo.read()

# Compila um shader de dado tipo (GL_VERTEX_SHADER ou GL_FRAGMENT_SHADER)
# codigo: string com o código fonte do shader
# tipo: GL_VERTEX_SHADER ou GL_FRAGMENT_SHADER
# retorna: id do shader compilado

def compilar_shader(codigo: str, tipo: int) -> int:
    id_shader = glCreateShader(tipo)
    glShaderSource(id_shader, codigo)
    glCompileShader(id_shader)
    verificar_erros(id_shader, "VERTEX" if tipo == GL_VERTEX_SHADER else "FRAGMENT")
    return id_shader

# Cria e linka um programa de shaders dado vertex e fragment shaders
# id_vertice: id do shader de vértice
# id_fragmento: id do shader de fragmento
# retorna: id do programa linked

def criar_programa(id_vertice: int, id_fragmento: int) -> int:
    programa = glCreateProgram()
    glAttachShader(programa, id_vertice)
    glAttachShader(programa, id_fragmento)
    glLinkProgram(programa)
    verificar_erros(programa, "PROGRAM")
    # Após link, podemos deletar os shaders individuais
    glDeleteShader(id_vertice)
    glDeleteShader(id_fragmento)
    return programa

# Verifica erros de compilação (shaders) ou linkagem (programa)
# id_objeto : id do shader ou programa
# tipo: "VERTEX", "FRAGMENT ou "PROGRAM"

def verificar_erros(id_objeto: int, tipo: str) -> None:
    if tipo in ("VERTEX", "FRAGMENT"):
        sucesso = glGetShaderiv(id_objeto, GL_COMPILE_STATUS)
        if not sucesso:
            log = glGetShaderInfoLog(id_objeto).decode()
            print(f"ERRO::COMPILACAO_SHADER do tipo: {tipo}\n{log}\n-- ---------------------------------------------- --")
    else:
        sucesso = glGetProgramiv(id_objeto, GL_LINK_STATUS)
        if not sucesso:
            log = glGetProgramInfoLog(id_objeto).decode()
            print(f"ERRO::LINKAGEM_PROGRAMA do tipo: {tipo}\n{log}\n-- ---------------------------------------------- --")

# Carrega, compila e linka shaders de vértice e fragmento
# caminho_vertice: caminho do arquivo de shader de vértice
# caminho_fragmento: caminho do arquivo de shader de fragmento
# retorna: id do programa de shader pronto pra uso


def criar_shader(caminho_vertice: str, caminho_fragmento: str) -> int:
    try:
        codigo_vert = carregar_codigo(caminho_vertice)
        codigo_frag = carregar_codigo(caminho_fragmento)

        id_vert = compilar_shader(codigo_vert, GL_VERTEX_SHADER)
        id_frag = compilar_shader(codigo_frag, GL_FRAGMENT_SHADER)

        return criar_programa(id_vert, id_frag)

    except IOError:
        print("ERRO::SOMBREADOR::FALHA_AO_LER_ARQUIVO")
        return 0

# Ativa o programa de shader para uso
# programa: id do programa obtido por criar_shader

def usar_shader(programa: int) -> None:
    glUseProgram(programa)
