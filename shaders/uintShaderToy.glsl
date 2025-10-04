struct SNNConfig {
    int iterations;
    vec2 u0;
    float beta;
    mat2 W;
    vec2 b;
    mat2 V;
    float theta;
    vec2 offset;
    float scale;
};

uint[4] first_layer(vec2 x, SNNConfig conf)
{
    vec2 u = conf.u0;
    uvec2 s = uvec2(0,0);
    uvec2 spiketrLow = uvec2(0,0);
    uvec2 spiketrUp = uvec2(0,0);
    for (int i = 0; i < conf.iterations; ++i) {
        u = conf.beta * u + conf.W * x + conf.b + conf.V * vec2(s) - conf.theta * conf.beta * vec2(s);
        s = uvec2(step(conf.theta,u));
        spiketrUp = (spiketrUp << 1) + (spiketrLow >> 31);
        spiketrLow = (spiketrLow << 1) + s;
    }
    return uint[4](spiketrLow.x, spiketrUp.x, spiketrLow.y, spiketrUp.y);
}

vec2 posToUV(vec2 pos, SNNConfig conf)
{
    vec2 nuv = pos/iResolution.xy;
    return conf.scale*nuv+conf.offset;
}

float uint2colScal(uint high, uint low, int iterations)
{
    float n = 10.;
    float x = float(high) * pow(2., 32.) + float(low);
    float a = ((1. / n) * log(1. + (exp(n) - 1.) * x / pow(2., float(iterations))));
    return a;
}

float uint2colGap(uint high, uint low, int iterations)
{
    int n = 0;
    int nMax = 0;
    for (int i = 0; i < iterations; ++i) {
        if ((low & 1u) == 1u) {
            n++;
            nMax = max(nMax, n);
        } else {
            n = 0;
        }
        low = (low >> 1) + (high << 31);
        high = (high >> 1);
    }
    return (float(nMax) / float(iterations));
}

vec4 uint2col(uint[4] res, int iterations)
{
    return vec4(uint2colGap(res[1], res[0], iterations),
                uint2colGap(res[3], res[2], iterations),
                0.0, 1.0);
}

vec4 uint2colBorder(vec2 fragCoord, uint[4] res, SNNConfig conf)
{
    vec2 aBitRightPos = posToUV(fragCoord.xy+vec2(1,0), conf);
    vec2 aBitUpPos    = posToUV(fragCoord.xy+vec2(0,1), conf);
    uint[4] aBitRight = first_layer(aBitRightPos, conf);
    uint[4] aBitUp = first_layer(aBitUpPos, conf);
    if (res != aBitRight || res != aBitUp) {
        return vec4(1.0); // white
    } else {
        return uint2col(res, conf.iterations);
    }
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    int iterations = 20;
    vec2 u0 = vec2(0.0, 0.0);
    float beta = 0.5;
    vec2 b = vec2(0.0, 0.0);
    mat2 W = mat2(1.0, 0.0, 0.0, 1.0);
    mat2 V = mat2(1.0, 0.0, 0.0, 1.0);
    float theta = 1.;
    vec2 offset = vec2(0.0, 0.0);
    float scale = 2.0;
    SNNConfig conf = SNNConfig(iterations, u0, beta, W, b, V, theta, offset, scale);

    vec2 uv = posToUV(fragCoord.xy, conf);
    uint index = uint(fragCoord.x + fragCoord.y * iResolution.x);

    uint[4] res = first_layer(uv, conf);

    fragColor = uint2colBorder(fragCoord, res, conf);
}
