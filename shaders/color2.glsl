#version 330
out vec4 fragColor;
uniform vec2 iResolution;
uniform int iterations;
uniform vec2 u0;
uniform float beta;
uniform vec2 b;
uniform mat2 W;
uniform mat2 V;
uniform float theta;
uniform vec2 offset;
uniform float scale;

vec2[2] first_layer(vec2 x, int iterations, vec2 u0, float beta, mat2 W, vec2 b, mat2 V, float theta)
{
    vec2 u = u0;
    vec2 s = vec2(0,0);
    vec2 col = vec2(0,0);
    vec2 col2 = vec2(0,0);
    for (int i = 0; i < iterations; ++i) {
        u = beta * u + W * x + b + V * s - theta * beta * s;
        s = step(theta,u);
        col = col + pow(2.,float(-i))*s;
        col2 = col2 + pow(2.,float(i-iterations+1))*s;
    }
    return vec2[2](col, col2);
}


void main()
{
    // Normalized pixel coordinates (from 0 to scale)
    vec2 nuv = gl_FragCoord.xy/iResolution.xy;
    vec2 uv = scale*nuv+offset;

    // Time varying pixel color

    // int iterations = 1;
    // vec2 u0 = vec2(0,0);
    // float beta = 1.;
    // vec2 b = vec2(0,0);
    // mat2 W = mat2(1,0,0,1);
    // mat2 V = mat2(0,0,0,0);
    // float theta = 1.;
    vec2[2] res = first_layer(uv, iterations, u0, beta, W, b, V, theta);

    // Output to screen
    fragColor = vec4(res[0], res[1]);
}
