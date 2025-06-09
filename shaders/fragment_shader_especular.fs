#version 330 core
out vec4 FragColor;

in vec2  out_texture;
in vec3  out_normal;
in vec3  out_fragPos;

// common uniforms
uniform vec3  viewPos;

// each light properties
uniform float ka_farol;
uniform float ks_farol;
uniform float kd_farol;
uniform float constant_farol;
uniform float linear_farol;
uniform float quadratic_farol;

uniform float ka_fone;
uniform float ks_fone;
uniform float kd_fone;
uniform float constant_fone;
uniform float linear_fone;
uniform float quadratic_fone;

uniform float ka_lampada;
uniform float ks_lampada;
uniform float kd_lampada;
uniform float constant_lampada;
uniform float linear_lampada;
uniform float quadratic_lampada;

uniform float ka_celular;
uniform float ks_celular;
uniform float kd_celular;
uniform float constant_celular;
uniform float linear_celular;
uniform float quadratic_celular;

uniform sampler2D samplerTexture;
uniform float mat_kd;
uniform float mat_ks;
uniform float mat_ns;

// ambient light (always)
uniform bool  luzAmbienteLigada;
uniform float luzAmbientePower;
uniform vec3  lightColorFarol;

// emissive
uniform bool  isEmissive;
uniform vec3  emissiveColor;
uniform float emissivePower;

// object type: 0=internal, 1=external, 2=bus
uniform int   objType;
uniform vec3 onibusMinBounds;
uniform vec3 onibusMaxBounds;

// spotlights (external)
uniform bool  luzFarolLigada;
uniform vec3  lightPos1;
uniform vec3  lightDir1;
uniform vec3  lightPos2;
uniform vec3  lightDir2;
uniform float lightCutOff;
uniform float lightOuterCutOff;
uniform float lightPower;

// internal point lights
uniform bool  luzFoneLigada;
uniform vec3  posFone;
uniform vec3  corFone;
uniform bool  luzLampadaLigada;
uniform vec3  posLampada;
uniform vec3  corLampada;

// external point light: celular
uniform bool  luzCelularLigada;
uniform vec3  posCelular;
uniform vec3  corCelular;

// helper: point light using Phong
vec3 calcPointLight(vec3 Lpos, vec3 Lcolor, bool ligado, float ka_curr_fonte, 
                    float ks_curr_fonte, float kd_curr_fonte,
                    float constant_curr_fonte, float linear_curr_fonte,
                    float quadratic_curr_fonte) {
    if (!ligado) return vec3(0.0);
    vec3 N = normalize(out_normal);
    vec3 L = normalize(Lpos - out_fragPos);
    vec3 viewDir = normalize(viewPos - out_fragPos);
    // diffuse shading
    float diff = max(dot(N, L), 0.0);
    // specular shading
    vec3 reflectDir = reflect(-L, N);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), mat_ns);

    // attenuation
    float distance = length(Lpos - out_fragPos);
    float attenuation = 1.0 / (constant_curr_fonte + linear_curr_fonte * distance + quadratic_curr_fonte * (distance * distance));
    // combine results
    vec3 ambient = luzAmbienteLigada ? ka_curr_fonte * Lcolor * vec3(texture(samplerTexture, out_texture)) * mat_kd : vec3(0.0);
    vec3 diffuse = kd_curr_fonte * Lcolor * diff * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    vec3 specular = ks_curr_fonte * Lcolor * spec * vec3(texture(samplerTexture, out_texture)) * mat_ks;

    ambient *= attenuation;
    diffuse *= attenuation;
    specular *= attenuation;
    return ambient + diffuse + specular;
}

// helper: spotlight using Phong
vec3 calcSpotLight(vec3 Lpos, vec3 Lcolor, vec3 Ldir, bool ligado, float ka_curr_fonte, 
                    float ks_curr_fonte, float kd_curr_fonte,
                    float constant_curr_fonte, float linear_curr_fonte,
                    float quadratic_curr_fonte) {
    if (!ligado) return vec3(0.0);
    vec3 N = normalize(out_normal);
    vec3 L = normalize(Lpos - out_fragPos);
    vec3 viewDir = normalize(viewPos - out_fragPos);
    // diffuse shading
    float diff = max(dot(N, L), 0.0);
    // specular shading
    vec3 reflectDir = reflect(-L, N);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), mat_ns);

    // attenuation
    float distance = length(Lpos - out_fragPos);
    float attenuation = 1.0 / (constant_curr_fonte + linear_curr_fonte * distance + quadratic_curr_fonte * (distance * distance));
    
    // spotlight intensity
    float theta = dot(L, normalize(-Ldir));
    float epsilon = lightCutOff - lightOuterCutOff;
    float intensity = clamp((theta - lightOuterCutOff) / epsilon, 0.0, 1.0);
    
    // combine results
    vec3 ambient = luzAmbienteLigada ? ka_curr_fonte * Lcolor * vec3(texture(samplerTexture, out_texture)) * mat_kd : vec3(0.0);
    vec3 diffuse = kd_curr_fonte * Lcolor * diff * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    vec3 specular = ks_curr_fonte * Lcolor * spec * vec3(texture(samplerTexture, out_texture)) * mat_ks;
    ambient *= attenuation * intensity;
    diffuse *= attenuation * intensity;
    specular *= attenuation * intensity;
    return ambient + diffuse + specular;
}

bool isInsideBus(vec3 fragPos) {
    return (fragPos.x >= onibusMinBounds.x && fragPos.x <= onibusMaxBounds.x &&
            fragPos.y >= onibusMinBounds.y && fragPos.y <= onibusMaxBounds.y &&
            fragPos.z >= onibusMinBounds.z && fragPos.z <= onibusMaxBounds.z);
}

void main() {
    // emissive objects
    if (isEmissive) {
        FragColor = vec4(emissiveColor * emissivePower, 1.0);
        return;
    }

    bool insideBus = isInsideBus(out_fragPos);
    vec3 colorAccum = vec3(0.0);

    // --- Luz ambiente (APENAS para objetos externos ou partes externas do ônibus) ---
    vec3 ambiente = vec3(0.0);
    if (luzAmbienteLigada) {
        if (objType == 1) { // Objetos externos sempre recebem
            ambiente = luzAmbientePower * vec3(texture(samplerTexture, out_texture)) * mat_kd;
        } 
        else if (objType == 2 && !insideBus) { // Ônibus só recebe na parte externa
            ambiente = luzAmbientePower * vec3(texture(samplerTexture, out_texture)) * mat_kd;
        }
    }

    // --- Luzes internas (APENAS dentro do ônibus) ---
    vec3 fone_effects = vec3(0.0);
    vec3 lampada_effects = vec3(0.0);

    if (insideBus) {
        fone_effects = calcPointLight(posFone, corFone, luzFoneLigada, 
                                    ka_fone, ks_fone, kd_fone, 
                                    constant_fone, linear_fone, quadratic_fone);

        lampada_effects = calcPointLight(posLampada, corLampada, luzLampadaLigada, 
                                    ka_lampada, ks_lampada, kd_lampada, 
                                    constant_lampada, linear_lampada, quadratic_lampada);
    }

    // --- Luzes externas ---
    vec3 l1_effects = calcSpotLight(lightPos1, lightColorFarol, lightDir1, luzFarolLigada, 
                                  ka_farol, ks_farol, kd_farol, 
                                  constant_farol, linear_farol, quadratic_farol) * lightPower;

    vec3 l2_effects = calcSpotLight(lightPos2, lightColorFarol, lightDir2, luzFarolLigada, 
                                  ka_farol, ks_farol, kd_farol, 
                                  constant_farol, linear_farol, quadratic_farol) * lightPower;
    
    vec3 celular_effects = calcPointLight(posCelular, corCelular, luzCelularLigada, 
                                        ka_celular, ks_celular, kd_celular, 
                                        constant_celular, linear_celular, quadratic_celular);

    // --- Combinação final ---
    if (objType == 0) { // Objetos internos
        colorAccum = fone_effects + lampada_effects;
    } 
    else if (objType == 1) { // Objetos externos
        colorAccum = ambiente + l1_effects + l2_effects + celular_effects;
    } 
    else { // Ônibus
        colorAccum = fone_effects + lampada_effects;
        if (!insideBus) {
            colorAccum += ambiente + l1_effects + l2_effects + celular_effects;
        }
    }

    FragColor = vec4(colorAccum, 1.0);
}