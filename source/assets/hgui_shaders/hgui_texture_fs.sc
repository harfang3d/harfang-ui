$input v_texcoord0,v_color0

#include<bgfx_shader.sh>

SAMPLER2D(u_tex,0);

void main(){
	vec4 c = texture2D(u_tex,v_texcoord0);
	gl_FragColor =  c * v_color0;
}
