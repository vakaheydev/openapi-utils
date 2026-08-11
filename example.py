from pprint import pprint

from openapi_utils import keep_openapi_operations


openapi = {
    "openapi": "3.0.3",
    "paths": {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/User"
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/CreateUserRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/User"
                                }
                            }
                        }
                    }
                },
            },
        },
        "/health": {
            "get": {
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            },
            "head": {
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            },
        },
    },
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "address": {
                        "$ref": "#/components/schemas/Address"
                    }
                },
            },
            "Address": {
                "type": "object"
            },
            "CreateUserRequest": {
                "type": "object"
            },
            "AbsolutelyUnusedSchema": {
                "type": "object"
            },
        }
    },
}


result = keep_openapi_operations(
    openapi,
    [
        ("/users", "GET"),
        ("/health", "all"),
    ],
)

pprint(result)
