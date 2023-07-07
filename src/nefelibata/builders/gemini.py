"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
# pylint: disable=unused-argument, no-self-use, missing-function-docstring, arguments-differ

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterator, Optional, Union, cast

import marko
from marko.renderer import Renderer

from nefelibata.builders.base import Builder
from nefelibata.config import Config

_logger = logging.getLogger(__name__)


def extract_links(
    paragraph,
) -> Iterator[Union[marko.inline.Link, marko.inline.AutoLink]]:
    """
    Extract links from a paragraph.
    """
    queue = [paragraph]
    while queue:
        element = queue.pop(0)

        if isinstance(element, (marko.inline.Link, marko.inline.AutoLink)):
            yield element
        elif hasattr(element, "children"):
            queue.extend(element.children)


class GemtextRenderer(Renderer):

    """
    Render Markdown to Gemtext.
    """

    def __init__(self) -> None:
        super().__init__()
        self.root_node: Optional[marko.block.Document] = None

    def render(
        self,
        element: marko.element.Element,
        append_links: bool = True,
    ) -> str:
        if self.root_node is None:
            self.root_node = cast(marko.block.Document, element)  # pragma: no cover
        if hasattr(element, "get_type"):  # pragma: no cover
            func_name = "render_" + element.get_type(snake_case=True)
            render_func = getattr(self, func_name, None)
            if render_func is not None and (
                getattr(render_func, "_force_delegate", False) or self.delegate
            ):
                return cast(str, render_func(element, append_links))
        return self.render_children(element, append_links)

    def render_children(self, element: Any, append_links: bool = True) -> str:
        if not hasattr(element, "children"):
            return str(element)

        rendered = [self.render(child, append_links) for child in element.children]
        return "".join(rendered)

    def render_paragraph(
        self,
        element: marko.block.Paragraph,
        append_links: bool = True,
    ) -> str:
        """
        Render a paragraph.

        Links are collected and displayed after the paragraph.
        """
        paragraph = self.render_children(element, append_links) + "\n"

        links = list(extract_links(element))
        if not links or not append_links:
            return paragraph

        return (
            paragraph
            + "\n"
            + "\n".join(self._render_paragraph_link(link) for link in links)
            + "\n"
        )

    def _render_paragraph_link(
        self,
        element: Union[marko.inline.Link, marko.inline.AutoLink],
    ) -> str:
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_list(self, element: marko.block.List, append_links: bool = True) -> str:
        return self.render_children(element, append_links)

    def render_list_item(
        self,
        element: marko.block.ListItem,
        append_links: bool = True,
    ) -> str:
        return "* " + self.render_children(element, append_links)

    def render_quote(
        self,
        element: marko.block.Quote,
        append_links: bool = True,
    ) -> str:
        quote = "\n".join(
            f"> {line}" if line else ""
            for line in self.render_children(element, append_links=False).split("\n")
        )

        links = list(extract_links(element))
        if not links or not append_links:
            return quote

        return (
            quote
            + "\n"
            + "\n".join(self._render_paragraph_link(link) for link in links)
            + "\n"
        )

    def render_fenced_code(
        self,
        element: marko.block.FencedCode,
        append_links: bool = True,
    ) -> str:
        """
        Render code inside triple backticks.
        """
        return "```\n" + self.render_children(element, append_links) + "```\n"

    def render_code_block(
        self,
        element: marko.block.CodeBlock,
        append_links: bool = True,
    ) -> str:
        return self.render_fenced_code(
            cast(marko.block.FencedCode, element),
            append_links,
        )

    def render_html_block(
        self,
        element: marko.block.HTMLBlock,
        append_links: bool = True,
    ) -> str:
        return self.render_fenced_code(
            cast(marko.block.FencedCode, element.body),
            append_links,
        )

    def render_thematic_break(
        self,
        element: marko.block.ThematicBreak,
        append_links: bool = True,
    ) -> str:
        return "----\n"

    def render_heading(
        self,
        element: marko.block.Heading,
        append_links: bool = True,
    ) -> str:
        level: int = min(element.level, 3)
        return "#" * level + " " + self.render_children(element, append_links) + "\n"

    def render_setext_heading(
        self,
        element: marko.block.SetextHeading,
        append_links: bool = True,
    ) -> str:
        return self.render_heading(cast(marko.block.Heading, element), append_links)

    def render_blank_line(
        self,
        element: marko.block.BlankLine,
        append_links: bool = True,
    ) -> str:
        return "\n"

    def render_link_ref_def(
        self,
        element: marko.block.LinkRefDef,
        append_links: bool = True,
    ) -> str:
        return ""

    def render_inline_html(
        self,
        element: marko.inline.InlineHTML,
        append_links: bool = True,
    ) -> str:
        return str(element.children)

    def render_image(
        self,
        element: marko.inline.Image,
        append_links: bool = True,
    ) -> str:
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_literal(
        self,
        element: marko.inline.Literal,
        append_links: bool = True,
    ) -> str:
        return str(element.children)

    def render_raw_text(
        self,
        element: marko.inline.RawText,
        append_links: bool = True,
    ) -> str:
        return str(element.children)

    def render_line_break(
        self,
        element: marko.inline.LineBreak,
        append_links: bool = True,
    ) -> str:
        return "\n"

    def render_code_span(
        self,
        element: marko.inline.CodeSpan,
        append_links: bool = True,
    ) -> str:
        return str(element.children)


class GeminiBuilder(Builder):

    """
    A builder for the Gemini protocol.
    """

    name = "gemini"
    label = "Gemini"
    extension = ".gmi"
    template_base = ""
    site_templates = ["index.gmi", "feed.gmi"]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        home: str,
        path: str = "",
        links: str = "paragraph",
        **kwargs: Any,
    ):
        super().__init__(root, config, home, path, **kwargs)
        self.links = links

        self.setup()

    def render(self, content: str) -> str:
        gemini = marko.Markdown(renderer=GemtextRenderer)
        return str(gemini.convert(content).strip())
