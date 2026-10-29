#version 330
uniform sampler2D image;
in vec2 uv;
out vec4 frag;
void main(){frag=texture(image,uv);}
