"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.gradeSubmission = exports.getTaskSubmissionStatus = exports.getPendingSummary = exports.getResultsSummary = exports.getSubmissions = exports.createSubmission = void 0;
const db_1 = __importDefault(require("../config/db"));
const response_1 = require("../utils/response");
async function getMainCollegeId() {
    const college = await db_1.default.college.findFirst({ orderBy: { createdAt: 'asc' } });
    return college?.id || '';
}
const createSubmission = async (req, res) => {
    try {
        const { userId, collegeId } = req.user;
        const { taskId, textAnswer } = req.body;
        const file = req.file;
        const tid = taskId;
        const task = await db_1.default.task.findFirst({ where: { id: tid, collegeId } });
        if (!task)
            return (0, response_1.error)(res, 'Task not found', 404);
        if (task.status !== 'active')
            return (0, response_1.error)(res, 'Task is closed', 400);
        const existing = await db_1.default.submission.findUnique({
            where: { taskId_studentId: { taskId: tid, studentId: userId } }
        });
        if (existing)
            return (0, response_1.error)(res, 'Already submitted', 400);
        const isLate = task.deadline && new Date() > task.deadline;
        if (isLate && !task.allowLate)
            return (0, response_1.error)(res, 'Deadline has passed', 400);
        const submission = await db_1.default.submission.create({
            data: {
                taskId: tid, studentId: userId,
                textAnswer: textAnswer || null,
                fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
                fileName: file?.originalname || null,
                status: (isLate ? 'late' : 'submitted'),
            },
            include: {
                student: { select: { name: true } },
                task: { select: { title: true, maxMarks: true } }
            }
        });
        await db_1.default.notification.create({
            data: {
                userId: task.createdBy,
                title: '📥 New Submission',
                body: (submission.student.name || 'Student') + ' submitted "' + task.title + '"',
                type: 'task', refId: tid
            }
        });
        return (0, response_1.success)(res, submission, 'Submitted!', 201);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.createSubmission = createSubmission;
const getSubmissions = async (req, res) => {
    try {
        const { userId, role } = req.user;
        const { taskId } = req.query;
        const submissions = await db_1.default.submission.findMany({
            where: {
                ...(taskId && { taskId: taskId }),
                ...(role === 'student' && { studentId: userId }),
            },
            include: {
                student: {
                    select: {
                        name: true, email: true, rollNumber: true, avatarUrl: true,
                        classSectionId: true,
                        classSection: { select: { name: true, section: true, branch: true } }
                    }
                },
                task: { select: { title: true, maxMarks: true, taskType: true, subjectName: true } }
            },
            orderBy: { submittedAt: 'desc' }
        });
        return (0, response_1.success)(res, submissions);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getSubmissions = getSubmissions;
const getResultsSummary = async (req, res) => {
    try {
        const { collegeId, userId } = req.user;
        const { classId } = req.query;
        const subs = await db_1.default.submission.findMany({
            where: {
                task: {
                    collegeId,
                    createdBy: userId,
                    ...(classId && classId !== 'undefined' && { classSectionId: classId })
                }
            },
            include: {
                student: {
                    select: {
                        id: true, name: true, email: true, rollNumber: true, classSectionId: true,
                        classSection: { select: { id: true, name: true, section: true, branch: true } }
                    }
                },
                task: { select: { id: true, title: true, maxMarks: true, taskType: true, subjectName: true } }
            },
            orderBy: { submittedAt: 'desc' }
        });
        const byClass = {};
        for (const sub of subs) {
            const cls = sub.student.classSection;
            const classKey = cls ? cls.id : 'no_class';
            const className = cls ? cls.name + ' ' + cls.section : 'No Class';
            if (!byClass[classKey]) {
                byClass[classKey] = { classId: classKey, className, branch: cls?.branch || '', students: {}, submissions: [] };
            }
            byClass[classKey].submissions.push(sub);
            const sid = sub.student.id;
            if (!byClass[classKey].students[sid]) {
                byClass[classKey].students[sid] = {
                    id: sid, name: sub.student.name, email: sub.student.email,
                    rollNumber: sub.student.rollNumber, tasks: [], totalObtained: 0, totalMax: 0
                };
            }
            byClass[classKey].students[sid].tasks.push({
                taskId: sub.task.id, title: sub.task.title, maxMarks: sub.task.maxMarks,
                subjectName: sub.task.subjectName, marksAwarded: sub.marksAwarded,
                status: sub.status, submittedAt: sub.submittedAt, feedback: sub.feedback,
                submissionId: sub.id
            });
            if (sub.marksAwarded !== null) {
                byClass[classKey].students[sid].totalObtained += sub.marksAwarded;
                byClass[classKey].students[sid].totalMax += sub.task.maxMarks;
            }
        }
        const result = Object.values(byClass).map((cls) => {
            const students = Object.values(cls.students).map((s) => ({
                ...s,
                avgPct: s.totalMax > 0 ? Math.round((s.totalObtained / s.totalMax) * 100) : null,
                grade: s.totalMax > 0 ? (s.totalObtained / s.totalMax >= 0.8 ? 'A' : s.totalObtained / s.totalMax >= 0.6 ? 'B' : s.totalObtained / s.totalMax >= 0.4 ? 'C' : 'F') : '-'
            })).sort((a, b) => (b.totalObtained || 0) - (a.totalObtained || 0));
            return { ...cls, students, studentCount: students.length };
        });
        return (0, response_1.success)(res, result);
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.getResultsSummary = getResultsSummary;
const getPendingSummary = async (req, res) => {
    try {
        const { userId, collegeId } = req.user;
        const tasks = await db_1.default.task.findMany({
            where: { collegeId, createdBy: userId },
            include: {
                classSection: { select: { name: true, section: true, branch: true } },
                submissions: { select: { id: true, marksAwarded: true, studentId: true } }
            }
        });
        const summary = await Promise.all(tasks.map(async (t) => {
            const total = t.submissions.length;
            const graded = t.submissions.filter(s => s.marksAwarded !== null).length;
            const f = { collegeId, role: 'student', isActive: true };
            if (t.classSectionId)
                f.classSectionId = t.classSectionId;
            const totalStudents = await db_1.default.user.count({ where: f });
            const submittedIds = t.submissions.map(s => s.studentId);
            const notSubmitted = await db_1.default.user.findMany({
                where: { ...f, id: { notIn: submittedIds } },
                select: { id: true, name: true, email: true, rollNumber: true }
            });
            return {
                taskId: t.id, title: t.title, maxMarks: t.maxMarks,
                className: t.classSection ? t.classSection.name + ' ' + t.classSection.section : 'All Students',
                totalStudents, submittedCount: total, notSubmittedCount: totalStudents - total,
                graded, pending: total - graded, notSubmitted
            };
        }));
        return (0, response_1.success)(res, { totalPending: summary.reduce((s, x) => s + x.pending, 0), tasks: summary });
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.getPendingSummary = getPendingSummary;
const getTaskSubmissionStatus = async (req, res) => {
    try {
        const { collegeId } = req.user;
        const taskId = req.params.taskId;
        const task = await db_1.default.task.findFirst({ where: { id: taskId, collegeId } });
        if (!task)
            return (0, response_1.error)(res, 'Not found', 404);
        const f = { collegeId, role: 'student', isActive: true };
        if (task.classSectionId)
            f.classSectionId = task.classSectionId;
        const allStudents = await db_1.default.user.findMany({ where: f, select: { id: true, name: true, rollNumber: true, avatarUrl: true } });
        const subs = await db_1.default.submission.findMany({
            where: { taskId },
            select: { studentId: true, status: true, marksAwarded: true, submittedAt: true }
        });
        const subMap = new Map(subs.map(s => [s.studentId, s]));
        return (0, response_1.success)(res, {
            total: allStudents.length, submittedCount: subs.length,
            notSubmittedCount: allStudents.length - subs.length,
            submitted: allStudents.filter(s => subMap.has(s.id)).map(s => ({ ...s, ...subMap.get(s.id) })),
            notSubmitted: allStudents.filter(s => !subMap.has(s.id))
        });
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.getTaskSubmissionStatus = getTaskSubmissionStatus;
const gradeSubmission = async (req, res) => {
    try {
        const { userId } = req.user;
        const id = req.params.id;
        const { marks, feedback } = req.body;
        const submission = await db_1.default.submission.update({
            where: { id },
            data: {
                marksAwarded: parseInt(marks), feedback: feedback || null,
                gradedBy: userId, gradedAt: new Date(), status: 'graded'
            },
            include: { task: { select: { title: true, maxMarks: true } } }
        });
        await db_1.default.notification.create({
            data: {
                userId: submission.studentId,
                title: '📊 Result Published!',
                body: '"' + submission.task.title + '" graded: ' + marks + '/' + submission.task.maxMarks + (feedback ? ' — ' + feedback : ''),
                type: 'result', refId: submission.taskId
            }
        });
        return (0, response_1.success)(res, submission, 'Graded!');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.gradeSubmission = gradeSubmission;
