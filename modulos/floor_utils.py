def setup_floor():
    # vertices do chão (x, y, z, u, v)
    floor_program = criar_shader("shaders/floor_shader.vs", "shaders/floor_shader.fs")
    floor_vertices = np.array([
        # pos               texcoords
        -1000.0, -1.5, -1000.0,   0.0, 0.0,
        1000.0, -1.5, -1000.0,   5.0, 0.0,  # u=5 para repetir 5 vezes
        1000.0, -1.5,  1000.0,   5.0, 5.0,
        -1000.0, -1.5,  1000.0,   0.0, 5.0,
    ], dtype=np.float32)

    floor_indices = np.array([
        0, 1, 2,
        2, 3, 0
    ], dtype=np.uint32)

    # criar VAO/VBO/EBO
    floor_VAO = glGenVertexArrays(1)
    floor_VBO = glGenBuffers(1)
    floor_EBO = glGenBuffers(1)

    glBindVertexArray(floor_VAO)
    glBindBuffer(GL_ARRAY_BUFFER, floor_VBO)
    glBufferData(GL_ARRAY_BUFFER, floor_vertices.nbytes, floor_vertices, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, floor_EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, floor_indices.nbytes, floor_indices, GL_STATIC_DRAW)

    # posição
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
    # texcoords
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))

    glBindVertexArray(0)

    return floor_program, floor_VAO