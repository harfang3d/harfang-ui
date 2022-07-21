$input v_texcoord0,v_color0

#include<bgfx_shader.sh>

SAMPLER2D(u_tex,0);

void main(){
	gl_FragColor=texture2D(u_tex,v_texcoord0)*v_color0;
}
