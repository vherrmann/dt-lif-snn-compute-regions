#version 460

uniform ivec2 iResolution;

layout (local_size_x = 8, local_size_y = 8, local_size_z = 1) in;

layout(std430, binding = 0) buffer GridData {
    uint[2] data[];
};
layout(std430, binding = 3) buffer RegionsN {
    uint regions_n;
};
// layout(binding = 3) uniform atomic_uint regions_n;

void main()
{
    int i = int(gl_GlobalInvocationID.x);
    int j = int(gl_GlobalInvocationID.y);

    // Check if the value at the current position is different
    // from the value to the left and below it.
    bool leftIsDiff = i == 0 || (data[(i-1) * iResolution.x + j] != data[i * iResolution.x + j]);
    bool belowIsDiff = j == 0 || (data[i * iResolution.x + (j - 1)] != data[i * iResolution.x + j]);

    // If it is different indeed, the current position is a ll corner of
    // a region.
    // atomicCounterIncrement(regions_n);
    if (leftIsDiff && belowIsDiff) {
        // regions_n += 1;
        atomicAdd(regions_n, 1);
    }
}
