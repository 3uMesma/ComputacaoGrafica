#version 330 core
out vec4 FragColor;

in vec2 out_texture;
in vec3 out_normal;
in vec3 out_fragPos;

// Uniforms para iluminação
uniform vec3 lightPos;    // Used in else clause
uniform vec3 lightPos1;   // define coordenadas de posicao da luz #1
uniform vec3 lightPos2;   // define coordenadas de posicao da luz #2
uniform vec3 lightColor;
uniform vec3 lightDir1;    // Direção do farol
uniform vec3 lightDir2;    // Direção do farol
uniform float lightCutOff; // Ângulo de corte (cos do ângulo)
uniform float lightPower;
uniform vec3 viewPos;

uniform float luzAmbientePower;
uniform bool luzAmbienteLigada;
uniform bool luzFarolLigada;

// Material
uniform float ka;
uniform float kd;
uniform float ks;
uniform float ns;
uniform sampler2D samplerTexture;

// Emissive
uniform bool isEmissive;
uniform vec3 emissiveColor;
uniform float emissivePower;

void main() {
    if (isEmissive) {
        FragColor = vec4(emissiveColor * emissivePower, 1.0);
        return;
    }
    
    vec3 norm = normalize(out_normal);

    // para cada farol
    vec3 lightToFrag1 = normalize(lightPos1 - out_fragPos);
    vec3 lightDirNorm1 = normalize(lightDir1);
    vec3 lightToFrag2 = normalize(lightPos2 - out_fragPos);
    vec3 lightDirNorm2 = normalize(lightDir2);
    
    // Cálculo do ângulo entre a direção do farol e a direção para o fragmento
    float theta1 = dot(lightToFrag1, -lightDirNorm1);
    float theta2 = dot(lightToFrag2, -lightDirNorm2);
    
    // Spotlight effect - só ilumina se estiver dentro do cone (farol 1)
    if(theta1 > lightCutOff) {
        // Suavização das bordas do cone
        float epsilon = lightCutOff * 0.9 - lightCutOff;
        float intensity = clamp((theta1 - lightCutOff) / epsilon, 0.0, 1.0);
        
        // Diffuse 
        float diff = max(dot(norm, lightToFrag1), 0.0);
        vec3 diffuse = kd * diff * lightColor * lightPower * intensity;
        
        // Specular
        vec3 viewDir = normalize(viewPos - out_fragPos);
        vec3 reflectDir = reflect(-lightToFrag1, norm);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), ns);
        vec3 specular = ks * spec * lightColor * lightPower * intensity;
        
        // Ambient reduzido quando dentro do cone
        vec3 ambient = luzFarolLigada
                    ? ka * lightColor * lightPower * 0.1
                    : (luzAmbienteLigada
                        ? ka * lightColor * luzAmbientePower
                        : vec3(0.0));  
          
        // Resultado final
        vec4 texColor = texture(samplerTexture, out_texture);
        vec3 result = (ambient + diffuse + specular) * texColor.rgb;
        FragColor = vec4(result, texColor.a);
    } else if (theta2 > lightCutOff) {
        // Suavização das bordas do cone
        float epsilon = lightCutOff * 0.9 - lightCutOff;
        float intensity = clamp((theta2 - lightCutOff) / epsilon, 0.0, 1.0);
        
        // Diffuse 
        float diff = max(dot(norm, lightToFrag2), 0.0);
        vec3 diffuse = kd * diff * lightColor * lightPower * intensity;
        
        // Specular
        vec3 viewDir = normalize(viewPos - out_fragPos);
        vec3 reflectDir = reflect(-lightToFrag2, norm);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), ns);
        vec3 specular = ks * spec * lightColor * lightPower * intensity;
        
        // Ambient reduzido quando dentro do cone
        vec3 ambient = luzFarolLigada
                    ? ka * lightColor * lightPower * 0.1
                    : (luzAmbienteLigada
                        ? ka * lightColor * luzAmbientePower
                        : vec3(0.0));  
          
        // Resultado final
        vec4 texColor = texture(samplerTexture, out_texture);
        vec3 result = (ambient + diffuse + specular) * texColor.rgb;
        FragColor = vec4(result, texColor.a);
    } else {
        // Fora do cone - apenas iluminação ambiente mínima
        vec3 norm = normalize(out_normal);
        vec4 texColor = texture(samplerTexture, out_texture);
        
        // Iluminação ambiente
        vec3 ambient = luzAmbienteLigada ? ka * lightColor * luzAmbientePower : vec3(0.0);
        
        // Iluminação difusa
        vec3 lightDir = normalize(lightPos - out_fragPos);
        float diff = max(dot(norm, lightDir), 0.0);
        vec3 diffuse = kd * diff * lightColor;
        
        // Iluminação especular
        vec3 viewDir = normalize(viewPos - out_fragPos);
        vec3 reflectDir = reflect(-lightDir, norm);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), ns);
        vec3 specular = ks * spec * lightColor;
        
        // Combina todos os componentes
        vec3 result = (ambient + diffuse + specular) * texColor.rgb;
        FragColor = vec4(result, texColor.a);
    }
}