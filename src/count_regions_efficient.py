import moderngl
import numpy as np
from common import getUniformsDict, getUniformsDictSpliced, compileCompShaderFile
from count_regions import CountRegions
import itertools


class CountRegionsEfficient(CountRegions):
    def __init__(self, imagep, spikeTrp, maxSizePot2):
        # Create context (offscreen)
        self.imagep = imagep
        self.spikeTrp = spikeTrp
        self.ctx = moderngl.create_standalone_context(backend="egl")
        self.shader = compileCompShaderFile(self.ctx, "shaders/uintEfficient.glsl")
        self.shaderCorners = compileCompShaderFile(self.ctx, "shaders/corners.glsl")

        self.resSize = 2
        assert maxSizePot2 >= 6
        self.maxSizeI = maxSizePot2 - 6
        self.initialSize = 64  # 2**6
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
            self.bufPrev.append(self.ctx.buffer(reserve=size * size * self.resSize * 4))

    def run(self, iterationsR, u0R, betaR, bR, WR, VR, thetaR, scale, offset):
        ctx = self.ctx
        shader = self.shader

        for iterations, u0, beta, b, W, V, theta in itertools.product(
            iterationsR, u0R, betaR, bR, WR, VR, thetaR
        ):
            for i in range(0, self.maxSizeI + 1):
                prevSize = self.initialSize * self.scalePrev ** (i - 1)
                size = self.initialSize * self.scalePrev**i
                print(size)

                self.bufData[i].bind_to_storage_buffer(binding=0)
                self.bufColor[i].bind_to_storage_buffer(binding=1)
                self.bufPrev[i].bind_to_storage_buffer(binding=2)

                initialRun = i == 0
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

                assert size % 8 == 0, "Size must be a multiple of 8"
                shader.run(group_x=size // 8, group_y=size // 8)

                assert self.resSize == 2
                self.bufRegionsN.write(np.array([0], dtype=np.uint32))
                self.shaderCorners["iResolution"] = size, size
                assert size % 8 == 0, "Size must be a multiple of 8"
                self.shaderCorners.run(group_x=size // 8, group_y=size // 8)
                regions_n = np.frombuffer(self.bufRegionsN.read(), dtype=np.uint32)[0]

                print(f"Regions for {size}:", regions_n)

                if i != self.maxSizeI:
                    ctx.copy_buffer(self.bufPrev[i + 1], self.bufData[i])

                imageArray = None
                if self.imagep:
                    imageArray = np.frombuffer(
                        self.bufColor[i].read()[0 : size * size * 4], dtype=np.byte
                    ).reshape((size, size, 4))

                uniforms = getUniformsDict(shader)
                uniformsSpliced = getUniformsDictSpliced(shader)
                yield regions_n, imageArray, uniforms, uniformsSpliced
