#version 330 core

in vec2 out_texture;
out vec4 FragColor;

uniform sampler2D texture1;  // Nome deve corresponder ao usado no código

void main() {
    FragColor = texture(texture1, out_texture);
}