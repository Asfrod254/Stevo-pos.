const supabase = require("../config/supabase");

const getAllProducts = async (req, res, next) => {
  try {
    console.log("Fetching all products");
    const { data, error } = await supabase.from("products").select("*").order("created_at", { ascending: false });

    if (error) throw error;

    return res.status(200).json({
      success: true,
      data,
    });
  } catch (error) {
    next(error);
  }
};

const getProductById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { data, error } = await supabase.from("products").select("*").eq("id", id).single();

    if (error) {
      if (error.code === "PGRST116") {
        return res.status(404).json({ success: false, error: "Product not found" });
      }
      throw error;
    }

    return res.status(200).json({ success: true, data });
  } catch (error) {
    next(error);
  }
};

const createProduct = async (req, res, next) => {
  try {
    const { name, price, stock } = req.body;

    if (!name || price === undefined || stock === undefined) {
      return res.status(400).json({
        success: false,
        error: "Name, price, and stock are required.",
      });
    }

    const { data, error } = await supabase
      .from("products")
      .insert([
        {
          name,
          price,
          stock,
        },
      ])
      .select();

    if (error) throw error;

    console.log("Product created:", data[0]);
    return res.status(201).json({ success: true, data: data[0] });
  } catch (error) {
    next(error);
  }
};

const updateProduct = async (req, res, next) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    const { data, error } = await supabase
      .from("products")
      .update({ ...updateData, updated_at: new Date().toISOString() })
      .eq("id", id)
      .select();

    if (error) throw error;

    return res.status(200).json({
      success: true,
      data: data[0],
    });
  } catch (error) {
    next(error);
  }
};

const deleteProduct = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { data, error } = await supabase.from("products").delete().eq("id", id).select();

    if (error) throw error;

    return res.status(200).json({
      success: true,
      message: "Product deleted successfully",
      data: data[0] || null,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getAllProducts,
  getProductById,
  createProduct,
  updateProduct,
  deleteProduct,
};
