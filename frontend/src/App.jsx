import { useEffect, useMemo, useState } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'https://stevo-pos.onrender.com';
const AUTH_STORAGE_KEY = 'stevo-pos-auth';

const initialProducts = [
  { id: 'prod-1001', name: 'Cement 50kg', price: 780, stock: 42, category: 'Building', created_at: '2026-09-01T08:00:00.000Z' },
  { id: 'prod-1002', name: 'Paint White', price: 620, stock: 18, category: 'Finishing', created_at: '2026-09-02T09:15:00.000Z' },
  { id: 'prod-1003', name: 'Steel Rod', price: 1450, stock: 9, category: 'Metal', created_at: '2026-09-03T11:30:00.000Z' },
  { id: 'prod-1004', name: 'Tiles', price: 950, stock: 33, category: 'Flooring', created_at: '2026-09-04T10:45:00.000Z' },
  { id: 'prod-1005', name: 'PVC Pipes', price: 430, stock: 66, category: 'Plumbing', created_at: '2026-09-05T14:00:00.000Z' },
];

const initialOrders = [
  {
    id: 'ord-1001',
    customer_name: 'Jane Njeri',
    total: 21400,
    status: 'pending',
    created_at: '2026-09-15T09:00:00.000Z',
    order_items: [
      { id: 'item-1', product_id: 'prod-1001', quantity: 2, subtotal: 1560 },
      { id: 'item-2', product_id: 'prod-1003', quantity: 1, subtotal: 1450 },
    ],
  },
  {
    id: 'ord-1002',
    customer_name: 'John Kamau',
    total: 13250,
    status: 'completed',
    created_at: '2026-09-16T10:20:00.000Z',
    order_items: [
      { id: 'item-3', product_id: 'prod-1002', quantity: 3, subtotal: 1860 },
    ],
  },
  {
    id: 'ord-1003',
    customer_name: 'Grace Muthoni',
    total: 9500,
    status: 'cancelled',
    created_at: '2026-09-17T12:40:00.000Z',
    order_items: [
      { id: 'item-4', product_id: 'prod-1005', quantity: 2, subtotal: 860 },
    ],
  },
];

const navItems = [
  { label: 'Overview', icon: '⌂' },
  { label: 'Products', icon: '◫' },
  { label: 'Orders', icon: '▣' },
  { label: 'Reports', icon: '◌' },
  { label: 'Settings', icon: '⚙' },
];

const pagePermissions = {
  Overview: ['admin', 'manager', 'cashier'],
  Products: ['admin', 'manager', 'cashier'],
  Orders: ['admin', 'manager', 'cashier'],
  Reports: ['admin', 'manager'],
  Settings: ['admin'],
  Users: ['admin'],
};

const readAuthSession = () => {
  try {
    const saved = localStorage.getItem(AUTH_STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
};

function BrandLogo({ compact = false }) {
  return (
    <div className={compact ? 'brand-logo compact' : 'brand-logo'}>
      <svg viewBox="0 0 980 320" role="img" aria-label="Stevo POS" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="stevo-green" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="#7ef66c" />
            <stop offset="28%" stopColor="#31d966" />
            <stop offset="68%" stopColor="#16a34a" />
            <stop offset="100%" stopColor="#0f6d3c" />
          </linearGradient>
          <linearGradient id="stevo-silver" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="35%" stopColor="#dfe7ef" />
            <stop offset="68%" stopColor="#aeb7c4" />
            <stop offset="100%" stopColor="#e7edf5" />
          </linearGradient>
          <filter id="softShadow" x="-20%" y="-20%" width="140%" height="160%">
            <feDropShadow dx="0" dy="14" stdDeviation="10" floodColor="rgba(18, 116, 50, 0.6)" />
          </filter>
        </defs>

        <g filter="url(#softShadow)">
          <path d="M178 71 C 135 23, 66 23, 42 76 C 18 129, 52 175, 110 197 C 146 211, 202 213, 225 242 C 250 273, 239 315, 170 312 C 132 310, 110 298, 90 278 L27 326 C 78 385, 155 409, 231 399 C 325 387, 384 331, 378 257 C 373 195, 321 157, 257 140 C 218 128, 180 120, 166 98 C 154 79, 161 59, 178 71 Z" fill="url(#stevo-green)" />
          <path d="M132 106 C 170 60, 220 61, 245 89 C 267 114, 260 146, 232 173 C 204 200, 155 201, 130 183 C 105 164, 96 136, 132 106 Z" fill="url(#stevo-silver)" opacity="0.88" />
          <path d="M160 216 C 231 228, 272 204, 304 155 C 330 113, 359 62, 432 39 C 485 21, 550 26, 577 65 C 607 109, 590 165, 532 188 C 505 199, 476 204, 451 204 C 421 204, 401 191, 402 167 C 405 134, 438 119, 467 120 C 495 122, 517 136, 530 161 L611 119 C 590 66, 537 38, 475 34 C 394 28, 331 65, 298 118 C 280 148, 263 181, 226 200 C 194 216, 172 220, 160 216 Z" fill="url(#stevo-green)" />
          <path d="M314 53 C 405 52, 496 106, 549 180 C 585 230, 578 278, 547 291 C 505 308, 455 257, 416 207 C 383 163, 340 141, 314 107 C 296 83, 292 71, 314 53 Z" fill="url(#stevo-silver)" opacity="0.88" />
          <path d="M93 244 C 214 275, 294 273, 345 224 C 391 180, 413 104, 500 85 C 540 77, 582 96, 609 124 L538 179 C 518 160, 494 152, 468 155 C 442 158, 424 170, 409 191 C 386 224, 323 249, 285 247 C 251 244, 211 230, 182 214 Z" fill="url(#stevo-green)" opacity="0.95" />
        </g>

        <g transform="translate(630 60)">
          <text x="0" y="80" fontSize="116" fontWeight="800" fill="#f5f7fb" letterSpacing="-4" style={{ fontFamily: 'Segoe UI, Arial, sans-serif' }}>Stevo</text>
          <text x="0" y="190" fontSize="110" fontWeight="800" fill="url(#stevo-green)" letterSpacing="-5" style={{ fontFamily: 'Segoe UI, Arial, sans-serif' }}>POS</text>
        </g>
      </svg>
    </div>
  );
}

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [authSession, setAuthSession] = useState(readAuthSession);
  const [authMode, setAuthMode] = useState('login');
  const [loginForm, setLoginForm] = useState({ username: 'admin', password: 'admin123' });
  const [registerForm, setRegisterForm] = useState({ username: '', password: '', confirmPassword: '', role: 'cashier' });
  const [loginError, setLoginError] = useState('');
  const [registerError, setRegisterError] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [activePage, setActivePage] = useState('Overview');
  const [darkMode, setDarkMode] = useState(false);
  const [products, setProducts] = useState(initialProducts);
  const [orders, setOrders] = useState(initialOrders);
  const [selectedOrder, setSelectedOrder] = useState(initialOrders[0]);
  const [successMessage, setSuccessMessage] = useState('');
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProductId, setEditingProductId] = useState(null);
  const [productForm, setProductForm] = useState({ name: '', price: '', stock: '' });
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [orderForm, setOrderForm] = useState({ customer_name: '', product_id: '', quantity: '1' });
  const [users, setUsers] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [settings, setSettings] = useState({
    storeName: 'STEVO POS Suite',
    taxRules: 'VAT enabled',
    security: 'JWT sessions active',
  });
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [salesRange, setSalesRange] = useState('week');

  const visibleNavItems = authSession?.role === 'admin'
    ? [...navItems, { label: 'Users', icon: '☰' }]
    : navItems;

  useEffect(() => {
    const splashTimer = window.setTimeout(() => setShowSplash(false), 1800);
    return () => window.clearTimeout(splashTimer);
  }, []);

  useEffect(() => {
    if (!authSession) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return;
    }

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authSession));
  }, [authSession]);

  useEffect(() => {
    if (!authSession?.token) return;

    let ignore = false;

    const validateSession = async () => {
      try {
        const response = await fetch(`${API_URL}/users/profile`, {
          headers: {
            Authorization: `Bearer ${authSession.token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Session expired');
        }

        const payload = await response.json();

        if (!ignore) {
          setAuthSession((current) => current ? {
            ...current,
            username: payload.data.username,
            role: payload.data.role,
          } : current);
        }
      } catch (error) {
        if (!ignore) {
          setAuthSession(null);
          setLoginError('Your session expired. Please sign in again.');
        }
      }
    };

    validateSession();

    return () => {
      ignore = true;
    };
  }, [authSession?.token]);

  useEffect(() => {
    if (!authSession) return;

    if (!pagePermissions[activePage]?.includes(authSession.role)) {
      setActivePage('Overview');
    }
  }, [activePage, authSession]);

  useEffect(() => {
    if (!authSession?.token) {
      setNotifications([]);
      return;
    }

    const fetchNotifications = async () => {
      try {
        const response = await fetch(`${API_URL}/notifications`, {
          headers: {
            Authorization: `Bearer ${authSession.token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to load notifications');
        }

        const payload = await response.json();
        setNotifications(Array.isArray(payload.data) ? payload.data : []);
      } catch (error) {
        setNotifications([]);
      }
    };

    fetchNotifications();
  }, [authSession?.token]);

  useEffect(() => {
    if (!authSession || authSession.role !== 'admin' || activePage !== 'Users') return;

    const fetchUsers = async () => {
      setIsLoadingUsers(true);

      try {
        const response = await fetch(`${API_URL}/users`, {
          headers: {
            Authorization: `Bearer ${authSession.token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to load users');
        }

        const payload = await response.json();
        setUsers(Array.isArray(payload.data) ? payload.data : []);
      } catch (error) {
        setUsers([]);
      } finally {
        setIsLoadingUsers(false);
      }
    };

    fetchUsers();
  }, [authSession, activePage]);

  const handleLogin = async (event) => {
    event.preventDefault();

    const username = loginForm.username.trim();
    const password = loginForm.password;

    if (!username || !password) {
      setLoginError('Please enter both username and password.');
      return;
    }

    try {
      setIsAuthenticating(true);
      setLoginError('');

      const response = await fetch(`${API_URL}/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload?.error || 'Login failed.');
      }

      const session = {
        token: payload.data.token,
        username: payload.data.user.username,
        role: payload.data.user.role,
      };

      setAuthSession(session);
      setSuccessMessage('Login successful.');
      setLoginForm({ username: payload.data.user.username, password: '' });
    } catch (error) {
      setLoginError(error.message || 'Unable to sign in.');
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();

    const username = registerForm.username.trim();
    const password = registerForm.password;
    const confirmPassword = registerForm.confirmPassword;
    const role = registerForm.role;

    if (!username || !password) {
      setRegisterError('Username and password are required.');
      return;
    }

    if (password.length < 6) {
      setRegisterError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setRegisterError('Passwords do not match.');
      return;
    }

    try {
      setIsRegistering(true);
      setRegisterError('');

      const response = await fetch(`${API_URL}/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload?.error || 'Registration failed.');
      }

      const session = {
        token: payload.data.token,
        username: payload.data.user.username,
        role: payload.data.user.role,
      };

      setAuthSession(session);
      setSuccessMessage('Account created successfully.');
      setRegisterForm({ username: '', password: '', confirmPassword: '', role: 'cashier' });
    } catch (error) {
      setRegisterError(error.message || 'Unable to create account.');
    } finally {
      setIsRegistering(false);
    }
  };

  const handleLogout = () => {
    setAuthSession(null);
    setLoginError('');
    setRegisterError('');
    setAuthMode('login');
    setSuccessMessage('Logged out successfully.');
  };

  const normalizedProducts = useMemo(
    () => products.map((product) => ({
      ...product,
      price: Number(product.price || 0),
      stock: Number(product.stock || 0),
      category: product.category || 'General',
    })),
    [products],
  );

  const normalizedOrders = useMemo(
    () => orders.map((order) => ({
      id: order.id,
      customer: order.customer_name || 'Walk-in Customer',
      total: Number(order.total || 0),
      status: (order.status || 'pending').charAt(0).toUpperCase() + (order.status || 'pending').slice(1),
      rawStatus: order.status || 'pending',
      items: Array.isArray(order.order_items) ? order.order_items.length : 0,
      createdAt: order.created_at || new Date().toISOString(),
      order_items: order.order_items || [],
    })),
    [orders],
  );

  const salesRangeLabel = {
    week: 'This Week',
    month: 'This Month',
    quarter: 'This Quarter',
  }[salesRange];

  const cycleSalesRange = () => {
    setSalesRange((current) => {
      const sequence = ['week', 'month', 'quarter'];
      const currentIndex = sequence.indexOf(current);
      return sequence[(currentIndex + 1) % sequence.length];
    });
  };

  const salesTrend = useMemo(() => {
    if (!normalizedOrders.length) return [];

    const rangeWindow = salesRange === 'week' ? 7 : salesRange === 'month' ? 30 : 90;
    const recent = [...normalizedOrders]
      .filter((order) => {
        const createdAt = new Date(order.createdAt);
        const diffDays = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24);
        return diffDays <= rangeWindow;
      })
      .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
      .slice(-7);

    if (!recent.length) return [];

    const maxValue = Math.max(...recent.map((order) => Number(order.total || 0)), 1);
    return recent.map((order) => Math.max(12, Math.round((Number(order.total || 0) / maxValue) * 100)));
  }, [normalizedOrders, salesRange]);

  const stockLevels = useMemo(() => {
    if (!normalizedProducts.length) return [];

    const topProducts = [...normalizedProducts]
      .sort((a, b) => Number(b.stock || 0) - Number(a.stock || 0))
      .slice(0, 6);

    const maxStock = Math.max(...topProducts.map((product) => Number(product.stock || 0)), 1);
    return topProducts.map((product) => ({
      label: product.name,
      value: Math.max(0, Math.min(100, Math.round((Number(product.stock || 0) / maxStock) * 100))),
    }));
  }, [normalizedProducts]);

  const overviewCards = useMemo(() => {
    const totalSales = normalizedOrders.reduce((sum, order) => sum + Number(order.total || 0), 0);
    const totalInventory = normalizedProducts.reduce((sum, product) => sum + Number(product.stock || 0), 0);
    const topProduct = normalizedProducts.reduce(
      (best, product) => (Number(product.stock || 0) > Number(best.stock || 0) ? product : best),
      normalizedProducts[0] || { name: 'No products', stock: 0 },
    );

    return [
      { label: 'Daily Sales', value: `Ksh ${totalSales.toLocaleString()}`, change: `${normalizedOrders.length} orders` },
      { label: 'Total Orders', value: String(normalizedOrders.length), change: 'Offline data' },
      { label: 'Top Product', value: topProduct.name, change: `${topProduct.stock} in stock` },
      { label: 'Inventory', value: `${normalizedProducts.length ? Math.round((totalInventory / Math.max(normalizedProducts.length * 100, 1)) * 100) : 0}%`, change: 'Current stock' },
    ];
  }, [normalizedOrders, normalizedProducts]);

  const salesTotal = useMemo(
    () => overviewCards[0]?.value.replace(/[^0-9]/g, '') || '0',
    [overviewCards],
  );

  const canManageProducts = ['admin', 'manager'].includes(authSession?.role || '');
  const canCreateOrders = ['admin', 'manager'].includes(authSession?.role || '');
  const canAccessReports = ['admin', 'manager'].includes(authSession?.role || '');
  const canAccessSettings = authSession?.role === 'admin';
  const canManageUsers = authSession?.role === 'admin';
  const unreadNotifications = notifications.filter((notification) => !notification.read).length;

  const toggleNotifications = () => {
    setShowNotifications((current) => !current);
  };

  useEffect(() => {
    if (!showNotifications) return;

    const handleClickOutside = (event) => {
      const notificationTrigger = document.querySelector('.notification-button');
      const notificationPanel = document.querySelector('.notification-panel');

      if (!notificationTrigger || !notificationPanel) {
        setShowNotifications(false);
        return;
      }

      const clickedInside = notificationTrigger.contains(event.target) || notificationPanel.contains(event.target);
      if (!clickedInside) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showNotifications]);

  const markNotificationAsRead = async (id) => {
    if (!authSession?.token) return;

    try {
      const response = await fetch(`${API_URL}/notifications/${id}/read`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${authSession.token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Unable to mark notification as read');
      }

      setNotifications((current) => current.map((notification) => (
        notification.id === id ? { ...notification, read: true } : notification
      )));
    } catch (error) {
      setNotifications((current) => current.map((notification) => (
        notification.id === id ? { ...notification, read: true } : notification
      )));
    }
  };

  const markAllNotificationsAsRead = () => {
    setNotifications((current) => current.map((notification) => ({ ...notification, read: true })));
  };

  const cancelProductForm = () => {
    setShowProductForm(false);
    setEditingProductId(null);
    setProductForm({ name: '', price: '', stock: '' });
  };

  const startEditProduct = (product) => {
    setEditingProductId(product.id);
    setProductForm({
      name: product.name,
      price: String(product.price),
      stock: String(product.stock),
    });
    setShowProductForm(true);
  };

  const handleProductSubmit = (event) => {
    event.preventDefault();

    const payload = {
      name: productForm.name.trim(),
      price: Number(productForm.price),
      stock: Number(productForm.stock),
    };

    if (!payload.name || Number.isNaN(payload.price) || Number.isNaN(payload.stock)) {
      return;
    }

    if (editingProductId) {
      setProducts((current) => current.map((product) => (product.id === editingProductId ? { ...product, ...payload } : product)));
      if (authSession?.token) {
        fetch(`${API_URL}/notifications`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authSession.token}`,
          },
          body: JSON.stringify({
            title: 'Product updated',
            message: `${payload.name} was updated successfully.`,
            type: 'info',
          }),
        }).then((response) => response.ok && response.json()).then((payloadResponse) => {
          if (payloadResponse?.data) {
            setNotifications((current) => [payloadResponse.data, ...current]);
          }
        }).catch(() => {});
      }
      setSuccessMessage('Product updated successfully.');
    } else {
      setProducts((current) => [
        {
          id: `prod-${Date.now()}`,
          name: payload.name,
          price: payload.price,
          stock: payload.stock,
          category: 'General',
          created_at: new Date().toISOString(),
        },
        ...current,
      ]);
      if (authSession?.token) {
        fetch(`${API_URL}/notifications`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authSession.token}`,
          },
          body: JSON.stringify({
            title: 'Product added',
            message: `${payload.name} is now available in stock.`,
            type: 'success',
          }),
        }).then((response) => response.ok && response.json()).then((payloadResponse) => {
          if (payloadResponse?.data) {
            setNotifications((current) => [payloadResponse.data, ...current]);
          }
        }).catch(() => {});
      }
      setSuccessMessage('Product added successfully.');
    }

    cancelProductForm();
  };

  const handleDeleteProduct = (id) => {
    const confirmed = window.confirm('Delete this product?');
    if (!confirmed) return;

    setProducts((current) => current.filter((product) => product.id !== id));
    setSuccessMessage('Product deleted successfully.');
  };

  const handleOrderSubmit = (event) => {
    event.preventDefault();

    if (!canCreateOrders) {
      setSuccessMessage('Only managers and admins can create orders.');
      return;
    }

    const quantity = Number(orderForm.quantity);
    const productId = orderForm.product_id;

    if (!orderForm.customer_name.trim() || !productId || Number.isNaN(quantity) || quantity <= 0) {
      return;
    }

    const chosenProduct = products.find((product) => product.id === productId);
    if (!chosenProduct || chosenProduct.stock < quantity) {
      return;
    }

    const subtotal = chosenProduct.price * quantity;
    const newOrder = {
      id: `ord-${Date.now()}`,
      customer_name: orderForm.customer_name.trim(),
      total: subtotal,
      status: 'pending',
      created_at: new Date().toISOString(),
      order_items: [
        {
          id: `item-${Date.now()}`,
          product_id: productId,
          quantity,
          subtotal,
        },
      ],
    };

    setProducts((current) => current.map((product) =>
      product.id === productId ? { ...product, stock: product.stock - quantity } : product,
    ));

    setOrders((current) => [newOrder, ...current]);
    setSelectedOrder(newOrder);
    if (authSession?.token) {
      fetch(`${API_URL}/notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authSession.token}`,
        },
        body: JSON.stringify({
          title: 'New order created',
          message: `${orderForm.customer_name.trim()} ordered ${quantity} ${chosenProduct.name}${quantity > 1 ? ' units' : ' unit'}.`,
          type: 'success',
        }),
      }).then((response) => response.ok && response.json()).then((payloadResponse) => {
        if (payloadResponse?.data) {
          setNotifications((current) => [payloadResponse.data, ...current]);
        }
      }).catch(() => {});
    }
    setOrderForm({ customer_name: '', product_id: '', quantity: '1' });
    setShowOrderForm(false);
    setSuccessMessage('Order created successfully.');
  };

  const handlePageChange = (page) => {
    const allowedRoles = pagePermissions[page] || [];
    if (authSession && !allowedRoles.includes(authSession.role)) {
      setSuccessMessage('Access denied for this role.');
      return;
    }

    setActivePage(page);
  };

  const handleDeleteUser = async (userId) => {
    if (!canManageUsers || !authSession) return;

    const confirmed = window.confirm('Delete this user?');
    if (!confirmed) return;

    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${authSession.token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Unable to delete user');
      }

      setUsers((current) => current.filter((user) => user.id !== userId));
      if (authSession?.token) {
        fetch(`${API_URL}/notifications`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authSession.token}`,
          },
          body: JSON.stringify({
            title: 'User removed',
            message: 'An account was removed from the system.',
            type: 'warning',
          }),
        }).then((response) => response.ok && response.json()).then((payloadResponse) => {
          if (payloadResponse?.data) {
            setNotifications((current) => [payloadResponse.data, ...current]);
          }
        }).catch(() => {});
      }
      setSuccessMessage('User removed successfully.');
    } catch (error) {
      setLoginError(error.message || 'Unable to delete user.');
    }
  };

  const openNewOrderForm = () => {
    setOrderForm({ customer_name: '', product_id: '', quantity: '1' });
    setShowOrderForm(true);
  };

  const handleExport = (filename = 'stevo-orders-export.csv') => {
    if (!orders.length) {
      setSuccessMessage('No orders available to export.');
      return;
    }

    const headers = ['ID', 'Customer', 'Total', 'Status', 'Created', 'Items'];
    const rows = orders.map((order) => {
      const itemCount = Array.isArray(order.order_items) ? order.order_items.length : 0;
      return [
        order.id || '',
        order.customer_name || 'Walk-in Customer',
        Number(order.total || 0),
        order.status || 'pending',
        order.created_at || new Date().toISOString(),
        itemCount,
      ].map((value) => `"${String(value).replace(/"/g, '""')}"`).join(',');
    });

    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setSuccessMessage('Export downloaded successfully.');
  };

  const handleGenerateReport = () => {
    handleExport('stevo-sales-report.csv');
  };

  const handlePrintOrder = () => {
    if (!selectedOrder) {
      setSuccessMessage('Select an order before printing.');
      return;
    }

    window.print();
    setSuccessMessage('Print dialog opened.');
  };

  const handleSettingsAction = (action) => {
    if (action === 'edit') {
      const nextName = window.prompt('Update the store name', settings.storeName);
      if (!nextName) {
        return;
      }

      const trimmed = nextName.trim();
      if (!trimmed) {
        setSuccessMessage('Store name cannot be empty.');
        return;
      }

      setSettings((current) => ({ ...current, storeName: trimmed }));
      setSuccessMessage('Store name updated successfully.');
      return;
    }

    if (action === 'manage') {
      setSettings((current) => ({
        ...current,
        taxRules: current.taxRules === 'VAT enabled' ? 'VAT disabled' : 'VAT enabled',
      }));
      setSuccessMessage('Tax rules updated successfully.');
      return;
    }

    if (action === 'review') {
      setSettings((current) => ({
        ...current,
        security: current.security === 'JWT sessions active' ? 'Session timeout tightened to 15 minutes' : 'JWT sessions active',
      }));
      setSuccessMessage('Security review updated successfully.');
    }
  };

  const handleMarkOrderPaid = () => {
    if (!selectedOrder) {
      setSuccessMessage('Select an order to update.');
      return;
    }

    setOrders((current) => current.map((order) => (
      order.id === selectedOrder.id ? { ...order, status: 'paid' } : order
    )));
    setSelectedOrder((current) => current ? { ...current, status: 'paid', rawStatus: 'paid' } : current);
    if (authSession?.token) {
      fetch(`${API_URL}/notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authSession.token}`,
        },
        body: JSON.stringify({
          title: 'Payment received',
          message: `Order ${selectedOrder.id} has been marked as paid.`,
          type: 'success',
        }),
      }).then((response) => response.ok && response.json()).then((payloadResponse) => {
        if (payloadResponse?.data) {
          setNotifications((current) => [payloadResponse.data, ...current]);
        }
      }).catch(() => {});
    }
    setSuccessMessage('Order marked as paid.');
  };

  if (showSplash) {
    return (
      <div className="splash-screen">
        <BrandLogo />
      </div>
    );
  }

  if (!authSession) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-brand">
            <BrandLogo compact />
          </div>

          <div className="auth-copy">
            <p className="eyebrow">{authMode === 'login' ? 'Welcome back' : 'New account'}</p>
            <h1>{authMode === 'login' ? 'Sign in to continue' : 'Create your account'}</h1>
          </div>

          <div className="auth-toggle" role="tablist" aria-label="Authentication mode selector">
            <button
              type="button"
              className={authMode === 'login' ? 'toggle-tab active' : 'toggle-tab'}
              onClick={() => setAuthMode('login')}
            >
              Sign in
            </button>
            <button
              type="button"
              className={authMode === 'register' ? 'toggle-tab active' : 'toggle-tab'}
              onClick={() => setAuthMode('register')}
            >
              Register
            </button>
          </div>

          {authMode === 'login' ? (
            <form className="auth-form" onSubmit={handleLogin}>
              <label className="auth-field">
                <span>Username</span>
                <input
                  type="text"
                  value={loginForm.username}
                  onChange={(event) => setLoginForm((current) => ({ ...current, username: event.target.value }))}
                  placeholder="admin"
                />
              </label>

              <label className="auth-field">
                <span>Password</span>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))}
                  placeholder="••••••••"
                />
              </label>

              {loginError && <div className="error-banner">{loginError}</div>}

              <button type="submit" className="primary-button auth-button" disabled={isAuthenticating}>
                {isAuthenticating ? 'Signing in...' : 'Log in'}
              </button>

              <div className="demo-note">
                Demo access: <strong>admin</strong> / <strong>admin123</strong>
              </div>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleRegister}>
              <label className="auth-field">
                <span>Username</span>
                <input
                  type="text"
                  value={registerForm.username}
                  onChange={(event) => setRegisterForm((current) => ({ ...current, username: event.target.value }))}
                  placeholder="new cashier"
                />
              </label>

              <label className="auth-field">
                <span>Password</span>
                <input
                  type="password"
                  value={registerForm.password}
                  onChange={(event) => setRegisterForm((current) => ({ ...current, password: event.target.value }))}
                  placeholder="At least 6 characters"
                />
              </label>

              <label className="auth-field">
                <span>Confirm password</span>
                <input
                  type="password"
                  value={registerForm.confirmPassword}
                  onChange={(event) => setRegisterForm((current) => ({ ...current, confirmPassword: event.target.value }))}
                  placeholder="Repeat password"
                />
              </label>

              <label className="auth-field">
                <span>Role</span>
                <select
                  value={registerForm.role}
                  onChange={(event) => setRegisterForm((current) => ({ ...current, role: event.target.value }))}
                >
                  <option value="cashier">Cashier</option>
                  <option value="manager">Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </label>

              {registerError && <div className="error-banner">{registerError}</div>}

              <button type="submit" className="primary-button auth-button" disabled={isRegistering}>
                {isRegistering ? 'Creating account...' : 'Create account'}
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={darkMode ? 'app-shell dark' : 'app-shell'}>
      <aside className="sidebar">
        <div className="brand-block">
          <BrandLogo compact />
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {visibleNavItems.map((item) => (
            <button
              key={item.label}
              type="button"
              className={item.label === activePage ? 'nav-item active' : 'nav-item'}
              onClick={() => handlePageChange(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <p className="mini-label">Quick stats</p>
          <strong>{salesTotal}</strong>
          <span>Sales this week</span>
        </div>
      </aside>

      <main className="content-panel">
        <header className="topbar">
          <div className="searchbar">
            <span>⌕</span>
            <input type="text" placeholder="Search products, orders, customers" />
          </div>

          <div className="topbar-actions">
            <div className="notification-wrapper">
              <button
                type="button"
                className={`icon-button notification-button ${showNotifications ? 'active' : ''}`}
                aria-label="Notifications"
                onClick={toggleNotifications}
              >
                🔔
                {unreadNotifications > 0 && (
                  <span className="notification-badge">{unreadNotifications}</span>
                )}
              </button>

              {showNotifications && (
                <div className="notification-panel" role="dialog" aria-label="Notifications panel">
                  <div className="notification-header">
                    <strong>Notifications</strong>
                    {unreadNotifications > 0 && (
                      <button type="button" className="notification-link" onClick={markAllNotificationsAsRead}>
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div className="notification-list">
                    {notifications.length ? notifications.map((notification) => (
                      <button
                        key={notification.id}
                        type="button"
                        className={`notification-item ${notification.read ? 'read' : 'unread'}`}
                        onClick={() => markNotificationAsRead(notification.id)}
                      >
                        <span className={`notification-dot ${notification.type}`} />
                        <div className="notification-copy">
                          <strong>{notification.title}</strong>
                          <small>{notification.message}</small>
                          <time>{notification.time}</time>
                        </div>
                      </button>
                    )) : (
                      <div className="empty-state">No notifications.</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <button
              type="button"
              className="theme-toggle"
              onClick={() => setDarkMode((current) => !current)}
            >
              {darkMode ? '☀' : '☾'}
            </button>
            <button type="button" className="theme-toggle" onClick={handleLogout} aria-label="Logout">
              ⎋
            </button>
            <div className="profile-block">
              <div className="avatar">{(authSession.username || 'A').slice(0, 2).toUpperCase()}</div>
              <div>
                <strong>{authSession.username || 'Admin'}</strong>
                <small>{(authSession.role || 'Store Manager').toUpperCase()}</small>
              </div>
            </div>
          </div>
        </header>

        <div className="page-header">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>{activePage}</h1>
          </div>

          <div className="page-actions">
            <button type="button" className="secondary-button" onClick={() => handleExport()}>Export</button>
            {canCreateOrders && (
              <button type="button" className="primary-button" onClick={openNewOrderForm}>+ New Order</button>
            )}
          </div>
        </div>

        {successMessage && <div className="success-banner">{successMessage}</div>}

        {activePage === 'Reports' && (
          <section className="panel-card full-panel">
            {!canAccessReports ? (
              <div className="info-banner">Read-only access: cashiers can view the dashboard, but reports are restricted to managers and admins.</div>
            ) : (
              <>
                <div className="panel-header">
                  <div>
                    <p className="mini-label">Analytics</p>
                    <h2>Reports</h2>
                  </div>
                </div>

                <div className="report-grid">
                  <article className="metric-card">
                    <span>Revenue</span>
                    <strong>Ksh 44,150</strong>
                    <small>+12.4% vs last week</small>
                  </article>
                  <article className="metric-card">
                    <span>Orders</span>
                    <strong>3</strong>
                    <small>Across active sales</small>
                  </article>
                  <article className="metric-card">
                    <span>Returns</span>
                    <strong>1</strong>
                    <small>Pending review</small>
                  </article>
                  <article className="metric-card">
                    <span>Performance</span>
                    <strong>94%</strong>
                    <small>Store efficiency</small>
                  </article>
                </div>

                <div className="form-actions report-actions">
                  <button type="button" className="primary-button" onClick={handleGenerateReport}>Generate Report</button>
                </div>
              </>
            )}
          </section>
        )}

        {activePage === 'Settings' && (
          <section className="panel-card full-panel">
            {!canAccessSettings ? (
              <div className="info-banner">Read-only access: only admins can change system settings.</div>
            ) : (
              <>
                <div className="panel-header">
                  <div>
                    <p className="mini-label">System</p>
                    <h2>Settings</h2>
                  </div>
                </div>

                <div className="settings-list">
                  <div className="setting-row">
                    <div>
                      <strong>Store name</strong>
                      <small>{settings.storeName}</small>
                    </div>
                    <button type="button" className="secondary-button" onClick={() => handleSettingsAction('edit')}>Edit</button>
                  </div>
                  <div className="setting-row">
                    <div>
                      <strong>Tax rules</strong>
                      <small>{settings.taxRules}</small>
                    </div>
                    <button type="button" className="secondary-button" onClick={() => handleSettingsAction('manage')}>Manage</button>
                  </div>
                  <div className="setting-row">
                    <div>
                      <strong>Security</strong>
                      <small>{settings.security}</small>
                    </div>
                    <button type="button" className="secondary-button" onClick={() => handleSettingsAction('review')}>Review</button>
                  </div>
                </div>
              </>
            )}
          </section>
        )}

        {activePage === 'Users' && canManageUsers && (
          <section className="panel-card full-panel">
            <div className="panel-header">
              <div>
                <p className="mini-label">Administration</p>
                <h2>User Management</h2>
              </div>
            </div>

            {isLoadingUsers ? (
              <div className="loading-banner">Loading users...</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Username</th>
                      <th>Role</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.length ? users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.id}</td>
                        <td>{user.username}</td>
                        <td><span className={`status-badge ${user.role}`}>{user.role}</span></td>
                        <td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td>
                        <td className="action-cell">
                          <button type="button" className="table-action delete" onClick={() => handleDeleteUser(user.id)}>Remove</button>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan="5" className="empty-state">No users found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {activePage === 'Overview' && (
          <>
            <section className="stats-grid">
              {overviewCards.map((card) => (
                <article key={card.label} className="stat-card">
                  <p>{card.label}</p>
                  <h3>{card.value}</h3>
                  <span>{card.change}</span>
                </article>
              ))}
            </section>

            <section className="charts-grid">
              <article className="panel-card sales-panel">
                <div className="panel-header">
                  <div>
                    <p className="mini-label">Revenue</p>
                    <h2>Sales Trends</h2>
                  </div>
                  <button type="button" className="ghost-button" onClick={cycleSalesRange}>{salesRangeLabel}</button>
                </div>

                <div className="chart-bars" aria-label="Sales trend chart">
                  {salesTrend.length ? salesTrend.map((value, index) => (
                    <div key={index} className="bar-group">
                      <span className="bar-fill" style={{ height: `${value}%` }} />
                      <small>{['M', 'T', 'W', 'T', 'F', 'S', 'S'][index]}</small>
                    </div>
                  )) : <div className="empty-state">No data</div>}
                </div>
              </article>

              <article className="panel-card stock-panel">
                <div className="panel-header">
                  <div>
                    <p className="mini-label">Inventory</p>
                    <h2>Stock Levels</h2>
                  </div>
                </div>

                <div className="stock-list">
                  {stockLevels.length ? stockLevels.map((item, index) => (
                    <div key={item.label || index} className="stock-row">
                      <label>{item.label}</label>
                      <div className="stock-track">
                        <span style={{ width: `${item.value}%` }} />
                      </div>
                      <strong>{item.value}%</strong>
                    </div>
                  )) : <div className="empty-state">No stock data</div>}
                </div>
              </article>
            </section>

            <section className="bottom-grid">
              <article className="panel-card list-panel">
                <div className="panel-header">
                  <div>
                    <p className="mini-label">Top Sellers</p>
                    <h2>Best Products</h2>
                  </div>
                </div>

                <div className="leaderboard">
                  {normalizedProducts.slice(0, 4).map((product, index) => (
                    <div key={product.id} className="leader-item">
                      <div className="rank">0{index + 1}</div>
                      <div>
                        <strong>{product.name}</strong>
                        <small>{product.stock} in stock</small>
                      </div>
                      <span>Ksh {product.price.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel-card quick-panel">
                <div className="panel-header">
                  <div>
                    <p className="mini-label">Actions</p>
                    <h2>Quick Actions</h2>
                  </div>
                </div>

                <div className="quick-actions">
                  {canManageProducts && (
                    <button type="button" className="primary-button" onClick={() => { setShowProductForm(true); setEditingProductId(null); setProductForm({ name: '', price: '', stock: '' }); }}>+ Add Product</button>
                  )}
                  {canCreateOrders && (
                    <button type="button" className="ghost-button" onClick={openNewOrderForm}>New Order</button>
                  )}
                  {canAccessReports && (
                    <button type="button" className="secondary-button" onClick={handleGenerateReport}>Generate Report</button>
                  )}
                </div>
              </article>
            </section>
          </>
        )}

        {activePage === 'Products' && (
          <section className="panel-card full-panel">
            <div className="panel-header">
              <div>
                <p className="mini-label">Catalogue</p>
                <h2>Products</h2>
              </div>

              {canManageProducts && (
                <button type="button" className="primary-button floating-add" onClick={() => {
                  setShowProductForm(true);
                  setEditingProductId(null);
                  setProductForm({ name: '', price: '', stock: '' });
                }}>
                  + Add Product
                </button>
              )}
            </div>

            {!canManageProducts && (
              <div className="info-banner">Read-only access: cashiers can view products, but only managers and admins can create, edit, or delete them.</div>
            )}

            {showProductForm && canManageProducts && (
              <form className="pos-form" onSubmit={handleProductSubmit}>
                <div className="form-grid">
                  <div className="field">
                    <label>Product name</label>
                    <input value={productForm.name} onChange={(event) => setProductForm((current) => ({ ...current, name: event.target.value }))} placeholder="e.g. Cement 50kg" required />
                  </div>
                  <div className="field">
                    <label>Price</label>
                    <input type="number" min="0" step="0.01" value={productForm.price} onChange={(event) => setProductForm((current) => ({ ...current, price: event.target.value }))} placeholder="0.00" required />
                  </div>
                  <div className="field">
                    <label>Stock</label>
                    <input type="number" min="0" step="1" value={productForm.stock} onChange={(event) => setProductForm((current) => ({ ...current, stock: event.target.value }))} placeholder="0" required />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" className="primary-button">{editingProductId ? 'Save Changes' : 'Create Product'}</button>
                  <button type="button" className="secondary-button" onClick={cancelProductForm}>Cancel</button>
                </div>
              </form>
            )}

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Price</th>
                    <th>Stock</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {normalizedProducts.map((product) => (
                    <tr key={product.id}>
                      <td>{product.id}</td>
                      <td>{product.name}</td>
                      <td>Ksh {product.price.toLocaleString()}</td>
                      <td>{product.stock}</td>
                      <td>{product.created_at ? new Date(product.created_at).toLocaleDateString() : '—'}</td>
                      <td className="action-cell">
                        {canManageProducts ? (
                          <>
                            <button type="button" className="table-action edit" onClick={() => startEditProduct(product)}>Edit</button>
                            <button type="button" className="table-action delete" onClick={() => handleDeleteProduct(product.id)}>Delete</button>
                          </>
                        ) : (
                          <span className="readonly-tag">Read only</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {activePage === 'Orders' && (
          <section className="orders-layout">
            <div className="panel-card full-panel orders-panel-card">
              <div className="panel-header">
                <div>
                  <p className="mini-label">Transactions</p>
                  <h2>Orders</h2>
                </div>
                {canCreateOrders && (
                  <button type="button" className="primary-button" onClick={() => {
                    if (showOrderForm) {
                      setShowOrderForm(false);
                      return;
                    }
                    openNewOrderForm();
                  }}>
                    {showOrderForm ? 'Close' : '+ New Order'}
                  </button>
                )}
              </div>

              {!canCreateOrders && (
                <div className="info-banner">Read-only access: cashiers can review orders, but only managers and admins can create new orders.</div>
              )}

              {showOrderForm && canCreateOrders && (
                <form className="pos-form" onSubmit={handleOrderSubmit}>
                  <div className="form-grid">
                    <div className="field">
                      <label>Customer name</label>
                      <input value={orderForm.customer_name} onChange={(event) => setOrderForm((current) => ({ ...current, customer_name: event.target.value }))} placeholder="Jane Njeri" required />
                    </div>
                    <div className="field">
                      <label>Product</label>
                      <select value={orderForm.product_id} onChange={(event) => setOrderForm((current) => ({ ...current, product_id: event.target.value }))} required>
                        <option value="">Select a product</option>
                        {normalizedProducts.map((product) => (
                          <option key={product.id} value={product.id}>{product.name} ({product.stock} in stock)</option>
                        ))}
                      </select>
                    </div>
                    <div className="field">
                      <label>Quantity</label>
                      <input type="number" min="1" value={orderForm.quantity} onChange={(event) => setOrderForm((current) => ({ ...current, quantity: event.target.value }))} required />
                    </div>
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="primary-button">Create Order</button>
                    <button type="button" className="secondary-button" onClick={() => setShowOrderForm(false)}>Cancel</button>
                  </div>
                </form>
              )}

              <div className="orders-list">
                {normalizedOrders.map((order) => (
                  <button
                    key={order.id}
                    type="button"
                    className={selectedOrder?.id === order.id ? 'order-row active' : 'order-row'}
                    onClick={() => setSelectedOrder(order)}
                  >
                    <div>
                      <strong>{order.id}</strong>
                      <small>{order.customer}</small>
                    </div>
                    <span className={`status-badge ${order.rawStatus.toLowerCase()}`}>{order.status}</span>
                    <strong className="order-total">Ksh {order.total.toLocaleString()}</strong>
                  </button>
                ))}
              </div>
            </div>

            <aside className="panel-card detail-panel">
              <div className="panel-header">
                <div>
                  <p className="mini-label">Details</p>
                  <h2>Order Summary</h2>
                </div>
              </div>

              <div className="order-detail">
                <div className="detail-head">
                  <div>
                    <strong>{selectedOrder?.id || '—'}</strong>
                    <small>{selectedOrder?.customer || 'No order selected'}</small>
                  </div>
                  <span className={`status-badge ${selectedOrder?.rawStatus?.toLowerCase() || 'pending'}`}>
                    {selectedOrder?.status || 'Pending'}
                  </span>
                </div>

                <ul>
                  <li>
                    <span>Items</span>
                    <strong>{selectedOrder?.items ?? 0}</strong>
                  </li>
                  <li>
                    <span>Subtotal</span>
                    <strong>Ksh {(selectedOrder?.total || 0).toLocaleString()}</strong>
                  </li>
                  <li>
                    <span>Status</span>
                    <strong>{selectedOrder?.status || 'Pending'}</strong>
                  </li>
                  <li>
                    <span>Total</span>
                    <strong>Ksh {(selectedOrder?.total || 0).toLocaleString()}</strong>
                  </li>
                </ul>

                <div className="detail-actions">
                  <button type="button" className="primary-button" onClick={handlePrintOrder}>Print</button>
                  <button type="button" className="secondary-button" onClick={handleMarkOrderPaid}>Mark Paid</button>
                </div>
              </div>
            </aside>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
