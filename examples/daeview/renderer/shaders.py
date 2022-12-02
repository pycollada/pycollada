######################################################################
# Flat Shader
# This shader applies the given model view matrix to the vertices,
# and uses a uniform color value.
flatShader = (['''
uniform mat4 mvpMatrix;
attribute vec4 vVertex;
void main(void)
{
  gl_Position = mvpMatrix * vVertex;
}'''],
              ['''
//precision mediump float;
uniform vec4 vColor;
void main(void)
{
  gl_FragColor = vColor;
}'''])

######################################################################
# Point light, diffuse lighting only
pointLightDiff = (['''
uniform mat4 mvMatrix;
uniform mat4 pMatrix;
uniform vec3 vLightPos;
uniform vec4 vColor;
attribute vec4 vVertex;
attribute vec3 vNormal;
varying vec4 vFragColor;
void main(void)
{
  mat3 mNormalMatrix;
  mNormalMatrix[0] = normalize(mvMatrix[0].xyz);
  mNormalMatrix[1] = normalize(mvMatrix[1].xyz);
  mNormalMatrix[2] = normalize(mvMatrix[2].xyz);
  vec3 vNorm = normalize(mNormalMatrix * vNormal);
  vec4 ecPosition;
  vec3 ecPosition3;
  ecPosition = mvMatrix * vVertex;
  ecPosition3 = ecPosition.xyz /ecPosition.w;
  vec3 vLightDir = normalize(vLightPos - ecPosition3);
  float fDot = max(0.0, dot(vNorm, vLightDir));
  vFragColor.rgb = vColor.rgb * fDot;
  vFragColor.a = vColor.a;
//  vFragColor = vColor;
  mat4 mvpMatrix;
  mvpMatrix = pMatrix * mvMatrix;
  gl_Position = mvpMatrix * vVertex;
}'''],
                  ['''
//precision mediump float;
varying vec4 vFragColor;
void main(void)
{
  gl_FragColor = vFragColor;
}'''])


######################################################################
# ADS Gouraud shader
ADSGouraud = (['''
uniform mat4 mvMatrix;
uniform mat4 pMatrix;
uniform vec3 vLightPos;
uniform vec4 ambientColor;
uniform vec4 diffuseColor;
uniform vec4 specularColor;
uniform float shininess;
uniform vec4 lightColor;
uniform float fConstantAttenuation;
uniform float fLinearAttenuation;
uniform float fQuadraticAttenuation;
attribute vec4 vVertex;
attribute vec3 vNormal;
varying vec4 vVaryingColor;
void main(void)
{
  mat3 mNormalMatrix;
  mNormalMatrix[0] = normalize(mvMatrix[0].xyz);
  mNormalMatrix[1] = normalize(mvMatrix[1].xyz);
  mNormalMatrix[2] = normalize(mvMatrix[2].xyz);
// Get surface normal in eye coordinates
  vec3 vEyeNormal = mNormalMatrix * vNormal;
// Get vertex position in eye coordinates
  vec4 vPosition4 = mvMatrix * vVertex;
  vec3 vPosition3 = vPosition4.xyz /vPosition4.w;
// Get vector to light source
  vec3 vLightDir = normalize(vLightPos - vPosition3);
// Get distance to light source
  float distanceToLight = length(vLightPos-vPosition3);
//  float attenuation = fConstantAttenuation / ((1.0 + fLinearAttenuation * distanceToLight) * (1.0 + fQuadraticAttenuation * distanceToLight * distanceToLight));
  float attenuation = 1.0 / (fConstantAttenuation + fLinearAttenuation * distanceToLight + fQuadraticAttenuation * distanceToLight * distanceToLight);
  vec4 attenuatedLight = lightColor * attenuation;
//  float attenuation = 1.0f;
// Dot product gives us diffuse intensity
  float diff = max(0.0, dot(vEyeNormal, vLightDir));
// Multiply intensity by diffuse color, force alpha to 1.0
  vVaryingColor = attenuatedLight * diffuseColor * diff;
// Add in ambient light
  vVaryingColor += ambientColor;
// Specular light
  vec3 vReflection = normalize(reflect(-vLightDir, vEyeNormal));
  float spec = max(0.0, dot(vEyeNormal, vReflection));
  if(diff != 0.0) {
    float fSpec = pow(spec, shininess);
    vVaryingColor.rgb += attenuatedLight.rgb * vec3(fSpec, fSpec, fSpec);
  }
// Don't forget to transform the geometry
  mat4 mvpMatrix = pMatrix * mvMatrix;
  gl_Position = mvpMatrix * vVertex;
}'''],
              ['''
//precision mediump float;
varying vec4 vVaryingColor;
void main(void)
{
  gl_FragColor = vVaryingColor;
}'''])


##############################################################################
# Simple phong shader by Jerome GUINOT aka 'JeGX' - jegx [at] ozone3d
# [dot] net see
# http://www.ozone3d.net/tutorials/glsl_lighting_phong.php

simplePhong = (['''
varying vec3 normal, lightDir0, eyeVec;
void main()
{
  normal = gl_NormalMatrix * gl_Normal;
  vec3 vVertex = vec3(gl_ModelViewMatrix * gl_Vertex);
  lightDir0 = vec3(gl_LightSource[0].position.xyz - vVertex);
  eyeVec = -vVertex;
  gl_Position = ftransform();
}
'''],
               ['''
uniform vec4 diffuse, specular, ambient;
uniform float shininess;
varying vec3 normal, lightDir0, eyeVec;
void main (void)
{
  vec4 final_color =
    (gl_FrontLightModelProduct.sceneColor * ambient)
    + (gl_LightSource[0].ambient * ambient);
  vec3 N = normalize(normal);
  vec3 L0 = normalize(lightDir0);
  float lambertTerm0 = dot(N,L0);
  if(lambertTerm0 > 0.0)
  {
    final_color += gl_LightSource[0].diffuse * diffuse * lambertTerm0;
    vec3 E = normalize(eyeVec);
    vec3 R = reflect(-L0, N);
    float spec = pow(max(dot(R, E), 0.0), shininess);
    final_color += gl_LightSource[0].specular * specular * spec;
  }
  gl_FragColor = final_color;
}
'''])

##############################################################################
# ADS Phong shader
ADSPhong = (['''
attribute vec4 vVertex;
attribute vec3 vNormal;
uniform mat4 mvMatrix;
uniform mat4 pMatrix;
uniform vec3 vLightPos;
// Color to fragment program
varying vec3 vVaryingNormal;
varying vec3 vVaryingLightDir;
varying float distanceToLight;
//varying float spotEffect;
void main(void)
{
  mat3 normalMatrix;
  normalMatrix[0] = normalize(mvMatrix[0].xyz);
  normalMatrix[1] = normalize(mvMatrix[1].xyz);
  normalMatrix[2] = normalize(mvMatrix[2].xyz);
// Get surface normal in eye coordinates
  vVaryingNormal = normalMatrix * vNormal;
// Get vertex position in eye coordinates
  vec4 vPosition4 = mvMatrix * vVertex;
  vec3 vPosition3 = vPosition4.xyz /vPosition4.w;
// Get vector to light source
  vVaryingLightDir = normalize(vLightPos - vPosition3);
// Get distance to light source
  distanceToLight = length(vLightPos-vPosition3);

//  spotEffect = dot(normalize(gl_LightSource[0].spotDirection), normalize(-lightDir));
//  spotEffect = dot(vec3(0.0, 0.0, -1.0), normalize(-vVaryingLightDir));

// Don't forget to transform the geometry
  mat4 mvpMatrix = pMatrix * mvMatrix;
  gl_Position = mvpMatrix * vVertex;
}'''],
            ['''
precision mediump float;
uniform vec4 ambientColor;
uniform vec4 diffuseColor;
uniform vec4 specularColor;
uniform float shininess;
uniform vec4 lightColor;
uniform float fConstantAttenuation;
uniform float fLinearAttenuation;
uniform float fQuadraticAttenuation;
varying vec3 vVaryingNormal;
varying vec3 vVaryingLightDir;
varying float distanceToLight;
//varying float spotEffect;
void main(void)
{
//  float attenuation = 1.0 / (fConstantAttenuation + fLinearAttenuation * distanceToLight + fQuadraticAttenuation * distanceToLight * distanceToLight);
  float attenuation = fConstantAttenuation / ((1.0 + fLinearAttenuation * distanceToLight) * (1.0 + fQuadraticAttenuation * distanceToLight * distanceToLight));
//  attenuation *= pow(spotEffect, 0.15);
//  float attenuation = 1.0;
  vec4 attenuatedLight = lightColor * attenuation;
  attenuatedLight.a = 1.0;
// Dot product gives us diffuse intensity
  float diff = max(0.0, dot(normalize(vVaryingNormal), normalize(vVaryingLightDir)));
// Multiply intensity by diffuse color, force alpha to 1.0
  gl_FragColor = attenuatedLight * (diffuseColor * diff + ambientColor);
// Specular light
  vec3 vReflection = normalize(reflect(-normalize(vVaryingLightDir), normalize(vVaryingNormal)));
  float spec = max(0.0, dot(normalize(vVaryingNormal), vReflection));
// If diffuse light is zero, do not even bother with the pow function
  if(diff != 0.0) {
    float fSpec = pow(spec, shininess);
    gl_FragColor.rgb += attenuatedLight.rgb * vec3(fSpec, fSpec, fSpec);
  }
// For some reaseons, without following multiplications, all scenes exported from Blender are dark.
// Need to investigate the real reason. For now, it is just workaround to make scene brighter.
//  gl_FragColor.rgb *= vec3(5.5, 5.5, 5.5);
//  gl_FragColor.rgb *= vec3(2.5, 2.5, 2.5);
//  gl_FragColor.rgb += vec3(0.3, 0.3, 0.3);
//  gl_FragColor = diffuseColor + ambientColor;
}'''])

######################################################################
# Point light (Diffuse only), with texture (modulated)
texturePointLightDiff = (['''
uniform mat4 mvMatrix;
uniform mat4 pMatrix;
uniform vec3 vLightPos;
uniform vec4 vColor;
attribute vec4 vVertex;
attribute vec3 vNormal;
varying vec4 vFragColor;
attribute vec2 vTexCoord0;
varying vec2 vTex;
void main(void)
{
 mat3 mNormalMatrix;
 mNormalMatrix[0] = normalize(mvMatrix[0].xyz);
 mNormalMatrix[1] = normalize(mvMatrix[1].xyz);
 mNormalMatrix[2] = normalize(mvMatrix[2].xyz);
 vec3 vNorm = normalize(mNormalMatrix * vNormal);
 vec4 ecPosition;
 vec3 ecPosition3;
 ecPosition = mvMatrix * vVertex;
 ecPosition3 = ecPosition.xyz /ecPosition.w;
 vec3 vLightDir = normalize(vLightPos - ecPosition3);
 float fDot = max(0.0, dot(vNorm, vLightDir));
 vFragColor.rgb = vColor.rgb * fDot;
 vFragColor.a = vColor.a;
 vTex = vTexCoord0;
 mat4 mvpMatrix;
 mvpMatrix = pMatrix * mvMatrix;
 gl_Position = mvpMatrix * vVertex;
}'''],
                         ['''
precision mediump float;
varying vec4 vFragColor;
varying vec2 vTex;
uniform sampler2D textureUnit0;
void main(void)
{
 gl_FragColor = texture2D(textureUnit0, vTex);
 if(gl_FragColor.a < 0.1)
  discard;
/* if(gl_FragColor.a < 1.0)
 {
  gl_FragColor.r = 1.0 - gl_FragColor.a;
  gl_FragColor.g = 0;
  gl_FragColor.b = 0;
  gl_FragColor.a = 1.0;
 }*/
// if(vFragColor.a != 0.0)
//  gl_FragColor *= vFragColor;
// else
//  discard;
// gl_FragColor = texture2D(textureUnit0, vTex);
// gl_FragColor = vFragColor;
}'''])


######################################################################
# Phong with textures
texturePhong = (['''
varying vec3 normal, lightDir0, eyeVec;

void main()
{
	normal = gl_NormalMatrix * gl_Normal;

	vec3 vVertex = vec3(gl_ModelViewMatrix * gl_Vertex);

	lightDir0 = vec3(gl_LightSource[0].position.xyz - vVertex);
	eyeVec = -vVertex;

	gl_Position = ftransform();
        gl_TexCoord[0]  = gl_TextureMatrix[0] * gl_MultiTexCoord0;
}
'''],
                ['''
varying vec3 normal, lightDir0, eyeVec;
uniform sampler2D my_color_texture[1]; //0 = ColorMap

void main (void)
{
        vec4 texColor = texture2D(my_color_texture[0], gl_TexCoord[0].st);
	vec4 final_color;

/*	final_color = (gl_FrontLightModelProduct.sceneColor * vec4(texColor.rgb,1.0)) +
		      gl_LightSource[0].ambient * vec4(texColor.rgb,1.0);*/
	final_color = (gl_FrontLightModelProduct.sceneColor * vec4(texColor.rgb,1.0)) +
		       vec4(texColor.rgb,1.0);

	vec3 N = normalize(normal);
	vec3 L0 = normalize(lightDir0);

	float lambertTerm0 = dot(N,L0);

	if(lambertTerm0 > 0.0)
	{
		final_color += gl_LightSource[0].diffuse *
		               gl_FrontMaterial.diffuse *
					   lambertTerm0;

		vec3 E = normalize(eyeVec);
		vec3 R = reflect(-L0, N);
		float specular = pow( max(dot(R, E), 0.0),
		                 gl_FrontMaterial.shininess );
		final_color += gl_LightSource[0].specular *
		               gl_FrontMaterial.specular *
					   specular;
	}
	gl_FragColor = final_color;
}
'''])
