#version 460

uniform dvec2 iResolution;
uniform int iterations;
uniform dvec2 u0;
uniform double beta;
// W and b can't be used with this optimization
// uniform dvec2 b;
dvec2 b = dvec2(0.0, 0.0);
// uniform mat2 W;
mat2 W = mat2(1.0, 0.0, 0.0, 1.0);
uniform mat2 V;
uniform double theta;
uniform dvec2 offset;
uniform double scale;
uniform int scalePrev;
uniform bool initialRun;
uniform bool imagep;

layout (local_size_x = 8, local_size_y = 8, local_size_z = 1) in;

layout(std430, binding = 0) buffer GridData {
    uint[4] data[];
};
layout(std430, binding = 1) buffer GridColor {
    uint color[];
};

// data from previous run with 1/scalePrev of size unless INITIAL_RUN is set
layout(std430, binding = 2) buffer GridPrevData {
    uint[4] prevData[];
};

uint[4] first_layer(dvec2 x, int iterations, dvec2 u0, double beta, mat2 V, double theta)
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

uint uint2colScalSimple(uint high, uint low)
{
    float x = float(high) * pow(2., 32.-float(iterations)) + float(low)/ pow(2., iterations);
    return uint(255.*x);
}

uint uint2colSimple(uint[4] res)
{
    return uint2colScalSimple(res[1], res[0]) | (uint2colScalSimple(res[3], res[2]) << 8) | uint(0xFF000000);
}

void main()
{
    dvec2 nuv = gl_GlobalInvocationID.xy/iResolution.xy;
    uint index = uint(gl_GlobalInvocationID.x + gl_GlobalInvocationID.y * iResolution.x);
    dvec2 uv = scale*nuv+offset;

    uint[4] res;
    ivec2 LDCorner = ivec2(gl_GlobalInvocationID.x / scalePrev, gl_GlobalInvocationID.y / scalePrev);
    uint LDCIndex = uint(LDCorner.x + LDCorner.y * (iResolution.x / scalePrev));
    ivec2 RUCorner = ivec2(LDCorner.x + 1, LDCorner.y + 1);
    uint RUCIndex = uint(RUCorner.x + RUCorner.y * (iResolution.x / scalePrev));

    bool test = initialRun
        || (RUCorner.x >= iResolution.x / scalePrev || RUCorner.y >= iResolution.y / scalePrev)
        || (prevData[LDCIndex] != prevData[RUCIndex]);
    if (test) {
        res = first_layer(uv, iterations, u0, beta, V, theta);
    } else {
        res = prevData[LDCIndex];
    }

    data[index] = res;
    if (imagep) {
        color[index] = uint2col(res);
    }
}
