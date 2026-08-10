import csv
import io
import os
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer, BadSignature
from passlib.context import CryptContext
from sqlalchemy import create_engine, String, Integer, Float, Date, DateTime, ForeignKey, Boolean, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/diamond_kpi.db")
# Render provides a PostgreSQL URL. Explicitly select psycopg 3 for SQLAlchemy.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
COMPANY_NAME = os.getenv("COMPANY_NAME", "晶鑽生醫")
APP_ENV = os.getenv("APP_ENV", "development")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() == "true"
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="sales")
    region: Mapped[str] = mapped_column(String(30), default="全區")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_no: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(30), default="專員")
    region: Mapped[str] = mapped_column(String(30), default="北區")
    manager: Mapped[str] = mapped_column(String(100), default="")
    monthly_target: Mapped[float] = mapped_column(Float, default=1000000)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(60), default="注射產品")
    unit: Mapped[str] = mapped_column(String(20), default="盒")
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    gross_margin: Mapped[float] = mapped_column(Float, default=0.7)
    monthly_target_qty: Mapped[float] = mapped_column(Float, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    region: Mapped[str] = mapped_column(String(30), default="北區")
    city: Mapped[str] = mapped_column(String(50), default="台北市")
    owner_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="有效客戶")
    last_order_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    owner: Mapped[Optional[Employee]] = relationship()

class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True)
    sale_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"))
    quantity: Mapped[float] = mapped_column(Float, default=1)
    amount: Mapped[float] = mapped_column(Float, default=0)
    gross_profit: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="已認列")
    note: Mapped[str] = mapped_column(String(255), default="")
    employee: Mapped[Employee] = relationship()
    product: Mapped[Product] = relationship()
    clinic: Mapped[Clinic] = relationship()

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_date: Mapped[date] = mapped_column(Date, default=date.today)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"))
    stage: Mapped[str] = mapped_column(String(30), default="拜訪")
    outcome: Mapped[str] = mapped_column(String(100), default="")
    next_action_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employee: Mapped[Employee] = relationship()
    clinic: Mapped[Clinic] = relationship()

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    username: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(100))
    entity: Mapped[str] = mapped_column(String(50))
    detail: Mapped[str] = mapped_column(String(500), default="")

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
signer = URLSafeSerializer(SECRET_KEY, salt="diamond-session")
app = FastAPI(title="Diamond KPI Enterprise")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(request: Request, db: Session = Depends(db_session)) -> User:
    token = request.cookies.get("diamond_session")
    if not token:
        raise HTTPException(401)
    try:
        data = signer.loads(token)
    except BadSignature:
        raise HTTPException(401)
    user = db.get(User, data.get("uid"))
    if not user or not user.active:
        raise HTTPException(401)
    return user


def audit(db: Session, user: User, action: str, entity: str, detail: str = ""):
    db.add(AuditLog(username=user.username, action=action, entity=entity, detail=detail[:500]))
    db.commit()


def authorize(user: User, *roles: str):
    if user.role not in roles:
        raise HTTPException(403, "權限不足")

@app.exception_handler(401)
async def unauthorized(request: Request, exc):
    return RedirectResponse("/login", status_code=303)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.scalar(select(func.count(User.id))):
            users = [
                User(username=ADMIN_USERNAME, full_name="系統管理員", password_hash=pwd.hash(ADMIN_PASSWORD), role="admin", region="全區")
            ]
            if SEED_DEMO_DATA:
                users.extend([
                    User(username="ceo", full_name="總經理", password_hash=pwd.hash("Ceo123!"), role="executive", region="全區"),
                    User(username="manager", full_name="北區經理", password_hash=pwd.hash("Manager123!"), role="manager", region="北區"),
                    User(username="sales", full_name="業務示範", password_hash=pwd.hash("Sales123!"), role="sales", region="北區"),
                ])
            db.add_all(users)
        if not db.scalar(select(func.count(Employee.id))):
            emps = [
                Employee(employee_no="E001", name="陳協理", title="協理", region="全區", monthly_target=50000000),
                Employee(employee_no="E101", name="王區經理", title="區域經理", region="北區", monthly_target=15000000),
                Employee(employee_no="E201", name="林襄理", title="襄理", region="北區", manager="王區經理", monthly_target=2500000),
                Employee(employee_no="E202", name="張主任", title="主任", region="中區", manager="陳協理", monthly_target=1800000),
                Employee(employee_no="E203", name="李專員", title="專員", region="南區", manager="陳協理", monthly_target=1000000),
            ]
            db.add_all(emps); db.flush()
            prods = [
                Product(code="MET", name="METEORA", unit="盒", unit_price=120000, gross_margin=.72, monthly_target_qty=20),
                Product(code="NEO", name="NeoFilera", unit="瓶", unit_price=80000, gross_margin=.75, monthly_target_qty=30),
                Product(code="NVB", name="NovaBright", unit="台", unit_price=0, gross_margin=.70, monthly_target_qty=0),
                Product(code="RON", name="Ronkylä", unit="盒", unit_price=60000, gross_margin=.68, monthly_target_qty=50),
                Product(code="PK", name="Pico-K", category="儀器", unit="台", unit_price=1500000, gross_margin=.55, monthly_target_qty=2),
                Product(code="PT", name="探頭系列", category="耗材", unit="支", unit_price=25000, gross_margin=.65, monthly_target_qty=80),
            ]
            db.add_all(prods); db.flush()
            clinics = [Clinic(code=f"C{i:03d}", name=n, region=r, city=c, owner_employee_id=emps[min(i-1,4)].id) for i,(n,r,c) in enumerate([
                ("晶采醫美診所","北區","台北市"),("澄美醫美診所","北區","新北市"),("璞研診所","中區","台中市"),("雅緻醫美診所","南區","高雄市"),("悅容診所","南區","台南市")],1)]
            db.add_all(clinics); db.flush()
            today=date.today()
            demo_sales=[
                (emps[2],prods[0],clinics[0],12,1440000),(emps[2],prods[1],clinics[1],18,1440000),
                (emps[3],prods[2],clinics[2],24,1440000),(emps[4],prods[4],clinics[3],38,950000),
                (emps[1],prods[3],clinics[0],1,1500000),(emps[0],prods[0],clinics[4],8,960000),
            ]
            for e,p,c,q,a in demo_sales:
                db.add(Sale(sale_date=today, employee_id=e.id, product_id=p.id, clinic_id=c.id, quantity=q, amount=a, gross_profit=a*p.gross_margin))
            stages=["拜訪","拜訪","提案","報價","成交","回購","拜訪","提案"]
            for i,st in enumerate(stages):
                db.add(Activity(activity_date=today, employee_id=emps[i%len(emps)].id, clinic_id=clinics[i%len(clinics)].id, stage=st, outcome="示範資料"))
        # Ensure NovaBright is present even on an existing Render/PostgreSQL database.
        if not db.scalar(select(Product).where(Product.code == "NVB")):
            db.add(Product(code="NVB", name="NovaBright", category="設備", unit="台", unit_price=0, gross_margin=.70, monthly_target_qty=0, active=True))
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "diamond-kpi"}

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "company": COMPANY_NAME})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.username == username))
    if not user or not pwd.verify(password, user.password_hash):
        return RedirectResponse("/login?error=1", status_code=303)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        "diamond_session",
        signer.dumps({"uid": user.id}),
        httponly=True,
        secure=(APP_ENV == "production"),
        samesite="lax",
        max_age=28800,
    )
    return response

@app.get("/logout")
def logout():
    r=RedirectResponse("/login",303); r.delete_cookie("diamond_session"); return r


def dashboard_context(db: Session, user: User):
    month_start = date.today().replace(day=1)
    sales_query = select(Sale).where(Sale.sale_date >= month_start)
    if user.role in ("manager", "sales"):
        sales_query = sales_query.join(Employee).where(Employee.region == user.region)
    sales = list(db.scalars(sales_query))
    revenue=sum(s.amount for s in sales); gp=sum(s.gross_profit for s in sales)
    emps=list(db.scalars(select(Employee).where(Employee.active == True)))
    if user.role in ("manager","sales"):
        emps=[e for e in emps if e.region==user.region]
    target=sum(e.monthly_target for e in emps)
    by_emp=[]
    for e in emps:
        amt=sum(s.amount for s in sales if s.employee_id==e.id)
        by_emp.append({"id":e.id,"name":e.name,"title":e.title,"region":e.region,"amount":amt,"target":e.monthly_target,"rate":(amt/e.monthly_target*100 if e.monthly_target else 0)})
    by_emp.sort(key=lambda x:x["rate"], reverse=True)
    products=list(db.scalars(select(Product).where(Product.active == True)))
    by_product=[]
    for p in products:
        qty=sum(s.quantity for s in sales if s.product_id==p.id); amt=sum(s.amount for s in sales if s.product_id==p.id)
        by_product.append({"name":p.name,"qty":qty,"target":p.monthly_target_qty,"amount":amt,"rate":qty/p.monthly_target_qty*100 if p.monthly_target_qty else 0})
    activities=list(db.scalars(select(Activity).where(Activity.activity_date>=month_start)))
    funnel={stage:sum(1 for a in activities if a.stage==stage) for stage in ["拜訪","提案","報價","成交","回購"]}
    regions=[]
    for r in ["北區","中區","南區"]:
        rs=[s for s in sales if s.employee.region==r]; rt=sum(e.monthly_target for e in emps if e.region==r)
        regions.append({"name":r,"amount":sum(s.amount for s in rs),"target":rt,"rate":sum(s.amount for s in rs)/rt*100 if rt else 0})
    return {"revenue":revenue,"gp":gp,"margin":gp/revenue*100 if revenue else 0,"target":target,"rate":revenue/target*100 if target else 0,"forecast":revenue/max(date.today().day,1)*30,"by_emp":by_emp,"by_product":by_product,"funnel":funnel,"regions":regions}

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session=Depends(db_session), user: User=Depends(current_user)):
    ctx=dashboard_context(db,user)
    return templates.TemplateResponse("dashboard.html", {"request":request,"user":user,"company":COMPANY_NAME,**ctx})

@app.get("/api/dashboard")
def api_dashboard(db: Session=Depends(db_session), user: User=Depends(current_user)):
    return dashboard_context(db,user)

@app.get("/employees", response_class=HTMLResponse)
def employees_page(request:Request, db:Session=Depends(db_session), user:User=Depends(current_user)):
    rows=list(db.scalars(select(Employee).order_by(Employee.region,Employee.title)))
    return templates.TemplateResponse("employees.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows})

@app.post("/employees")
def employee_add(employee_no:str=Form(...),name:str=Form(...),title:str=Form(...),region:str=Form(...),manager:str=Form(""),monthly_target:float=Form(...),db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin","executive")
    db.add(Employee(employee_no=employee_no,name=name,title=title,region=region,manager=manager,monthly_target=monthly_target)); db.commit(); audit(db,user,"新增","員工",f"{employee_no} {name}")
    return RedirectResponse("/employees",303)

@app.post("/employees/{eid}/delete")
def employee_delete(eid:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin")
    e=db.get(Employee,eid)
    if e: e.active=False; db.commit(); audit(db,user,"停用","員工",e.name)
    return RedirectResponse("/employees",303)

@app.get("/sales", response_class=HTMLResponse)
def sales_page(request:Request,db:Session=Depends(db_session),user:User=Depends(current_user)):
    rows=list(db.scalars(select(Sale).order_by(Sale.sale_date.desc(),Sale.id.desc()).limit(300)))
    emps=list(db.scalars(select(Employee).where(Employee.active==True))); products=list(db.scalars(select(Product).where(Product.active==True))); clinics=list(db.scalars(select(Clinic)))
    return templates.TemplateResponse("sales.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows,"employees":emps,"products":products,"clinics":clinics})

@app.post("/sales")
def sale_add(sale_date:date=Form(...),employee_id:int=Form(...),product_id:int=Form(...),clinic_id:int=Form(...),quantity:float=Form(...),amount:float=Form(...),note:str=Form(""),db:Session=Depends(db_session),user:User=Depends(current_user)):
    p=db.get(Product,product_id); gp=amount*(p.gross_margin if p else 0)
    db.add(Sale(sale_date=sale_date,employee_id=employee_id,product_id=product_id,clinic_id=clinic_id,quantity=quantity,amount=amount,gross_profit=gp,note=note));
    c=db.get(Clinic,clinic_id)
    if c: c.last_order_date=sale_date
    db.commit(); audit(db,user,"新增","業績",f"金額 {amount:,.0f}")
    return RedirectResponse("/sales",303)

@app.get("/sales/{sid}/edit", response_class=HTMLResponse)
def sale_edit_page(sid:int, request:Request, db:Session=Depends(db_session), user:User=Depends(current_user)):
    authorize(user,"admin","executive","manager")
    sale=db.get(Sale,sid)
    if not sale:
        raise HTTPException(404,"找不到業績資料")
    emps=list(db.scalars(select(Employee).where(Employee.active==True).order_by(Employee.region,Employee.name)))
    products=list(db.scalars(select(Product).where(Product.active==True).order_by(Product.name)))
    clinics=list(db.scalars(select(Clinic).order_by(Clinic.region,Clinic.name)))
    return templates.TemplateResponse("sales_edit.html",{
        "request":request,"user":user,"company":COMPANY_NAME,"sale":sale,
        "employees":emps,"products":products,"clinics":clinics
    })

@app.post("/sales/{sid}/edit")
def sale_edit(sid:int,sale_date:date=Form(...),employee_id:int=Form(...),product_id:int=Form(...),clinic_id:int=Form(...),quantity:float=Form(...),amount:float=Form(...),status:str=Form("已認列"),note:str=Form(""),db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin","executive","manager")
    sale=db.get(Sale,sid)
    if not sale:
        raise HTTPException(404,"找不到業績資料")
    product=db.get(Product,product_id)
    sale.sale_date=sale_date
    sale.employee_id=employee_id
    sale.product_id=product_id
    sale.clinic_id=clinic_id
    sale.quantity=quantity
    sale.amount=amount
    sale.gross_profit=amount*(product.gross_margin if product else 0)
    sale.status=status
    sale.note=note
    clinic=db.get(Clinic,clinic_id)
    if clinic:
        clinic.last_order_date=sale_date
    db.commit()
    audit(db,user,"修改","業績",f"#{sid} 金額 {amount:,.0f}")
    return RedirectResponse("/sales",303)

@app.post("/sales/{sid}/delete")
def sale_delete(sid:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin","executive","manager")
    s=db.get(Sale,sid)
    if s: db.delete(s); db.commit(); audit(db,user,"刪除","業績",str(sid))
    return RedirectResponse("/sales",303)

@app.get("/products", response_class=HTMLResponse)
def products_page(request:Request,db:Session=Depends(db_session),user:User=Depends(current_user)):
    rows=list(db.scalars(select(Product).order_by(Product.name)))
    return templates.TemplateResponse("products.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows})

@app.post("/products")
def product_add(code:str=Form(...),name:str=Form(...),category:str=Form(...),unit:str=Form(...),unit_price:float=Form(...),gross_margin:float=Form(...),monthly_target_qty:float=Form(...),db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin","executive")
    db.add(Product(code=code,name=name,category=category,unit=unit,unit_price=unit_price,gross_margin=gross_margin/100,monthly_target_qty=monthly_target_qty)); db.commit(); audit(db,user,"新增","產品",name)
    return RedirectResponse("/products",303)

@app.get("/clinics",response_class=HTMLResponse)
def clinics_page(request:Request,db:Session=Depends(db_session),user:User=Depends(current_user)):
    rows=list(db.scalars(select(Clinic).order_by(Clinic.region,Clinic.name))); emps=list(db.scalars(select(Employee).where(Employee.active==True)))
    return templates.TemplateResponse("clinics.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows,"employees":emps})

@app.post("/clinics")
def clinic_add(code:str=Form(...),name:str=Form(...),region:str=Form(...),city:str=Form(...),owner_employee_id:int=Form(...),status:str=Form(...),db:Session=Depends(db_session),user:User=Depends(current_user)):
    db.add(Clinic(code=code,name=name,region=region,city=city,owner_employee_id=owner_employee_id,status=status)); db.commit(); audit(db,user,"新增","診所",name)
    return RedirectResponse("/clinics",303)

@app.get("/activities",response_class=HTMLResponse)
def activities_page(request:Request,db:Session=Depends(db_session),user:User=Depends(current_user)):
    rows=list(db.scalars(select(Activity).order_by(Activity.activity_date.desc(),Activity.id.desc()).limit(300))); emps=list(db.scalars(select(Employee).where(Employee.active==True))); clinics=list(db.scalars(select(Clinic)))
    return templates.TemplateResponse("activities.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows,"employees":emps,"clinics":clinics})

@app.post("/activities")
def activity_add(activity_date:date=Form(...),employee_id:int=Form(...),clinic_id:int=Form(...),stage:str=Form(...),outcome:str=Form(""),next_action_date:Optional[date]=Form(None),db:Session=Depends(db_session),user:User=Depends(current_user)):
    db.add(Activity(activity_date=activity_date,employee_id=employee_id,clinic_id=clinic_id,stage=stage,outcome=outcome,next_action_date=next_action_date)); db.commit(); audit(db,user,"新增","CRM活動",stage)
    return RedirectResponse("/activities",303)

@app.get("/users",response_class=HTMLResponse)
def users_page(request:Request,db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin"); rows=list(db.scalars(select(User).order_by(User.username)))
    return templates.TemplateResponse("users.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows})

@app.post("/users")
def user_add(username:str=Form(...),full_name:str=Form(...),password:str=Form(...),role:str=Form(...),region:str=Form(...),db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin"); db.add(User(username=username,full_name=full_name,password_hash=pwd.hash(password),role=role,region=region)); db.commit(); audit(db,user,"新增","使用者",username)
    return RedirectResponse("/users",303)

@app.get("/audit",response_class=HTMLResponse)
def audit_page(request:Request,db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin","executive"); rows=list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500)))
    return templates.TemplateResponse("audit.html",{"request":request,"user":user,"company":COMPANY_NAME,"rows":rows})

@app.get("/export/sales.csv")
def export_sales(db:Session=Depends(db_session),user:User=Depends(current_user)):
    out=io.StringIO(); w=csv.writer(out); w.writerow(["日期","員工編號","員工","產品代碼","產品","診所代碼","診所","數量","金額","毛利","狀態","備註"])
    for s in db.scalars(select(Sale).order_by(Sale.sale_date)):
        w.writerow([s.sale_date,s.employee.employee_no,s.employee.name,s.product.code,s.product.name,s.clinic.code,s.clinic.name,s.quantity,s.amount,s.gross_profit,s.status,s.note])
    data=out.getvalue().encode("utf-8-sig")
    return StreamingResponse(io.BytesIO(data),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=diamond_sales.csv"})

@app.post("/import/sales")
async def import_sales(file:UploadFile=File(...),db:Session=Depends(db_session),user:User=Depends(current_user)):
    authorize(user,"admin","executive","manager")
    raw=await file.read(); text=raw.decode("utf-8-sig"); reader=csv.DictReader(io.StringIO(text)); count=0
    for row in reader:
        emp=db.scalar(select(Employee).where(Employee.employee_no==row.get("員工編號")))
        prod=db.scalar(select(Product).where(Product.code==row.get("產品代碼")))
        clinic=db.scalar(select(Clinic).where(Clinic.code==row.get("診所代碼")))
        if not (emp and prod and clinic): continue
        amount=float(row.get("金額",0)); qty=float(row.get("數量",0)); d=date.fromisoformat(row.get("日期"))
        db.add(Sale(sale_date=d,employee_id=emp.id,product_id=prod.id,clinic_id=clinic.id,quantity=qty,amount=amount,gross_profit=amount*prod.gross_margin,note=row.get("備註", ""))); count+=1
    db.commit(); audit(db,user,"匯入","業績",f"{count} 筆")
    return RedirectResponse("/sales",303)

@app.get("/health")
def health(): return {"status":"ok","time":datetime.utcnow().isoformat()}
