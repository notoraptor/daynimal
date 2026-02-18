"""
Mock responses for GBIF Media API tests.

Contains a mix of CC-BY (accepted) and CC-BY-NC (rejected) images
to test license filtering.
"""

# Response with a mix of licenses — some commercial, some not
GBIF_MEDIA_MIXED_LICENSES = {
    "offset": 0,
    "limit": 20,
    "endOfRecords": True,
    "results": [
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/wolf1.jpg",
            "license": "http://creativecommons.org/licenses/by/4.0/",
            "rightsHolder": "John Photographer",
            "creator": "John Photographer",
            "description": "Gray wolf in the wild",
            "references": "https://www.gbif.org/occurrence/123",
        },
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/wolf2.jpg",
            "license": "http://creativecommons.org/licenses/by-nc/4.0/",
            "rightsHolder": "NC Author",
            "creator": "NC Author",
            "description": "Wolf - non commercial",
        },
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/wolf3.jpg",
            "license": "http://creativecommons.org/publicdomain/zero/1.0/",
            "rightsHolder": "Public Domain Author",
            "description": "Wolf CC0",
        },
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/wolf4.jpg",
            "license": "http://creativecommons.org/licenses/by-sa/4.0/",
            "creator": "SA Author",
            "description": "Wolf CC-BY-SA",
        },
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/wolf5.jpg",
            "license": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
            "creator": "NC-SA Author",
            "description": "Wolf NC-SA - should be rejected",
        },
        {
            "type": "Sound",
            "identifier": "https://example.com/sounds/wolf_howl.mp3",
            "license": "http://creativecommons.org/licenses/by/4.0/",
            "creator": "Sound Guy",
            "description": "Wolf howl - not a StillImage, should be filtered",
        },
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/wolf6.jpg",
            "license": "http://creativecommons.org/licenses/by-nd/4.0/",
            "creator": "ND Author",
            "description": "Wolf ND - should be rejected",
        },
    ],
}

# Response with only NC images — should return empty after filtering
GBIF_MEDIA_ALL_NC = {
    "offset": 0,
    "limit": 20,
    "endOfRecords": True,
    "results": [
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/nc1.jpg",
            "license": "http://creativecommons.org/licenses/by-nc/4.0/",
            "creator": "NC Only Author",
        },
        {
            "type": "StillImage",
            "identifier": "https://example.com/images/nc2.jpg",
            "license": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
            "creator": "NC-SA Only Author",
        },
    ],
}

# Empty response
GBIF_MEDIA_EMPTY = {"offset": 0, "limit": 20, "endOfRecords": True, "results": []}
