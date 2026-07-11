"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getUnreadCount = exports.studentAlertTeacher = exports.sendBulkNotification = exports.deleteNotification = exports.markAllRead = exports.markRead = exports.getNotifications = void 0;
const db_1 = __importDefault(require("../config/db"));
const response_1 = require("../utils/response");
async function getMainCollegeId() {
    const college = await db_1.default.college.findFirst({ orderBy: { createdAt: 'asc' } });
    return college?.id || '';
}
const getNotifications = async (req, res) => {
    try {
        const { userId } = req.user;
        const notifications = await db_1.default.notification.findMany({
            where: { userId }, orderBy: { createdAt: 'desc' }, take: 50
        });
        return (0, response_1.success)(res, notifications);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getNotifications = getNotifications;
const markRead = async (req, res) => {
    try {
        const { userId } = req.user;
        await db_1.default.notification.updateMany({ where: { id: req.params.id, userId }, data: { isRead: true } });
        return (0, response_1.success)(res, null);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.markRead = markRead;
const markAllRead = async (req, res) => {
    try {
        const { userId } = req.user;
        await db_1.default.notification.updateMany({ where: { userId, isRead: false }, data: { isRead: true } });
        return (0, response_1.success)(res, null);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.markAllRead = markAllRead;
const deleteNotification = async (req, res) => {
    try {
        const { userId } = req.user;
        await db_1.default.notification.deleteMany({ where: { id: req.params.id, userId } });
        return (0, response_1.success)(res, null);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.deleteNotification = deleteNotification;
const sendBulkNotification = async (req, res) => {
    try {
        const { title, body, type, target, classIds } = req.body;
        const collegeId = await getMainCollegeId();
        let userFilter = { collegeId, isActive: true };
        if (target === 'all_students') {
            userFilter.role = 'student';
        }
        else if (target === 'specific_classes' && classIds?.length > 0) {
            userFilter.role = 'student';
            userFilter.classSectionId = { in: classIds };
        }
        else if (target === 'teachers') {
            userFilter.role = 'teacher';
        }
        else if (target === 'no_submission' && classIds?.length > 0) {
            // Send to students who haven't submitted a specific task
            userFilter.role = 'student';
            userFilter.classSectionId = { in: classIds };
        }
        const users = await db_1.default.user.findMany({ where: userFilter, select: { id: true, email: true, name: true } });
        if (users.length > 0) {
            await db_1.default.notification.createMany({
                data: users.map(u => ({ userId: u.id, title, body, type: type || 'announcement' }))
            });
        }
        return (0, response_1.success)(res, { sent: users.length, recipients: users.map(u => ({ name: u.name, email: u.email })) }, 'Sent to ' + users.length + ' users');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.sendBulkNotification = sendBulkNotification;
// Student alerts teacher that no data in class
const studentAlertTeacher = async (req, res) => {
    try {
        const { userId } = req.user;
        const { classSectionId, message } = req.body;
        const student = await db_1.default.user.findUnique({ where: { id: userId }, select: { name: true, email: true } });
        const cls = await db_1.default.classSection.findUnique({ where: { id: classSectionId }, select: { name: true, section: true } });
        const collegeId = await getMainCollegeId();
        // Notify all teachers
        const teachers = await db_1.default.user.findMany({ where: { collegeId, role: 'teacher', isActive: true }, select: { id: true } });
        if (teachers.length > 0) {
            await db_1.default.notification.createMany({
                data: teachers.map(t => ({
                    userId: t.id,
                    title: '📢 Student Alert from ' + (student?.name || 'Student'),
                    body: 'Class: ' + (cls?.name || '') + ' ' + (cls?.section || '') + ' — ' + (message || 'Please upload study materials for our class!'),
                    type: 'complaint',
                }))
            });
        }
        return (0, response_1.success)(res, null, 'Alert sent to teachers!');
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.studentAlertTeacher = studentAlertTeacher;
const getUnreadCount = async (req, res) => {
    try {
        const { userId } = req.user;
        const count = await db_1.default.notification.count({
            where: { userId, isRead: false }
        });
        return (0, response_1.success)(res, { count });
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getUnreadCount = getUnreadCount;
