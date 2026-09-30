# STEVO POS Suite

## Standalone Offline Python POS

The workspace includes a self-contained Windows desktop POS in `offline_pos.py`. It uses Python's built-in Tkinter and SQLite libraries, so sales, stock, users, and settings stay on this computer and the app does not contact the web backend or require an internet connection.

To start it, double-click `run_offline_pos.bat`, or run `python offline_pos.py` with Python 3.10 or newer and Tkinter installed. No Python packages need to be installed.

First-run login: `admin` / `admin123`. Change staff access by adding accounts in **Users**. The local database is created at `data/stevo_pos.sqlite3`; keep a backup of that file to preserve sales and inventory. CSV reports and printed receipt text files are also saved locally. M-Pesa and card sales are recorded as payment methods; this offline app does not connect to payment providers.

Checkout supports multi-item baskets, quick product creation, and saving an order as pending. Pending orders reserve stock, appear in the header and dashboard, and can be reviewed from **Orders**; completing one records payment first. Press **F1** for the shortcut list: **F2** or **Ctrl+N** opens checkout, **Ctrl+Shift+P** adds a product, **Ctrl+O** opens orders, **Ctrl+R** opens reports, **Ctrl+F** focuses search, and **F5** refreshes the current screen.

Run the storage and sales-rule tests with `python -m unittest -v test_pos_db`.

## Web POS

STEVO POS Suite is a full-stack point-of-sale dashboard built for retail and inventory management. It combines a React + Vite frontend with an Express backend for user authentication, product catalog management, order handling, reporting, and admin controls.

## Features

- Role-based access for admin, manager, and cashier users
- Secure login and registration with JWT-based sessions
- Product catalog with add, edit, and delete actions
- Order creation and summary tracking
- Sales overview dashboard with inventory and activity cards
- Reports export and printable order summaries
- User management for admin accounts
- Notification center and lightweight settings panel

## Tech Stack

- Frontend: React, Vite, CSS
- Backend: Node.js, Express
- Auth: JWT
- Data layer: Supabase-style client abstraction with local fallback data

## Project Structure

```text
stevo pos/
├── backend/
│   ├── config/
│   ├── controllers/
│   ├── middleware/
│   ├── model/
│   ├── routes/
│   ├── sql/
│   ├── .env
│   ├── package.json
│   └── server.js
├── frontend/
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── README.md
└── package.json (not present at repo root)
```

## Prerequisites

- Node.js 18 or newer
- npm

## Installation

1. Open a terminal in the backend folder:

```bash
cd backend
npm install
```

2. Open a terminal in the frontend folder:

```bash
cd frontend
npm install
```

## Environment Configuration

The backend includes a `.env` file with the required settings:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
JWT_SECRET=stevo-pos-super-secret-key
PORT=5000
```

> The project includes a local Supabase-compatible mock implementation in `backend/config/supabase.js`, so the app can run without a live remote database during local development.

## Running the App

### Start the backend

```bash
cd backend
npm run dev
```

The API runs on:

```text
http://localhost:5000
```

### Start the frontend

```bash
cd frontend
npm run dev
```

The dashboard runs on:

```text
http://localhost:5173
```

## Demo Login

Use the following credentials on the login screen:

```text
Username: admin
Password: admin123
```

## Default Roles

- Admin: full access to all pages and user administration
- Manager: access to products, orders, reports, and settings
- Cashier: limited access to overview and order viewing

## Main API Routes

### Users

- `POST /users/register`
- `POST /users/login`
- `GET /users/profile`
- `GET /users`
- `DELETE /users/:id`

### Products

- `GET /products`
- `POST /products`
- `GET /products/:id`
- `PUT /products/:id`
- `DELETE /products/:id`

### Orders

- `GET /orders`
- `GET /orders/:id`
- `POST /orders`
- `PUT /orders/:id/status`
- `DELETE /orders/:id`

## Build Verification

To build the frontend for production:

```bash
cd frontend
npm run build
```

## Notes

- The frontend is a demo dashboard styled as a modern POS management system.
- Some actions are designed for local flow and UI validation while the backend is lightweight and local-first.
- If you later connect this to a real Supabase instance, update the environment values and backend data access calls accordingly.

## License

This project is currently shared for local development and demonstration purposes.
