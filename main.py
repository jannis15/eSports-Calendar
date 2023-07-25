import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

import db_event_listener
import db_models
from db_handler import DBHandler, get_db
from db_session import engine
from schemas import LoginCredentials, RegistrationCredentials, OrganizationCreateSchema, TeamCreateSchema, \
    PostOrgCalendarSchema, ChangeTeamRoleSchema
from utils import hash_password, verify_password

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
db_handler = DBHandler()
db_models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")


@app.exception_handler(HTTPException)
async def exc_handle(request: Request, exc: HTTPException):
    if (request.method == 'GET') and (exc.status_code == 403):
        current_url = request.url.path
        login_url = f"/login?next={current_url}"
        return RedirectResponse(login_url)
    elif exc.status_code == 401:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    else:
        error_context = {
            "request": request,
            "error_code": exc.status_code,
            "detail": exc.detail,
        }
        return templates.TemplateResponse("error_template.html", error_context)


@app.get("/")
@app.get('/home')
async def get_home(request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    organizations = db_handler.get_user_organizations(db, user_id)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id,
        "username": db_handler.get_username_by_id(user_id, db),
        "organizations": organizations,
    })


@app.get('/org/{org_id}/calendar')
async def get_calendar_detail(org_id, request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not a member of the organization you want to visit.')

    return templates.TemplateResponse("calendar_detail.html", {
        "request": request,
        "org_id": org_id,
        "org_name": db_handler.get_org_name_by_id(db, org_id),
        "user_id": user_id,
        "calendar": db_handler.get_org_calendar_details(user_id, org_id, db),
    })


@app.post('/org/{org_id}/calendar')
async def post_calendar_details(org_id, calendar_details: PostOrgCalendarSchema, token: str = Cookie(None),
                                db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if user_id == calendar_details.memberEvents.user_id:
        db_handler.update_events_for_user(user_id, calendar_details.memberEvents.events, db)
    else:
        raise HTTPException(status_code=403, detail='You are not allowed to modify events from the provided user.')

    for team in calendar_details.teamsEvents:
        db_handler.update_events_for_team(user_id, org_id, team.team_id, team.events, db)

    db_handler.delete_unused_events(db)

    return {}


@app.get('/org/{org_id}/team-creation')
async def get_team_creation(org_id, request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not a member of the organization you want to visit.')

    return templates.TemplateResponse("create_team.html", {
        "request": request,
        "org_id": org_id,
        "org_name": db_handler.get_org_name_by_id(db, org_id),
        "user_id": user_id,
    })


@app.post('/org/{org_id}/team-creation')
async def post_team_creation(request: TeamCreateSchema, org_id, token: str = Cookie(None),
                             db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not eligible to create a team because you are not a '
                                                    'member of the organization.')

    team_id = db_handler.create_team(user_id, request.team_name, org_id, db)

    return {
        "message": "Registration successful",
        "org_id": org_id,
        "user_id": user_id,
        "team_id": team_id,
    }


@app.post('/org/{org_id}/team/{team_id}/join-team')
async def join_team(org_id, team_id, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not eligible to join a team because you are not a member '
                                                    'of the organization.')

    db_handler.add_user_to_team(user_id, team_id, org_id, user_id, db)

    return {
        "user_id": user_id,
        "message": "Team join successful",
    }


@app.post('/org/{org_id}/team/{team_id}/leave-team')
async def leave_team(org_id, team_id, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not eligible to leave a team because you are not a '
                                                    'member of the organization.')

    db_handler.delete_user_from_team(user_id, team_id, org_id, user_id, db)

    return {
        "message": "Team join successful",
        "user_id": user_id,
    }


@app.get('/org/{org_id}')
async def get_org(org_id, request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not a member of the organization you want to visit.')

    return templates.TemplateResponse("org.html", {
        "request": request,
        "org_id": org_id,
        "org_name": db_handler.get_org_name_by_id(db, org_id),
        "user_id": user_id,
        "organization_details": db_handler.get_organization_details(org_id, db),
    })


@app.get('/org/{org_id}/team/{team_id}')
async def get_team(org_id, team_id, request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not a member of the organization you want to visit.')

    return templates.TemplateResponse("team.html", {
        "request": request,
        "org_id": org_id,
        "org_name": db_handler.get_org_name_by_id(db, org_id),
        "team_id": team_id,
        "user_id": user_id,
        "team_details": db_handler.get_team_details(db, org_id, team_id),
    })


@app.get('/org/{org_id}/team/{team_id}/team-members')
async def get_team_members(org_id, team_id, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    if not db_handler.is_user_member_of_org(db, user_id, org_id):
        raise HTTPException(status_code=403, detail='You are not a member of the organization you want to visit.')

    team_members = db_handler.get_team_members(db, org_id, team_id)

    return {
        "user_id": user_id,
        "team_members": team_members,
    }


@app.post('/org/{org_id}/team/{team_id}/change-team-role')
async def change_team_role(org_id, team_id, schema: ChangeTeamRoleSchema, token: str = Cookie(None),
                           db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)

    db_handler.change_team_role(db, org_id, team_id, user_id, schema)
    team_members = db_handler.get_team_members(db, org_id, team_id)

    return {
        "user_id": user_id,
        "team_members": team_members,
    }


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
    db_handler.add_user_to_organization(db, user_id, '3079534e670845e7b5a129e6ddb5bd6e')
    return {
        "message": "Registration successful",
        "user_id": user_id,
    }


@app.get("/admin")
async def get_org_creation(request: Request, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    username = db_handler.get_username_by_id(user_id, db)
    if username == 'admin':
        return templates.TemplateResponse("admin.html", {"request": request})
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
            "org_id": org_id,
        }
    else:
        raise HTTPException(status_code=403, detail='Only the admin can create an organization.')


@app.get("/invite/{invite_id}")
async def get_invite(invite_id, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    org_id, team_id = db_handler.use_invite(db, invite_id, user_id)
    redirect_url = f"/org/{org_id}/team/{team_id}"
    response = RedirectResponse(url=redirect_url)
    return response


@app.post('/org/{org_id}/team/{team_id}/generate-invite')
async def generate_invite(org_id, team_id, token: str = Cookie(None), db: DBSession = Depends(get_db)):
    user_id = db_handler.verify_user_session(db, token)
    invite_id = db_handler.generate_invite(db, org_id, team_id, user_id)

    return {
        "invite_id": invite_id,
    }

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
