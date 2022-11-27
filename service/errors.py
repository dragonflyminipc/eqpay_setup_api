from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi import Request

class ErrorResponse(BaseModel):
    message: str = Field(example="Example error message")
    code: str = Field(example="example_error")

errors = {
    "general": {
        "wrong-mac": ["Wrong mac address", 400],
        "wrong-product-id": ["Wrong product id", 400],
        "not-initialised": ["Node not initialised", 400],
        "not-synced": ["Node isn't fully synced yet", 400],
        "internal-error": ["Service couldn't get the necessary data. Api or node is probably down", 500],
    },
    "init": {
        "already-initialised": ["Already initialised", 400],
        "no-node-files": ["Couldn't download node files", 500],
    },
    "update": {
        "no-node-files": ["Couldn't get the node files", 500],
    }
}

class Abort(Exception):
    def __init__(self, scope: str, message: str):
        self.scope = scope
        self.message = message

async def abort_handler(request: Request, exc: Abort):
    error_code = exc.scope.replace("-", "_") + "_" + exc.message.replace("-", "_")

    try:
        error_message = errors[exc.scope][exc.message][0]
        status_code = errors[exc.scope][exc.message][1]
    except Exception:
        error_message = "Unknown error"
        status_code = 400

    return JSONResponse(
        content={"error": {
            "message": error_message, "code": error_code
        }, "data": {}},
        status_code=status_code
    )

async def validation_handler(request: Request, exc: RequestValidationError):
    exc_str = str(exc).replace("\n", " ").replace("   ", " ")
    return JSONResponse(
        content={"error": {
            "message": exc_str, "code": "validation_error"
        }, "data": {}},
        status_code=422
    )
