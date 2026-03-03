/**
 * Shared JavaScript for Person Detail pages
 * Contains all interactive functionality for video player, sorting, filtering
 */

// Global state for video navigation
var currentAllVideos = [];
var currentVideoUrl = "";
var currentVideoIndex = 0;
var autoPlayEnabled = localStorage.getItem("autoPlay") !== "false"; // Default to true

// Initialize tags data if available
var tagsData = typeof allTagsData !== 'undefined' ? JSON.parse(JSON.stringify(allTagsData)) : { tags: {}, video_tags: {} };

/**
 * Theme toggle - switches between light and dark modes
 */
function toggleTheme() {
    var body = document.body;
    if (body.hasAttribute("data-theme")) {
        body.removeAttribute("data-theme");
        localStorage.removeItem("theme");
    } else {
        body.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
    }
}

/**
 * Toggle sort type (count/time) with ascending/descending toggle
 */
function toggleSort(sortType) {
    var btn = document.getElementById("sort-" + sortType);
    if (!btn) return;

    var alreadyActive = btn.classList.contains("active");

    if (alreadyActive) {
        var currentDir = btn.dataset.dir;
        btn.dataset.dir = currentDir === "desc" ? "asc" : "desc";
    } else {
        document.querySelectorAll(".sort-btn").forEach(function (b) {
            b.classList.remove("active");
        });
        btn.classList.add("active");
    }

    // Preserve Chinese labels
    var label = sortType === "count" ? "数量" : "时间";
    btn.textContent = label + " " + (btn.dataset.dir === "desc" ? "↓" : "↑");

    applySort();
}

/**
 * Filter video groups by year
 */
function filterByYear() {
    applySort(); // Re-apply combined filter and sort
}

/**
 * Apply combined sort and filter to visible groups
 */
function applySort() {
    var select = document.getElementById("yearFilter");
    var year = select ? select.value : "all";
    var container = document.querySelector(".video-groups");
    if (!container) return;

    var groups = Array.from(document.querySelectorAll(".video-group"));

    // Filter first
    groups.forEach(function (group) {
        if (year === "all" || group.dataset.year === year) {
            group.style.display = "";
        } else {
            group.style.display = "none";
        }
    });

    // Sort ALL groups (including hidden ones to maintain a consistent order in DOM)
    var activeBtn = document.querySelector(".sort-btn.active");
    if (!activeBtn) return;

    var sortType = activeBtn.dataset.sort;
    var dir = activeBtn.dataset.dir;

    groups.sort(function (a, b) {
        var countA = parseInt(a.dataset.count) || 0;
        var countB = parseInt(b.dataset.count) || 0;
        var timeA = parseFloat(a.dataset.time) || 0;
        var timeB = parseFloat(b.dataset.time) || 0;
        var result = 0;

        if (sortType === "count") {
            result = countB - countA;
            // secondary sort by time if counts are equal
            if (result === 0) result = timeB - timeA;
        } else {
            result = timeB - timeA;
            // secondary sort by count if times are equal
            if (result === 0) result = countB - countA;
        }

        return dir === "desc" ? result : -result;
    });

    // Re-append to container
    groups.forEach(function (g) {
        container.appendChild(g);
    });
}

/**
 * Open video player modal with all videos for a person
 */
function openAllVideos(personId, videoUrl) {
    var allVideos = personVideos[personId];
    if (!allVideos || allVideos.length === 0) return;

    currentAllVideos = allVideos;
    currentVideoIndex = 0;

    // Find index if videoUrl provided
    if (videoUrl) {
        for (var i = 0; i < allVideos.length; i++) {
            if (allVideos[i].video_url === videoUrl) {
                currentVideoIndex = i;
                break;
            }
        }
    }

    var modal = document.getElementById("videoModal");
    var videoList = document.getElementById("modalVideoList");

    if (!modal || !videoList) return;

    // Render video list in sidebar
    videoList.innerHTML = "";
    allVideos.forEach(function (v, index) {
        var div = document.createElement("div");
        div.className = "modal-video-item";
        div.dataset.videoUrl = v.video_url;
        div.dataset.timestamp = v.first_timestamp;
        div.dataset.index = index;

        div.innerHTML = '<div class="modal-video-main">' +
            '<div class="modal-video-info"><div class="modal-video-name">' + v.video_name + '</div>' +
            '<div class="modal-video-meta">' + v.create_date + (v.size ? ' | ' + v.size : '') + ' | ' + v.duration + ' | ' + v.face_count + ' 条记录</div></div>' +
            '</div>';

        // Add faces grid
        if (v.faces && v.faces.length > 0) {
            var facesGrid = document.createElement("div");
            facesGrid.className = "modal-video-faces";
            v.faces.forEach(function (face) {
                var img = document.createElement("img");
                img.src = DataManager.getThumbnailPath(face.t);
                img.className = "modal-face-thumb";
                img.title = "跳转到 " + formatTime(face.s);
                img.onclick = function (e) {
                    e.stopPropagation(); // 阻止触发视频切换
                    if (currentVideoIndex === index) {
                        seekToTime(face.s);
                    } else {
                        currentVideoIndex = index;
                        playVideo(v.video_url, face.s, v.video_name, currentVideoIndex);
                        updateVideoListSelection();
                    }
                };
                facesGrid.appendChild(img);
            });
            div.appendChild(facesGrid);
        }

        if (index === currentVideoIndex) {
            div.classList.add("active");
        }

        div.onclick = function () {
            currentVideoIndex = index;
            playVideo(v.video_url, 0, v.video_name, currentVideoIndex);
            updateVideoListSelection();
            updateNavButtons();
        };

        videoList.appendChild(div);
    });

    // Update nav buttons state
    updateNavButtons();

    // Play selected video
    var selected = allVideos[currentVideoIndex];
    playVideo(selected.video_url, 0, selected.video_name, currentVideoIndex);

    // Show modal
    modal.classList.add("active");
    document.body.style.overflow = "hidden"; // Prevent background scroll

    // Scroll selected item into view after a short delay
    setTimeout(function () {
        updateVideoListSelection();
    }, 100);
}

/**
 * Play a specific video at given timestamp
 */
function playVideo(videoUrl, timestamp, videoName, videoIndex) {
    if (!videoUrl) return;

    var video = document.getElementById("modalVideo");
    var title = document.getElementById("modalTitle");

    if (!video || !title) return;

    currentVideoUrl = videoUrl;
    currentVideoIndex = videoIndex;

    // Get metadata from currentAllVideos
    var v = currentAllVideos[videoIndex] || {};
    var metaStr = (v.create_date || "") + (v.size ? " | " + v.size : "") + (v.duration ? " | " + v.duration : "");

    title.innerHTML = '<div>' + videoName + '</div><span class="modal-title-meta">' + metaStr + '</span>';

    video.src = videoUrl;
    video.currentTime = timestamp;
    video.play();
    updateNavButtons();
    renderModalTags(videoName);
}

/**
 * Close the video player modal
 */
function closeModal() {
    var modal = document.getElementById("videoModal");
    var video = document.getElementById("modalVideo");

    if (modal) {
        modal.classList.remove("active");
        document.body.style.overflow = ""; // Restore background scroll
    }

    if (video) {
        video.pause();
        video.src = "";
    }
}

/**
 * Copy current video path to clipboard
 */
function copyVideoPath() {
    if (!currentVideoUrl) return;

    // Copy to clipboard
    navigator.clipboard.writeText(currentVideoUrl).then(function () {
        // Find the copy button and show success feedback
        var btn = document.querySelector(".copy-btn");
        if (btn) {
            var originalText = btn.textContent;
            btn.textContent = "已复制";
            btn.style.color = "#4CAF50";
            btn.style.borderColor = "#4CAF50";

            setTimeout(function () {
                btn.textContent = originalText;
                btn.style.color = "";
                btn.style.borderColor = "";
            }, 2000);
        }
    }).catch(function (err) {
        console.error('无法复制: ', err);
    });
}

/**
 * Update navigation button states based on current video index
 */
function updateNavButtons() {
    var prevBtn = document.getElementById("prevVideo");
    var nextBtn = document.getElementById("nextVideo");

    if (prevBtn) {
        prevBtn.disabled = currentVideoIndex <= 0;
    }
    if (nextBtn) {
        nextBtn.disabled = currentVideoIndex >= currentAllVideos.length - 1;
    }
}

/**
 * Navigate to previous video
 */
function prevVideo() {
    if (currentVideoIndex > 0) {
        currentVideoIndex--;
        var v = currentAllVideos[currentVideoIndex];
        playVideo(v.video_url, 0, v.video_name, currentVideoIndex);
        updateVideoListSelection();
        updateNavButtons();
    }
}

/**
 * Navigate to next video
 */
function nextVideo() {
    if (currentVideoIndex < currentAllVideos.length - 1) {
        currentVideoIndex++;
        var v = currentAllVideos[currentVideoIndex];
        playVideo(v.video_url, 0, v.video_name, currentVideoIndex);
        updateVideoListSelection();
        updateNavButtons();
    }
}

/**
 * Update video list selection highlight
 */
function updateVideoListSelection() {
    document.querySelectorAll(".modal-video-item").forEach(function (item, idx) {
        if (parseInt(item.dataset.index) === currentVideoIndex) {
            item.classList.add("active");
            item.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } else {
            item.classList.remove("active");
        }
    });
}

/**
 * Toggle auto-play setting
 */
function toggleAutoPlay(enabled) {
    autoPlayEnabled = enabled;
    localStorage.setItem("autoPlay", enabled);
}

/**
 * Sort videos in modal by name, date, or count
 */
function sortVideosInModal(sortType) {
    // Update sort button states
    document.querySelectorAll(".modal-sort-btn").forEach(function (btn) {
        btn.classList.remove("active");
    });
    document.getElementById("sort-by-" + sortType).classList.add("active");

    // Sort currentAllVideos
    currentAllVideos.sort(function (a, b) {
        if (sortType === "name") {
            return a.video_name.localeCompare(b.video_name);
        } else if (sortType === "date") {
            // Fallback to timestamp if create_date not available
            var dateA = a.create_timestamp || a.first_timestamp || 0;
            var dateB = b.create_timestamp || b.first_timestamp || 0;
            return dateB - dateA; // Descending (newest first)
        } else if (sortType === "count") {
            return b.face_count - a.face_count; // Descending
        }
        return 0;
    });

    // Re-render video list
    var videoList = document.getElementById("modalVideoList");
    videoList.innerHTML = "";
    currentAllVideos.forEach(function (v, index) {
        var div = document.createElement("div");
        div.className = "modal-video-item";
        div.dataset.videoUrl = v.video_url;
        div.dataset.timestamp = v.first_timestamp;
        div.dataset.index = index;

        div.innerHTML = '<div class="modal-video-main">' +
            '<div class="modal-video-info"><div class="modal-video-name">' + v.video_name + '</div>' +
            '<div class="modal-video-meta">' + v.create_date + (v.size ? ' | ' + v.size : '') + ' | ' + v.duration + ' | ' + v.face_count + ' 条记录</div></div>' +
            '</div>';

        // Add faces grid
        if (v.faces && v.faces.length > 0) {
            var facesGrid = document.createElement("div");
            facesGrid.className = "modal-video-faces";
            v.faces.forEach(function (face) {
                var img = document.createElement("img");
                img.src = DataManager.getThumbnailPath(face.t);
                img.className = "modal-face-thumb";
                img.title = "跳转到 " + formatTime(face.s);
                img.onclick = function (e) {
                    e.stopPropagation();
                    if (currentVideoIndex === index) {
                        seekToTime(face.s);
                    } else {
                        currentVideoIndex = index;
                        playVideo(v.video_url, face.s, v.video_name, currentVideoIndex);
                        updateVideoListSelection();
                    }
                };
                facesGrid.appendChild(img);
            });
            div.appendChild(facesGrid);
        }

        if (v.video_url === currentVideoUrl) {
            div.classList.add("active");
            currentVideoIndex = index; // Update index to match new sort
        }

        div.onclick = function () {
            currentVideoIndex = index;
            playVideo(v.video_url, 0, v.video_name, currentVideoIndex);
            updateVideoListSelection();
            updateNavButtons();
        };

        videoList.appendChild(div);
    });

    // Update nav buttons after sorting
    updateNavButtons();
}

/**
 * Seek current video to a specific timestamp
 */
function seekToTime(timestamp) {
    var video = document.getElementById("modalVideo");
    if (video) {
        video.currentTime = timestamp;
        video.play();
    }
}

/**
 * Format seconds to MM:SS
 */
function formatTime(seconds) {
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
}


// ===== Event Listeners =====

// Close modal on ESC key
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        closeModal();
    }
});

// Close modal on backdrop click
var videoModal = document.getElementById("videoModal");
if (videoModal) {
    videoModal.addEventListener("click", function (e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

// Handle video ended for auto-play
var modalVideo = document.getElementById("modalVideo");
if (modalVideo) {
    modalVideo.addEventListener("ended", function () {
        if (autoPlayEnabled) {
            nextVideo();
        }
    });
}

// Load saved preferences
(function () {
    // Theme
    if (localStorage.getItem("theme") === "dark") {
        document.body.setAttribute("data-theme", "dark");
    }

    // Auto-play toggle state
    var autoPlayToggle = document.getElementById("autoPlayToggle");
    if (autoPlayToggle) {
        autoPlayToggle.checked = autoPlayEnabled;
    }
})();

/**
 * Render tags for current video in modal
 */
function renderModalTags(videoName) {
    var tagSection = document.getElementById("modalTagSection");
    if (!tagSection) return;

    var tagIds = Object.keys(tagsData.tags);
    if (tagIds.length === 0) {
        tagSection.innerHTML = '<div style="font-size:12px;color:rgba(255,255,255,0.4);padding:8px 16px;">请至标签管理页创建标签</div>';
        return;
    }

    var videoTags = tagsData.video_tags[videoName] || [];

    var html = '<div class="modal-tag-header">';
    html += '<span>视频标签管理</span>';
    html += '<button class="add-tag-btn" onclick="createTagInModal(\'' + videoName + '\')" title="快捷添加新标签">+</button>';
    html += '</div>';

    html += '<div class="modal-tag-list">';
    tagIds.forEach(function (id) {
        var tag = tagsData.tags[id];
        var isActive = videoTags.indexOf(id) > -1;
        html += '<span class="modal-tag-pill ' + (isActive ? 'active' : '') + '" style="' + (isActive ? 'background:' + tag.color : '') + '" onclick="toggleVideoTagModal(\'' + videoName + '\', \'' + id + '\')">' + tag.name + '</span>';
    });
    html += '</div>';

    html += '<div style="padding: 10px 16px; border-top: 1px solid var(--border-color); text-align: right;">';
    html += '<span style="font-size:10px; color:var(--text-secondary); opacity:0.8;">💡 修改已自动存入浏览器缓存，请至<b>标签管理页</b>统一导出并覆盖 tags.json</span>';
    html += '</div>';

    tagSection.innerHTML = html;
}

/**
 * Create a new tag directly from the modal and assign it to current video
 */
function createTagInModal(videoName) {
    var name = prompt("请输入新标签名称:");
    if (!name || !name.trim()) return;

    name = name.trim();

    var tagId = 'tag_' + Date.now();
    var randomColors = ['#667eea', '#764ba2', '#27ae60', '#e74c3c', '#f39c12', '#3498db', '#9b59b6'];
    var color = randomColors[Math.floor(Math.random() * randomColors.length)];

    tagsData.tags[tagId] = {
        name: name,
        color: color
    };

    if (!tagsData.video_tags[videoName]) {
        tagsData.video_tags[videoName] = [];
    }
    tagsData.video_tags[videoName].push(tagId);

    if (typeof DataManager !== 'undefined') DataManager.set('tags_data', tagsData);
    renderModalTags(videoName);
}

/**
 * Toggle a tag for a video within the modal
 */
function toggleVideoTagModal(videoName, tagId) {
    if (!tagsData.video_tags[videoName]) {
        tagsData.video_tags[videoName] = [];
    }

    var idx = tagsData.video_tags[videoName].indexOf(tagId);
    if (idx > -1) {
        tagsData.video_tags[videoName].splice(idx, 1);
    } else {
        tagsData.video_tags[videoName].push(tagId);
    }

    if (typeof DataManager !== 'undefined') DataManager.set('tags_data', tagsData);
    renderModalTags(videoName);
}

/**
 * Export current tags configuration
 */
function exportTags() {
    var json = JSON.stringify(tagsData, null, 2);
    var blob = new Blob([json], { type: 'application/json' });
    var url = URL.createObjectURL(blob);

    var a = document.createElement('a');
    a.href = url;
    a.download = 'tags.json';
    a.click();

    URL.revokeObjectURL(url);

    if (typeof DataManager !== 'undefined') {
        DataManager.clear().then(() => {
            alert('已生成新的 tags.json 并清空缓存，请务必覆盖原文件，下次打开页面将自动读取新文件。');
        });
    } else {
        alert('已生成新的 tags.json，请替换原文件并重新生成页面。');
    }
}
