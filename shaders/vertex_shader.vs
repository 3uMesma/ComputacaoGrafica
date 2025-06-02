#version 330 core

// Entradas
layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texture_coord;
layout(location = 2) in vec3 normal;  // Adicione esta linha para as normais

// Saídas
out vec2 out_texture;
out vec3 out_normal;     // Adicione para iluminação
out vec3 out_fragPos;    // Adicione para iluminação

// Uniformes
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    // Posição do vértice transformada
    gl_Position = projection * view * model * vec4(position, 1.0);
    
    // Coordenadas de textura
    out_texture = texture_coord;
    
    // Normal transformada (considerando a matriz de modelo)
    out_normal = mat3(transpose(inverse(model))) * normal;
    
    // Posição do fragmento no espaço do mundo
    out_fragPos = vec3(model * vec4(position, 1.0));
}