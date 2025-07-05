from contextlib import contextmanager
import time
import moderngl
from pathlib import Path


@contextmanager
def measure_perf(label):
    start = time.perf_counter()
    try:
        yield ()
    finally:
        end = time.perf_counter()
        print(f"Elapsed time ({label}): {end - start:.6f} seconds")


@contextmanager
def measure_perf_gpu(ctx, label):
    timer = ctx.query(time=True)
    try:
        with timer:
            yield ()
    finally:
        elapsed_ns = timer.elapsed
        print(f"Elapsed time ({label}): {elapsed_ns/10**9:.6f} seconds")


def mkdirp(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def chunked_iterable(iterable, n):
    """Yield successive n-sized chunks from iterable."""
    for i in range(0, len(iterable), n):
        yield iterable[i : i + n]


def getUniformsDict(shader):
    return {
        name: shader[name].value
        for name in shader
        if isinstance(shader[name], moderngl.Uniform)
    }


def compileCompShaderFile(ctx, filename):
    """Compile a compute shader from a file."""
    with open(filename, "r") as f:
        shader_code = f.read()
    return ctx.compute_shader(shader_code)


def getUniformsDictSpliced(shader):
    res = {}
    for name in shader:
        uniform = shader[name]
        if isinstance(uniform, moderngl.Uniform):
            for i in range(uniform.array_length):
                for j in range(uniform.dimension):
                    cpName = f"{name}"
                    value = uniform.value
                    if uniform.array_length > 1:
                        cpName += f"[{i}]"
                        value = value[i]
                    if uniform.dimension > 1:
                        cpName += f"[{j}]"
                        value = value[j]
                    res[cpName] = value
    return res
