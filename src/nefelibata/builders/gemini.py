"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
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

        if isinstance(element, marko.inline.Link):
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
        )

    def render_paragraph_link(self, element) -> str:
        """
        Render links after a paragraph.
        """
        return f"=> {element.dest} {self.render_children(element)}"

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
        return "\n```\n" + self.render_children(element) + "```\n"

    def render_heading(self, element) -> str:
        """
        Render heading.

        The maximum level is 3.
        """
        level = min(element.level, 3)
        return "#" * level + " " + self.render_children(element) + "\n"

    render_setext_heading = render_heading

    @staticmethod
    def render_blank_line(element) -> str:  # pylint: disable=unused-argument
        """
        Render a blank line.
        """
        return "\n"

    render_line_break = render_blank_line

    @staticmethod
    def render_raw_text(element) -> str:
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
        return gemini.convert(content)
