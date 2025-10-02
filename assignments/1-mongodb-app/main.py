from fastapi import FastAPI

def main():
    print("Hello from 1-mongodb-app!")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    main()