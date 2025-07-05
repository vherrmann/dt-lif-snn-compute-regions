import moderngl
import time
from contextlib import contextmanager

resSize = 4


@contextmanager
def measure_perf(label):
    start = time.perf_counter()
    try:
        yield ()
    finally:
        end = time.perf_counter()
        print(f"Elapsed time ({label}): {end - start:.6f} seconds")


def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0


# gven buffer has to be bound to binding=0
def count_unique(buffer, ctx=None):
    copyBuffer = False
    if ctx is None:
        copyBuffer = True
        ctx = moderngl.create_standalone_context()
    with measure_perf(f"Count regions inner"):
        valSize = resSize * 4  # resSize many uints
        dataSize = buffer.size
        print("DataSize:", dataSize)
        if dataSize % valSize != 0:
            raise ValueError("Data length must be a multiple of 4.")
        if not is_power_of_two(dataSize // valSize):
            raise ValueError("Data length must be a power of two.")
        if copyBuffer:
            with measure_perf(f"reserve buffer"):
                bufData = ctx.buffer(buffer.read())
                # bufData = ctx.buffer(reserve=buffer.size)
            # with measure_perf(f"copy buffer"):
            # ctx.copy_buffer(bufData, buffer)
            with measure_perf(f"bind buffer"):
                bufData.bind_to_storage_buffer(binding=0)
        else:
            bufData = buffer
        with measure_perf(f"compute shader"):
            with open("shaders/uniques.glsl", "r") as f:
                shader = ctx.compute_shader(f.read())

        with measure_perf(f"shader2"):
            resNum = ctx.buffer(reserve=4)  # one uint
            resNum.bind_to_storage_buffer(binding=1)

        with measure_perf(f"run"):
            i = 1
            while 2**i * valSize < dataSize:
                prevBatchSize = 2**i
                shader["prevBatchSize"] = prevBatchSize

                batchSize = 2 * prevBatchSize
                shader.run(group_x=dataSize // (valSize * batchSize))
                i += 1

        with measure_perf(f"read"):
            res = int.from_bytes(resNum.read(), byteorder="little", signed=False)
            resNum.release()
            if copyBuffer:
                bufData.release()
            return res
