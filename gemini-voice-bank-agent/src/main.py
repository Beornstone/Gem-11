from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent.router import router

app = FastAPI(title="Gemini Voice Bank Agent")
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/demo")
def demo_page() -> FileResponse:
    return FileResponse("static/demo.html")
