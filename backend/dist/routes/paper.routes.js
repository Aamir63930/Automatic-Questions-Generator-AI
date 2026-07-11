"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const auth_middleware_1 = require("../middleware/auth.middleware");
const db_1 = __importDefault(require("../config/db"));
const router = (0, express_1.Router)();
router.post('/', auth_middleware_1.authenticate, async (req, res) => {
    try {
        const { userId, collegeId } = req.user;
        const { title, subject, examType, totalMarks, duration, questions } = req.body;
        const paper = await db_1.default.paper.create({
            data: { collegeId, createdBy: userId, title, subject, examType: examType || 'end_term', totalMarks, duration: duration || 180, questions: questions || [] }
        });
        return res.json({ success: true, data: paper });
    }
    catch (e) {
        return res.status(500).json({ success: false, message: e.message });
    }
});
router.get('/', auth_middleware_1.authenticate, async (req, res) => {
    try {
        const { collegeId } = req.user;
        const papers = await db_1.default.paper.findMany({ where: { collegeId }, orderBy: { createdAt: 'desc' } });
        return res.json({ success: true, data: papers });
    }
    catch (e) {
        return res.status(500).json({ success: false, message: e.message });
    }
});
router.get('/:id', auth_middleware_1.authenticate, async (req, res) => {
    try {
        const paper = await db_1.default.paper.findUnique({ where: { id: req.params.id } });
        return res.json({ success: true, data: paper });
    }
    catch (e) {
        return res.status(500).json({ success: false, message: e.message });
    }
});
exports.default = router;
