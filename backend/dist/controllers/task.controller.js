"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deleteTask = exports.extendDeadline = exports.updateTaskStatus = exports.getTask = exports.getTasks = exports.createBulkTasks = exports.createTask = void 0;
const db_1 = __importDefault(require("../config/db"));
const response_1 = require("../utils/response");
async function getMainCollegeId() {
    const college = await db_1.default.college.findFirst({ orderBy: { createdAt: 'asc' } });
    return college?.id || '';
}
const createTask = async (req, res) => {
    try {
        const { userId } = req.user;
        const collegeId = await getMainCollegeId();
        const { title, description, taskType, subjectName, classSectionId, deadline, maxMarks, instructions, allowLate } = req.body;
        const task = await db_1.default.task.create({
            data: {
                collegeId, createdBy: userId, title,
                description: description || null,
                taskType: taskType,
                subjectName: subjectName || null,
                classSectionId: classSectionId || null,
                deadline: deadline ? new Date(deadline) : null,
                maxMarks: parseInt(maxMarks) || 10,
                instructions: instructions || null,
                allowLate: allowLate === 'true' || allowLate === true,
                attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,
            },
            include: {
                creator: { select: { name: true } },
                classSection: { select: { name: true, section: true, branch: true } }
            }
        });
        // IMPORTANT: Only notify students in the specific class
        // If no class selected, notify ALL students
        let studentFilter = { collegeId, role: 'student', isActive: true };
        if (classSectionId && classSectionId !== '' && classSectionId !== 'null') {
            // Only this class
            studentFilter.classSectionId = classSectionId;
        }
        // else: all students
        const students = await db_1.default.user.findMany({ where: studentFilter, select: { id: true } });
        if (students.length > 0) {
            await db_1.default.notification.createMany({
                data: students.map(s => ({
                    userId: s.id,
                    title: '📋 New ' + (taskType || 'assignment').replace('_', ' '),
                    body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }) : ''),
                    type: 'task', refId: task.id,
                }))
            });
        }
        return (0, response_1.success)(res, task, 'Task created', 201);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.createTask = createTask;
const createBulkTasks = async (req, res) => {
    try {
        const { userId } = req.user;
        const collegeId = await getMainCollegeId();
        const { tasks } = req.body;
        const created = [];
        for (const t of tasks) {
            const task = await db_1.default.task.create({
                data: { collegeId, createdBy: userId, title: t.title, taskType: t.taskType, subjectName: t.subjectName || null, classSectionId: t.classSectionId || null, deadline: t.deadline ? new Date(t.deadline) : null, maxMarks: parseInt(t.maxMarks) || 10 }
            });
            created.push(task);
        }
        return (0, response_1.success)(res, created, created.length + ' tasks created', 201);
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.createBulkTasks = createBulkTasks;
const getTasks = async (req, res) => {
    try {
        const { role, userId } = req.user;
        const collegeId = await getMainCollegeId();
        const { classId } = req.query;
        let where = { collegeId };
        if (role === 'student') {
            where.status = 'active';
            const classIdStr = classId;
            if (classIdStr && classIdStr !== 'undefined' && classIdStr !== '') {
                // Student sees: tasks for THEIR class + tasks with NO class (college-wide)
                where.OR = [
                    { classSectionId: classIdStr },
                    { classSectionId: null }
                ];
            }
            // If no classId: show only college-wide tasks (no class assigned)
        }
        else if (role === 'teacher') {
            const classIdStr = classId;
            if (classIdStr && classIdStr !== 'undefined' && classIdStr !== '') {
                where.classSectionId = classIdStr;
            }
        }
        const tasks = await db_1.default.task.findMany({
            where,
            include: {
                creator: { select: { name: true, email: true } },
                classSection: { select: { name: true, section: true, branch: true } },
                _count: { select: { submissions: true } }
            },
            orderBy: { createdAt: 'desc' }
        });
        return (0, response_1.success)(res, tasks);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.getTasks = getTasks;
const getTask = async (req, res) => {
    try {
        const collegeId = await getMainCollegeId();
        const task = await db_1.default.task.findFirst({
            where: { id: req.params.id, collegeId },
            include: { creator: { select: { name: true } }, classSection: { select: { name: true, section: true } }, submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } } }
        });
        if (!task)
            return (0, response_1.error)(res, 'Not found', 404);
        return (0, response_1.success)(res, task);
    }
    catch {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getTask = getTask;
const updateTaskStatus = async (req, res) => {
    try {
        const task = await db_1.default.task.update({ where: { id: req.params.id }, data: { status: req.body.status } });
        return (0, response_1.success)(res, task);
    }
    catch {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.updateTaskStatus = updateTaskStatus;
const extendDeadline = async (req, res) => {
    try {
        const collegeId = await getMainCollegeId();
        const { newDeadline } = req.body;
        const task = await db_1.default.task.update({
            where: { id: req.params.id },
            data: { deadline: new Date(newDeadline), allowLate: true }
        });
        const f = { collegeId, role: 'student', isActive: true };
        if (task.classSectionId)
            f.classSectionId = task.classSectionId;
        const students = await db_1.default.user.findMany({ where: f, select: { id: true } });
        if (students.length > 0) {
            await db_1.default.notification.createMany({
                data: students.map(s => ({ userId: s.id, title: '⏰ Deadline Extended', body: '"' + task.title + '" extended to ' + new Date(newDeadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }), type: 'task', refId: task.id }))
            });
        }
        return (0, response_1.success)(res, task, 'Extended');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.extendDeadline = extendDeadline;
const deleteTask = async (req, res) => {
    try {
        await db_1.default.task.delete({ where: { id: req.params.id } });
        return (0, response_1.success)(res, null, 'Deleted');
    }
    catch {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.deleteTask = deleteTask;
