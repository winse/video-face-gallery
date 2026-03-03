
/**
 * Core Sorting Logic extracted for testing
 */

const SortUtils = {
    /**
     * Array-based sorting (for objects)
     * @param {Array} list 
     * @param {string} type 'name' | 'date' | 'count'
     * @param {string} dir 'asc' | 'desc'
     */
    sortArray(list, type, dir) {
        const factor = dir === 'asc' ? 1 : -1;
        return [...list].sort((a, b) => {
            if (type === 'name') {
                const valA = a.name || a.video_name || "";
                const valB = b.name || b.video_name || "";
                return factor * valA.localeCompare(valB, 'zh-CN');
            }
            if (type === 'date' || type === 'time') {
                const valA = parseFloat(a.rawTime || a.sort_time || a.mtime_raw || 0);
                const valB = parseFloat(b.rawTime || b.sort_time || b.mtime_raw || 0);
                let res = valA - valB;
                if (res === 0) { // Secondary sort by name
                    const nameA = a.name || a.video_name || "";
                    const nameB = b.name || b.video_name || "";
                    return nameA.localeCompare(nameB, 'zh-CN');
                }
                return factor * res;
            }
            if (type === 'count') {
                const valA = parseInt(a.face_count || a.count || 0);
                const valB = parseInt(b.face_count || b.count || 0);
                let res = valA - valB;
                if (res === 0) { // Secondary sort by time
                    const timeA = parseFloat(a.rawTime || a.sort_time || 0);
                    const timeB = parseFloat(b.rawTime || b.sort_time || 0);
                    return timeB - timeA; // default time desc for ties
                }
                return factor * res;
            }
            return 0;
        });
    },

    /**
     * DOM element sorting logic
     * Returns the sorted array of elements, caller should append them
     */
    sortElements(elements, sortType, dir) {
        const factor = dir === 'asc' ? 1 : -1;
        return [...elements].sort((a, b) => {
            const countA = parseInt(a.dataset.count) || 0;
            const countB = parseInt(b.dataset.count) || 0;
            const timeA = parseFloat(a.dataset.time) || 0;
            const timeB = parseFloat(b.dataset.time) || 0;

            let result = 0;
            if (sortType === "count") {
                result = countA - countB;
                if (result === 0) result = timeA - timeB;
            } else {
                result = timeA - timeB;
                if (result === 0) result = countA - countB;
            }

            return factor * result;
        });
    }
};

// Test Runner
function runTests() {
    console.log("Starting Sorting Tests...");
    const results = [];

    // Test Data
    const testData = [
        { name: "C.mp4", rawTime: 100, face_count: 5 },
        { name: "A.mp4", rawTime: 300, face_count: 2 },
        { name: "B.mp4", rawTime: 200, face_count: 10 },
        { name: "D.mp4", rawTime: 200, face_count: 5 }
    ];

    // 1. Array Name ASC
    let sorted = SortUtils.sortArray(testData, 'name', 'asc');
    results.push({
        name: "Array Name ASC",
        pass: sorted[0].name === "A.mp4" && sorted[2].name === "C.mp4",
        actual: sorted.map(x => x.name)
    });

    // 2. Array Date DESC
    sorted = SortUtils.sortArray(testData, 'date', 'desc');
    results.push({
        name: "Array Date DESC",
        pass: sorted[0].rawTime === 300 && sorted[1].rawTime === 200,
        actual: sorted.map(x => x.rawTime)
    });

    // 3. Array Count DESC
    sorted = SortUtils.sortArray(testData, 'count', 'desc');
    results.push({
        name: "Array Count DESC",
        pass: sorted[0].face_count === 10 && sorted[1].face_count === 5,
        actual: sorted.map(x => x.face_count)
    });

    // Mock DOM Test
    const mockElements = testData.map(d => {
        return {
            dataset: { count: d.face_count, time: d.rawTime },
            name: d.name // for verification
        };
    });

    // 4. DOM Count DESC
    let sortedEl = SortUtils.sortElements(mockElements, 'count', 'desc');
    results.push({
        name: "DOM Count DESC",
        pass: parseInt(sortedEl[0].dataset.count) === 10,
        actual: sortedEl.map(e => e.dataset.count)
    });

    // 5. DOM Time DESC
    sortedEl = SortUtils.sortElements(mockElements, 'time', 'desc');
    results.push({
        name: "DOM Time DESC",
        pass: parseFloat(sortedEl[0].dataset.time) === 300,
        actual: sortedEl.map(e => e.dataset.time)
    });

    // Log Results
    console.table(results);
    const allPass = results.every(r => r.pass);
    if (allPass) {
        console.log("%c ALL TESTS PASSED! ", "background: green; color: white; padding: 10px;");
    } else {
        console.error("SOME TESTS FAILED!");
    }
}

if (typeof window !== 'undefined') {
    runTests();
} else {
    module.exports = { SortUtils, runTests };
}
