const express = require("express");
const router = express.Router();
const notificationController = require("../controllers/notificationController");
const { auth } = require("../middleware/auth");

router.get("/", auth, notificationController.getNotifications);
router.post("/", auth, notificationController.createNotification);
router.patch("/:id/read", auth, notificationController.markNotificationRead);

module.exports = router;
