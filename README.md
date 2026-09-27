# STEVO POS Suite

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
