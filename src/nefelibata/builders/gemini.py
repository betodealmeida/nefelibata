"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
# pylint: disable=unused-argument, no-self-use

import logging
from pathlib import Path
from typing import Any, Iterator, List, Tuple, cast

from marko import Markdown
from marko.block import (
    BlankLine,
    CodeBlock,
    FencedCode,
    Heading,
    LinkRefDef,
    List as List_,
    ListItem,
    Paragraph,
    Quote,
    ThematicBreak,
)
from marko.element import Element
from marko.inline import AutoLink, Image, Link, RawText
from marko.renderer import Renderer

from nefelibata.builders.base import Builder
from nefelibata.config import Config

_logger = logging.getLogger(__name__)


def extract_links(paragraph: Paragraph) -> Iterator[Link]:
    """
    Extract links from a paragraph.
    """
    queue = [paragraph]
    while queue:
        element = queue.pop(0)

        if isinstance(element, (Link, AutoLink)):
            yield element
        elif hasattr(element, "children"):
            queue.extend(element.children)


class GeminiRenderer(Renderer):

    """
    Render Markdown to Gemtext.
    """

    def __init__(
        self,
        index_links: bool = False,
        link_index_start: int = 0,
        links_at_footer: bool = True,
    ) -> None:
        super().__init__()

        self.index_links = index_links
        self.link_index = self.link_index_start = link_index_start
        self.links_at_footer = links_at_footer

        # store links to show them at the footer of the document
        self.links: List[Link] = []

    def render_document(self, element: Element) -> str:
        """
        Render the document.
        """
        rendered = self.render_children(element)

        if self.links and self.links_at_footer:
            formatted_links = "\n".join(
                self.render_paragraph_link(link, self.link_index_start + i)
                for i, link in enumerate(self.links)
            )
            rendered = f"{rendered}\n{formatted_links}\n"

        return rendered

    def render_children(self, element: Element) -> str:
        """
        Render children.

        Dummy method to help with type annotations.
        """
        if isinstance(element, str):
            return element

        return cast(str, super().render_children(element))

    def render_thematic_break(self, element: ThematicBreak) -> str:
        """
        Render a ``---``.
        """
        return "—\n"

    def render_paragraph(self, element: Paragraph) -> str:
        """
        Render a paragraph.

        Links are collected and displayed after the paragraph.
        """
        paragraph = self.render_children(element) + "\n"

        links = list(extract_links(element))
        self.links.extend(links)

        if not links or self.links_at_footer:
            return paragraph

        formatted_links = "\n".join(
            self.render_paragraph_link(link, self.link_index - len(links) + i)
            for i, link in enumerate(links)
        )

        return f"{paragraph}\n{formatted_links}\n"

    def render_paragraph_link(self, element: Link, index: int) -> str:
        """
        Render links after a paragraph.
        """
        link_index = f"[{index}] " if self.index_links else ""
        if element.title:
            return f"=> {element.dest} {link_index}{element.title}"

        return f"=> {element.dest} {link_index}{self.render_children(element)}"

    def render_link(self, element: Link) -> str:
        """
        Render a link.
        """
        rendered = self.render_children(element)
        link = f"{rendered} [{self.link_index}]" if self.index_links else rendered
        self.link_index += 1

        return link

    def render_link_ref_def(self, element: LinkRefDef) -> str:
        """
        Render a link reference definition.
        """
        return ""

    def render_list(self, element: List_) -> str:
        """
        Render a list.
        """
        return self.render_children(element)

    def render_list_item(self, element: ListItem) -> str:
        """
        Render a list item.
        """
        return "* " + self.render_children(element)

    def render_quote(self, element: Quote) -> str:
        """
        Render a blockquote.
        """
        return "\n".join(
            f"> {line}" if line else ""
            for line in self.render_children(element).split("\n")
        )

    def render_fenced_code(self, element: FencedCode) -> str:
        """
        Render code inside triple backticks.
        """
        return "```\n" + self.render_children(element) + "```\n"

    def render_code_block(self, element: CodeBlock) -> str:
        """
        Render code indented by 4 spaces.
        """
        return "```\n" + self.render_children(element) + "```\n"

    def render_heading(self, element: Heading) -> str:
        """
        Render heading.

        The maximum level is 3.
        """
        level: int = min(element.level, 3)
        return "#" * level + " " + self.render_children(element) + "\n"

    render_setext_heading = render_heading

    def render_image(self, element: Image) -> str:
        """
        Render an image.
        """
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_blank_line(self, element: BlankLine) -> str:
        """
        Render a blank line.
        """
        return "\n"

    render_line_break = render_blank_line

    def render_raw_text(self, element: RawText) -> str:
        """
        Render raw text.
        """
        return str(element.children)

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
        gemini = Markdown(renderer=GeminiRenderer)
        return str(gemini.convert(content).strip())
