let notifications = [
  {
    id: 1,
    title: "Low stock alert",
    message: "Paint White is running low on inventory.",
    time: "2 min ago",
    type: "warning",
    read: false,
  },
  {
    id: 2,
    title: "Order received",
    message: "Jane Njeri placed an order for 2 items.",
    time: "15 min ago",
    type: "success",
    read: true,
  },
  {
    id: 3,
    title: "Daily summary",
    message: "Revenue is tracking above last week’s average.",
    time: "1 hour ago",
    type: "info",
    read: false,
  },
];

const getNotifications = async (req, res, next) => {
  try {
    return res.status(200).json({
      success: true,
      data: notifications,
    });
  } catch (error) {
    next(error);
  }
};

const createNotification = async (req, res, next) => {
  try {
    const { title, message, type = "info" } = req.body;

    if (!title || !message) {
      return res.status(400).json({
        success: false,
        error: "Title and message are required.",
      });
    }

    const newNotification = {
      id: Date.now(),
      title,
      message,
      time: "Just now",
      type,
      read: false,
    };

    notifications = [newNotification, ...notifications].slice(0, 20);

    return res.status(201).json({
      success: true,
      data: newNotification,
    });
  } catch (error) {
    next(error);
  }
};

const markNotificationRead = async (req, res, next) => {
  try {
    const { id } = req.params;
    const numericId = Number(id);

    if (Number.isNaN(numericId)) {
      return res.status(400).json({
        success: false,
        error: "Invalid notification id.",
      });
    }

    notifications = notifications.map((notification) => (
      notification.id === numericId ? { ...notification, read: true } : notification
    ));

    const updated = notifications.find((notification) => notification.id === numericId) || null;

    return res.status(200).json({
      success: true,
      data: updated,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getNotifications,
  createNotification,
  markNotificationRead,
};
