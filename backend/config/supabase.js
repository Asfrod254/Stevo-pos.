const bcrypt = require('bcryptjs');

const localData = {
  products: [
    { id: 'prod-1001', name: 'Cement 50kg', price: 780, stock: 42, created_at: '2026-09-01T08:00:00.000Z' },
    { id: 'prod-1002', name: 'Paint White', price: 620, stock: 18, created_at: '2026-09-02T09:15:00.000Z' },
    { id: 'prod-1003', name: 'Steel Rod', price: 1450, stock: 9, created_at: '2026-09-03T11:30:00.000Z' },
    { id: 'prod-1004', name: 'Tiles', price: 950, stock: 33, created_at: '2026-09-04T10:45:00.000Z' },
    { id: 'prod-1005', name: 'PVC Pipes', price: 430, stock: 66, created_at: '2026-09-05T14:00:00.000Z' },
  ],
  orders: [
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
  ],
  users: [
    {
      id: 'user-admin',
      username: 'admin',
      password_hash: bcrypt.hashSync('admin123', 10),
      role: 'admin',
      created_at: '2026-09-20T08:00:00.000Z',
    },
  ],
  order_items: [],
};

const createLocalQuery = (table) => {
  const query = {
    _table: table,
    _filters: [],
    _single: false,
    _operation: 'select',
    _payload: null,
    select() {
      return this;
    },
    eq(column, value) {
      this._filters.push({ column, value });
      return this;
    },
    order() {
      return this;
    },
    insert(rows) {
      this._operation = 'insert';
      this._payload = Array.isArray(rows) ? rows : [rows];
      return this;
    },
    update(values) {
      this._operation = 'update';
      this._payload = values;
      return this;
    },
    delete() {
      this._operation = 'delete';
      return this;
    },
    single() {
      this._single = true;
      return this;
    },
    execute() {
      let rows = [...(localData[table] || [])];

      this._filters.forEach(({ column, value }) => {
        rows = rows.filter((row) => row[column] === value);
      });

      if (this._operation === 'insert') {
        const inserted = this._payload.map((row) => ({
          ...row,
          id: `local-${Date.now()}-${Math.random().toString(16).slice(2)}`,
          created_at: new Date().toISOString(),
        }));
        localData[table] = [...localData[table], ...inserted];
        return { data: this._single ? inserted[0] : inserted, error: null };
      }

      if (this._operation === 'update') {
        const updated = rows.map((row) => ({ ...row, ...this._payload }));
        localData[table] = localData[table].map((row) => updated.find((item) => item.id === row.id) || row);
        return { data: this._single ? (updated[0] || null) : updated, error: null };
      }

      if (this._operation === 'delete') {
        const deleted = [...rows];
        localData[table] = localData[table].filter((row) => !rows.some((item) => item.id === row.id));
        return { data: deleted, error: null };
      }

      return { data: this._single ? rows[0] || null : rows, error: null };
    },
    then(resolve, reject) {
      return Promise.resolve(this.execute()).then(resolve, reject);
    },
  };

  return query;
};

const supabase = {
  from: (table) => createLocalQuery(table),
};

module.exports = supabase;
