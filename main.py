from schemas import LoginCredentials, RegistrationCredentials
from utils import hash_password, verify_password
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session as DBSession
from db_handler import DBHandler, get_db
import db_models
from db_session import engine
import uvicorn
import db_event_listener

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
db_handler = DBHandler()
db_models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")


# THIS IS AWESOME!

@app.exception_handler(HTTPException)
async def exc_handle(request: Request, exc: HTTPException):
    if (request.method == 'GET') and (exc.status_code == 403):
        current_url = request.url.path
        login_url = f"/login?next={current_url}"
        return RedirectResponse(login_url)
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


@app.get("/")
@app.get('/home')
async def get_home(request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id,
    })


@app.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def post_login(response: Response, credentials: LoginCredentials, db: DBSession = Depends(get_db)):
    user_id, hashed_password = db_handler.get_user_id_and_password(db, credentials.username)
    if user_id != '' and hashed_password != '' and verify_password(credentials.password, hashed_password):
        token = db_handler.update_session(db, user_id)
        return {
            "message": "Login successful",
            "token": token,
        }
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password.")


@app.post("/logout")
async def logout(response: Response, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    db_handler.end_session(db, token)
    response.delete_cookie(key='token')
    return {'message': 'Logged out successfully'}


@app.get("/signup")
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def post_register(credentials: RegistrationCredentials, db: DBSession = Depends(get_db)):
    credentials.password = hash_password(credentials.password)
    db_handler.create_user(credentials, db)
    return {
            "message": "Registration successful",
        }

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
