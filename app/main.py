from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
import os

DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./ecommerce.db")
connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {}
engine=create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal=sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base=declarative_base()

class Product(Base):
    __tablename__="products"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(120),nullable=False)
    sku=Column(String(50),unique=True,index=True,nullable=False)
    price=Column(Numeric(10,2),nullable=False)
    stock=Column(Integer,default=0,nullable=False)
    category=Column(String(80),nullable=False)
    order_items=relationship("OrderItem",back_populates="product")

class Customer(Base):
    __tablename__="customers"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(120),nullable=False)
    email=Column(String(160),unique=True,index=True,nullable=False)
    orders=relationship("Order",back_populates="customer")

class Order(Base):
    __tablename__="orders"
    id=Column(Integer,primary_key=True,index=True)
    customer_id=Column(Integer,ForeignKey("customers.id"),nullable=False)
    status=Column(String(30),default="PLACED",nullable=False)
    total_amount=Column(Numeric(10,2),nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)
    customer=relationship("Customer",back_populates="orders")
    items=relationship("OrderItem",back_populates="order",cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__="order_items"
    id=Column(Integer,primary_key=True,index=True)
    order_id=Column(Integer,ForeignKey("orders.id"),nullable=False)
    product_id=Column(Integer,ForeignKey("products.id"),nullable=False)
    quantity=Column(Integer,nullable=False)
    unit_price=Column(Numeric(10,2),nullable=False)
    order=relationship("Order",back_populates="items")
    product=relationship("Product",back_populates="order_items")

Base.metadata.create_all(bind=engine)

app=FastAPI(title="E-Commerce Inventory & Order Management System",version="1.0.0")

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProductCreate(BaseModel):
    name:str
    sku:str
    price:Decimal=Field(gt=0)
    stock:int=Field(ge=0)
    category:str

class CustomerCreate(BaseModel):
    name:str
    email:str

class OrderItemCreate(BaseModel):
    product_id:int
    quantity:int=Field(gt=0)

class OrderCreate(BaseModel):
    customer_id:int
    items:list[OrderItemCreate]

@app.get("/health")
def health():
    return {"status":"ok","service":"ecommerce-inventory-order-management"}

@app.post("/products")
def create_product(data:ProductCreate,db:Session=Depends(get_db)):
    if db.query(Product).filter(Product.sku==data.sku).first():
        raise HTTPException(409,"SKU already exists")
    p=Product(**data.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p

@app.get("/products")
def list_products(db:Session=Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()

@app.get("/products/{product_id}")
def get_product(product_id:int,db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,"Product not found")
    return p

@app.post("/customers")
def create_customer(data:CustomerCreate,db:Session=Depends(get_db)):
    if db.query(Customer).filter(Customer.email==data.email).first():
        raise HTTPException(409,"Email already exists")
    c=Customer(**data.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c

@app.get("/customers")
def list_customers(db:Session=Depends(get_db)):
    return db.query(Customer).order_by(Customer.id).all()

@app.post("/orders")
def create_order(data:OrderCreate,db:Session=Depends(get_db)):
    customer=db.get(Customer,data.customer_id)
    if not customer: raise HTTPException(404,"Customer not found")
    if not data.items: raise HTTPException(400,"Order must contain at least one item")

    products=[]
    total=Decimal("0.00")
    for item in data.items:
        product=db.get(Product,item.product_id)
        if not product: raise HTTPException(404,f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(400,f"Insufficient stock for {product.name}")
        products.append((product,item))
        total += Decimal(product.price) * item.quantity

    order=Order(customer_id=data.customer_id,status="PLACED",total_amount=total)
    db.add(order)
    for product,item in products:
        product.stock -= item.quantity
        order.items.append(OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price
        ))
    db.commit(); db.refresh(order)
    return order

@app.get("/orders")
def list_orders(db:Session=Depends(get_db)):
    return db.query(Order).order_by(Order.id.desc()).all()

@app.get("/orders/{order_id}")
def get_order(order_id:int,db:Session=Depends(get_db)):
    order=db.get(Order,order_id)
    if not order: raise HTTPException(404,"Order not found")
    return {
        "id":order.id,
        "customer_id":order.customer_id,
        "status":order.status,
        "total_amount":float(order.total_amount),
        "created_at":order.created_at,
        "items":[
            {"product_id":i.product_id,"quantity":i.quantity,"unit_price":float(i.unit_price)}
            for i in order.items
        ]
    }

@app.patch("/orders/{order_id}/status")
def update_order_status(order_id:int,status:str,db:Session=Depends(get_db)):
    allowed={"PLACED","PROCESSING","SHIPPED","DELIVERED","CANCELLED"}
    status=status.upper()
    if status not in allowed: raise HTTPException(400,f"Status must be one of {sorted(allowed)}")
    order=db.get(Order,order_id)
    if not order: raise HTTPException(404,"Order not found")
    if order.status=="DELIVERED": raise HTTPException(400,"Delivered orders cannot be changed")
    order.status=status
    db.commit(); db.refresh(order)
    return order
