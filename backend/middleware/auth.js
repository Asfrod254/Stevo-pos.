const jwt = require("jsonwebtoken");

const getJwtSecret = () => {
  const secret = process.env.JWT_SECRET;

  if (!secret) {
    throw new Error("JWT_SECRET is missing. Add it to Render Environment Variables or your backend .env file.");
  }

  return secret;
};

const auth = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ success: false, error: "Authentication token missing." });
  }

  const token = authHeader.split(" ")[1];

  try {
    const decoded = jwt.verify(token, getJwtSecret());
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ success: false, error: "Invalid or expired token." });
  }
};

const authorizeRoles = (...allowedRoles) => (req, res, next) => {
  if (!req.user) {
    return res.status(401).json({ success: false, error: "Authentication required." });
  }

  if (!allowedRoles.includes(req.user.role)) {
    return res.status(403).json({
      success: false,
      error: "You do not have permission to access this resource.",
    });
  }

  next();
};

module.exports = {
  auth,
  authorizeRoles,
};
