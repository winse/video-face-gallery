/**
 * Common Data Manager with IndexedDB caching
 */
const DB_NAME = 'VideoTagSystemDB';
const DB_VERSION = 1;
const STORE_NAME = 'data_cache';
const DATA_BASE = (window.WEB_DATA_BASE || 'face_data').replace(/\/+$/, '');

const DataManager = {
    _db: null,

    async open() {
        if (this._db) return this._db;
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);
            request.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME);
                }
            };
            request.onsuccess = (e) => {
                this._db = e.target.result;
                resolve(this._db);
            };
            request.onerror = (e) => reject(e.target.error);
        });
    },

    async get(key) {
        const db = await this.open();
        return new Promise((resolve) => {
            const transaction = db.transaction(STORE_NAME, 'readonly');
            const store = transaction.objectStore(STORE_NAME);
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => resolve(null);
        });
    },

    async set(key, value) {
        const db = await this.open();
        const transaction = db.transaction(STORE_NAME, 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        store.put(value, key);
    },

    async clear() {
        const db = await this.open();
        const transaction = db.transaction(STORE_NAME, 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        store.clear();
        console.log('IndexedDB cache cleared.');
    },

    // High level data loading logic
    async loadData(jsonPath, cacheKey) {
        // 1. Try IndexedDB
        let data = await this.get(cacheKey);
        if (data) {
            console.log(`Loaded ${cacheKey} from IndexedDB cache.`);
            return data;
        }

        // 2. Fallback to JSON
        console.log(`Fetching ${jsonPath} from server...`);
        const response = await fetch(jsonPath + '?t=' + Date.now());
        if (!response.ok) throw new Error(`Could not load ${jsonPath}`);
        data = await response.json();

        // 3. Save to cache
        await this.set(cacheKey, data);
        return data;
    },

    getDataPath(filename) {
        if (!filename) return DATA_BASE;
        return `${DATA_BASE}/${filename}`;
    },

    getThumbnailPath(name) {
        return `${DATA_BASE}/thumbnails/${name}`;
    },

    /**
     * Normalize time-like values (timestamp number or datetime string) to epoch milliseconds.
     * Returns fallback if parsing fails.
     */
    toTimestamp(value, fallback = 0) {
        if (value === null || value === undefined || value === '') return fallback;

        if (typeof value === 'number' && Number.isFinite(value)) {
            // If value looks like seconds, convert to ms.
            return value < 1e12 ? value * 1000 : value;
        }

        if (typeof value === 'string') {
            const raw = value.trim();
            if (!raw) return fallback;

            // Numeric string support.
            const num = Number(raw);
            if (Number.isFinite(num)) {
                return num < 1e12 ? num * 1000 : num;
            }

            // Common local datetime format: "YYYY-MM-DD HH:mm:ss(.ffffff)"
            // Convert to ISO-like string for broader Date.parse compatibility.
            let normalized = raw.replace(' ', 'T');
            if (normalized.includes('.')) {
                const [base, fracPart] = normalized.split('.', 2);
                const frac = (fracPart || '').replace(/[^0-9].*$/, '');
                const ms = frac ? frac.slice(0, 3).padEnd(3, '0') : '000';
                normalized = `${base}.${ms}`;
            }

            const parsed = Date.parse(normalized);
            if (Number.isFinite(parsed)) return parsed;

            const parsedRaw = Date.parse(raw);
            if (Number.isFinite(parsedRaw)) return parsedRaw;
        }

        return fallback;
    },

    /**
     * Pick the best sortable time from video metadata and return epoch milliseconds.
     */
    getVideoSortTime(meta, fallback = 0) {
        if (!meta || typeof meta !== 'object') return fallback;
        const candidates = [
            meta.v_create_raw,
            meta.ctime_raw,
            meta.mtime_raw,
            meta.v_create_date,
            meta.create_date,
            meta.ctime,
            meta.mtime
        ];
        for (const value of candidates) {
            const ts = this.toTimestamp(value, 0);
            if (ts > 0) return ts;
        }
        return fallback;
    },

    /**
     * Convert absolute Windows path to server-relative path
     */
    getRelativeVideoPath(absPath) {
        if (!absPath) return "";
        let path = absPath.replace(/\\/g, '/');

        // Prefer paths relative to web root, e.g. ".../py/web/data/a.mp4" -> "data/a.mp4"
        const webMarker = '/py/web/';
        let idx = path.lastIndexOf(webMarker);
        if (idx !== -1) {
            return path.substring(idx + webMarker.length);
        }

        const genericWebMarker = '/web/';
        idx = path.lastIndexOf(genericWebMarker);
        if (idx !== -1) {
            return path.substring(idx + genericWebMarker.length);
        }

        return path;
    }
};
