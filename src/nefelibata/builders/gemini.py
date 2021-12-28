"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
# pylint: disable=unused-argument, no-self-use

import logging
from pathlib import Path
from typing import Any, Iterator

import marko
from marko.renderer import Renderer

from nefelibata.builders.base import Builder
from nefelibata.config import Config

_logger = logging.getLogger(__name__)


def extract_links(paragraph) -> Iterator[marko.inline.Link]:
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


class GeminiRenderer(Renderer):

    """
    Render Markdown to Gemtext.
    """

    def render_paragraph(self, element) -> str:
        """
        Render a paragraph.

        Links are collected and displayed after the paragraph.
        """
        paragraph = self.render_children(element) + "\n"

        links = list(extract_links(element))
        if not links:
            return paragraph

        return (
            paragraph
            + "\n"
            + "\n".join(self.render_paragraph_link(link) for link in links)
            + "\n"
        )

    def render_paragraph_link(self, element) -> str:
        """
        Render links after a paragraph.
        """
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_link_ref_def(self, element) -> str:
        """
        Render a link reference definition.
        """
        return ""

    def render_list(self, element) -> str:
        """
        Render a list.
        """
        return self.render_children(element)

    def render_list_item(self, element) -> str:
        """
        Render a list item.
        """
        return "* " + self.render_children(element)

    def render_quote(self, element) -> str:
        """
        Render a blockquote.
        """
        return "\n".join(
            f"> {line}" if line else ""
            for line in self.render_children(element).split("\n")
        )

    def render_fenced_code(self, element) -> str:
        """
        Render code inside triple backticks.
        """
        return "```\n" + self.render_children(element) + "```\n"

    def render_heading(self, element) -> str:
        """
        Render heading.

        The maximum level is 3.
        """
        level = min(element.level, 3)
        return "#" * level + " " + self.render_children(element) + "\n"

    render_setext_heading = render_heading

    def render_image(self, element) -> str:
        """
        Render an image.
        """
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_blank_line(self, element) -> str:
        """
        Render a blank line.
        """
        return "\n"

    render_line_break = render_blank_line

    def render_raw_text(self, element) -> str:
        """
        Render raw text.
        """
        return element.children

    render_code_span = render_raw_text
    render_literal = render_raw_text
    render_inline_html = render_raw_text


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
        gemini = marko.Markdown(renderer=GeminiRenderer)
        return gemini.convert(content).strip()
