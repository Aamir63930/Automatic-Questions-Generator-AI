"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const material_controller_1 = require("../controllers/material.controller");
const auth_middleware_1 = require("../middleware/auth.middleware");
const upload_middleware_1 = require("../middleware/upload.middleware");
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
const client_1 = require("@prisma/client");
const prisma = new client_1.PrismaClient();
const router = (0, express_1.Router)();
router.post('/upload', auth_middleware_1.authenticate, (0, auth_middleware_1.authorize)('teacher', 'admin'), upload_middleware_1.upload.single('file'), material_controller_1.uploadMaterial);
router.get('/', auth_middleware_1.authenticate, material_controller_1.getMaterials);
router.get('/:id/download', auth_middleware_1.authenticate, material_controller_1.downloadMaterial);
router.get('/:id/preview', auth_middleware_1.authenticate, material_controller_1.previewMaterial);
router.delete('/:id', auth_middleware_1.authenticate, (0, auth_middleware_1.authorize)('teacher', 'admin'), material_controller_1.deleteMaterial);
// Public inline view - no auth - opens PDF directly in browser
router.get('/:id/view', async (req, res) => {
    try {
        const material = await prisma.material.findUnique({ where: { id: req.params.id } });
        if (!material)
            return res.status(404).send('File not found');
        const filePath = path_1.default.join(process.cwd(), material.fileUrl);
        if (!fs_1.default.existsSync(filePath))
            return res.status(404).send('File not on server');
        const ext = path_1.default.extname(material.fileName).toLowerCase();
        const mimes = { '.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.txt': 'text/plain' };
        res.setHeader('Content-Type', mimes[ext] || 'application/pdf');
        res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"');
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('X-Frame-Options', 'SAMEORIGIN');
        return res.sendFile(path_1.default.resolve(filePath));
    }
    catch (e) {
        return res.status(500).send(e.message);
    }
});
exports.default = router;
