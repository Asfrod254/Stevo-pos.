const express = require("express");
const router = express.Router();
const supabase = require("../config/supabase");
const { auth, authorizeRoles } = require("../middleware/auth");

router.use(auth);

// GET all products
router.get("/", async (req, res) => {
  const { data, error } = await supabase.from("products").select("*");
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});

// POST new product
router.post("/", authorizeRoles("admin", "manager"), async (req, res) => {
  const { name, price, stock } = req.body;
  const { data, error } = await supabase
    .from("products")
    .insert([{ name, price, stock }]);
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
  console.log("Product added:", data);
});

// GET product by ID
router.get("/:id", async (req, res) => {
  const { id } = req.params;
  const { data, error } = await supabase.from("products").select("*").eq("id", id);
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});

// PUT update product
router.put("/:id", authorizeRoles("admin", "manager"), async (req, res) => {
  const { id } = req.params;
  const { name, price, stock } = req.body;
  const { data, error } = await supabase
    .from("products")
    .update({ name, price, stock })
    .eq("id", id);
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});

// DELETE product
router.delete("/:id", authorizeRoles("admin", "manager"), async (req, res) => {
  const { id } = req.params;
  const { data, error } = await supabase.from("products").delete().eq("id", id);
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});

module.exports = router;
