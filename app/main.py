from fastapi import FastAPI, HTTPException
from .routers import bitcoin

# Initialize FastAPI constructor
app = FastAPI()
app.include_router(bitcoin.router)
# Initialize endpoint URL



def main():
    print("Hello from timechain-backend!")

@app.get("/")
async def root():
    return {"message": "Hello World!"}


if __name__ == "__main__":
    main()
