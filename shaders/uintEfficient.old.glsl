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

layout (local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(std430, binding = 0) buffer GridData {
    uint[2] data[];
};
layout(std430, binding = 1) buffer GridColor {
    uint color[];
};

// data from previous run with 1/scalePrev of size unless INITIAL_RUN is set
layout(std430, binding = 2) buffer GridPrevData {
    uint[2] prevData[];
};

uint[2] first_layer(dvec2 x, int iterations, dvec2 u0, double beta, mat2 V, double theta)
{
    dvec2 u = u0;
    uvec2 s = uvec2(0,0);
    uvec2 spiketr = uvec2(0,0);
    for (int i = 0; i < iterations; ++i) {
        u = beta * u + W * x + b + V * s - theta * s;
        s = uvec2(step(theta,u));
        spiketr = (spiketr << 1) + s;
    }
    return uint[2](spiketr.x, spiketr.y);
}

uint uint2col(uint x)
{
    float n = 10.;
    float a = ((1. / n) * log(1 + (exp(n) - 1) * x / pow(2., float(iterations))));
    // a should be in [0,1] by definition. But just to make sure:
    return min(255, uint(floor(255*a)));
}

void main()
{
    dvec2 nuv = gl_GlobalInvocationID.xy/iResolution.xy;
    uint index = uint(gl_GlobalInvocationID.x + gl_GlobalInvocationID.y * iResolution.x);
    dvec2 uv = scale*nuv+offset;

    uint[2] res;
    #ifdef INITIAL_RUN
    res = first_layer(uv, iterations, u0, beta, V, theta);
    #else
    // points of corners
    ivec2 LDCorner = ivec2(gl_GlobalInvocationID.x / scalePrev, gl_GlobalInvocationID.y / scalePrev);
    uint LDCIndex = uint(LDCorner.x + LDCorner.y * (iResolution.x / scalePrev));
    ivec2 RUCorner = ivec2(LDCorner.x + 1, LDCorner.y + 1);
    uint RUCIndex = uint(RUCorner.x + RUCorner.y * (iResolution.x / scalePrev));

    bool test = (RUCorner.x >= iResolution.x / scalePrev || RUCorner.y >= iResolution.y / scalePrev) || (prevData[LDCIndex] != prevData[RUCIndex]);

    res = test ? first_layer(uv, iterations, u0, beta, V, theta) : prevData[LDCIndex];
    // if (RUCorner.x >= iResolution.x / scalePrev || RUCorner.y >= iResolution.y / scalePrev) {
    //     // out of bounds, compute new data
    //     res = first_layer(uv, iterations, u0, beta, V, theta);
    // } else if (prevData[LDCIndex] == prevData[RUCIndex]) {
    //     // due to convexity and since the borders are on the axis
    //     res = prevData[LDCIndex];
    // } else {
    //     res = first_layer(uv, iterations, u0, beta, V, theta);
    // }
    #endif

    data[index] = res;
    color[index] = uint2col(res[0]) | (uint2col(res[1]) << 8) | uint(0xFF000000);
}
