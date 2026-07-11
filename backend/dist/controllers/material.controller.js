"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deleteMaterial = exports.previewMaterial = exports.downloadMaterial = exports.getMaterials = exports.uploadMaterial = void 0;
const db_1 = __importDefault(require("../config/db"));
const response_1 = require("../utils/response");
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
async function getMainCollegeId() {
    const college = await db_1.default.college.findFirst({ orderBy: { createdAt: 'asc' } });
    return college?.id || '';
}
const uploadMaterial = async (req, res) => {
    try {
        const { userId } = req.user;
        const collegeId = await getMainCollegeId();
        const file = req.file;
        if (!file)
            return (0, response_1.error)(res, 'No file uploaded', 400);
        const { title, fileType, isPyq, year, subject, unit, examType, classSectionId } = req.body;
        const material = await db_1.default.material.create({
            data: {
                collegeId, uploadedBy: userId,
                title: title || file.originalname.replace(/\.[^.]+$/, ''),
                fileName: file.originalname,
                fileUrl: '/uploads/' + collegeId + '/' + file.filename,
                fileType: (isPyq === 'true' ? 'pyq' : fileType || 'notes'),
                fileSizeKb: Math.round(file.size / 1024),
                status: 'ready',
                isPyq: isPyq === 'true',
                subject: subject || null,
                unit: unit || null,
                year: year ? parseInt(year) : null,
                examType: examType || null,
                classSectionId: classSectionId || null,
            },
            include: { uploader: { select: { name: true } } }
        });
        // Notify ALL students in college (or class if specified)
        let f = { collegeId, role: 'student', isActive: true };
        if (classSectionId)
            f.classSectionId = classSectionId;
        const students = await db_1.default.user.findMany({ where: f, select: { id: true } });
        if (students.length > 0) {
            await db_1.default.notification.createMany({
                data: students.map(s => ({
                    userId: s.id,
                    title: isPyq === 'true' ? '📋 New PYQ Available' : '📚 New Study Material',
                    body: (title || file.originalname) + (subject ? ' — ' + subject : '') + (unit ? ' (' + unit + ')' : ''),
                    type: 'announcement',
                    refId: material.id,
                }))
            });
        }
        return (0, response_1.success)(res, material, 'Uploaded!', 201);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Upload failed: ' + err.message, 500);
    }
};
exports.uploadMaterial = uploadMaterial;
const getMaterials = async (req, res) => {
    try {
        const collegeId = await getMainCollegeId();
        const { isPyq, year, subject, unit, examType, search, classId } = req.query;
        const where = { collegeId };
        if (isPyq !== undefined)
            where.isPyq = isPyq === 'true';
        if (year)
            where.year = parseInt(year);
        if (subject)
            where.subject = { contains: subject, mode: 'insensitive' };
        if (unit)
            where.unit = { contains: unit, mode: 'insensitive' };
        if (examType)
            where.examType = examType;
        if (search)
            where.title = { contains: search, mode: 'insensitive' };
        // If classId given: show class materials + general materials
        // Otherwise: show ALL materials (for all students)
        if (classId && classId !== 'undefined' && classId !== '') {
            where.OR = [
                { classSectionId: classId },
                { classSectionId: null }
            ];
        }
        const materials = await db_1.default.material.findMany({
            where,
            include: {
                uploader: { select: { name: true } },
                classSection: { select: { name: true, section: true } }
            },
            orderBy: { createdAt: 'desc' }
        });
        return (0, response_1.success)(res, materials);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed: ' + err.message, 500);
    }
};
exports.getMaterials = getMaterials;
const downloadMaterial = async (req, res) => {
    try {
        const material = await db_1.default.material.findUnique({ where: { id: req.params.id } });
        if (!material)
            return (0, response_1.error)(res, 'Not found', 404);
        const filePath = path_1.default.join(process.cwd(), material.fileUrl);
        if (!fs_1.default.existsSync(filePath))
            return (0, response_1.success)(res, { fileUrl: material.fileUrl, fileName: material.fileName });
        res.setHeader('Content-Disposition', 'attachment; filename="' + material.fileName + '"');
        res.setHeader('Access-Control-Allow-Origin', '*');
        return res.download(filePath, material.fileName);
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.downloadMaterial = downloadMaterial;
const previewMaterial = async (req, res) => {
    try {
        const material = await db_1.default.material.findUnique({ where: { id: req.params.id } });
        if (!material)
            return (0, response_1.error)(res, 'Not found', 404);
        const filePath = path_1.default.join(process.cwd(), material.fileUrl);
        if (!fs_1.default.existsSync(filePath))
            return (0, response_1.error)(res, 'File not found', 404);
        const ext = path_1.default.extname(material.fileName).toLowerCase();
        const mimes = { '.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.txt': 'text/plain' };
        res.setHeader('Content-Type', mimes[ext] || 'application/pdf');
        res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"');
        res.setHeader('Access-Control-Allow-Origin', '*');
        return res.sendFile(path_1.default.resolve(filePath));
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.previewMaterial = previewMaterial;
const deleteMaterial = async (req, res) => {
    try {
        const material = await db_1.default.material.findUnique({ where: { id: req.params.id } });
        if (!material)
            return (0, response_1.error)(res, 'Not found', 404);
        const fp = path_1.default.join(process.cwd(), material.fileUrl);
        if (fs_1.default.existsSync(fp))
            fs_1.default.unlinkSync(fp);
        await db_1.default.material.delete({ where: { id: req.params.id } });
        return (0, response_1.success)(res, null, 'Deleted');
    }
    catch (err) {
        return (0, response_1.error)(res, 'Failed', 500);
    }
};
exports.deleteMaterial = deleteMaterial;
