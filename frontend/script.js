const API_URL = "https://project-optics.onrender.com";

const promptForm = document.getElementById("promptForm");
const promptInput = document.getElementById("promptInput");
const stepsContainer = document.getElementById("stepsContainer");
const videoWrapper = document.getElementById("videoWrapper");
const videoPlaceholder = document.getElementById("videoPlaceholder");
const progressBar = document.getElementById("progressBar");
const progressFill = document.getElementById("progressFill");

let videoEl = null;
let segments = [];
let activeStep = -1;
let currentVideoUrl = null;

/* Settings dropdown toggle */
const settingsBtn = document.getElementById("settingsBtn");
const settingsDropdown = document.getElementById("settingsDropdown");

settingsBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = settingsBtn.classList.toggle("active");
    settingsDropdown.classList.toggle("open", isOpen);
});

document.addEventListener("click", (e) => {
    if (!e.target.closest(".settings-wrapper")) {
        settingsBtn.classList.remove("active");
        settingsDropdown.classList.remove("open");
    }
});

/* Theme toggle */
const themeToggle = document.getElementById("themeToggle");
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
    themeToggle.classList.add("active");
}

themeToggle.addEventListener("click", (e) => {
    e.stopPropagation();
    const isLight = themeToggle.classList.toggle("active");

    const applyTheme = () => {
        if (isLight) {
            document.documentElement.setAttribute("data-theme", "light");
            localStorage.setItem("theme", "light");
        } else {
            document.documentElement.removeAttribute("data-theme");
            localStorage.setItem("theme", "dark");
        }
        if (videoEl && currentVideoUrl) {
            const wasPlaying = !videoEl.paused;
            const time = videoEl.currentTime;
            videoEl.src = isLight
                ? currentVideoUrl.replace(".mp4", "-light.mp4")
                : currentVideoUrl;
            videoEl.currentTime = time;
            if (wasPlaying) videoEl.play();
        }
    };

    if (document.startViewTransition) {
        document.startViewTransition(applyTheme);
    } else {
        applyTheme();
    }
});

promptForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const topic = promptInput.value.trim();
    if (!topic) return;

    promptInput.value = "";
    showLoading(topic);

    try {
        const res = await fetch(`${API_URL}/lesson`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic }),
        });
        const data = await res.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        segments = data.segments;
        renderSteps(data.topic, data.segments);
        loadVideo(data.video_url);
    } catch (err) {
        showError("Something went wrong. Try again.");
        console.error(err);
    }
});

function showLoading(topic) {
    stepsContainer.innerHTML = `
        <div class="topic-label loading-topic">${topic}</div>
        <div class="loading-container">
          <div class="loading-logo">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 981 508" fill="none">
              <path class="dot dot-1" fill="currentColor" fill-rule="evenodd" d="M 220 312 L 207 313 L 166 327 L 12 387 L 5 394 L 1 403 L 0 429 L 8 461 L 16 477 L 26 491 L 33 498 L 44 505 L 59 507 L 261 430 L 261 426 L 239 396 L 223 360 L 220 350 Z M 216 317 L 216 351 L 220 364 L 236 399 L 255 425 L 255 428 L 57 503 L 48 502 L 40 498 L 31 490 L 21 477 L 13 462 L 4 429 L 5 404 L 9 396 L 15 390 L 170 330 L 208 317 Z"/>
              <path class="dot dot-2" fill="currentColor" fill-rule="evenodd" d="M 535 156 L 251 263 L 238 274 L 234 281 L 230 296 L 230 323 L 236 352 L 242 369 L 256 396 L 269 414 L 279 424 L 291 431 L 303 433 L 329 429 L 368 413 L 437 389 L 452 381 L 582 331 L 601 320 L 598 314 L 576 287 L 558 254 L 545 215 L 541 194 L 541 168 Z M 533 161 L 537 169 L 537 194 L 541 216 L 551 248 L 569 284 L 596 319 L 524 350 L 451 377 L 436 385 L 364 410 L 328 425 L 305 429 L 295 428 L 285 423 L 273 412 L 258 391 L 247 370 L 240 351 L 235 329 L 235 291 L 241 277 L 249 269 Z"/>
              <path class="dot dot-3" fill="currentColor" fill-rule="evenodd" d="M 877 24 L 870 30 L 864 49 L 866 86 L 875 122 L 892 158 L 908 182 L 921 195 L 939 205 L 946 205 L 955 195 L 960 175 L 959 145 L 947 101 L 934 72 L 916 45 L 895 27 L 884 23 Z M 878 28 L 883 27 L 895 32 L 912 47 L 928 70 L 943 102 L 951 127 L 956 152 L 955 181 L 953 189 L 945 201 L 940 201 L 929 195 L 912 180 L 897 158 L 881 126 L 873 100 L 868 70 L 869 44 L 873 33 Z M 917 16 L 906 8 L 890 1 L 869 2 L 717 58 L 595 106 L 584 112 L 574 126 L 569 144 L 568 176 L 571 201 L 577 227 L 587 253 L 600 278 L 619 304 L 633 317 L 648 326 L 662 330 L 678 330 L 929 235 L 962 221 L 972 209 L 979 187 L 980 147 L 977 124 L 969 97 L 955 66 L 934 34 Z M 915 20 L 931 37 L 949 64 L 963 93 L 972 120 L 976 148 L 975 186 L 971 201 L 965 212 L 959 218 L 681 325 L 662 326 L 654 324 L 639 316 L 626 305 L 611 287 L 597 264 L 584 235 L 578 215 L 573 186 L 572 154 L 577 130 L 586 116 L 601 108 L 726 59 L 870 6 L 889 5 L 901 10 Z"/>
            </svg>
          </div>
          <h3 class="loading-title">Generating lesson</h3>
          <p class="loading-subtitle">Hold tight while we build your animation.</p>
        </div>
      `;
    videoPlaceholder.querySelector("span").textContent =
        "Rendering animation…";
}

function showError(msg) {
    stepsContainer.innerHTML = `
        <div class="empty-state error-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          </div>
          <h3>Error</h3>
          <p>${msg}</p>
        </div>
      `;
}

function renderSteps(topic, steps) {
    let html = `<div class="steps-list"><div class="topic-label">${topic}</div>`;

    steps.forEach((step, i) => {
        const startMin = Math.floor(step.start_time_seconds / 60);
        const startSec = String(step.start_time_seconds % 60).padStart(2, "0");
        const timestamp = `${startMin}:${startSec}`;

        html += `
          <div class="step-card${i === 0 ? " active" : ""}" data-index="${i}" onclick="seekToStep(${i})">
            <div class="step-top">
              <div class="step-indicator">${step.step_number}</div>
              <span class="step-timestamp">${timestamp}</span>
            </div>
            <div class="step-explanation">${step.explanation}</div>
          </div>
        `;
    });

    html += `</div>`;
    stepsContainer.innerHTML = html;
    activeStep = 0;
    stepsContainer.scrollTop = 0;
}

function loadVideo(url) {
    videoPlaceholder.style.display = "none";

    if (videoEl) videoEl.remove();

    currentVideoUrl = url;
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    videoEl = document.createElement("video");
    videoEl.src = isLight ? url.replace(".mp4", "-light.mp4") : url;
    videoEl.autoplay = true;
    videoEl.playsInline = true;
    videoWrapper.appendChild(videoEl);

    videoEl.addEventListener("click", () => {
        if (videoEl.paused) videoEl.play();
        else videoEl.pause();
    });

    progressBar.style.display = "block";

    videoEl.addEventListener("timeupdate", () => {
        const t = videoEl.currentTime;
        const dur = videoEl.duration || 1;
        progressFill.style.width = `${(t / dur) * 100}%`;

        for (let i = segments.length - 1; i >= 0; i--) {
            if (t >= segments[i].start_time_seconds) {
                if (activeStep !== i) {
                    setActiveStep(i);
                }
                break;
            }
        }
    });
}

function seekToStep(index) {
    if (!videoEl || !segments[index]) return;
    videoEl.currentTime = segments[index].start_time_seconds;
    videoEl.play();
    setActiveStep(index);
}

function setActiveStep(index) {
    activeStep = index;
    document.querySelectorAll(".step-card").forEach((card, i) => {
        card.classList.toggle("active", i === index);
    });

    const activeCard = document.querySelector(
        `.step-card[data-index="${index}"]`,
    );
    if (activeCard) {
        activeCard.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
        });
    }
}
