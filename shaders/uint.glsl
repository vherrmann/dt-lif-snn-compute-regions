#version 460
uniform dvec2 iResolution;
uniform int iterations;
uniform dvec2 u0;
uniform double beta;
uniform dvec2 b;
uniform mat2 W;
uniform mat2 V;
uniform double theta;
uniform dvec2 offset;
uniform double scale;

layout (local_size_x = 32, local_size_y = 32, local_size_z = 1) in;

layout(std430, binding = 0) buffer GridData {
    uint[4] data[];
};
layout(std430, binding = 1) buffer GridColor {
    uint color[];
};

uint[4] first_layer(dvec2 x, int iterations, dvec2 u0, double beta, mat2 W, dvec2 b, mat2 V, double theta)
{
    dvec2 u = u0;
    uvec2 s = uvec2(0,0);
    uvec2 spiketrLow = uvec2(0,0);
    uvec2 spiketrUp = uvec2(0,0);
    for (int i = 0; i < iterations; ++i) {
        u = beta * (u - theta * s) + W * x + b + V * s;
        s = uvec2(step(theta,u));
        spiketrUp = (spiketrUp << 1) + (spiketrLow >> 31);
        spiketrLow = (spiketrLow << 1) + s;
    }
    return uint[4](spiketrLow.x, spiketrUp.x, spiketrLow.y, spiketrUp.y);
}

dvec2 posToUV(uvec2 pos)
{
    dvec2 nuv = dvec2(pos)/iResolution.xy;
    return scale*nuv+offset;
}

uint uint2colScal(uint high, uint low)
{
    float n = 10.;
    float x = float(high) * pow(2., 32.) + float(low);
    double a = ((1. / n) * log(1 + (exp(n) - 1) * x / pow(2., float(iterations))));
    // a should be in [0,1] by definition. But just to make sure:
    return min(255, uint(floor(255*a)));
}

uint uint2col(uint[4] res)
{
    return uint2colScal(res[1], res[0]) | (uint2colScal(res[3], res[2]) << 8) | uint(0xFF000000);
}

uint uint2colBorder(uint[4] res)
{
    dvec2 aBitRightPos = posToUV(gl_GlobalInvocationID.xy+uvec2(1,0));
    dvec2 aBitUpPos    = posToUV(gl_GlobalInvocationID.xy+uvec2(0,1));
    uint[4] aBitRight = first_layer(aBitRightPos, iterations, u0, beta, W, b, V, theta);
    uint[4] aBitUp = first_layer(aBitUpPos, iterations, u0, beta, W, b, V, theta);
    if (res != aBitRight || res != aBitUp) {
        return 0xFFFFFFFF; // white
    } else {
        return uint2col(res);
    }
}

void main()
{
    dvec2 uv = posToUV(gl_GlobalInvocationID.xy);
    uint index = uint(gl_GlobalInvocationID.x + gl_GlobalInvocationID.y * iResolution.x);

    uint[4] res = first_layer(uv, iterations, u0, beta, W, b, V, theta);

    data[index] = res;
    color[index] = uint2colBorder(res);
}
