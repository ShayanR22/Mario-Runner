#version 330
uniform sampler2D current_tex;
uniform sampler2D previous_tex;
uniform float reveal;
in vec2 uv;
out vec4 frag;
void main(){
 float eased=reveal*reveal*(3.0-2.0*reveal);
 frag=mix(texture(previous_tex,uv),texture(current_tex,uv),eased);
}
