"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.assignClass = exports.selectClass = exports.joinClassByCode = exports.deleteClass = exports.createClass = exports.getClasses = exports.updateSubjects = exports.getUsers = exports.getMe = exports.azureLogin = void 0;
const db_1 = __importDefault(require("../config/db"));
const jwt_1 = require("../utils/jwt");
const response_1 = require("../utils/response");
const crypto_1 = __importDefault(require("crypto"));
// SINGLE FIXED COLLEGE - everyone belongs to KRMU
const COLLEGE_NAME = 'K.R Mangalam University';
const COLLEGE_DOMAIN = 'krmu.edu.in';
async function getMainCollege() {
    // Always use the FIRST college created - everyone shares it
    let college = await db_1.default.college.findFirst({ orderBy: { createdAt: 'asc' } });
    if (!college) {
        college = await db_1.default.college.create({
            data: { name: COLLEGE_NAME, domain: COLLEGE_DOMAIN }
        });
    }
    return college;
}
function genCode(branch, sem, section) {
    const base = (branch.slice(0, 3) + sem + section).toUpperCase().replace(/[^A-Z0-9]/g, '');
    const hash = crypto_1.default.randomBytes(2).toString('hex').toUpperCase();
    return base + '-' + hash;
}
const azureLogin = async (req, res) => {
    try {
        const { email, name, azureOid, avatarUrl } = req.body;
        if (!email)
            return (0, response_1.error)(res, 'Email required', 400);
        const role = (0, jwt_1.getRoleFromEmail)(email);
        if (role === 'unknown')
            return (0, response_1.error)(res, 'Access denied', 403);
        // EVERYONE goes to the SAME college
        const college = await getMainCollege();
        let user = await db_1.default.user.findUnique({ where: { email } });
        if (!user) {
            const prefix = email.split('@')[0];
            user = await db_1.default.user.create({
                data: {
                    collegeId: college.id,
                    name: name || prefix,
                    email,
                    role: role,
                    azureOid: azureOid || null,
                    avatarUrl: avatarUrl || null,
                    rollNumber: /^[0-9]/.test(prefix) ? prefix : null,
                }
            });
        }
        else {
            // Always update to main college (fixes old users in wrong college)
            user = await db_1.default.user.update({
                where: { id: user.id },
                data: {
                    collegeId: college.id, // Force correct college
                    lastLogin: new Date(),
                    avatarUrl: avatarUrl || user.avatarUrl,
                    name: name || user.name,
                }
            });
        }
        const token = (0, jwt_1.signToken)({
            userId: user.id,
            email: user.email,
            role: user.role,
            name: user.name,
            collegeId: college.id, // Always main college
            classSectionId: user.classSectionId,
        });
        return (0, response_1.success)(res, {
            token,
            user: {
                id: user.id, name: user.name, email: user.email,
                role: user.role, avatarUrl: user.avatarUrl,
                rollNumber: user.rollNumber, classSectionId: user.classSectionId,
                collegeId: college.id,
            }
        });
    }
    catch (err) {
        console.error('Login error:', err);
        return (0, response_1.error)(res, 'Login failed: ' + err.message, 500);
    }
};
exports.azureLogin = azureLogin;
const getMe = async (req, res) => {
    try {
        const { userId } = req.user;
        const user = await db_1.default.user.findUnique({
            where: { id: userId },
            select: {
                id: true, name: true, email: true, role: true,
                avatarUrl: true, rollNumber: true, subjects: true, classSectionId: true,
                classSection: { select: { id: true, name: true, section: true, branch: true, semester: true, uniqueCode: true } },
                college: { select: { name: true } }
            }
        });
        if (!user)
            return (0, response_1.error)(res, 'Not found', 404);
        // For students without class, also send available classes
        let availableClasses = [];
        if (user.role === 'student' && !user.classSectionId) {
            availableClasses = await db_1.default.classSection.findMany({
                where: { isActive: true },
                include: { _count: { select: { students: true } } },
                orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
            });
        }
        return (0, response_1.success)(res, { ...user, availableClasses });
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getMe = getMe;
const getUsers = async (req, res) => {
    try {
        const college = await getMainCollege();
        const { role, classSectionId } = req.query;
        const users = await db_1.default.user.findMany({
            where: {
                collegeId: college.id,
                ...(role && { role: role }),
                ...(classSectionId && { classSectionId: classSectionId }),
                isActive: true,
            },
            select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, classSectionId: true, classSection: { select: { id: true, name: true, section: true, branch: true, semester: true } } },
            orderBy: { name: 'asc' }
        });
        return (0, response_1.success)(res, users);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.getUsers = getUsers;
const updateSubjects = async (req, res) => {
    try {
        const { userId } = req.user;
        const { subjects } = req.body;
        const user = await db_1.default.user.update({ where: { id: userId }, data: { subjects } });
        return (0, response_1.success)(res, { subjects: user.subjects });
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.updateSubjects = updateSubjects;
const getClasses = async (req, res) => {
    try {
        const college = await getMainCollege();
        const classes = await db_1.default.classSection.findMany({
            where: { collegeId: college.id, isActive: true },
            include: { _count: { select: { students: true } } },
            orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
        });
        return (0, response_1.success)(res, classes);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.getClasses = getClasses;
const createClass = async (req, res) => {
    try {
        const college = await getMainCollege();
        const { name, section, semester, branch, year } = req.body;
        let uniqueCode = genCode(branch, semester, section);
        while (await db_1.default.classSection.findUnique({ where: { uniqueCode } })) {
            uniqueCode = genCode(branch, semester, section);
        }
        const cls = await db_1.default.classSection.create({
            data: { collegeId: college.id, name, section, semester: parseInt(semester), branch, year: parseInt(year), uniqueCode }
        });
        return (0, response_1.success)(res, cls, 'Created', 201);
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.createClass = createClass;
const deleteClass = async (req, res) => {
    try {
        await db_1.default.classSection.update({ where: { id: req.params.id }, data: { isActive: false } });
        return (0, response_1.success)(res, null, 'Deleted');
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.deleteClass = deleteClass;
const joinClassByCode = async (req, res) => {
    try {
        const { userId } = req.user;
        const { code } = req.body;
        if (!code)
            return (0, response_1.error)(res, 'Code required', 400);
        const cls = await db_1.default.classSection.findUnique({ where: { uniqueCode: code.toUpperCase().trim() } });
        if (!cls)
            return (0, response_1.error)(res, 'Invalid code: ' + code.toUpperCase().trim(), 404);
        if (!cls.isActive)
            return (0, response_1.error)(res, 'Class is inactive', 400);
        await db_1.default.user.update({ where: { id: userId }, data: { classSectionId: cls.id } });
        const user = await db_1.default.user.findUnique({ where: { id: userId } });
        const newToken = (0, jwt_1.signToken)({
            userId: user.id, email: user.email, role: user.role,
            name: user.name, collegeId: user.collegeId, classSectionId: cls.id
        });
        return (0, response_1.success)(res, { class: cls, token: newToken }, 'Joined class!');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.joinClassByCode = joinClassByCode;
const selectClass = async (req, res) => {
    try {
        const { userId } = req.user;
        const { classSectionId } = req.body;
        await db_1.default.user.update({ where: { id: userId }, data: { classSectionId } });
        const user = await db_1.default.user.findUnique({ where: { id: userId } });
        const newToken = (0, jwt_1.signToken)({
            userId: user.id, email: user.email, role: user.role,
            name: user.name, collegeId: user.collegeId, classSectionId
        });
        return (0, response_1.success)(res, { token: newToken }, 'Class selected');
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.selectClass = selectClass;
const assignClass = async (req, res) => {
    try {
        const { studentId, classSectionId } = req.body;
        await db_1.default.user.update({ where: { id: studentId }, data: { classSectionId } });
        return (0, response_1.success)(res, null, 'Assigned');
    }
    catch (err) {
        return (0, response_1.error)(res, err.message, 500);
    }
};
exports.assignClass = assignClass;
