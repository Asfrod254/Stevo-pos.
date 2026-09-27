const express = require("express");
const router = express.Router();
const userController = require("../controllers/userController");
const { auth, authorizeRoles } = require("../middleware/auth");

router.post("/register", userController.registerUser);
router.post("/login", userController.loginUser);
router.get("/profile", auth, userController.getProfile);
router.get("/", auth, authorizeRoles("admin"), userController.getUsers);
router.delete("/:id", auth, authorizeRoles("admin"), userController.deleteUser);

module.exports = router;
