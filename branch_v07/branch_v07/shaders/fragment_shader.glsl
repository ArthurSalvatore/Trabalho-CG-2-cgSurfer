#version 460 core

in vec2 vTexCoord;
in vec3 vNormal;
in vec3 vFragPos;

out vec4 fragColor;

uniform sampler2D texture1;
uniform vec3 objectTint;
uniform vec3 viewPos;
uniform vec3 sunPos;    
uniform vec3 sunColor;    
uniform vec3 flashPos;   
uniform vec3 flashDir;     
uniform float flashOn;     

void main(){
    vec3 norm = normalize(vNormal);
    vec3 viewDir = normalize(viewPos - vFragPos);
    vec4 texColor = texture(texture1, vTexCoord);

    //ILUMINAÇÃO DO SOL
    float sunIntensity = clamp(sunPos.y / 20.0, 0.0, 1.0);
    
    vec3 ambient = (0.1 + 0.5 * sunIntensity) * vec3(1.0);

    //Difusa
    vec3 sunLightDir = normalize(sunPos - vFragPos);
    float diff = max(dot(norm, sunLightDir), 0.0);
    vec3 diffuse = diff * sunColor * sunIntensity;

    //Especular
    vec3 reflectDir = reflect(-sunLightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
    vec3 specular = 0.5 * spec * sunColor * sunIntensity;


    //ILUMINAÇÃO DA LANTERNA (Spotlight)
    vec3 flashLight = vec3(0.0);
    
    if (flashOn > 0.5) {
        vec3 fLightDir = normalize(flashPos - vFragPos);
        
        //Ângulo entre o vetor da luz e a direção que a lanterna aponta
        float theta = dot(fLightDir, normalize(-flashDir));
        float cutOff = 0.91;      //Ângulo interno (foco)
        float outerCutOff = 0.82; //Ângulo externo (suavização)

        if(theta > outerCutOff) {
            //Suavização da borda (Soft Edge)
            float epsilon = cutOff - outerCutOff;
            float intensity = clamp((theta - outerCutOff) / epsilon, 0.0, 1.0);
            
            //atenuação
            float distance = length(flashPos - vFragPos);
            float attenuation = 1.0 / (1.0 + 0.045 * distance + 0.0075 * (distance * distance));

            //Difusa
            float diffF = max(dot(norm, fLightDir), 0.0);
            vec3 flashColor = vec3(1.0, 0.95, 0.8); 
            
            //ESpecular
            vec3 reflectFlash = reflect(-fLightDir, norm);
            float specFlash = pow(max(dot(viewDir, reflectFlash), 0.0), 32);

            flashLight = (diffF + specFlash) * flashColor * intensity * attenuation * 2.5;
        }
    }

    vec3 result = (ambient + diffuse + specular + flashLight) * texColor.rgb * objectTint;
    fragColor = vec4(result, texColor.a);
}