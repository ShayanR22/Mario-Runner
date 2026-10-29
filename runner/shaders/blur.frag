#version 330
uniform sampler2D image;
uniform vec2 direction;
in vec2 uv;
out vec4 frag;
void main(){
 vec3 c=texture(image,uv).rgb*.227027;
 c+=texture(image,uv+direction*1.384615).rgb*.316216;
 c+=texture(image,uv-direction*1.384615).rgb*.316216;
 c+=texture(image,uv+direction*3.230769).rgb*.070270;
 c+=texture(image,uv-direction*3.230769).rgb*.070270;
 frag=vec4(c,1.0);
}
