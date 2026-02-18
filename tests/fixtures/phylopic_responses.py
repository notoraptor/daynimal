"""
Mock responses for PhyloPic API tests.
"""

# Resolve GBIF key → PhyloPic node
PHYLOPIC_RESOLVE_SUCCESS = {
    "_links": {"self": {"href": "/nodes/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}}
}

# Node with embedded primary image (CC0 license)
PHYLOPIC_NODE_WITH_IMAGE = {
    "_links": {"self": {"href": "/nodes/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}},
    "_embedded": {
        "primaryImage": {
            "_links": {
                "self": {"href": "/images/11111111-2222-3333-4444-555555555555"},
                "license": {
                    "href": "https://creativecommons.org/publicdomain/zero/1.0/"
                },
                "rasterFiles": [
                    {
                        "href": "https://images.phylopic.org/images/11111111-2222-3333-4444-555555555555/raster/1536x703.png",
                        "sizes": "1536x703",
                        "type": "image/png",
                    },
                    {
                        "href": "https://images.phylopic.org/images/11111111-2222-3333-4444-555555555555/raster/1024x469.png",
                        "sizes": "1024x469",
                        "type": "image/png",
                    },
                ],
                "thumbnailFiles": [
                    {
                        "href": "https://images.phylopic.org/images/11111111-2222-3333-4444-555555555555/thumbnail/192x192.png",
                        "sizes": "192x192",
                        "type": "image/png",
                    },
                    {
                        "href": "https://images.phylopic.org/images/11111111-2222-3333-4444-555555555555/thumbnail/64x64.png",
                        "sizes": "64x64",
                        "type": "image/png",
                    },
                ],
            },
            "attribution": "T. Michael Keesey",
        }
    },
}

# Node with NC-licensed image (should be rejected)
PHYLOPIC_NODE_NC_IMAGE = {
    "_links": {"self": {"href": "/nodes/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}},
    "_embedded": {
        "primaryImage": {
            "_links": {
                "self": {"href": "/images/11111111-2222-3333-4444-555555555555"},
                "license": {
                    "href": "https://creativecommons.org/licenses/by-nc-sa/3.0/"
                },
                "rasterFiles": [
                    {
                        "href": "https://images.phylopic.org/images/11111111-2222-3333-4444-555555555555/raster/512x512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                    }
                ],
                "thumbnailFiles": [
                    {
                        "href": "https://images.phylopic.org/images/11111111-2222-3333-4444-555555555555/thumbnail/64x64.png",
                        "sizes": "64x64",
                        "type": "image/png",
                    }
                ],
            },
            "attribution": "Restricted Author",
        }
    },
}

# Node without primary image
PHYLOPIC_NODE_NO_IMAGE = {
    "_links": {"self": {"href": "/nodes/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}},
    "_embedded": {},
}

# CC-BY licensed image
PHYLOPIC_NODE_CC_BY_IMAGE = {
    "_links": {"self": {"href": "/nodes/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}},
    "_embedded": {
        "primaryImage": {
            "_links": {
                "self": {"href": "/images/aaaabbbb-cccc-dddd-eeee-ffffffffffff"},
                "license": {"href": "https://creativecommons.org/licenses/by/4.0/"},
                "rasterFiles": [
                    {
                        "href": "https://images.phylopic.org/images/aaaabbbb-cccc-dddd-eeee-ffffffffffff/raster/800x600.png",
                        "sizes": "800x600",
                        "type": "image/png",
                    }
                ],
                "thumbnailFiles": [
                    {
                        "href": "https://images.phylopic.org/images/aaaabbbb-cccc-dddd-eeee-ffffffffffff/thumbnail/128x128.png",
                        "sizes": "128x128",
                        "type": "image/png",
                    }
                ],
            },
            "attribution": "CC-BY Artist",
        }
    },
}
