import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from Platform.src.user_management.router import router as user_management_router
from Platform.src.problem_management.router.problem_router import router as problem_management_router
from Platform.src.core.lifespan import lifespan
from Platform.src.problem_management.router.testcasesrouter import router as testcase_management_router
from asgi_correlation_id import CorrelationIdMiddleware

from Platform.src.user_management.exceptions import *
logger = logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include user_management endpoints at the root level (no prefix)
app.include_router(user_management_router, tags=["users"])
app.include_router(testcase_management_router, tags=["test-cases"])
# ...existing code for additional middleware/routers if any...
app.include_router(problem_management_router)
# Exception handlers

@app.exception_handler(UserExistsException)
async def user_exists_exception_handler(request: Request, exc: UserExistsException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message}
    )

@app.exception_handler(UserNotFoundException)
async def user_not_found_exception_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message}
    )

@app.exception_handler(AuthenticationFailedException)
async def authentication_failed_exception_handler(request: Request, exc: AuthenticationFailedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
