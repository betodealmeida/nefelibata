"""
The configuration of a Nefelibata blog.
"""
# pylint: disable=too-few-public-methods

from typing import Dict, List

from pydantic import BaseModel, Extra, Field


class AuthorModel(BaseModel):
    """
    Model representing the author of the blog.
    """

    name: str
    url: str
    email: str
    note: str = ""


class SocialModel(BaseModel):
    """
    Model representing links to social media presence.
    """

    title: str
    url: str


class CategoryModel(BaseModel):
    """
    Model representing a category and the associated tags.
    """

    label: str
    description: str
    tags: List[str]


class BuilderModel(BaseModel):
    """
    Model representing a Nefelibata builder.
    """

    plugin: str
    announce_on: List[str] = Field(..., alias="announce-on")
    publish_to: List[str] = Field(..., alias="publish-to")
    home: str
    path: str

    class Config:
        """
        Allow extra attributes that are builder-specific.
        """

        extra = Extra.allow


class AssistantModel(BaseModel):
    """
    Model representing a Nefelibata assistant.
    """

    plugin: str

    class Config:
        """
        Allow extra attributes that are assistant-specific.
        """

        extra = Extra.allow


class AnnouncerModel(BaseModel):
    """
    Model representing a Nefelibata announcer.
    """

    plugin: str

    class Config:
        """
        Allow extra attributes that are announcer-specific.
        """

        extra = Extra.allow


class PublisherModel(BaseModel):
    """
    Model representing a Nefelibata publisher.
    """

    plugin: str

    class Config:
        """
        Allow extra attributes that are publisher-specific.
        """

        extra = Extra.allow


class Config(BaseModel):
    """
    Model representing the blog configuration.
    """

    title: str
    subtitle: str = ""
    author: AuthorModel
    language: str

    social: List[SocialModel]
    categories: Dict[str, CategoryModel]

    templates: Dict[str, List[str]]

    builders: Dict[str, BuilderModel]
    assistants: Dict[str, AssistantModel]
    announcers: Dict[str, AnnouncerModel]
    publishers: Dict[str, PublisherModel]
