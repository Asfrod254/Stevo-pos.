const supabase = require("../config/supabase");

const getAllOrders = async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from("orders")
      .select(`*, order_items(*, products(*))`)
      .order("created_at", { ascending: false });

    if (error) throw error;

    return res.status(200).json({ success: true, data });
  } catch (error) {
    next(error);
  }
};

const getOrderById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { data, error } = await supabase
      .from("orders")
      .select(`*, order_items(*, products(*))`)
      .eq("id", id)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return res.status(404).json({ success: false, error: "Order not found" });
      }
      throw error;
    }

    return res.status(200).json({ success: true, data });
  } catch (error) {
    next(error);
  }
};

const createOrder = async (req, res, next) => {
  try {
    const { customer_name, items } = req.body;

    if (!customer_name || !Array.isArray(items) || items.length === 0) {
      return res.status(400).json({
        success: false,
        error: "Customer name and at least one item are required.",
      });
    }

    let total = 0;
    const preparedItems = [];

    for (const item of items) {
      const { product_id, quantity } = item;

      if (!product_id || !quantity) {
        return res.status(400).json({ success: false, error: "Each item needs product_id and quantity." });
      }

      const { data: product, error: productError } = await supabase
        .from("products")
        .select("id, price, stock")
        .eq("id", product_id)
        .single();

      if (productError || !product) {
        return res.status(404).json({ success: false, error: `Product ${product_id} not found.` });
      }

      if (product.stock < quantity) {
        return res.status(400).json({
          success: false,
          error: `Insufficient stock for product ${product_id}`,
        });
      }

      const subtotal = Number(product.price) * Number(quantity);
      total += subtotal;

      preparedItems.push({
        product_id,
        quantity,
        subtotal,
      });
    }

    const { data: order, error: orderError } = await supabase
      .from("orders")
      .insert([
        {
          customer_name,
          total,
          status: "pending",
        },
      ])
      .select()
      .single();

    if (orderError) throw orderError;

    const orderItems = preparedItems.map((item) => ({
      ...item,
      order_id: order.id,
    }));

    const { error: itemsError } = await supabase.from("order_items").insert(orderItems);

    if (itemsError) throw itemsError;

    for (const item of preparedItems) {
      const { data: currentProduct, error: stockLookupError } = await supabase
        .from("products")
        .select("stock")
        .eq("id", item.product_id)
        .single();

      if (stockLookupError || !currentProduct) {
        throw new Error(`Unable to fetch current stock for product ${item.product_id}`);
      }

      const remainingStock = Number(currentProduct.stock) - Number(item.quantity);

      const { error: stockUpdateError } = await supabase
        .from("products")
        .update({ stock: remainingStock })
        .eq("id", item.product_id);

      if (stockUpdateError) throw stockUpdateError;
    }

    return res.status(201).json({
      success: true,
      data: {
        order,
        items: orderItems,
      },
    });
  } catch (error) {
    next(error);
  }
};

const updateOrderStatus = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!status) {
      return res.status(400).json({ success: false, error: "Status is required." });
    }

    const { data, error } = await supabase
      .from("orders")
      .update({ status })
      .eq("id", id)
      .select();

    if (error) throw error;

    return res.status(200).json({ success: true, data: data[0] });
  } catch (error) {
    next(error);
  }
};

const deleteOrder = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { data, error } = await supabase.from("orders").delete().eq("id", id).select();

    if (error) throw error;

    return res.status(200).json({
      success: true,
      message: "Order deleted successfully",
      data: data[0] || null,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getAllOrders,
  getOrderById,
  createOrder,
  updateOrderStatus,
  deleteOrder,
};
