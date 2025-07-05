import moderngl
import numpy as np
import unique_bytes
import itertools
from common import getUniformsDict, getUniformsDictSpliced, compileCompShaderFile
from count_regions import CountRegions


class CountRegionsSimple(CountRegions):
    def __init__(self, imagep, spikeTrp, sizeR):
        # Create context (offscreen)
        self.imagep = imagep
        self.spikeTrp = spikeTrp
        self.ctx = moderngl.create_standalone_context(backend="egl")
        self.shader = compileCompShaderFile(self.ctx, "shaders/uint.glsl")
        self.sizeR = sizeR

    def setUniforms(self, **kwargs):
        """Set uniforms for the shader."""
        for key, value in kwargs.items():
            if key in self.shader:
                self.shader[key] = value
            else:
                raise KeyError(f"Uniform '{key}' not found in shader.")

    def getSpiketrains(self, bufData, size, resSize):
        """Count unique chunks in the data buffer."""
        return unique_bytes.unique_regions(bufData.read(), size, resSize * 4)

    def printSpikeTrains(self, regionsSt, resSize, iterations):
        """Print spiketrains from the data buffer."""
        for spiketrain in regionsSt:
            rs = resSize
            # fmt: off
            print("x:", "".join(f"{byte:08b}"[::-1] for byte in spiketrain[0      : rs * 2])[:iterations][::-1],
                  "y:", "".join(f"{byte:08b}"[::-1] for byte in spiketrain[rs * 2 : rs * 4])[:iterations][::-1])
            # fmt: on

    def countUniqueChunks(self, bufData, size, resSize):
        """Count unique chunks in the data buffer."""
        return len(self.getSpiketrains(bufData, size, resSize))

    def run(self, iterationsR, u0R, betaR, bR, WR, VR, thetaR, scale, offset):
        ctx = self.ctx
        shader = self.shader
        for size in self.sizeR:
            resSize = 4

            # size * size * resSize many uints
            bufData = ctx.buffer(reserve=size * size * resSize * 4)
            bufColor = ctx.buffer(reserve=size * size * 4)

            # Bind buffer to binding=0
            bufData.bind_to_storage_buffer(binding=0)
            bufColor.bind_to_storage_buffer(binding=1)

            for iterations, u0, beta, b, W, V, theta in itertools.product(
                iterationsR, u0R, betaR, bR, WR, VR, thetaR
            ):
                self.setUniforms(
                    iResolution=(size, size),
                    iterations=iterations,
                    u0=u0,
                    beta=beta,
                    b=b,
                    W=W,
                    V=V,
                    theta=theta,
                    scale=scale,
                    offset=offset,
                )

                assert size % 32 == 0, "Size must be a multiple of 32"
                shader.run(group_x=size // 32, group_y=size // 32)

                regions_n = self.countUniqueChunks(bufData, size, resSize)

                imageArray = None
                if self.imagep:
                    imageArray = np.frombuffer(bufColor.read(), dtype=np.byte).reshape(
                        (size, size, 4)
                    )

                uniforms = getUniformsDict(shader)
                uniformsSpliced = getUniformsDictSpliced(shader)
                yield regions_n, imageArray, uniforms, uniformsSpliced
