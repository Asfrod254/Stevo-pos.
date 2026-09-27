const express = require("express");
const router = express.Router();
const orderController = require("../controllers/orderController");
const { auth, authorizeRoles } = require("../middleware/auth");

router.use(auth);

router.get("/", orderController.getAllOrders);
router.get("/:id", orderController.getOrderById);
router.post("/", authorizeRoles("admin", "manager"), orderController.createOrder);
router.put("/:id/status", authorizeRoles("admin", "manager"), orderController.updateOrderStatus);
router.delete("/:id", authorizeRoles("admin", "manager"), orderController.deleteOrder);

module.exports = router;
