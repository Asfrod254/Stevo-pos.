const errorHandler = (err, req, res, next) => {
  console.error("Error:", err);

  const statusCode = err.statusCode || 500;

  return res.status(statusCode).json({
    success: false,
    error: err.message || "Internal Server Error",
  });
};

module.exports = errorHandler;
