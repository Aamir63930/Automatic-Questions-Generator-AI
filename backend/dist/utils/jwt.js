"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRoleFromEmail = getRoleFromEmail;
exports.signToken = signToken;
exports.verifyToken = verifyToken;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const SECRET = process.env.JWT_SECRET || 'aiqpg-secret-key-krmu-2024';
const EXPIRES = process.env.JWT_EXPIRES_IN || '30d';
const SPECIAL_TEACHERS = ['akumarjaan123@gmail.com'];
function getRoleFromEmail(email) {
    if (!email)
        return 'unknown';
    if (SPECIAL_TEACHERS.includes(email.toLowerCase()))
        return 'teacher';
    const prefix = email.split('@')[0];
    const domain = email.split('@')[1];
    // Accept any domain for now (college-wide access)
    if (!domain)
        return 'unknown';
    // Numbers = student, letters = teacher
    if (/^[0-9]/.test(prefix))
        return 'student';
    if (/^[a-zA-Z]/.test(prefix))
        return 'teacher';
    return 'unknown';
}
function signToken(payload) {
    return jsonwebtoken_1.default.sign(payload, SECRET, { expiresIn: EXPIRES });
}
function verifyToken(token) {
    return jsonwebtoken_1.default.verify(token, SECRET);
}
