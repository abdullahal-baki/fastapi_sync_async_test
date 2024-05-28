import multiprocessing
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr, constr, ValidationError
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

DATABASE_URL = "sqlite:///./messages.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key='074c12072674c95c390ee09218f355ce1d54966a589d6e90')

class FlashMessageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if 'flash_messages' in request.session:
            del request.session['flash_messages']
        return response

app.add_middleware(FlashMessageMiddleware)

templates = Jinja2Templates(directory="templates")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

class MessageForm(BaseModel):
    name: constr(min_length=1)
    last_name: constr(min_length=1)
    phone_number: constr(min_length=1)
    email: EmailStr
    content: constr(min_length=10)

def process_async_message(name, last_name, phone_number, email, content):
    db = SessionLocal()
    new_message = Message(name=name, last_name=last_name, phone_number=phone_number, email=email, content=content)
    db.add(new_message)
    db.commit()
    db.close()

def set_flash_message(request: Request, message: str):
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append(message)

def get_flash_messages(request: Request):
    return request.session.get('flash_messages', [])

@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    request.session['flash_messages'].clear()
    return templates.TemplateResponse("index.html", {"request": request, "messages": get_flash_messages(request)})


@app.get("/add_message_sync/", response_class=HTMLResponse, name="add_message_sync_get")
async def add_message_sync_get(request: Request):
    return templates.TemplateResponse("add_message_sync.html", {"request": request, "form_errors": {}})

@app.post("/add_message_sync/", response_class=HTMLResponse, name="add_message_sync_post")
async def add_message_sync_post(request: Request, name: str = Form(...), last_name: str = Form(...), phone_number: str = Form(...), email: str = Form(...), content: str = Form(...)):
    form_errors = {}
    try:
        form = MessageForm(name=name, last_name=last_name, phone_number=phone_number, email=email, content=content)
        db = SessionLocal()
        new_message = Message(name=form.name, last_name=form.last_name, phone_number=form.phone_number, email=form.email, content=form.content)
        db.add(new_message)
        db.commit()
        db.close()
        set_flash_message(request, "Message added successfully!")
        
        return templates.TemplateResponse("index.html", {"request": request, "messages": get_flash_messages(request)})
    except ValidationError as e:
        # print("error", e)
        form_errors = e.errors()
        print(form_errors)
        return templates.TemplateResponse("add_message_sync.html", {"request": request, "form_errors": form_errors[0]})


@app.get("/add_message_async/", response_class=HTMLResponse, name="add_message_async_get")
async def add_message_async_get(request: Request):
    return templates.TemplateResponse("add_message_async.html", {"request": request, "form_errors": {}})


@app.post("/add_message_async/", name="add_message_async_post")  
async def add_message_async_post(request: Request, name: str = Form(...), last_name: str = Form(...), phone_number: str = Form(...), email: str = Form(...), content: str = Form(...)):
    try:
        form = MessageForm(name=name, last_name=last_name, phone_number=phone_number, email=email, content=content)
        t = multiprocessing.Process(target=process_async_message, args=(form.name, form.last_name, form.phone_number, form.email, form.content))
        t.start()
        return JSONResponse({"message": "Message sent asynchronously!"}, status_code=200)
    except ValidationError as e:
        return JSONResponse({"errors": e.errors()[0]}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
