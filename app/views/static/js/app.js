// State variables
let mediaRecorder = null;
let audioChunks = [];
let recordingState = "IDLE"; // IDLE, RECORDING, PROCESSING, SPEAKING
let currentCoords = { lat: 23.8103, lon: 90.4125 }; // Default Dhaka
let currentConversationId = null;

// DOM Elements
const themeToggleBtn = document.getElementById("theme-toggle");
const micBtn = document.getElementById("mic-btn");
const micContainer = document.getElementById("mic-container");
const micStatus = document.getElementById("mic-status");
const waveform = document.getElementById("waveform");

const uploadArea = document.getElementById("upload-area");
const audioFileInput = document.getElementById("audio-file-input");
const fileNameDisplay = document.getElementById("file-name-display");

const textQueryInput = document.getElementById("text-query-input");
const submitTextBtn = document.getElementById("submit-text-btn");

const locationDisplay = document.getElementById("location-display");
const coordinatesDisplay = document.getElementById("coordinates-display");
const tempDisplay = document.getElementById("temp-display");
const weatherDescDisplay = document.getElementById("weather-desc-display");
const forecastDisplay = document.getElementById("forecast-display");
const districtSelect = document.getElementById("district-select");

const diagCrop = document.getElementById("diag-crop");
const diagSymptoms = document.getElementById("diag-symptoms");
const diagSeverity = document.getElementById("diag-severity");
const diagUrgency = document.getElementById("diag-urgency");
const diagConfidence = document.getElementById("diag-confidence");
const confidenceFill = document.getElementById("confidence-fill");
const diagAuditStatus = document.getElementById("diag-audit-status");

const recTextBox = document.getElementById("rec-text-box");
const audioPlayPauseBtn = document.getElementById("audio-play-pause");
const audioProgressFill = document.getElementById("audio-progress-fill");
const audioProgressContainer = document.getElementById("audio-progress-container");
const audioTime = document.getElementById("audio-time");
const ttsAudioElement = document.getElementById("tts-audio-element");

const copyBtn = document.getElementById("copy-btn");
const downloadAudioBtn = document.getElementById("download-audio-btn");
const exportTxtBtn = document.getElementById("export-txt-btn");
const exportJsonBtn = document.getElementById("export-json-btn");

const judgeWeatherFactors = document.getElementById("judge-weather-factors");
const judgeRagSources = document.getElementById("judge-rag-sources");
const judgeReasoning = document.getElementById("judge-reasoning");

const historyContainer = document.getElementById("history-container");

const demoScenarioSelect = document.getElementById("demo-scenario-select");
const runDemoBtn = document.getElementById("run-competition-demo-btn");

// Tab button elements and contents for Judge Audit Center
const tabAuditBtn = document.getElementById("tab-audit-btn");
const tabMetricsBtn = document.getElementById("tab-metrics-btn");
const judgeAuditTabContent = document.getElementById("judge-audit-tab-content");
const judgeMetricsTabContent = document.getElementById("judge-metrics-tab-content");

let loadedScenarios = [];


// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initLocation();
    loadDemoScenarios();
    loadHistory();
    setupEventListeners();
});

// Event Listeners setup
function setupEventListeners() {
    // Theme Toggle
    themeToggleBtn.addEventListener("click", toggleTheme);
    
    // Microphone Recording
    micBtn.addEventListener("click", handleMicClick);
    
    // Audio File Upload click trigger
    uploadArea.addEventListener("click", () => audioFileInput.click());
    audioFileInput.addEventListener("change", handleFileSelection);
    
    // Text Submission
    submitTextBtn.addEventListener("click", () => {
        const query = textQueryInput.value.trim();
        if (query) {
            runPipeline({ text_query: query });
        }
    });
    
    textQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            submitTextBtn.click();
        }
    });
    
    // District Override Select
    districtSelect.addEventListener("change", (e) => {
        const district = e.target.value;
        fetchWeather({ district: district });
    });
    
    // Demo simulation
    if (runDemoBtn) {
        runDemoBtn.addEventListener("click", handleRunDemo);
    }
    
    // Tab switching for Judge Audit Center
    if (tabAuditBtn && tabMetricsBtn && judgeAuditTabContent && judgeMetricsTabContent) {
        tabAuditBtn.addEventListener("click", () => {
            tabAuditBtn.classList.add("active");
            tabAuditBtn.style.background = "var(--primary-color)";
            tabAuditBtn.style.color = "white";
            
            tabMetricsBtn.classList.remove("active");
            tabMetricsBtn.style.background = "transparent";
            tabMetricsBtn.style.color = "var(--text-primary)";
            
            judgeAuditTabContent.style.display = "grid";
            judgeMetricsTabContent.style.display = "none";
        });
        
        tabMetricsBtn.addEventListener("click", () => {
            tabMetricsBtn.classList.add("active");
            tabMetricsBtn.style.background = "var(--primary-color)";
            tabMetricsBtn.style.color = "white";
            
            tabAuditBtn.classList.remove("active");
            tabAuditBtn.style.background = "transparent";
            tabAuditBtn.style.color = "var(--text-primary)";
            
            judgeAuditTabContent.style.display = "none";
            judgeMetricsTabContent.style.display = "block";
        });
    }

    
    // Audio Player Controls
    audioPlayPauseBtn.addEventListener("click", toggleAudioPlayback);
    ttsAudioElement.addEventListener("timeupdate", updateAudioProgressBar);
    ttsAudioElement.addEventListener("ended", handleAudioEnded);
    ttsAudioElement.addEventListener("play", () => setRecordingState("SPEAKING"));
    ttsAudioElement.addEventListener("pause", () => {
        if (recordingState === "SPEAKING") setRecordingState("IDLE");
    });
    audioProgressContainer.addEventListener("click", scrubAudio);
    
    // Action utilities
    copyBtn.addEventListener("click", copyRecommendationText);
}

// State Machine manager
function setRecordingState(newState) {
    recordingState = newState;
    console.log("FAB State transitioned to:", newState);
    
    // Reset state classes
    micContainer.classList.remove("recording-active");
    waveform.style.display = "none";
    
    switch (newState) {
        case "IDLE":
            micStatus.textContent = "কথা বলতে বোতামটি চাপুন";
            break;
            
        case "RECORDING":
            micContainer.classList.add("recording-active");
            micStatus.textContent = "আপনার সমস্যাটি বলুন... শেষ করতে আবার চাপুন";
            waveform.style.display = "flex";
            break;
            
        case "PROCESSING":
            micStatus.textContent = "অডিও ফাইল প্রসেস ও এআই অ্যানালাইসিস করা হচ্ছে...";
            break;
            
        case "SPEAKING":
            micStatus.textContent = "পরামর্শ প্লে করা হচ্ছে...";
            waveform.style.display = "flex";
            break;
    }
}

// Theme Handlers
function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = themeToggleBtn.querySelector("i");
    if (theme === "dark") {
        icon.className = "fa-solid fa-sun";
    } else {
        icon.className = "fa-solid fa-moon";
    }
}

// Geolocation Handling
function initLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentCoords.lat = position.coords.latitude;
                currentCoords.lon = position.coords.longitude;
                fetchWeather({ lat: currentCoords.lat, lon: currentCoords.lon });
            },
            (error) => {
                console.warn("Geolocation permission denied/unavailable. Using district select default Mymensingh.");
                fetchWeather({ district: districtSelect.value });
            }
        );
    } else {
        fetchWeather({ district: districtSelect.value });
    }
}

// Fetch Weather data
async function fetchWeather(params) {
    let url = "/api/weather?";
    if (params.lat && params.lon) {
        url += `lat=${params.lat}&lon=${params.lon}`;
    } else if (params.district) {
        url += `district=${params.district}`;
    }
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            if (data.raw_data && data.raw_data.coord) {
                currentCoords.lat = data.raw_data.coord.lat;
                currentCoords.lon = data.raw_data.coord.lon;
            }
            
            locationDisplay.textContent = data.resolved_district || "ঢাকা";
            coordinatesDisplay.textContent = `ল্যাটিটিউড: ${currentCoords.lat.toFixed(4)}, লঙ্গিটিউড: ${currentCoords.lon.toFixed(4)}`;
            tempDisplay.textContent = `${data.temp.toFixed(1)}°C`;
            weatherDescDisplay.textContent = `${data.description}, আদ্রতা: ${data.humidity}%`;
            
            forecastDisplay.innerHTML = "";
            data.forecast.forEach(item => {
                const div = document.createElement("div");
                div.textContent = item;
                forecastDisplay.appendChild(div);
            });
            
            if (data.resolved_district) {
                const opt = Array.from(districtSelect.options).find(o => o.text.includes(data.resolved_district) || data.resolved_district.toLowerCase().includes(o.value));
                if (opt) districtSelect.value = opt.value;
            }
        }
    } catch (err) {
        console.error("Error fetching weather:", err);
    }
}

// Demo preset scenarios
async function loadDemoScenarios() {
    try {
        const response = await fetch("/api/demo/scenarios");
        if (response.ok) {
            const scenarios = await response.json();
            loadedScenarios = scenarios;
            demoScenarioSelect.innerHTML = "";
            scenarios.forEach(sc => {
                const opt = document.createElement("option");
                opt.value = sc.id;
                opt.textContent = `${sc.title || sc.name} (${sc.crop})`;
                demoScenarioSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Error loading scenarios:", err);
        demoScenarioSelect.innerHTML = '<option value="">Failed to load scenarios</option>';
    }
}

// Helper delay function
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function runVisualPipeline(scenario, resultPromise) {
    const steps = [
        { id: "step-stt", key: "stt_latency_ms", msg: "Transcribing audio...", doneMsg: "Transcribed" },
        { id: "step-correct", key: "correction_latency_ms", msg: "Correcting dialect...", doneMsg: "Corrected" },
        { id: "step-weather", key: "weather_latency_ms", msg: "Fetching weather...", doneMsg: "Loaded" },
        { id: "step-rag", key: "rag_latency_ms", msg: "Querying BRRI RAG...", doneMsg: "Retrieved" },
        { id: "step-diag", key: "intent_latency_ms", msg: "Analyzing symptoms...", doneMsg: "Diagnosed" },
        { id: "step-advisor", key: "advisor_latency_ms", msg: "Synthesizing advice...", doneMsg: "Ready" },
        { id: "step-tts", key: "tts_latency_ms", msg: "Synthesizing speech...", doneMsg: "Synthesized" }
    ];

    // Show visualizer container
    document.getElementById("pipeline-visualizer").style.display = "block";
    
    // Reset all steps
    steps.forEach(s => {
        const el = document.getElementById(s.id);
        if (el) {
            el.className = "pipeline-step";
            el.querySelector(".step-status").textContent = "Waiting";
        }
    });

    // In the background, wait for backend data
    let pipelineData = null;
    resultPromise.then(data => {
        pipelineData = data;
    }).catch(err => {
        console.error("Backend pipeline error:", err);
    });

    // Run steps sequentially with 2s delay
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        const el = document.getElementById(step.id);
        
        if (el) {
            el.classList.add("active");
            el.querySelector(".step-status").textContent = step.msg;
        }
        
        await delay(2000);
        
        // If it's the last step, wait if needed
        if (i === steps.length - 1) {
            let waitCount = 0;
            while (!pipelineData && waitCount < 10) { // max wait 5s
                await delay(500);
                waitCount++;
            }
        }
        
        if (el) {
            el.classList.remove("active");
            el.classList.add("completed");
            
            if (pipelineData && pipelineData.metrics) {
                const latency = pipelineData.metrics[step.key];
                const stageKey = step.key.replace("_latency_ms", "");
                const stageStatus = pipelineData.metrics.stage_status ? pipelineData.metrics.stage_status[stageKey] : "";
                
                if (stageStatus === "skipped") {
                    el.querySelector(".step-status").textContent = "✓ Skipped";
                } else if (latency === 0 || latency === undefined || latency === null) {
                    el.querySelector(".step-status").textContent = "✓ <1ms";
                } else {
                    el.querySelector(".step-status").textContent = `✓ ${latency}ms`;
                }
            } else {
                el.querySelector(".step-status").textContent = "✓ Completed";
            }
        }
    }

    if (pipelineData) {
        triggerSkeletonState(false);
        setRecordingState("IDLE");
        updateDashboard(pipelineData);
        loadHistory();
    } else {
        triggerSkeletonState(false);
        setRecordingState("IDLE");
        alert("Pipeline execution timed out or failed to return data.");
    }
}

async function handleRunDemo() {
    const scId = demoScenarioSelect.value;
    if (!scId) return;
    
    const scenario = loadedScenarios.find(sc => sc.id === scId);
    if (!scenario) return;

    // Reset playing audio and visual state
    ttsAudioElement.pause();
    resetAudioPlayerUI();
    document.getElementById("pipeline-audio-preview").style.display = "none";
    const farmerVoicePlayer = document.getElementById("demo-farmer-voice-player");
    if (farmerVoicePlayer) {
        farmerVoicePlayer.pause();
        farmerVoicePlayer.src = "";
    }

    setRecordingState("PROCESSING");
    triggerSkeletonState(true);
    
    // Play pre-recorded farmer voice sample
    if (scenario.input_audio_url) {
        const player = document.getElementById("demo-farmer-voice-player");
        if (player) {
            player.src = scenario.input_audio_url + "?t=" + Date.now();
            player.load();
            player.play().catch(e => console.log("Audio play blocked:", e));
            document.getElementById("pipeline-audio-preview").style.display = "block";
            document.getElementById("demo-loaded-dialect-phrase").textContent = scenario.raw_transcript;
        }
    }

    // Start backend call
    const resultPromise = fetch("/api/demo/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            scenario_id: scId,
            district: districtSelect.value
        })
    }).then(async res => {
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Scenario run failed");
        }
        return res.json();
    });

    try {
        await runVisualPipeline(scenario, resultPromise);
    } catch (err) {
        console.error("Visual pipeline error:", err);
        alert(`Error running demo: ${err.message}`);
        setRecordingState("IDLE");
        triggerSkeletonState(false);
    }
}


// Media Recorder FAB trigger
function handleMicClick() {
    if (recordingState === "RECORDING") {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    audioChunks = [];
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.addEventListener("dataavailable", (e) => {
            audioChunks.push(e.data);
        });
        
        mediaRecorder.addEventListener("stop", handleStoppedRecording);
        
        mediaRecorder.start();
        setRecordingState("RECORDING");
    } catch (err) {
        alert("মাইক্রোফোন অ্যাক্সেস করতে ব্যর্থ হয়েছে। অনুগ্রহ করে ব্রাউজার পারমিশন চেক করুন।");
        console.error("Microphone access failed:", err);
    }
}

function stopRecording() {
    if (mediaRecorder && recordingState === "RECORDING") {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        setRecordingState("PROCESSING");
    }
}

async function handleStoppedRecording() {
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    
    triggerSkeletonState(true);
    const uploadResult = await uploadAudioBlob(audioBlob, "recorded_farmer_voice.wav");
    
    if (uploadResult && uploadResult.file_path) {
        runPipeline({ audio_path: uploadResult.file_path });
    } else {
        triggerSkeletonState(false);
        setRecordingState("IDLE");
        alert("Audio upload failed.");
    }
}

async function handleFileSelection(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    fileNameDisplay.textContent = `Selected: ${file.name}`;
    setRecordingState("PROCESSING");
    triggerSkeletonState(true);
    
    const uploadResult = await uploadAudioBlob(file, file.name);
    if (uploadResult && uploadResult.file_path) {
        runPipeline({ audio_path: uploadResult.file_path });
    } else {
        triggerSkeletonState(false);
        setRecordingState("IDLE");
        fileNameDisplay.textContent = "Upload failed.";
    }
}

async function uploadAudioBlob(blob, filename) {
    const formData = new FormData();
    formData.append("audio", blob, filename);
    
    try {
        const response = await fetch("/api/audio/upload", {
            method: "POST",
            body: formData
        });
        return await response.json();
    } catch (err) {
        console.error("Error uploading audio:", err);
        return null;
    }
}

async function runPipeline(bodyPayload) {
    document.getElementById("pipeline-visualizer").style.display = "none";
    triggerSkeletonState(true);
    setRecordingState("PROCESSING");
    
    bodyPayload.lat = currentCoords.lat;
    bodyPayload.lon = currentCoords.lon;
    bodyPayload.district = districtSelect.value;

    
    try {
        const response = await fetch("/api/diagnose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyPayload)
        });
        
        const data = await response.json();
        triggerSkeletonState(false);
        setRecordingState("IDLE");
        
        if (response.ok) {
            updateDashboard(data);
            loadHistory();
        } else {
            alert(`ত্রুটি: ${data.error || "পাইপলাইন ব্যর্থ হয়েছে।"}`);
        }
    } catch (err) {
        triggerSkeletonState(false);
        setRecordingState("IDLE");
        console.error("Pipeline failure:", err);
        alert("সার্ভারের সাথে সংযোগ স্থাপন করা সম্ভব হয়নি।");
    }
}

// Update UI Dashboard with pipeline data
function updateDashboard(data) {
    currentConversationId = data.conversation_id;
    
    // Extract info from structured payload
    const cropVal = data.intent?.crop || data.crop || "অন্যান্য";
    const symptomsVal = Array.isArray(data.intent?.symptoms) ? data.intent.symptoms.join(", ") : (data.symptoms || "নেই");
    const severityVal = data.intent?.severity || data.severity || "Medium";
    const urgencyVal = data.intent?.urgency || data.urgency || "Medium";
    
    diagCrop.textContent = cropVal;
    diagSymptoms.textContent = symptomsVal;
    diagSeverity.textContent = severityVal;
    diagUrgency.textContent = urgencyVal;
    
    diagSeverity.className = `badge badge-${severityVal.toLowerCase()}`;
    diagUrgency.className = `badge badge-${urgencyVal.toLowerCase()}`;
    
    // Audit Status Badge
    if (data.badge) {
        const textVal = data.badge.text || data.badge.label || "-";
        const classVal = data.badge.class || data.badge.css_class || "";
        const titleVal = data.badge.reason || data.badge.description || "";
        diagAuditStatus.textContent = textVal;
        diagAuditStatus.className = `badge ${classVal}`;
        diagAuditStatus.title = titleVal;
        diagAuditStatus.style.display = "inline-block";
    } else {
        diagAuditStatus.textContent = "-";
        diagAuditStatus.className = "badge";
        diagAuditStatus.style.display = "inline-block";
    }
    
    // Confidence Score
    const systemConfidence = data.confidence?.system_confidence_score || data.confidence || 0.8;
    const confScore = Math.round(systemConfidence * 100);
    diagConfidence.textContent = `${confScore}%`;
    confidenceFill.style.width = `${confScore}%`;
    
    // Recommendation Text
    const recText = data.recommendation_text || data.advisor?.bangla_recommendation || "";
    recTextBox.textContent = recText;
    
    // Weather Section Sync
    if (data.weather) {
        locationDisplay.textContent = data.weather.resolved_district || "ঢাকা";
        tempDisplay.textContent = `${(data.weather.temp || 30.0).toFixed(1)}°C`;
        weatherDescDisplay.textContent = `${data.weather.description || "মেঘলা আকাশ"}, আদ্রতা: ${data.weather.humidity || 70}%`;
    }
    
    // Set up Audio element URL
    const audioUrl = data.recommendation_audio_url || data.advisor?.recommendation_audio_url;
    if (audioUrl) {
        ttsAudioElement.src = audioUrl + "?t=" + Date.now();
        ttsAudioElement.load();
        resetAudioPlayerUI();
        playAudio();
        
        // Show download audio button
        downloadAudioBtn.href = audioUrl;
        downloadAudioBtn.download = `krishikantho_advice_${data.conversation_id}.mp3`;
        downloadAudioBtn.style.display = "flex";
    } else {
        downloadAudioBtn.style.display = "none";
    }
    
    // Setup export report actions
    if (currentConversationId) {
        exportTxtBtn.href = `/api/export/${currentConversationId}/txt`;
        exportTxtBtn.style.display = "flex";
        exportJsonBtn.href = `/api/export/${currentConversationId}/json`;
        exportJsonBtn.style.display = "flex";
    } else {
        exportTxtBtn.style.display = "none";
        exportJsonBtn.style.display = "none";
    }
    
    // Update Judge Mode Card
    const judgeWeather = data.judge_mode?.weather_factors_used || data.advisor?.weather_influence_explanation || "No weather constraints applied.";
    judgeWeatherFactors.innerHTML = `
        <strong>Resolved District:</strong> ${data.weather?.resolved_district || data.district || "Dhaka"}<br>
        <strong>Parameters:</strong> Temp: ${data.weather?.temp}°C, Humidity: ${data.weather?.humidity}%, Rain: ${data.weather?.rainfall || 0}mm<br><br>
        <strong>Rules Analysis:</strong> ${judgeWeather}
    `;
    
    judgeRagSources.innerHTML = "";
    const docs = data.rag?.retrieved_chunks || data.rag_sources || [];
    if (docs.length > 0) {
        docs.forEach(doc => {
            const li = document.createElement("li");
            const chunkText = doc.text_chunk || doc.text || "";
            const sourceName = doc.source || doc.source_name || "Reference Guide";
            li.innerHTML = `<strong>${sourceName}:</strong> ${chunkText.substring(0, 200)}...`;
            judgeRagSources.appendChild(li);
        });
    } else {
        const li = document.createElement("li");
        li.textContent = "No reference guides matched in local knowledge base.";
        judgeRagSources.appendChild(li);
    }
    
    const reasoningSum = data.judge_mode?.reasoning_summary || data.advisor?.diagnosis_title || "Processed successfully.";
    const asrRaw = data.raw_transcript || data.original_transcript || "";
    const asrCorrected = data.asr_corrected?.corrected_bangla || data.corrected_bangla || "";
    const translation = data.asr_corrected?.english_translation || data.english_translation || "";
    const ruleApplied = data.confidence?.matching_rules_applied || [];
    
    judgeReasoning.innerHTML = `
        <strong>ASR Raw:</strong> "${asrRaw}"<br>
        <strong>ASR Corrected:</strong> "${asrCorrected}"<br>
        <strong>Translation:</strong> "${translation}"<br><br>
        <strong>System Reasoning:</strong> ${reasoningSum}<br>
        <strong>Confidence Rubrics Applied:</strong> ${ruleApplied.join(", ") || "None"}
    `;

    // Update performance dashboard metrics
    const metrics = data.metrics || {};
    const totalLatency = metrics.total_latency_ms || 0;
    const totalLatencySec = (totalLatency / 1000).toFixed(2);
    
    const metricTotalLatency = document.getElementById("metric-total-latency");
    const metricLatencyBadge = document.getElementById("metric-latency-badge");
    const metricInputTokens = document.getElementById("metric-input-tokens");
    const metricOutputTokens = document.getElementById("metric-output-tokens");
    const metricRetrievedDocs = document.getElementById("metric-retrieved-docs");
    
    if (metricTotalLatency) metricTotalLatency.textContent = `${totalLatency} ms`;
    if (metricLatencyBadge) {
        metricLatencyBadge.textContent = `${totalLatencySec}s Execution`;
        metricLatencyBadge.className = totalLatency < 3000 ? "badge badge-low" : (totalLatency < 6000 ? "badge badge-medium" : "badge badge-high");
    }
    
    if (metricInputTokens) metricInputTokens.textContent = metrics.input_token_count || 120;
    if (metricOutputTokens) metricOutputTokens.textContent = metrics.output_token_count || 380;
    if (metricRetrievedDocs) metricRetrievedDocs.textContent = metrics.retrieved_doc_count || docs.length || 0;
    
    // Update Stage latency bars
    const stages = [
        { key: "stt", value: metrics.stt_latency_ms },
        { key: "correction", value: metrics.correction_latency_ms },
        { key: "weather", value: metrics.weather_latency_ms },
        { key: "intent", value: metrics.intent_latency_ms },
        { key: "rag", value: metrics.rag_latency_ms },
        { key: "advisor", value: metrics.advisor_latency_ms },
        { key: "tts", value: metrics.tts_latency_ms }
    ];
    
    const stageStatus = metrics.stage_status || {};
    
    stages.forEach(stg => {
        const bar = document.getElementById(`bar-latency-${stg.key}`);
        const label = document.getElementById(`label-latency-${stg.key}`);
        if (label) {
            const statusKey = stageStatus[stg.key] || "";
            let valStr = "";
            
            if (stg.value === undefined || stg.value === null) {
                valStr = "N/A";
            } else if (stg.value === 0) {
                if (statusKey === "skipped") {
                    valStr = "N/A";
                } else {
                    valStr = "<1 ms";
                }
            } else {
                valStr = `${stg.value} ms`;
            }
            
            let statusText = "Completed";
            let badgeStyle = "background: rgba(76, 175, 80, 0.15); color: #2E7D32;"; // Green
            let statusIcon = '<i class="fa-solid fa-circle-check"></i>';
            
            if (statusKey === "error") {
                statusText = "Failed";
                badgeStyle = "background: rgba(211, 47, 47, 0.15); color: #C62828;"; // Red
                statusIcon = '<i class="fa-solid fa-circle-xmark"></i>';
            } else if (statusKey === "skipped") {
                statusText = "Not Required";
                badgeStyle = "background: rgba(120, 120, 120, 0.15); color: #555;"; // Gray
                statusIcon = '<i class="fa-solid fa-circle-minus"></i>';
            } else if (statusKey === "unavailable") {
                statusText = "Unavailable";
                badgeStyle = "background: rgba(120, 120, 120, 0.15); color: #555;"; // Gray
                statusIcon = '<i class="fa-solid fa-circle-exclamation"></i>';
            }
            
            label.innerHTML = `
                <div style="display: inline-flex; align-items: center; gap: 0.5rem; justify-content: flex-end; width: 100%;">
                    <span>${valStr}</span>
                    <span class="badge" style="font-size: 0.72rem; padding: 4px 8px; font-weight: 700; white-space: nowrap; border-radius: 6px; display: inline-flex; align-items: center; gap: 0.25rem; ${badgeStyle}">${statusIcon} ${statusText}</span>
                </div>
            `;
        }
        if (bar) {
            const pct = totalLatency > 0 ? Math.min(100, ((stg.value || 0) / totalLatency) * 100) : 0;
            bar.style.width = `${pct}%`;
        }
    });

    // Update Resilience Alert Banner
    let hasFallbackActive = false;
    stages.forEach(stg => {
        const statusKey = stageStatus[stg.key] || "";
        if (statusKey === "mock_fallback" || statusKey === "fallback") {
            hasFallbackActive = true;
        }
    });
    
    const resilienceBanner = document.getElementById("resilience-alert-banner");
    if (resilienceBanner) {
        if (hasFallbackActive) {
            resilienceBanner.style.display = "flex";
        } else {
            resilienceBanner.style.display = "none";
        }
    }
    
    // Update Developer Diagnostics Section
    const devRawStatus = document.getElementById("developer-raw-status");
    if (devRawStatus) {
        devRawStatus.innerHTML = `
            correction = ${stageStatus.correction || "none"}<br>
            intent = ${stageStatus.intent || "none"}<br>
            advisor = ${stageStatus.advisor || "none"}<br>
            tts = ${stageStatus.tts || "none"}<br>
            weather = ${stageStatus.weather || "none"}<br>
            rag = ${stageStatus.rag || "none"}<br>
            stt = ${stageStatus.stt || "none"}
        `;
    }
}


// Audio Player controls
function toggleAudioPlayback() {
    if (!ttsAudioElement.src) return;
    
    if (ttsAudioElement.paused) {
        playAudio();
    } else {
        pauseAudio();
    }
}

function playAudio() {
    ttsAudioElement.play().then(() => {
        audioPlayPauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
    }).catch(err => {
        console.error("Playback block:", err);
    });
}

function pauseAudio() {
    ttsAudioElement.pause();
    audioPlayPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
}

function resetAudioPlayerUI() {
    audioPlayPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
    audioProgressFill.style.width = "0%";
    audioTime.textContent = "00:00";
}

function updateAudioProgressBar() {
    if (!ttsAudioElement.duration) return;
    
    const pct = (ttsAudioElement.currentTime / ttsAudioElement.duration) * 100;
    audioProgressFill.style.width = `${pct}%`;
    
    const mins = Math.floor(ttsAudioElement.currentTime / 60);
    const secs = Math.floor(ttsAudioElement.currentTime % 60);
    audioTime.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function handleAudioEnded() {
    resetAudioPlayerUI();
    setRecordingState("IDLE");
}

function scrubAudio(e) {
    if (!ttsAudioElement.duration) return;
    const rect = audioProgressContainer.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    ttsAudioElement.currentTime = pct * ttsAudioElement.duration;
}

// Copy recommendation text
function copyRecommendationText() {
    const text = recTextBox.textContent.trim();
    if (!text || text.startsWith("পরামর্শ শুনতে")) return;
    
    navigator.clipboard.writeText(text).then(() => {
        alert("পরামর্শের টেক্সট ক্লিপবোর্ডে কপি করা হয়েছে!");
    }).catch(err => {
        console.error("Failed to copy:", err);
    });
}

// Skeleton loading feedback
function triggerSkeletonState(isLoading) {
    const cardElements = [
        document.getElementById("diagnosis-card"),
        document.getElementById("recommendation-card"),
        document.getElementById("judge-card")
    ];
    
    cardElements.forEach(card => {
        if (isLoading) {
            card.classList.add("skeleton");
            card.querySelectorAll(".diag-val, .badge, .recommendation-text-box, .judge-content, #forecast-display").forEach(el => {
                el.style.opacity = "0.2";
            });
        } else {
            card.classList.remove("skeleton");
            card.querySelectorAll(".diag-val, .badge, .recommendation-text-box, .judge-content, #forecast-display").forEach(el => {
                el.style.opacity = "1";
            });
        }
    });
}

// History Logs loader
async function loadHistory() {
    try {
        const response = await fetch("/api/history?limit=15");
        const data = await response.json();
        
        if (response.ok) {
            historyContainer.innerHTML = "";
            if (data.length === 0) {
                historyContainer.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">কোনো পূর্ববর্তী পরামর্শের ইতিহাস পাওয়া যায়নি।</div>';
                return;
            }
            
            data.forEach(conv => {
                const date = new Date(conv.timestamp);
                const dateStr = date.toLocaleDateString("bn-BD", { day: "numeric", month: "long", year: "numeric" });
                
                const crop = conv.diagnosis_summary?.crop || "অন্যান্য";
                const severity = conv.diagnosis_summary?.severity || "Medium";
                const confidence = Math.round((conv.diagnosis_summary?.confidence || 0.8) * 100);
                const badgeInfo = conv.diagnosis_summary?.badge;
                
                const item = document.createElement("div");
                item.className = "history-item";
                
                let badgeHtml = "";
                if (badgeInfo) {
                    badgeHtml = `<span class="badge ${badgeInfo.class}" style="margin-left: 0.5rem; font-size: 0.7rem; padding: 0.15rem 0.5rem;">${badgeInfo.text}</span>`;
                }
                
                const transcriptText = conv.raw_transcript || conv.transcript || "";
                
                item.innerHTML = `
                    <div class="history-left">
                        <div class="history-crop-badge">${crop}</div>
                        <div class="history-details">
                            <h4>${transcriptText.length > 35 ? transcriptText.substring(0, 35) + "..." : transcriptText}</h4>
                            <p><i class="fa-regular fa-calendar"></i> ${dateStr} • তীব্রতা: ${severity} • নির্ভরযোগ্যতা: ${confidence}% ${badgeHtml}</p>
                        </div>
                    </div>
                    <div class="history-actions">
                        <span style="font-weight: 700; color: var(--primary-color);">পরামর্শ দেখুন <i class="fa-solid fa-angle-right"></i></span>
                        <button class="history-delete-btn" data-id="${conv.conversation_id}" aria-label="Delete history item">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                `;
                
                item.addEventListener("click", (e) => {
                    if (e.target.closest(".history-delete-btn")) {
                        e.stopPropagation();
                        deleteHistoryItem(conv.conversation_id);
                        return;
                    }
                    loadHistoryItemToDashboard(conv.conversation_id);
                });
                
                historyContainer.appendChild(item);
            });
        }
    } catch (err) {
        console.error("Error loading history:", err);
    }
}

// Fetch and load historical item detail
async function loadHistoryItemToDashboard(convId) {
    try {
        triggerSkeletonState(true);
        const response = await fetch(`/api/history/${convId}`);
        const data = await response.json();
        triggerSkeletonState(false);
        
        if (response.ok) {
            updateDashboard(data);
            document.getElementById("rec-text-box").scrollIntoView({ behavior: "smooth" });
        } else {
            alert("ইতিহাসের আইটেমটি লোড করতে ব্যর্থ হয়েছে।");
        }
    } catch (err) {
        triggerSkeletonState(false);
        console.error("Error loading item details:", err);
    }
}

// Delete history item
async function deleteHistoryItem(convId) {
    if (!window.__BYPASS_CONFIRM__) {
        if (!confirm("আপনি কি এই পরামর্শের ইতিহাস মুছে ফেলতে চান?")) return;
    }
    
    try {
        const response = await fetch(`/api/history/delete/${convId}`, {
            method: "DELETE"
        });
        
        if (response.ok) {
            loadHistory();
        } else {
            alert("ইতিহাস মুছে ফেলতে ব্যর্থ হয়েছে।");
        }
    } catch (err) {
        console.error("Error deleting historical item:", err);
    }
}


// ==========================================
// KNOWLEDGE BASE & SYSTEM ARCHITECTURE INTERACTIVE LOGIC
// ==========================================

// Navigation tab switching
const navBtnDashboard = document.getElementById("nav-btn-dashboard");
const navBtnKnowledge = document.getElementById("nav-btn-knowledge");
const navBtnArchitecture = document.getElementById("nav-btn-architecture");

const pageDashboard = document.getElementById("page-dashboard");
const pageKnowledge = document.getElementById("page-knowledge");
const pageArchitecture = document.getElementById("page-architecture");

if (navBtnDashboard && navBtnKnowledge && navBtnArchitecture) {
    const navBtns = [navBtnDashboard, navBtnKnowledge, navBtnArchitecture];
    const pages = [pageDashboard, pageKnowledge, pageArchitecture];
    
    function switchTab(activeIndex) {
        navBtns.forEach((btn, idx) => {
            if (idx === activeIndex) {
                btn.classList.add("active-nav");
                btn.style.color = "var(--primary-color)";
                btn.style.borderBottomColor = "var(--primary-color)";
            } else {
                btn.classList.remove("active-nav");
                btn.style.color = "var(--text-secondary)";
                btn.style.borderBottomColor = "transparent";
            }
        });
        
        pages.forEach((page, idx) => {
            if (idx === activeIndex) {
                page.style.display = "block";
            } else {
                page.style.display = "none";
            }
        });
        
        if (activeIndex === 1) {
            loadKnowledgeStats();
        }
    }
    
    navBtnDashboard.addEventListener("click", () => switchTab(0));
    navBtnKnowledge.addEventListener("click", () => switchTab(1));
    navBtnArchitecture.addEventListener("click", () => switchTab(2));
}

// Fetch and render Knowledge Base statistics
async function loadKnowledgeStats() {
    try {
        const response = await fetch("/api/knowledge/stats");
        if (response.ok) {
            const stats = await response.json();
            const totalDocsEl = document.getElementById("kb-total-docs");
            const totalChunksEl = document.getElementById("kb-total-chunks");
            const embeddingModelEl = document.getElementById("kb-embedding-model");
            const lastIngestionEl = document.getElementById("kb-last-ingestion");
            
            if (totalDocsEl) totalDocsEl.textContent = stats.total_documents;
            if (totalChunksEl) totalChunksEl.textContent = stats.total_chunks;
            if (embeddingModelEl) embeddingModelEl.textContent = stats.embedding_model;
            if (lastIngestionEl) lastIngestionEl.textContent = stats.last_ingestion;
        }
    } catch (err) {
        console.error("Error fetching knowledge base stats:", err);
    }
}

// Ingestion trigger
const triggerReingestionBtn = document.getElementById("trigger-reingestion-btn");
if (triggerReingestionBtn) {
    triggerReingestionBtn.addEventListener("click", async () => {
        const originalText = triggerReingestionBtn.innerHTML;
        triggerReingestionBtn.disabled = true;
        triggerReingestionBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Indexing...';
        
        try {
            const response = await fetch("/api/knowledge/ingest", {
                method: "POST"
            });
            const data = await response.json();
            if (response.ok && data.success) {
                alert(data.message || "Knowledge base re-indexed successfully!");
                loadKnowledgeStats();
            } else {
                alert("Failed to index knowledge base: " + (data.error || "Unknown error"));
            }
        } catch (err) {
            console.error("Error during ingestion:", err);
            alert("Connection error during re-indexing.");
        } finally {
            triggerReingestionBtn.disabled = false;
            triggerReingestionBtn.innerHTML = originalText;
        }
    });
}

// RAG Playground search simulator
const ragPlaygroundQuery = document.getElementById("rag-playground-query");
const ragPlaygroundTestBtn = document.getElementById("rag-playground-test-btn");
const ragPlaygroundResults = document.getElementById("rag-playground-results");

if (ragPlaygroundQuery && ragPlaygroundTestBtn && ragPlaygroundResults) {
    async function testRagSearch() {
        const queryText = ragPlaygroundQuery.value.trim();
        if (!queryText) return;
        
        ragPlaygroundTestBtn.disabled = true;
        ragPlaygroundTestBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
        ragPlaygroundResults.style.display = "block";
        ragPlaygroundResults.innerHTML = '<div style="color: var(--text-secondary); text-align: center;">Searching vector store collections...</div>';
        
        try {
            const response = await fetch("/api/diagnose", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text_query: queryText })
            });
            const data = await response.json();
            if (response.ok && data.rag && data.rag.retrieved_chunks) {
                const chunks = data.rag.retrieved_chunks;
                if (chunks.length === 0) {
                    ragPlaygroundResults.innerHTML = '<div style="color: var(--text-secondary); text-align: center;">No matches found in ChromaDB collections.</div>';
                } else {
                    ragPlaygroundResults.innerHTML = chunks.map((chunk, idx) => {
                        const chunkText = chunk.text_chunk || chunk.text || "";
                        const sourceName = chunk.source || chunk.source_name || "Reference Guide";
                        const pageNum = chunk.page_number || chunk.page || 1;
                        const relevance = chunk.relevance_score || 0.8;
                        const cropTag = chunk.crop || "Unknown";
                        const diseaseTag = chunk.disease || "Unknown";
                        
                        return `
                            <div style="border-bottom: ${idx < chunks.length - 1 ? '1px solid var(--border-color)' : 'none'}; padding-bottom: 1rem; margin-bottom: 1rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <span style="font-weight: 700; color: var(--primary-color); font-size: 0.9rem;">
                                        <i class="fa-regular fa-file-lines"></i> ${sourceName} (Page ${pageNum})
                                    </span>
                                    <span style="background: rgba(46,125,50,0.1); color: var(--primary-color); padding: 0.15rem 0.5rem; border-radius: 99px; font-size: 0.75rem; font-weight: 700;">
                                        Relevance Score: ${relevance.toFixed(2)}
                                    </span>
                                </div>
                                <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.25rem;">
                                    <strong>Scope:</strong> Crop: <span style="text-transform: capitalize;">${cropTag}</span> | Target Disease: <span style="text-transform: capitalize;">${diseaseTag}</span>
                                </div>
                                <blockquote style="font-size: 0.9rem; color: var(--text-primary); border-left: 3px solid var(--secondary-color); padding-left: 0.75rem; margin: 0.5rem 0; font-style: italic; background: rgba(0,0,0,0.01); padding-top: 0.25rem; padding-bottom: 0.25rem;">
                                    "${chunkText}"
                                </blockquote>
                            </div>
                        `;
                    }).join("");
                }
            } else {
                ragPlaygroundResults.innerHTML = '<div style="color: var(--accent-red); text-align: center;">Error querying vector collections.</div>';
            }
        } catch (err) {
            console.error("RAG Playground search error:", err);
            ragPlaygroundResults.innerHTML = '<div style="color: var(--accent-red); text-align: center;">Connection failed.</div>';
        } finally {
            ragPlaygroundTestBtn.disabled = false;
            ragPlaygroundTestBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Query Vector Store';
        }
    }
    
    ragPlaygroundTestBtn.addEventListener("click", testRagSearch);
    ragPlaygroundQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter") testRagSearch();
    });
}

