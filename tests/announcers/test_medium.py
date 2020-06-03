import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from freezegun import freeze_time
from nefelibata.announcers.medium import MediumAnnouncer

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_announcer(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, Medium!
        keywords: test
        summary: My first Medium post
        announce-on: medium

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MediumAnnouncer(root, config, "token", "public")

    requests_mock.get(
        "https://api.medium.com/v1/me", json={"data": {"id": 1}},
    )
    mock_post = requests_mock.post(
        "https://api.medium.com/v1/users/1/posts",
        json={"data": {"url": "https://medium.com/@user/12345"}},
    )

    url = announcer.announce(post)
    assert url == "https://medium.com/@user/12345"
    assert urllib.parse.parse_qs(mock_post.last_request.text) == {
        "canonicalUrl": ["https://blog.example.com/first/index.html"],
        "content": ["<p>Hi, there!</p>"],
        "contentFormat": ["html"],
        "publishStatus": ["public"],
        "tags": ["test"],
        "title": ["Hello, Medium!"],
    }

    post.parsed["medium-url"] = "https://medium.com/@user/12345"

    comments = {
        "success": True,
        "payload": {
            "value": [
                {
                    "id": "f6ef329e473b",
                    "versionId": "47cbe38f39fa",
                    "creatorId": "702bc7b1e1f2",
                    "homeCollectionId": "",
                    "title": "Testing.",
                    "detectedLanguage": "un",
                    "latestVersion": "47cbe38f39fa",
                    "latestPublishedVersion": "47cbe38f39fa",
                    "hasUnpublishedEdits": False,
                    "latestRev": 4,
                    "createdAt": 1590375977885,
                    "updatedAt": 1590375978662,
                    "acceptedAt": 0,
                    "firstPublishedAt": 1590375978427,
                    "latestPublishedAt": 1590375978427,
                    "vote": False,
                    "experimentalCss": "",
                    "displayAuthor": "",
                    "content": {"postDisplay": {"coverless": True}},
                    "virtuals": {
                        "allowNotes": True,
                        "previewImage": {
                            "imageId": "",
                            "filter": "",
                            "backgroundSize": "",
                            "originalWidth": 0,
                            "originalHeight": 0,
                            "strategy": "resample",
                            "height": 0,
                            "width": 0,
                        },
                        "wordCount": 1,
                        "imageCount": 0,
                        "readingTime": 0.0037735849056603774,
                        "subtitle": "",
                        "usersBySocialRecommends": [],
                        "noIndex": False,
                        "recommends": 0,
                        "isBookmarked": False,
                        "tags": [],
                        "socialRecommendsCount": 0,
                        "responsesCreatedCount": 0,
                        "links": {
                            "entries": [],
                            "version": "0.3",
                            "generatedAt": 1590375978622,
                        },
                        "isLockedPreviewOnly": False,
                        "metaDescription": "",
                        "totalClapCount": 0,
                        "sectionCount": 1,
                        "readingList": 0,
                        "topics": [],
                    },
                    "coverless": True,
                    "slug": "testing",
                    "translationSourcePostId": "",
                    "translationSourceCreatorId": "",
                    "isApprovedTranslation": False,
                    "inResponseToPostId": "fc7dc73166a2",
                    "inResponseToRemovedAt": 0,
                    "isTitleSynthesized": True,
                    "allowResponses": True,
                    "importedUrl": "",
                    "importedPublishedAt": 0,
                    "visibility": 0,
                    "uniqueSlug": "testing-f6ef329e473b",
                    "previewContent": {
                        "bodyModel": {
                            "paragraphs": [
                                {
                                    "name": "07c0",
                                    "type": 1,
                                    "text": "Testing.",
                                    "markups": [],
                                    "alignment": 1,
                                },
                            ],
                            "sections": [{"startIndex": 0}],
                        },
                        "isFullContent": True,
                        "subtitle": "",
                    },
                    "license": 0,
                    "inResponseToMediaResourceId": "6f4c7e236677c3fdf8969c13e58f3ac9",
                    "canonicalUrl": "",
                    "approvedHomeCollectionId": "",
                    "newsletterId": "",
                    "webCanonicalUrl": "",
                    "mediumUrl": "",
                    "migrationId": "",
                    "notifyFollowers": True,
                    "notifyTwitter": False,
                    "notifyFacebook": False,
                    "responseHiddenOnParentPostAt": 0,
                    "isSeries": False,
                    "isSubscriptionLocked": False,
                    "seriesLastAppendedAt": 0,
                    "audioVersionDurationSec": 0,
                    "sequenceId": "",
                    "isEligibleForRevenue": False,
                    "isBlockedFromHightower": False,
                    "deletedAt": 0,
                    "lockedPostSource": 0,
                    "hightowerMinimumGuaranteeStartsAt": 0,
                    "hightowerMinimumGuaranteeEndsAt": 0,
                    "featureLockRequestAcceptedAt": 0,
                    "mongerRequestType": 1,
                    "layerCake": 0,
                    "socialTitle": "",
                    "socialDek": "",
                    "editorialPreviewTitle": "",
                    "editorialPreviewDek": "",
                    "curationEligibleAt": 0,
                    "isProxyPost": False,
                    "proxyPostFaviconUrl": "",
                    "proxyPostProviderName": "",
                    "proxyPostType": 0,
                    "isSuspended": False,
                    "isLimitedState": False,
                    "seoTitle": "",
                    "previewContent2": {
                        "bodyModel": {
                            "paragraphs": [
                                {
                                    "name": "07c0",
                                    "type": 1,
                                    "text": "Testing.",
                                    "markups": [],
                                },
                            ],
                            "sections": [{"startIndex": 0}],
                        },
                        "isFullContent": True,
                        "subtitle": "",
                    },
                    "cardType": 0,
                    "isDistributionAlertDismissed": False,
                    "isShortform": False,
                    "shortformType": 0,
                    "type": "Post",
                },
            ],
            "references": {
                "User": {
                    "702bc7b1e1f2": {
                        "userId": "702bc7b1e1f2",
                        "name": "Beto Dealmeida",
                        "username": "betodealmeida",
                        "createdAt": 1404672231924,
                        "imageId": "0*vp08cv2-BUz9Ry8r.jpg",
                        "backgroundImageId": "",
                        "bio": "I like building, inventing and fixing things.",
                        "twitterScreenName": "",
                        "allowNotes": 1,
                        "mediumMemberAt": 0,
                        "isWriterProgramEnrolled": True,
                        "isSuspended": False,
                        "isMembershipTrialEligible": True,
                        "optOutOfIceland": False,
                        "type": "User",
                    },
                },
                "MediaResource": {
                    "6f4c7e236677c3fdf8969c13e58f3ac9": {
                        "mediaResourceId": "6f4c7e236677c3fdf8969c13e58f3ac9",
                        "mediaResourceType": "MediaResourceMediumPost",
                        "href": "https://medium.com/@betodealmeida/medium-integration-fc7dc73166a2",
                        "domain": "medium.com",
                        "title": "Medium integration",
                        "description": "",
                        "iframeWidth": 0,
                        "iframeHeight": 0,
                        "iframeSrc": "",
                        "thumbnailUrl": "",
                        "thumbnailWidth": 0,
                        "thumbnailHeight": 0,
                        "display": 1,
                        "thumbnailImageId": "",
                        "authorName": "",
                        "mediumPost": {"postId": "fc7dc73166a2"},
                        "type": "MediaResource",
                    },
                },
                "Post": {
                    "fc7dc73166a2": {
                        "id": "fc7dc73166a2",
                        "versionId": "50de1743bb88",
                        "creatorId": "702bc7b1e1f2",
                        "homeCollectionId": "",
                        "title": "Medium integration",
                        "detectedLanguage": "en",
                        "latestVersion": "50de1743bb88",
                        "latestPublishedVersion": "50de1743bb88",
                        "hasUnpublishedEdits": False,
                        "latestRev": 4,
                        "createdAt": 1590374323943,
                        "updatedAt": 1590374744556,
                        "acceptedAt": 0,
                        "firstPublishedAt": 1590374744316,
                        "latestPublishedAt": 1590374744316,
                        "vote": False,
                        "experimentalCss": "",
                        "displayAuthor": "",
                        "content": {
                            "subtitle": "Italic. Bold.",
                            "postDisplay": {"coverless": True},
                        },
                        "virtuals": {
                            "allowNotes": True,
                            "previewImage": {
                                "imageId": "",
                                "filter": "",
                                "backgroundSize": "",
                                "originalWidth": 0,
                                "originalHeight": 0,
                                "strategy": "resample",
                                "height": 0,
                                "width": 0,
                            },
                            "wordCount": 26,
                            "imageCount": 0,
                            "readingTime": 0.09811320754716982,
                            "subtitle": "Italic. Bold.",
                            "usersBySocialRecommends": [],
                            "noIndex": False,
                            "recommends": 0,
                            "isBookmarked": False,
                            "tags": [
                                {
                                    "slug": "medium",
                                    "name": "Medium",
                                    "postCount": 11140,
                                    "metadata": {
                                        "postCount": 11140,
                                        "coverImage": {
                                            "id": "0*if1co4LjFZ0HKHSH",
                                            "originalWidth": 5760,
                                            "originalHeight": 3840,
                                            "isFeatured": True,
                                            "unsplashPhotoId": "zJDqiEGUCHY",
                                        },
                                    },
                                    "type": "Tag",
                                },
                                {
                                    "slug": "blog",
                                    "name": "Blog",
                                    "postCount": 63298,
                                    "metadata": {
                                        "postCount": 63298,
                                        "coverImage": {
                                            "id": "0*DaafgJYBfla2Xd4w",
                                            "originalWidth": 4787,
                                            "originalHeight": 3191,
                                            "isFeatured": True,
                                            "unsplashPhotoId": "fDsCIIGdw9g",
                                        },
                                    },
                                    "type": "Tag",
                                },
                                {
                                    "slug": "nefelibata",
                                    "name": "Nefelibata",
                                    "postCount": 5,
                                    "metadata": {
                                        "postCount": 5,
                                        "coverImage": {
                                            "id": "1*wgAVpf-fg6b15vwOkKWBgw.jpeg",
                                            "originalWidth": 2256,
                                            "originalHeight": 1504,
                                            "isFeatured": True,
                                        },
                                    },
                                    "type": "Tag",
                                },
                                {
                                    "slug": "python",
                                    "name": "Python",
                                    "postCount": 51218,
                                    "metadata": {
                                        "postCount": 51218,
                                        "coverImage": {
                                            "id": "1*ygY3KuGOgmu5rU3ijQNRxg.jpeg",
                                            "originalWidth": 835,
                                            "originalHeight": 265,
                                        },
                                    },
                                    "type": "Tag",
                                },
                                {
                                    "slug": "indieweb",
                                    "name": "Indieweb",
                                    "postCount": 146,
                                    "metadata": {
                                        "postCount": 146,
                                        "coverImage": {
                                            "id": "0*mO5RDg-sdOHnuzEU.jpg",
                                            "originalWidth": 795,
                                            "originalHeight": 748,
                                            "isFeatured": True,
                                            "externalSrc": "https://remysharp.com/images/new-comments.jpg",
                                            "alt": "Comments",
                                        },
                                    },
                                    "type": "Tag",
                                },
                            ],
                            "socialRecommendsCount": 0,
                            "responsesCreatedCount": 2,
                            "links": {
                                "entries": [
                                    {
                                        "url": "https://github.com/betodealmeida/nefelibata",
                                        "alts": [],
                                        "httpStatus": 200,
                                    },
                                ],
                                "version": "0.3",
                                "generatedAt": 1590374744986,
                            },
                            "isLockedPreviewOnly": False,
                            "metaDescription": "",
                            "totalClapCount": 0,
                            "sectionCount": 1,
                            "readingList": 0,
                            "topics": [
                                {
                                    "topicId": "322406d81cea",
                                    "slug": "writing",
                                    "createdAt": 1521567437830,
                                    "deletedAt": 0,
                                    "image": {
                                        "id": "1*QlNwBOYjMnGYgGZPtG_hhg@2x.jpeg",
                                        "originalWidth": 500,
                                        "originalHeight": 343,
                                    },
                                    "name": "Writing",
                                    "description": "Tell your story.",
                                    "relatedTopics": [],
                                    "visibility": 1,
                                    "relatedTags": [],
                                    "relatedTopicIds": [],
                                    "type": "Topic",
                                },
                            ],
                        },
                        "coverless": True,
                        "slug": "medium-integration",
                        "translationSourcePostId": "",
                        "translationSourceCreatorId": "",
                        "isApprovedTranslation": False,
                        "inResponseToPostId": "",
                        "inResponseToRemovedAt": 0,
                        "isTitleSynthesized": False,
                        "allowResponses": True,
                        "importedUrl": "",
                        "importedPublishedAt": 0,
                        "visibility": 0,
                        "uniqueSlug": "medium-integration-fc7dc73166a2",
                        "previewContent": {
                            "bodyModel": {
                                "paragraphs": [
                                    {
                                        "name": "previewTitle",
                                        "type": 3,
                                        "text": "Medium integration",
                                        "alignment": 1,
                                    },
                                    {
                                        "name": "previewSubtitle",
                                        "type": 13,
                                        "text": "Italic. Bold.",
                                        "alignment": 1,
                                    },
                                    {
                                        "name": "previewSnippet0",
                                        "type": 1,
                                        "text": "This is a test of the integration between my blog engine, Nefelibata and Medium. With it, I can choose to publish posts to Medium.",
                                        "alignment": 1,
                                    },
                                ],
                                "sections": [{"startIndex": 0}],
                            },
                            "isFullContent": True,
                            "subtitle": "Italic. Bold.",
                        },
                        "license": 0,
                        "inResponseToMediaResourceId": "",
                        "canonicalUrl": "",
                        "approvedHomeCollectionId": "",
                        "newsletterId": "",
                        "webCanonicalUrl": "https://blog.taoetc.org/medium_integration/index.html",
                        "mediumUrl": "",
                        "migrationId": "",
                        "notifyFollowers": True,
                        "notifyTwitter": False,
                        "notifyFacebook": False,
                        "responseHiddenOnParentPostAt": 0,
                        "isSeries": False,
                        "isSubscriptionLocked": False,
                        "seriesLastAppendedAt": 0,
                        "audioVersionDurationSec": 0,
                        "sequenceId": "",
                        "isEligibleForRevenue": False,
                        "isBlockedFromHightower": False,
                        "deletedAt": 0,
                        "lockedPostSource": 0,
                        "hightowerMinimumGuaranteeStartsAt": 0,
                        "hightowerMinimumGuaranteeEndsAt": 0,
                        "featureLockRequestAcceptedAt": 0,
                        "mongerRequestType": 1,
                        "layerCake": 0,
                        "socialTitle": "",
                        "socialDek": "",
                        "editorialPreviewTitle": "",
                        "editorialPreviewDek": "",
                        "curationEligibleAt": 1590374743631,
                        "isProxyPost": False,
                        "proxyPostFaviconUrl": "",
                        "proxyPostProviderName": "",
                        "proxyPostType": 0,
                        "isSuspended": False,
                        "isLimitedState": False,
                        "seoTitle": "",
                        "previewContent2": {
                            "bodyModel": {
                                "paragraphs": [
                                    {
                                        "name": "dde6",
                                        "type": 1,
                                        "text": "This is a test of the integration between my blog engine, Nefelibata and Medium. With it, I can choose to publish posts to Medium.",
                                        "markups": [
                                            {
                                                "type": 3,
                                                "start": 58,
                                                "end": 68,
                                                "href": "https://github.com/betodealmeida/nefelibata",
                                                "title": "",
                                                "rel": "",
                                                "anchorType": 0,
                                            },
                                        ],
                                    },
                                    {
                                        "name": "f6c9",
                                        "type": 1,
                                        "text": "Italic. Bold.",
                                        "markups": [
                                            {"type": 1, "start": 8, "end": 12},
                                            {"type": 2, "start": 0, "end": 6},
                                        ],
                                    },
                                ],
                                "sections": [{"startIndex": 0}],
                            },
                            "isFullContent": True,
                            "subtitle": "Italic. Bold.",
                        },
                        "cardType": 0,
                        "isDistributionAlertDismissed": False,
                        "isShortform": False,
                        "shortformType": 0,
                        "type": "Post",
                    },
                },
            },
        },
        "v": 3,
        "b": "41204-62dd32e",
    }
    payload = json.dumps(comments)
    garbled = f"])}}while(1);</x>{payload}"
    requests_mock.get("https://medium.com/p/12345/responses/?format=json", text=garbled)

    responses = announcer.collect(post)
    assert responses == [
        {
            "source": "Testing.",
            "url": "https://medium.com/p/fc7dc73166a2/responses/show",
            "color": "#333333",
            "id": "medium:f6ef329e473b",
            "timestamp": "2020-05-25T03:06:17.885000+00:00",
            "user": {
                "name": "Beto Dealmeida",
                "image": "https://miro.medium.com/fit/c/128/128/0*vp08cv2-BUz9Ry8r.jpg",
                "url": "https://medium.com/@betodealmeida",
                "description": "I like building, inventing and fixing things.",
            },
            "comment": {
                "text": "Testing.",
                "url": "https://medium.com/@betodealmeida/testing-f6ef329e473b",
            },
        },
    ]


def test_announcer_relative_links(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, Medium!
        keywords: test
        summary: My first Medium post
        announce-on: medium

        Hi, there!

        Here's a link that goes with this post: [somefile](somefile.txt)

        And I also have this one in the root: [anotherfile](/anotherfile.txt)
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MediumAnnouncer(root, config, "token", "public")

    requests_mock.get(
        "https://api.medium.com/v1/me", json={"data": {"id": 1}},
    )
    mock_post = requests_mock.post(
        "https://api.medium.com/v1/users/1/posts",
        json={"data": {"url": "https://medium.com/@user/12345"}},
    )

    url = announcer.announce(post)
    assert url == "https://medium.com/@user/12345"
    assert urllib.parse.parse_qs(mock_post.last_request.text) == {
        "title": ["Hello, Medium!"],
        "contentFormat": ["html"],
        "content": [
            '<p>Hi, there!</p>\n<p>Here\'s a link that goes with this post: <a href="https://blog.example.com/first/somefile.txt">somefile</a></p>\n<p>And I also have this one in the root: <a href="https://blog.example.com/anotherfile.txt">anotherfile</a></p>',
        ],
        "tags": ["test"],
        "canonicalUrl": ["https://blog.example.com/first/index.html"],
        "publishStatus": ["public"],
    }
