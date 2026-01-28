#version 460 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in vec3 aNormal; // Recebe a normal do Python

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

out vec2 vTexCoord;
out vec3 vNormal;
out vec3 vFragPos;

void main(){
    vFragPos = vec3(model * vec4(aPos, 1.0));
    
    // Calcula Normal corrigindo distorções de escala do modelo
    vNormal = mat3(transpose(inverse(model))) * aNormal;
    
    vTexCoord = aTexCoord;
    gl_Position = projection * view * vec4(vFragPos, 1.0);
}