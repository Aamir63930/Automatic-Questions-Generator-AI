"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateComplaintStatus = exports.replyComplaint = exports.getComplaints = exports.createComplaint = void 0;
const db_1 = __importDefault(require("../config/db"));
const response_1 = require("../utils/response");
const createComplaint = async (req, res) => {
    try {
        const { userId, collegeId, role } = req.user;
        const { subject, category, description, targetRole } = req.body;
        const user = await db_1.default.user.findUnique({ where: { id: userId }, select: { name: true, role: true } });
        const complaint = await db_1.default.complaint.create({
            data: {
                raisedBy: userId, subject,
                category: category || 'General',
                messages: {
                    create: { sentBy: userId, senderName: user?.name || 'User', senderRole: user?.role || role, message: description }
                }
            },
            include: { raiser: { select: { name: true, email: true } }, messages: true }
        });
        // Notify relevant users
        // Students notify teachers; teachers notify admins or other teachers
        const notifyFilter = { collegeId, isActive: true };
        if (role === 'student') {
            notifyFilter.role = 'teacher';
        }
        else {
            // Teacher complaint - notify all teachers
            notifyFilter.role = 'teacher';
        }
        const toNotify = await db_1.default.user.findMany({ where: notifyFilter, select: { id: true } });
        const filtered = toNotify.filter(u => u.id !== userId); // don't notify self
        if (filtered.length > 0) {
            await db_1.default.notification.createMany({
                data: filtered.map(u => ({
                    userId: u.id,
                    title: 'New Complaint from ' + (user?.name || 'User'),
                    body: subject + ' — ' + (category || 'General'),
                    type: 'complaint', refId: complaint.id,
                }))
            });
        }
        return (0, response_1.success)(res, complaint, 'Complaint raised', 201);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.createComplaint = createComplaint;
const getComplaints = async (req, res) => {
    try {
        const { userId, role } = req.user;
        const complaints = await db_1.default.complaint.findMany({
            where: role === 'student' ? { raisedBy: userId } : {},
            include: {
                raiser: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } },
                messages: { orderBy: { createdAt: 'asc' } }
            },
            orderBy: { createdAt: 'desc' }
        });
        return (0, response_1.success)(res, complaints);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getComplaints = getComplaints;
const replyComplaint = async (req, res) => {
    try {
        const { userId } = req.user;
        const id = req.params.id;
        const { message } = req.body;
        const sender = await db_1.default.user.findUnique({ where: { id: userId }, select: { name: true, role: true } });
        const msg = await db_1.default.complaintMessage.create({
            data: { complaintId: id, sentBy: userId, senderName: sender?.name || 'User', senderRole: sender?.role || 'student', message }
        });
        await db_1.default.complaint.update({ where: { id }, data: { status: 'in_progress', updatedAt: new Date() } });
        const complaint = await db_1.default.complaint.findUnique({ where: { id } });
        if (complaint && sender?.role === 'teacher') {
            await db_1.default.notification.create({
                data: { userId: complaint.raisedBy, title: 'Reply from Teacher', body: message.slice(0, 80), type: 'complaint', refId: id }
            });
        }
        else if (complaint && sender?.role === 'student') {
            // Find teachers to notify
            const teachers = await db_1.default.user.findMany({ where: { role: 'teacher', isActive: true }, select: { id: true }, take: 3 });
            if (teachers.length > 0) {
                await db_1.default.notification.createMany({
                    data: teachers.map(t => ({ userId: t.id, title: 'New Reply on Complaint', body: message.slice(0, 80), type: 'complaint', refId: id }))
                });
            }
        }
        return (0, response_1.success)(res, msg, 'Reply sent');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.replyComplaint = replyComplaint;
const updateComplaintStatus = async (req, res) => {
    try {
        const id = req.params.id;
        const { status } = req.body;
        const complaint = await db_1.default.complaint.update({
            where: { id },
            data: { status: status, ...(status === 'resolved' && { resolvedAt: new Date() }) }
        });
        await db_1.default.notification.create({
            data: { userId: complaint.raisedBy, title: 'Complaint ' + status.replace('_', ' '), body: '"' + complaint.subject + '" is now ' + status.replace('_', ' '), type: 'complaint', refId: id }
        });
        return (0, response_1.success)(res, complaint, 'Updated');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.updateComplaintStatus = updateComplaintStatus;
