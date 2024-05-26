from __future__ import annotations

import pathlib
import warnings

import numpy as np

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.config import PATH
from gdsfactory.constants import _glyph, _indent, _width
from gdsfactory.typings import LayerSpec, LayerSpecs, PathType


@gf.cell
def text_freetype(
    text: str = "abcd",
    size: int = 10,
    justify: str = "left",
    font: PathType = PATH.font_ocr,
    layer: LayerSpec = "WG",
    layers: LayerSpecs | None = None,
) -> Component:
    """Returns text Component.

    Args:
        text: string.
        size: in um.
        justify: left, right, center.
        font: Font face to use. Default DEPLOF does not require additional libraries,
            otherwise freetype load fonts. You can choose font by name
            (e.g. "Times New Roman"), or by file OTF or TTF filepath.
        layer: list of layers to use for the text.
        layers: list of layers to use for the text.

    """
    t = Component()
    yoffset = 0
    layers = layers or [layer]

    face = font
    xoffset = 0
    if face == "DEPLOF":
        scaling = size / 1000

        for line in text.split("\n"):
            char = Component()
            for c in line:
                ascii_val = ord(c)
                if c == " ":
                    xoffset += 500 * scaling
                elif (33 <= ascii_val <= 126) or (ascii_val == 181):
                    for poly in _glyph[ascii_val]:
                        xpts = np.array(poly)[:, 0] * scaling + xoffset
                        ypts = np.array(poly)[:, 1] * scaling + yoffset
                        points = list(zip(xpts, ypts))
                        char.add_polygon(points, layer=layer)
                    xoffset += (_width[ascii_val] + _indent[ascii_val]) * scaling
                else:
                    valid_chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~µ"
                    warnings.warn(
                        f'text(): Warning, some characters ignored, no geometry for character "{chr(ascii_val)}" with ascii value {ascii_val}. Valid characters: {valid_chars}'
                    )
            ref = t.add_ref(char)
            yoffset -= 1500 * scaling
            xoffset = 0
    else:
        from gdsfactory.font import _get_font_by_file, _get_font_by_name, _get_glyph

        font_path = pathlib.Path(font)
        # Load the font. If we've passed a valid file, try to load that, otherwise search system fonts
        if font_path.is_file() and font_path.suffix in {".otf", ".ttf"}:
            font = _get_font_by_file(str(font))
        else:
            font = _get_font_by_name(font)
        if font is None:
            raise ValueError(
                f"Failed to find font: {font!r}. "
                "Try specifying the exact (full) path to the .ttf or .otf file. "
            )

        # Render each character
        for line in text.split("\n"):
            char = Component()
            xoffset = 0
            for letter in line:
                letter_dev = Component()
                letter_template, advance_x = _get_glyph(font, letter)
                for _, polygon_points in letter_template.get_polygons_points(
                    scale=size
                ).items():
                    for layer in layers:
                        for points in polygon_points:
                            letter_dev.add_polygon(points, layer=layer)
                ref = char.add_ref(letter_dev)
                ref.d.move((xoffset, 0))
                xoffset += size * advance_x

            ref = t.add_ref(char)
            ref.d.move((0, yoffset))
            yoffset -= size

    justify = justify.lower()
    for ref in t.references:
        if justify == "center":
            ref.d.move((0, 0))

        elif justify == "right":
            ref.d.xmax = 0
    t.flatten()
    return t


if __name__ == "__main__":
    c2 = text_freetype("hello")
    # print(c2.name)
    # c2 = text_freetype()
    c2.show()
