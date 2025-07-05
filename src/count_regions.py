from abc import ABC, abstractmethod


class CountRegions(ABC):
    def setUniforms(self, **kwargs):
        """Set uniforms for the shader."""
        for key, value in kwargs.items():
            if key in self.shader:
                self.shader[key] = value
            else:
                raise KeyError(f"Uniform '{key}' not found in shader.")

    @abstractmethod
    def run(self, iterationsR, u0R, betaR, bR, WR, VR, thetaR, scale, offset):
        pass
