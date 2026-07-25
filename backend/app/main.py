from fastapi import FastAPI

app = FastAPI(title="Qeymatban API")


@app.get("/health")
def health():
    return {"status": "ok"}
