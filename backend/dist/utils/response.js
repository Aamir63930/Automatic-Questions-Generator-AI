"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.error = exports.success = void 0;
const success = (res, data, message = 'Success', status = 200) => {
    return res.status(status).json({ success: true, message, data });
};
exports.success = success;
const error = (res, message = 'Error', status = 500, details) => {
    return res.status(status).json({ success: false, message, ...(details && { details }) });
};
exports.error = error;
