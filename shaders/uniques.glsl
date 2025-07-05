#version 460
uniform int prevBatchSize;

layout (local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(std430, binding = 0) buffer Data {
    uint[4] data[];
};

layout(std430, binding = 1) buffer ResNum {
    uint resNum[];
};

uint chunkSize = 4;

void main()
{
    uint batchSize = 2*prevBatchSize;
    uint batchIndex = uint(gl_GlobalInvocationID.x) * batchSize;

    // we merge the batch of uniques at batchIndex with the one at batchIndex + prevBatchSize
    uint readPointer = batchIndex + prevBatchSize;
    while (true) {
        uint writePointer = batchIndex;
        while (true) {
            // check if value already exists in lower batch
            if (data[writePointer] == data[readPointer]) {
                break;
            }
            writePointer += 1;

            // we have reached the end of the uniques of the lower batch
            // (either because we have reached a marker (two equal values) or because we have reached the end of the batch)
            if ((data[writePointer-1] == data[writePointer]) || (writePointer - batchIndex >= prevBatchSize)) {
                data[writePointer] = data[readPointer];
                // mark the end of the next unique values
                data[writePointer+1] = data[readPointer];
                break;
            }
        }

        readPointer += 1;
        // we have reached the end of the uniques of the upper batch
        // (either because we have reached a marker (two equal values) or because we have reached the end of the batch)
        if ((data[readPointer-1] == data[readPointer]) || readPointer == batchSize + batchIndex) {
            break;
        }
    }

    uint pointer = batchIndex;
    while (true) {
        if ((data[pointer] == data[pointer+1])) {
            resNum[0] = pointer - batchIndex + 1;
            break;
        }
        if (pointer - batchIndex >= prevBatchSize) {
            resNum[0] = pointer - batchIndex;
            break;
        }

        pointer += 1;
    }
}
