const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const supabase = require("../config/supabase");

const generateToken = (user) => {
  return jwt.sign(
    {
      id: user.id,
      username: user.username,
      role: user.role,
    },
    process.env.JWT_SECRET,
    { expiresIn: "1d" }
  );
};

const registerUser = async (req, res, next) => {
  try {
    const { username, password, role = "cashier" } = req.body;

    if (!username || !password) {
      return res.status(400).json({ success: false, error: "Username and password are required." });
    }

    const password_hash = await bcrypt.hash(password, 10);

    const { data, error } = await supabase
      .from("users")
      .insert([{ username, password_hash, role }])
      .select("id, username, role")
      .single();

    if (error) {
      if (error.code === "23505") {
        return res.status(409).json({ success: false, error: "Username already exists." });
      }
      throw error;
    }

    const token = generateToken(data);

    return res.status(201).json({
      success: true,
      data: {
        user: data,
        token,
      },
    });
  } catch (error) {
    next(error);
  }
};

const loginUser = async (req, res, next) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ success: false, error: "Username and password are required." });
    }

    const { data, error } = await supabase
      .from("users")
      .select("*")
      .eq("username", username)
      .single();

    if (error || !data) {
      return res.status(401).json({ success: false, error: "Invalid username or password." });
    }

    const isPasswordValid = await bcrypt.compare(password, data.password_hash);

    if (!isPasswordValid) {
      return res.status(401).json({ success: false, error: "Invalid username or password." });
    }

    const token = generateToken(data);

    return res.status(200).json({
      success: true,
      data: {
        user: {
          id: data.id,
          username: data.username,
          role: data.role,
        },
        token,
      },
    });
  } catch (error) {
    next(error);
  }
};

const getProfile = async (req, res, next) => {
  try {
    return res.status(200).json({
      success: true,
      data: {
        id: req.user.id,
        username: req.user.username,
        role: req.user.role,
      },
    });
  } catch (error) {
    next(error);
  }
};

const getUsers = async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from("users")
      .select("id, username, role, created_at")
      .order("created_at", { ascending: false });

    if (error) throw error;

    return res.status(200).json({
      success: true,
      data,
    });
  } catch (error) {
    next(error);
  }
};

const deleteUser = async (req, res, next) => {
  try {
    const { id } = req.params;

    if (id === req.user.id) {
      return res.status(400).json({
        success: false,
        error: "You cannot delete your own account.",
      });
    }

    const { data, error } = await supabase
      .from("users")
      .delete()
      .eq("id", id)
      .select("id, username");

    if (error) throw error;

    return res.status(200).json({
      success: true,
      data: data[0] || null,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  registerUser,
  loginUser,
  getProfile,
  getUsers,
  deleteUser,
};
