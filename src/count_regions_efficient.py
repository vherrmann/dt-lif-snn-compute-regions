import moderngl
import numpy as np
from common import getUniformsDict, getUniformsDictSpliced, compileCompShaderFile
from count_regions import CountRegions
import itertools
import unique_bytes


class CountRegionsEfficient(CountRegions):
    def __init__(self, imagep, spikeTrp, maxSizePot2):
        # Create context (offscreen)
        self.imagep = imagep
        self.spikeTrp = spikeTrp
        self.ctx = moderngl.create_standalone_context(backend="egl")
        self.shader = compileCompShaderFile(self.ctx, "shaders/uintEfficient.glsl")
        self.shaderCorners = compileCompShaderFile(self.ctx, "shaders/corners.glsl")

        self.resSize = 4
        assert maxSizePot2 >= 5
        self.maxSizeI = maxSizePot2 - 5
        self.initialSize = 2**5
        self.scalePrev = 2

        self.bufData = []
        self.bufColor = []
        self.bufPrev = []
        self.bufRegionsN = self.ctx.buffer(reserve=4)
        self.bufRegionsN.bind_to_storage_buffer(binding=3)
        for i in range(0, self.maxSizeI + 1):
            size = self.initialSize * self.scalePrev**i
            self.bufData.append(self.ctx.buffer(reserve=size * size * self.resSize * 4))
            self.bufColor.append(self.ctx.buffer(reserve=size * size * 4))
            prevSize = self.initialSize * self.scalePrev ** (i - 1) if i > 0 else 1
            self.bufPrev.append(
                self.ctx.buffer(reserve=prevSize * prevSize * self.resSize * 4)
            )

    def run(self, iterationsR, u0R, betaR, bR, WR, VR, thetaR, scale, offset):
        ctx = self.ctx
        shader = self.shader

        for iterations, u0, beta, b, W, V, theta in itertools.product(
            iterationsR, u0R, betaR, bR, WR, VR, thetaR
        ):
            for i in range(0, self.maxSizeI + 1):
                size = self.initialSize * self.scalePrev**i
                print(size)

                self.bufData[i].bind_to_storage_buffer(binding=0)
                self.bufColor[i].bind_to_storage_buffer(binding=1)
                self.bufPrev[i].bind_to_storage_buffer(binding=2)

                initialRun = True  # i == 0
                self.setUniforms(
                    iResolution=(size, size),
                    iterations=iterations,
                    u0=u0,
                    beta=beta,
                    # b=b,
                    # W=W,
                    V=V,
                    theta=theta,
                    scale=scale,
                    offset=offset,
                    initialRun=initialRun,
                    scalePrev=self.scalePrev,
                    imagep=self.imagep,
                )

                assert (
                    size % 8 == 0
                ), "size must be multiple of 8; if you want to lower this, you need to amend the shader"
                groupSize = size // 8
                shader.run(group_x=groupSize, group_y=groupSize)

                assert self.resSize == 4
                self.bufRegionsN.write(np.array([0], dtype=np.uint32))
                self.shaderCorners["iResolution"] = size, size
                self.shaderCorners.run(group_x=groupSize, group_y=groupSize)
                regions_n = np.frombuffer(self.bufRegionsN.read(), dtype=np.uint32)[0]

                print(f"Regions for {size}:", regions_n)

                if i != self.maxSizeI:
                    ctx.copy_buffer(self.bufPrev[i + 1], self.bufData[i])

                if self.spikeTrp:
                    spikeTrains = unique_bytes.unique_regions(
                        self.bufData[i].read(), size, self.resSize * 4
                    )

                    for spiketrain in spikeTrains:
                        rs = self.resSize
                        # fmt: off
                        print("x:", "".join(f"{byte:08b}"[::-1] for byte in spiketrain[0      : rs * 2])[:iterations][::-1],
                            "y:", "".join(f"{byte:08b}"[::-1] for byte in spiketrain[rs * 2 : rs * 4])[:iterations][::-1])
                        # fmt: on

                imageArray = None
                if self.imagep:
                    imageArray = np.frombuffer(
                        self.bufColor[i].read()[0 : size * size * 4], dtype=np.byte
                    ).reshape((size, size, 4))

                uniforms = getUniformsDict(shader)
                uniformsSpliced = getUniformsDictSpliced(shader)
                yield regions_n, imageArray, uniforms, uniformsSpliced
