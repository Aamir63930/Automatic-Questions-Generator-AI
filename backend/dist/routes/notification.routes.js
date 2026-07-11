"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const notification_controller_1 = require("../controllers/notification.controller");
const auth_middleware_1 = require("../middleware/auth.middleware");
const db_1 = __importDefault(require("../config/db"));
const router = (0, express_1.Router)();
router.get('/', auth_middleware_1.authenticate, notification_controller_1.getNotifications);
router.get('/unread-count', auth_middleware_1.authenticate, notification_controller_1.getUnreadCount);
router.patch('/read-all', auth_middleware_1.authenticate, notification_controller_1.markAllRead);
router.patch('/:id/read', auth_middleware_1.authenticate, notification_controller_1.markRead);
router.delete('/:id', auth_middleware_1.authenticate, notification_controller_1.deleteNotification);
router.post('/send', auth_middleware_1.authenticate, (0, auth_middleware_1.authorize)('teacher', 'admin'), notification_controller_1.sendBulkNotification);
router.post('/student-alert', auth_middleware_1.authenticate, (0, auth_middleware_1.authorize)('student'), notification_controller_1.studentAlertTeacher);
// Direct notification to one user
router.post('/', auth_middleware_1.authenticate, async (req, res) => {
    try {
        const { userId, title, body, type, refId } = req.body;
        if (!userId || !title)
            return res.status(400).json({ success: false, message: 'userId and title required' });
        const notif = await db_1.default.notification.create({
            data: { userId, title, body: body || '', type: type || 'announcement', refId: refId || null }
        });
        return res.json({ success: true, data: notif });
    }
    catch (e) {
        return res.status(500).json({ success: false, message: e.message });
    }
});
exports.default = router;
