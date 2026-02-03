"""
Mock responses for Wikimedia Commons API.

These fixtures simulate real API responses without network calls.
"""

# Response for image info query
COMMONS_IMAGE_INFO_WOLF = {
    "query": {
        "pages": {
            "12345": {
                "pageid": 12345,
                "title": "File:Eurasian wolf 2.jpg",
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/d/d0/Eurasian_wolf_2.jpg",
                        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Eurasian_wolf_2.jpg/800px-Eurasian_wolf_2.jpg",
                        "width": 2048,
                        "height": 1365,
                        "mime": "image/jpeg",
                        "user": "Retron",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                            "Artist": {"value": "Retron"},
                            "ImageDescription": {
                                "value": "Eurasian wolf at Kolmården Zoo, Sweden"
                            },
                        },
                    }
                ],
            }
        }
    }
}

# Response for category members (images in Canis_lupus category)
COMMONS_CATEGORY_CANIS_LUPUS = {
    "query": {
        "pages": {
            "12345": {
                "title": "File:Eurasian wolf 2.jpg",
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/commons/wolf1.jpg",
                        "thumburl": "https://upload.wikimedia.org/commons/thumb/wolf1.jpg",
                        "width": 1024,
                        "height": 768,
                        "mime": "image/jpeg",
                        "user": "Photographer1",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 3.0"},
                            "Artist": {"value": "John Doe"},
                        },
                    }
                ],
            },
            "12346": {
                "title": "File:Gray wolf portrait.jpg",
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/commons/wolf2.jpg",
                        "thumburl": "https://upload.wikimedia.org/commons/thumb/wolf2.jpg",
                        "width": 800,
                        "height": 600,
                        "mime": "image/jpeg",
                        "user": "Photographer2",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC0"},
                            "Artist": {"value": "Jane Smith"},
                        },
                    }
                ],
            },
        }
    }
}

# Response for search
COMMONS_SEARCH_WOLF = {
    "query": {
        "pages": {
            "12345": {
                "title": "File:Wolf photo.jpg",
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/commons/wolf.jpg",
                        "thumburl": "https://upload.wikimedia.org/commons/thumb/wolf.jpg",
                        "width": 1024,
                        "height": 768,
                        "mime": "image/jpeg",
                        "user": "WildlifePhotographer",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY 4.0"},
                            "Artist": {"value": "Wildlife Photographer"},
                        },
                    }
                ],
            }
        }
    }
}

# Response for image not found
COMMONS_NOT_FOUND = {"query": {"pages": {"-1": {"missing": ""}}}}
