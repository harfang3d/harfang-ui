$input v_texcoord0, v_color0

#include<bgfx_shader.sh>

SAMPLER2D(s_texTexture,0);

void main(){
    gl_FragColor=vec4((texture2D(s_texTexture,v_texcoord0)*v_color0).rgb,v_color0.a);
}
