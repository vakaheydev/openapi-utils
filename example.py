from pprint import pprint

from openapi_utils import remove_openapi_operations


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
        }
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


result = remove_openapi_operations(
    openapi,
    [
        ("/users", "POST"),
    ],
)

pprint(result)
