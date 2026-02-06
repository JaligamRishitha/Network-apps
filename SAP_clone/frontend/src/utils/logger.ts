/**
 * Enhanced Logging Utility
 * Provides structured logging with different levels and better error handling
 */

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
}

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    data?: any;
    context?: string;
    userId?: string;
}

class Logger {
    private logLevel: LogLevel;
    private isDevelopment: boolean;
    private logs: LogEntry[] = [];
    private maxLogs = 1000; // Keep last 1000 logs in memory

    constructor() {
        this.isDevelopment = import.meta.env.DEV;
        this.logLevel = this.isDevelopment ? LogLevel.DEBUG : LogLevel.INFO;
    }

    private formatMessage(level: string, message: string, data?: any, context?: string): LogEntry {
        const entry: LogEntry = {
            timestamp: new Date().toISOString(),
            level,
            message,
            context,
        };

        if (data !== undefined) {
            entry.data = data;
        }

        // Add user context if available
        const user = localStorage.getItem('user');
        if (user) {
            try {
                const userData = JSON.parse(user);
                entry.userId = userData.username;
            } catch (e) {
                // Ignore parsing errors
            }
        }

        return entry;
    }

    private addToMemory(entry: LogEntry) {
        this.logs.push(entry);
        if (this.logs.length > this.maxLogs) {
            this.logs.shift(); // Remove oldest log
        }
    }

    private shouldLog(level: LogLevel): boolean {
        return level >= this.logLevel;
    }

    debug(message: string, data?: any, context?: string) {
        if (!this.shouldLog(LogLevel.DEBUG)) return;

        const entry = this.formatMessage('DEBUG', message, data, context);
        this.addToMemory(entry);

        if (this.isDevelopment) {
            console.log(`🔍 [${entry.timestamp}] ${context ? `[${context}] ` : ''}${message}`, data || '');
        }
    }

    info(message: string, data?: any, context?: string) {
        if (!this.shouldLog(LogLevel.INFO)) return;

        const entry = this.formatMessage('INFO', message, data, context);
        this.addToMemory(entry);

        if (this.isDevelopment) {
            console.info(`ℹ️ [${entry.timestamp}] ${context ? `[${context}] ` : ''}${message}`, data || '');
        }
    }

    warn(message: string, data?: any, context?: string) {
        if (!this.shouldLog(LogLevel.WARN)) return;

        const entry = this.formatMessage('WARN', message, data, context);
        this.addToMemory(entry);

        console.warn(`⚠️ [${entry.timestamp}] ${context ? `[${context}] ` : ''}${message}`, data || '');
    }

    error(message: string, error?: any, context?: string) {
        if (!this.shouldLog(LogLevel.ERROR)) return;

        // Enhanced error processing
        let errorData = error;
        if (error instanceof Error) {
            errorData = {
                name: error.name,
                message: error.message,
                stack: error.stack,
            };
        } else if (error?.response) {
            // Axios error
            errorData = {
                status: error.response.status,
                statusText: error.response.statusText,
                data: error.response.data,
                url: error.config?.url,
                method: error.config?.method,
            };
        }

        const entry = this.formatMessage('ERROR', message, errorData, context);
        this.addToMemory(entry);

        console.error(`❌ [${entry.timestamp}] ${context ? `[${context}] ` : ''}${message}`, errorData || '');

        // In production, you might want to send errors to a logging service
        if (!this.isDevelopment) {
            this.sendToLoggingService(entry);
        }
    }

    // API call logging helper
    apiCall(method: string, url: string, data?: any, context?: string) {
        this.debug(`API ${method.toUpperCase()} ${url}`, data, context || 'API');
    }

    apiSuccess(method: string, url: string, response?: any, context?: string) {
        this.info(`API ${method.toUpperCase()} ${url} - Success`, response, context || 'API');
    }

    apiError(method: string, url: string, error: any, context?: string) {
        this.error(`API ${method.toUpperCase()} ${url} - Failed`, error, context || 'API');
    }

    // User action logging
    userAction(action: string, data?: any, context?: string) {
        this.info(`User action: ${action}`, data, context || 'USER');
    }

    // Performance logging
    performance(operation: string, duration: number, context?: string) {
        const level = duration > 1000 ? 'WARN' : 'INFO';
        const message = `Performance: ${operation} took ${duration}ms`;

        if (level === 'WARN') {
            this.warn(message, { duration }, context || 'PERF');
        } else {
            this.info(message, { duration }, context || 'PERF');
        }
    }

    // Get logs for debugging
    getLogs(level?: string, limit?: number): LogEntry[] {
        let filteredLogs = this.logs;

        if (level) {
            filteredLogs = this.logs.filter(log => log.level === level.toUpperCase());
        }

        if (limit) {
            return filteredLogs.slice(-limit);
        }

        return filteredLogs;
    }

    // Clear logs
    clearLogs() {
        this.logs = [];
        this.info('Logs cleared', undefined, 'LOGGER');
    }

    // Export logs as JSON
    exportLogs(): string {
        return JSON.stringify(this.logs, null, 2);
    }

    // Send to external logging service (placeholder)
    private async sendToLoggingService(entry: LogEntry) {
        try {
            // In a real application, you would send to services like:
            // - Sentry
            // - LogRocket
            // - DataDog
            // - Custom logging endpoint

            // Example implementation:
            // await fetch('/api/logs', {
            //   method: 'POST',
            //   headers: { 'Content-Type': 'application/json' },
            //   body: JSON.stringify(entry)
            // });
        } catch (e) {
            // Fail silently to avoid logging loops
        }
    }

    // Set log level dynamically
    setLogLevel(level: LogLevel) {
        this.logLevel = level;
        this.info(`Log level changed to ${LogLevel[level]}`, undefined, 'LOGGER');
    }
}

// Create singleton instance
const logger = new Logger();

// Export both the instance and the class for flexibility
export { Logger };
export default logger;

// Convenience functions for quick access
export const log = {
    debug: (message: string, data?: any, context?: string) => logger.debug(message, data, context),
    info: (message: string, data?: any, context?: string) => logger.info(message, data, context),
    warn: (message: string, data?: any, context?: string) => logger.warn(message, data, context),
    error: (message: string, error?: any, context?: string) => logger.error(message, error, context),
    apiCall: (method: string, url: string, data?: any, context?: string) => logger.apiCall(method, url, data, context),
    apiSuccess: (method: string, url: string, response?: any, context?: string) => logger.apiSuccess(method, url, response, context),
    apiError: (method: string, url: string, error: any, context?: string) => logger.apiError(method, url, error, context),
    userAction: (action: string, data?: any, context?: string) => logger.userAction(action, data, context),
    performance: (operation: string, duration: number, context?: string) => logger.performance(operation, duration, context),
};