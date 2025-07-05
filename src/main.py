import numpy as np
from PIL import Image
import sys
import csv
import itertools
from count_regions_simple import CountRegionsSimple
from count_regions_efficient import CountRegionsEfficient

## args
efficientp = "--efficient" in sys.argv[1:]
imagep = "--image" in sys.argv[1:]
spikeTrp = "--spiketrain" in sys.argv[1:]


def once(v):
    yield v


ls = np.linspace
itpr = itertools.product
iterationsR = range(10, 20)
u0R = itpr(ls(0.0123456789, 1, 5), ls(0.0123456789, 1, 5))
betaR = ls(0.5, 1, 10)
WR = once((1.0, 0.0, 0.0, 1.0))  # doesn't increase number of regions if changed
bR = once((0.0, 0.0))  # doesn't increase number of regions if changed
VR = itpr(ls(-1, 1, 10), ls(-1, 1, 10), ls(-1, 1, 10), ls(-1, 1, 10))
thetaR = ls(0, 1, 10)
scale = 2
offset = -0.5, -0.5
maxSizePot2 = 12  # size = 2**maxSizePot2

if efficientp:
    counter = CountRegionsEfficient(
        imagep=imagep,
        spikeTrp=spikeTrp,
        maxSizePot2=maxSizePot2,
    )
else:
    sizeR = map(lambda x: 2**x, range(6, maxSizePot2 + 1))
    counter = CountRegionsSimple(imagep=imagep, spikeTrp=spikeTrp, sizeR=sizeR)

counterGen = counter.run(iterationsR, u0R, betaR, bR, WR, VR, thetaR, scale, offset)

regions = []
for regions_n, imageArray, uniforms, uniformsSpliced in counterGen:
    iResolution = uniforms["iResolution"]
    iResolution = (int(iResolution[0]), int(iResolution[1]))
    iterations = uniforms["iterations"]
    print(f"iResolution: {iResolution}, iterations: {iterations}")
    if imagep:
        image = Image.frombytes(
            "RGBA",
            iResolution,
            imageArray,
        )
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(
            f"images/output_size{iResolution[0]:04}_{iResolution[1]:04}_iteration{iterations:02}.png"
        )

    regions.append({"regions_n": regions_n} | uniformsSpliced)
    print(f"Regions for {uniformsSpliced}:\n{regions_n}")


with open("output.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["regions_n"] + list(uniformsSpliced.keys()))
    writer.writeheader()
    writer.writerows(regions)
