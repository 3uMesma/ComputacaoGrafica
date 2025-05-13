#version 330 core
in vec2 TexCoords;
out vec4 FragColor;
uniform sampler2D tex_diffuse;
void main() {
    FragColor = texture(tex_diffuse, TexCoords);
}