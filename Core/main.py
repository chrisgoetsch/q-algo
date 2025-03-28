from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Q Algo is live"}
