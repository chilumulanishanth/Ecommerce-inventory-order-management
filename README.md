# E-Commerce Inventory & Order Management System

A backend system for managing products, inventory, customers and orders with transactional stock updates.

## Features

- Product and SKU management
- Inventory tracking
- Customer management
- Order creation
- Automatic stock deduction
- Insufficient-stock validation
- Order totals calculated from stored product prices
- Order status workflow
- PostgreSQL database
- SQLAlchemy ORM
- FastAPI REST API
- Docker Compose
- Automated tests and CI

## Data model

Customer 1 -> many Orders  
Order 1 -> many OrderItems  
Product 1 -> many OrderItems

`OrderItem` acts as the junction entity between orders and products.

## Business rule

When an order is created:
1. Customer must exist.
2. Every product must exist.
3. Requested quantity must be available.
4. Total is calculated from database prices.
5. Stock is reduced.
6. Order items are persisted.

The transaction is committed only after validation succeeds.

## Run with Docker

```bash
docker compose up --build
```

API docs:
`http://localhost:8000/docs`

## Main endpoints

- `POST /products`
- `GET /products`
- `GET /products/{product_id}`
- `POST /customers`
- `GET /customers`
- `POST /orders`
- `GET /orders`
- `GET /orders/{order_id}`
- `PATCH /orders/{order_id}/status`

## Example product

```json
{
  "name": "Mechanical Keyboard",
  "sku": "KB-001",
  "price": 2499.00,
  "stock": 25,
  "category": "Electronics"
}
```

## Example order

```json
{
  "customer_id": 1,
  "items": [
    {"product_id": 1, "quantity": 2}
  ]
}
```

## Interview talking points

- Why use a separate `OrderItem` table?
- Why store `unit_price` in `OrderItem`?
- How is stock consistency maintained?
- What happens when stock is insufficient?
- Why use PostgreSQL?
- What indexes are useful?
- Where would database transactions and row locking become important at scale?
