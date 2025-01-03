import uvicorn


HOST = "0.0.0.0"
PORT = 8000
LOOP = "auto"  # uvloop
RELOAD = True  # For auto-reloading in development


def start_app():
    uvicorn.run(
        "zeon:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        loop="auto",
        workers=1,
    )


if __name__ == "__main__":
    start_app()
