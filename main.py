from schemas import LoginCredentials, RegistrationCredentials, OrganizationCreateSchema
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


@app.exception_handler(HTTPException)
# todo: dont really redirect with next anymore. rethinking needed
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


# @app.get("/")
# @app.get('/home')
# async def get_home(request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
#     user_id = db_handler.verify_user_session(db, token)
#     return templates.TemplateResponse("calendar_detail.html", {
#         "request": request,
#         "user_id": user_id,
#     })


@app.get('/c')
@app.get('/c/{org_id}')
async def get_detail_home(org_id, request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not a member of the organization you want to visit.')

    return templates.TemplateResponse("calendar_detail.html", {
        "request": request,
        "user_id": user_id,
    })


@app.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def post_login(credentials: LoginCredentials, db: DBSession = Depends(get_db)):
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
    user_id = db_handler.create_user(credentials, db)
    db_handler.add_user_to_organization(db, user_id, 'acf2f88980964af9914ff1767686e05e')
    return {
        "message": "Registration successful",
        "user_id": user_id,
    }


@app.get("/org-creation")
async def get_org_creation(request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    username = db_handler.get_username_by_id(user_id, db)
    if username == 'admin':
        return templates.TemplateResponse("org_creation.html", {"request": request})
    else:
        raise HTTPException(status_code=403, detail='Only the admin can access this route.')


@app.post("/org-creation")
async def post_org(request: OrganizationCreateSchema, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    username = db_handler.get_username_by_id(user_id, db)
    if username == 'admin':
        org_id = db_handler.create_organization(user_id, request.name, db)
        return {
            "message": "Organization created successfully.",
            "organization_id": org_id,
        }
    else:
        raise HTTPException(status_code=403, detail='Only the admin can create an organization.')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
