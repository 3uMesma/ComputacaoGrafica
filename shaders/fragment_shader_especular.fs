#version 330 core
out vec4 FragColor;

in vec2  out_texture;
in vec3  out_normal;
in vec3  out_fragPos;

uniform vec3  viewPos;

uniform float ka_farol, ks_farol, kd_farol, constant_farol, linear_farol, quadratic_farol;
uniform float ka_fone, ks_fone, kd_fone, constant_fone, linear_fone, quadratic_fone;
uniform float ka_lampada, ks_lampada, kd_lampada, constant_lampada, linear_lampada, quadratic_lampada;
uniform float ka_celular, ks_celular, kd_celular, constant_celular, linear_celular, quadratic_celular;

uniform sampler2D samplerTexture;
uniform float mat_kd, mat_ks, mat_ns;

uniform bool  luzAmbienteLigada;
uniform float luzAmbientePower;
uniform vec3  lightColorFarol;

uniform bool  isEmissive;
uniform vec3  emissiveColor;
uniform float emissivePower;

uniform int   objType;
uniform vec3  onibusMinBounds;
uniform vec3  onibusMaxBounds;

uniform bool  luzFarolLigada;
uniform vec3  lightPos1, lightDir1, lightPos2, lightDir2;
uniform float lightCutOff, lightOuterCutOff, lightPower;

uniform bool  luzFoneLigada;
uniform vec3  posFone;
uniform vec3  corFone;
uniform float aroFoneRaio;
uniform float aroFoneEspessura;
uniform float aroFoneIntensidade;

uniform bool  luzLampadaLigada;
uniform vec3  posLampada;
uniform vec3  corLampada;

uniform bool  luzCelularLigada;
uniform vec3  posCelular;
uniform vec3  corCelular;

vec3 calcPointLight(vec3 Lpos, vec3 Lcolor, bool ligado, float ka, float ks, float kd,
                    float constant, float linear, float quadratic) {
    if (!ligado) return vec3(0.0);
    vec3 N = normalize(out_normal);
    vec3 L = normalize(Lpos - out_fragPos);
    vec3 viewDir = normalize(viewPos - out_fragPos);
    float diff = max(dot(N, L), 0.0);
    vec3 reflectDir = reflect(-L, N);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), mat_ns);
    float distance = length(Lpos - out_fragPos);
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));
    vec3 ambient = ka * Lcolor * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    vec3 diffuse = kd * Lcolor * diff * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    vec3 specular = ks * Lcolor * spec * vec3(texture(samplerTexture, out_texture)) * mat_ks;
    return (ambient + diffuse + specular) * attenuation;
}

vec3 calcSpotLight(vec3 Lpos, vec3 Lcolor, vec3 Ldir, bool ligado, float ka, float ks, float kd,
                   float constant, float linear, float quadratic) {
    if (!ligado) return vec3(0.0);
    vec3 N = normalize(out_normal);
    vec3 L = normalize(Lpos - out_fragPos);
    vec3 viewDir = normalize(viewPos - out_fragPos);
    float diff = max(dot(N, L), 0.0);
    vec3 reflectDir = reflect(-L, N);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), mat_ns);
    float distance = length(Lpos - out_fragPos);
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));
    float theta = dot(L, normalize(-Ldir));
    float epsilon = lightCutOff - lightOuterCutOff;
    float intensity = clamp((theta - lightOuterCutOff) / epsilon, 0.0, 1.0);
    vec3 ambient = ka * Lcolor * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    vec3 diffuse = kd * Lcolor * diff * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    vec3 specular = ks * Lcolor * spec * vec3(texture(samplerTexture, out_texture)) * mat_ks;
    return (ambient + diffuse + specular) * attenuation * intensity;
}

bool isInsideBus(vec3 fragPos) {
    // Parte retangular (corpo principal)
    bool inMainBody = (fragPos.x >= onibusMinBounds.x && fragPos.x <= onibusMaxBounds.x &&
                       fragPos.y >= onibusMinBounds.y && fragPos.y <= onibusMinBounds.y + 3.2 &&
                       fragPos.z >= onibusMinBounds.z && fragPos.z <= onibusMaxBounds.z);
    
    if (inMainBody) return true;
    
    float halfWidth = (onibusMaxBounds.x - onibusMinBounds.x) * 0.5;
    float centerX = onibusMinBounds.x + halfWidth;
    float radius = halfWidth;
    float distFromCenterX = abs(fragPos.x - centerX);
    
    if (distFromCenterX > radius) return false;
    
    float yBase = onibusMinBounds.y + 4.5;
    float arcHeight = 0.05;
    
    float relativeY = (fragPos.y - yBase) / arcHeight;
    float circleEq = (distFromCenterX * distFromCenterX) / (radius * radius) + relativeY * relativeY;
    
    return (fragPos.z >= onibusMinBounds.z && fragPos.z <= onibusMaxBounds.z &&
            fragPos.y >= yBase && fragPos.y <= onibusMaxBounds.y &&
            circleEq <= 1.0);
}

void main() {
    if (isEmissive) {
        FragColor = vec4(emissiveColor * emissivePower, 1.0);
        return;
    }

    bool insideBus = isInsideBus(out_fragPos);
    vec3 colorAccum = vec3(0.0);

    // --- Luz ambiente  ---
    vec3 ambiente = vec3(0.0);
    if (luzAmbienteLigada && (objType == 1 || !insideBus)) {
        ambiente = luzAmbientePower * vec3(texture(samplerTexture, out_texture)) * mat_kd;
    }

    // --- Luzes internas (só aplicam dentro do ônibus) ---
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

    // --- Luzes externas (faróis e celular) ---
    vec3 l1_effects = calcSpotLight(lightPos1, lightColorFarol, lightDir1, luzFarolLigada,
                                  ka_farol, ks_farol, kd_farol,
                                  constant_farol, linear_farol, quadratic_farol) * lightPower;

    vec3 l2_effects = calcSpotLight(lightPos2, lightColorFarol, lightDir2, luzFarolLigada,
                                  ka_farol, ks_farol, kd_farol,
                                  constant_farol, linear_farol, quadratic_farol) * lightPower;

    vec3 celular_effects = calcPointLight(posCelular, corCelular, luzCelularLigada,
                                        ka_celular, ks_celular, kd_celular,
                                        constant_celular, linear_celular, quadratic_celular);

    if (luzFoneLigada && (objType == 0 || (objType == 2 && insideBus))) {
        float distXZ = distance(out_fragPos.xz, posFone.xz);
        float centerRadius = 30.0;
        float ringWidth = 10.0;
        float edgeSmooth = 0.01;

        float outer = smoothstep(centerRadius + ringWidth, centerRadius + ringWidth - edgeSmooth, distXZ);
        float inner = 1.0 - smoothstep(centerRadius - ringWidth + edgeSmooth, centerRadius - ringWidth, distXZ);
        float glow = outer * inner;

        vec3 aroColor = corFone * glow * aroFoneIntensidade;
        colorAccum += aroColor;
    }

    // --- Combinação final ---
    if (objType == 0) {
        // Objetos internos (só luzes do fone/lâmpada)
        colorAccum = fone_effects + lampada_effects;
    } else if (objType == 1) {
        // Cenário externo (luz ambiente + faróis + celular)
        colorAccum = ambiente + l1_effects + l2_effects + celular_effects;
    } else {
        // Ônibus (luzes internas + externas se estiver fora)
        colorAccum = fone_effects + lampada_effects;
        if (!insideBus) {
            colorAccum += ambiente + l1_effects + l2_effects + celular_effects;
        }
    }

    FragColor = vec4(colorAccum, 1.0);
}
