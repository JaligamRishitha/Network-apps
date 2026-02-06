/**
 * Performance Monitoring Utility
 * Tracks API calls, component renders, and user interactions
 */
import logger from './logger';

interface PerformanceEntry {
    name: string;
    startTime: number;
    endTime?: number;
    duration?: number;
    metadata?: any;
}

class PerformanceMonitor {
    private entries: Map<string, PerformanceEntry> = new Map();
    private completedEntries: PerformanceEntry[] = [];
    private maxEntries = 500;

    // Start timing an operation
    start(name: string, metadata?: any): void {
        const entry: PerformanceEntry = {
            name,
            startTime: performance.now(),
            metadata,
        };

        this.entries.set(name, entry);
        logger.debug(`Performance tracking started: ${name}`, metadata, 'PERF');
    }

    // End timing an operation
    end(name: string, additionalMetadata?: any): number | null {
        const entry = this.entries.get(name);
        if (!entry) {
            logger.warn(`Performance tracking not found: ${name}`, undefined, 'PERF');
            return null;
        }

        entry.endTime = performance.now();
        entry.duration = entry.endTime - entry.startTime;

        if (additionalMetadata) {
            entry.metadata = { ...entry.metadata, ...additionalMetadata };
        }

        // Move to completed entries
        this.completedEntries.push({ ...entry });
        this.entries.delete(name);

        // Maintain max entries limit
        if (this.completedEntries.length > this.maxEntries) {
            this.completedEntries.shift();
        }

        // Log performance
        logger.performance(name, entry.duration, 'PERF');

        return entry.duration;
    }

    // Measure a function execution
    measure<T>(name: string, fn: () => T, metadata?: any): T {
        this.start(name, metadata);
        try {
            const result = fn();
            this.end(name);
            return result;
        } catch (error) {
            this.end(name, { error: true });
            throw error;
        }
    }

    // Measure an async function execution
    async measureAsync<T>(name: string, fn: () => Promise<T>, metadata?: any): Promise<T> {
        this.start(name, metadata);
        try {
            const result = await fn();
            this.end(name);
            return result;
        } catch (error) {
            this.end(name, { error: true });
            throw error;
        }
    }

    // Get performance statistics
    getStats(): {
        averageDuration: number;
        totalOperations: number;
        slowestOperations: PerformanceEntry[];
        fastestOperations: PerformanceEntry[];
    } {
        if (this.completedEntries.length === 0) {
            return {
                averageDuration: 0,
                totalOperations: 0,
                slowestOperations: [],
                fastestOperations: [],
            };
        }

        const durations = this.completedEntries
            .filter(entry => entry.duration !== undefined)
            .map(entry => entry.duration!);

        const averageDuration = durations.reduce((sum, duration) => sum + duration, 0) / durations.length;

        const sortedEntries = [...this.completedEntries]
            .filter(entry => entry.duration !== undefined)
            .sort((a, b) => b.duration! - a.duration!);

        return {
            averageDuration,
            totalOperations: this.completedEntries.length,
            slowestOperations: sortedEntries.slice(0, 10),
            fastestOperations: sortedEntries.slice(-10).reverse(),
        };
    }

    // Get entries by name pattern
    getEntriesByName(namePattern: string): PerformanceEntry[] {
        return this.completedEntries.filter(entry =>
            entry.name.includes(namePattern)
        );
    }

    // Clear all entries
    clear(): void {
        this.entries.clear();
        this.completedEntries = [];
        logger.info('Performance entries cleared', undefined, 'PERF');
    }

    // Export performance data
    export(): string {
        return JSON.stringify({
            activeEntries: Array.from(this.entries.values()),
            completedEntries: this.completedEntries,
            stats: this.getStats(),
        }, null, 2);
    }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// Higher-order component for measuring React component render time
export function withPerformanceTracking<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    componentName?: string
) {
    const displayName = componentName || WrappedComponent.displayName || WrappedComponent.name || 'Component';

    return function PerformanceTrackedComponent(props: P) {
        const renderName = `${displayName}_render`;

        React.useEffect(() => {
            performanceMonitor.start(renderName);
            return () => {
                performanceMonitor.end(renderName);
            };
        });

        return React.createElement(WrappedComponent, props);
    };
}

// Hook for measuring operations within components
export function usePerformanceTracking() {
    return {
        start: (name: string, metadata?: any) => performanceMonitor.start(name, metadata),
        end: (name: string, additionalMetadata?: any) => performanceMonitor.end(name, additionalMetadata),
        measure: <T>(name: string, fn: () => T, metadata?: any) => performanceMonitor.measure(name, fn, metadata),
        measureAsync: <T>(name: string, fn: () => Promise<T>, metadata?: any) => performanceMonitor.measureAsync(name, fn, metadata),
    };
}

// API call performance wrapper
export function trackApiCall<T>(
    method: string,
    url: string,
    apiCall: () => Promise<T>
): Promise<T> {
    const operationName = `API_${method.toUpperCase()}_${url.replace(/[^a-zA-Z0-9]/g, '_')}`;

    return performanceMonitor.measureAsync(
        operationName,
        apiCall,
        { method, url }
    );
}

export default performanceMonitor;