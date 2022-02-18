from dataclasses import dataclass
from typing import NewType

Colour = NewType('Colour', tuple[float, float, float, float])


@dataclass(frozen=True)
class SurfProp:
    A: float
    """
    This value in the range 0...1 defines the intensity of the surface’s ambient colour,
    as a proportion of the surface’s specified colour.
    """
    D: float
    """
    This value in the range 0...1 sets the diffuse reflectivity of the object’s surface, as
    a proportion of the surface’s specified colour.
    """
    S: float
    """
    This value in the range 0...1 specifies the specular reflectance of the object sur-
    face. Specular reflectance is assumed to be uniform over the colour spectrum
    """
    SE: int
    """
    This value in the range 0...128 specifies the specular scattering exponent of the
    material. The higher the value, the smoother the surface appearance and the more
    focused the specular highlight.
    """
    T: float
    """
    This value in the range 0...1 specifies the transparency of the surface. This value
    may be ignored in many implementations, depending on the graphics library in
    use and the capabilities of the graphics controller.
    """
