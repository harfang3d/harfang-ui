$input v_texcoord0, v_color0

#include<bgfx_shader.sh>

SAMPLER2D(s_texTexture,0);

void main(){
    vec4 color = texture2D(s_texTexture,v_texcoord0) * v_color0;
    gl_FragColor = color;
}
