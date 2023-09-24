from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from dataproperty import Align
from tcolorpy import Color, tcolor

from ._font import FontSize, FontStyle, FontWeight
from ._style import DecorationLine, Style, ThousandSeparator
from ._styler_interface import StylerInterface


if TYPE_CHECKING:
    from ..writer._table_writer import AbstractTableWriter


_align_char_mapping: Dict[Align, str] = {
    Align.AUTO: "<",
    Align.LEFT: "<",
    Align.RIGHT: ">",
    Align.CENTER: "^",
}


def get_align_char(align: Align) -> str:
    return _align_char_mapping[align]


def _to_latex_rgb(color: Color, value: str) -> str:
    return r"\textcolor{" + color.color_code + "}{" + value + "}"


class AbstractStyler(StylerInterface):
    def __init__(self, writer: "AbstractTableWriter") -> None:
        self._writer = writer
        self._font_size_map = self._get_font_size_map()

    def get_font_size(self, style: Style) -> Optional[str]:
        return self._font_size_map.get(style.font_size)

    def get_additional_char_width(self, style: Style) -> int:
        return 0

    def apply(self, value: Any, style: Style) -> str:
        return value

    def apply_align(self, value: str, style: Style) -> str:
        return value

    def apply_terminal_style(self, value: str, style: Style) -> str:
        return value

    def _get_font_size_map(self) -> Dict[FontSize, str]:
        return {}


class NullStyler(AbstractStyler):
    def get_font_size(self, style: Style) -> Optional[str]:
        return ""


class TextStyler(AbstractStyler):
    def apply_terminal_style(self, value: str, style: Style) -> str:
        if not self._writer.enable_ansi_escape:
            return value

        ansi_styles = []

        if style.decoration_line in (DecorationLine.STRIKE, DecorationLine.LINE_THROUGH):
            ansi_styles.append("strike")
        if style.decoration_line == DecorationLine.UNDERLINE:
            ansi_styles.append("underline")

        if style.font_weight == FontWeight.BOLD:
            ansi_styles.append("bold")

        if self._writer.colorize_terminal:
            return tcolor(value, color=style.color, bg_color=style.bg_color, styles=ansi_styles)

        return tcolor(value, styles=ansi_styles)

    def __get_align_format(self, style: Style) -> str:
        align_char = get_align_char(style.align)
        format_items = ["{:" + align_char]
        if style.padding is not None and style.padding > 0:
            format_items.append(str(style.padding))
        format_items.append("s}")

        return "".join(format_items)

    def apply_align(self, value: str, style: Style) -> str:
        return self.__get_align_format(style).format(value)

    def apply(self, value: str, style: Style) -> str:
        if value:
            if style.thousand_separator == ThousandSeparator.SPACE:
                value = value.replace(",", " ")
            elif style.thousand_separator == ThousandSeparator.UNDERSCORE:
                value = value.replace(",", "_")

        return value


class HtmlStyler(TextStyler):
    def _get_font_size_map(self) -> Dict[FontSize, str]:
        return {
            FontSize.TINY: "font-size:x-small",
            FontSize.SMALL: "font-size:small",
            FontSize.MEDIUM: "font-size:medium",
            FontSize.LARGE: "font-size:large",
        }


class LatexStyler(TextStyler):
    class Command:
        BOLD = r"\bf"
        ITALIC = r"\it"
        TYPEWRITER = r"\tt"
        UNDERLINE = r"\underline"
        STRIKEOUT = r"\sout"

    def get_additional_char_width(self, style: Style) -> int:
        width = 0
        CURLY_BRACES_LEN = 2

        if self.get_font_size(style):
            width += len(cast(str, self.get_font_size(style))) + CURLY_BRACES_LEN

        if style.font_weight == FontWeight.BOLD:
            width += len(self.Command.BOLD) + CURLY_BRACES_LEN

        if style.font_style != FontStyle.NORMAL:
            width += 3 + CURLY_BRACES_LEN

        return width

    def apply(self, value: Any, style: Style) -> str:
        value = super().apply(value, style)
        if not value:
            return value

        font_size = self.get_font_size(style)
        commands = []

        if font_size:
            commands.append(font_size)

        if style.font_weight == FontWeight.BOLD:
            commands.append(self.Command.BOLD)

        if style.font_style == FontStyle.ITALIC:
            commands.append(self.Command.ITALIC)
        elif style.font_style == FontStyle.TYPEWRITER:
            commands.append(self.Command.TYPEWRITER)

        if style.decoration_line in (DecorationLine.STRIKE, DecorationLine.LINE_THROUGH):
            commands.append(self.Command.STRIKEOUT)
        elif style.decoration_line == DecorationLine.UNDERLINE:
            commands.append(self.Command.UNDERLINE)

        for cmd in commands:
            value = cmd + "{" + value + "}"

        value = self.__apply_color(value, style)

        return value

    def __apply_color(self, value: str, style: Style) -> str:
        if not style.fg_color:
            return value

        value = _to_latex_rgb(style.fg_color, value)

        return value

    def _get_font_size_map(self) -> Dict[FontSize, str]:
        return {
            FontSize.TINY: r"\tiny",
            FontSize.SMALL: r"\small",
            FontSize.MEDIUM: r"\normalsize",
            FontSize.LARGE: r"\large",
        }


class MarkdownStyler(TextStyler):
    def get_additional_char_width(self, style: Style) -> int:
        width = 0

        if style.font_weight == FontWeight.BOLD:
            width += 4

        if style.font_style == FontStyle.ITALIC:
            width += 2

        return width

    def apply(self, value: Any, style: Style) -> str:
        value = super().apply(value, style)
        if not value:
            return value

        if style.font_weight == FontWeight.BOLD:
            value = f"**{value}**"

        if style.font_style == FontStyle.ITALIC:
            value = f"_{value}_"

        return value


class GFMarkdownStyler(MarkdownStyler):
    """
    A styler class for GitHub Flavored Markdown
    """

    def get_additional_char_width(self, style: Style) -> int:
        width = super().get_additional_char_width(style)

        if style.decoration_line in (DecorationLine.STRIKE, DecorationLine.LINE_THROUGH):
            width += 4

        return width

    def apply(self, value: Any, style: Style) -> str:
        value = super().apply(value, style)
        if not value:
            return value

        if style.decoration_line in (DecorationLine.STRIKE, DecorationLine.LINE_THROUGH):
            value = f"~~{value}~~"

        return value


class ReStructuredTextStyler(TextStyler):
    def get_additional_char_width(self, style: Style) -> int:
        from ..writer import RstCsvTableWriter

        width = 0

        if style.font_weight == FontWeight.BOLD:
            width += 4
        elif style.font_style == FontStyle.ITALIC:
            width += 2

        if (
            style.thousand_separator == ThousandSeparator.COMMA
            and self._writer.format_name == RstCsvTableWriter.FORMAT_NAME
        ):
            width += 2

        return width

    def apply(self, value: Any, style: Style) -> str:
        from ..writer import RstCsvTableWriter

        value = super().apply(value, style)
        if not value:
            return value

        if style.font_weight == FontWeight.BOLD:
            value = f"**{value}**"
        elif style.font_style == FontStyle.ITALIC:
            # in reStructuredText, some custom style definition will be required to
            # set for both bold and italic (currently not supported)
            value = f"*{value}*"

        if (
            style.thousand_separator == ThousandSeparator.COMMA
            and self._writer.format_name == RstCsvTableWriter.FORMAT_NAME
        ):
            value = f'"{value}"'

        return value
