"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const path_1 = __importDefault(require("path"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const auth_routes_1 = __importDefault(require("./routes/auth.routes"));
const material_routes_1 = __importDefault(require("./routes/material.routes"));
const task_routes_1 = __importDefault(require("./routes/task.routes"));
const submission_routes_1 = __importDefault(require("./routes/submission.routes"));
const notification_routes_1 = __importDefault(require("./routes/notification.routes"));
const complaint_routes_1 = __importDefault(require("./routes/complaint.routes"));
const ai_routes_1 = __importDefault(require("./routes/ai.routes"));
const paper_routes_1 = __importDefault(require("./routes/paper.routes"));
const app = (0, express_1.default)();
const PORT = process.env.PORT || 5000;
app.use((0, cors_1.default)({
    origin: [
        "https://aiqpg-frontend-3wh6.vercel.app",
        "http://localhost:3000"
    ],
    credentials: true
}));
app.use(express_1.default.json({ limit: '50mb' }));
app.use(express_1.default.urlencoded({ extended: true, limit: '50mb' }));
app.use('/uploads', express_1.default.static(path_1.default.join(process.cwd(), 'uploads')));
app.get('/health', (_req, res) => res.json({ status: 'OK', time: new Date() }));
app.use('/api/v1/auth', auth_routes_1.default);
app.use('/api/v1/materials', material_routes_1.default);
app.use('/api/v1/tasks', task_routes_1.default);
app.use('/api/v1/submissions', submission_routes_1.default);
app.use('/api/v1/notifications', notification_routes_1.default);
app.use('/api/v1/complaints', complaint_routes_1.default);
app.use('/api/v1/ai', ai_routes_1.default);
app.use('/api/v1/papers', paper_routes_1.default);
app.listen(PORT, () => {
    console.log('Backend running on http://localhost:' + PORT);
    console.log('Frontend URL: http://localhost:3000');
});
exports.default = app;
