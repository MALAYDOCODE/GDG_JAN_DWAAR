const API_URL = "https://gdg-jan-dwaar-1.onrender.com";

const submitButton = document.getElementById("submit-button");
const problemInput = document.getElementById("problem");
const languageInput = document.getElementById("language");
const locationInput = document.getElementById("location");
const voiceButton = document.getElementById("voice-button");
const voiceText = document.getElementById("voice-text");
const recordingStatus = document.getElementById("recording-status");
const characterCount = document.getElementById("character-count");
const aiSection = document.getElementById("ai-section");
const successSection = document.getElementById("success-section");

const aiProblem = document.getElementById("ai-problem");
const aiCategory = document.getElementById("ai-category");
const aiSeverity = document.getElementById("ai-severity");
const aiLocation = document.getElementById("ai-location");
const aiSummary = document.getElementById("ai-summary-text");

const editButton = document.getElementById("edit-button");
const confirmButton = document.getElementById("confirm-button");
const requestId = document.getElementById("request-id");

const photoInput = document.getElementById("photo");
const photoPreview = document.getElementById("photo-preview");

let selectedCategory = "";
let recorder = null;
let chunks = [];
let isRecording = false;
let latestReport = null;

document.querySelectorAll(".category-btn").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".category-btn").forEach((item) => {
            item.classList.remove("selected");
        });

        button.classList.add("selected");

        selectedCategory =
            button.dataset.category || "";
    });
});

problemInput.addEventListener("input", () => {
    const length = problemInput.value.length;

    characterCount.textContent =
        `${length} / 500`;
});

photoInput.addEventListener("change", () => {
    photoPreview.innerHTML = "";

    const file = photoInput.files[0];

    if (!file) {
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        alert(
            "Please choose an image smaller than 5MB."
        );

        photoInput.value = "";

        return;
    }

    const image =
        document.createElement("img");

    image.src =
        URL.createObjectURL(file);

    image.alt =
        "Selected image";

    photoPreview.appendChild(
        image
    );
});

function validateReport() {
    const problem =
        problemInput.value.trim();

    const language =
        languageInput.value;

    if (!problem) {
        alert(
            "Please describe the problem."
        );

        problemInput.focus();

        return false;
    }

    if (problem.length < 5) {
        alert(
            "Please provide a little more detail about the problem."
        );

        problemInput.focus();

        return false;
    }

    if (!language) {
        alert(
            "Please select a language."
        );

        return false;
    }

    if (!selectedCategory) {
        alert(
            "Please select a category."
        );

        return false;
    }

    if (!locationInput.value.trim()) {
        alert(
            "Please enter or detect the location."
        );

        locationInput.focus();

        return false;
    }

    return true;
}

function showAIResult(result) {
    aiProblem.textContent =
        result.english_text ||
        result.original_text ||
        problemInput.value.trim();

    aiCategory.textContent =
        result.category ||
        selectedCategory ||
        "Other";

    aiSeverity.textContent =
        result.severity ||
        "Normal";

    aiLocation.textContent =
        result.location ||
        locationInput.value.trim() ||
        "Not provided";

    aiSummary.textContent =
        result.summary ||
        result.english_text ||
        problemInput.value.trim();

    aiSection.classList.remove(
        "hidden"
    );

    aiSection.scrollIntoView({
        behavior: "smooth"
    });
}

submitButton.addEventListener(
    "click",
    async () => {
        if (!validateReport()) {
            return;
        }

        const token =
            localStorage.getItem("token");

        if (!token) {
            alert(
                "Please login before submitting a report."
            );

            return;
        }

        const reportData = {
            message:
                problemInput.value.trim(),

            complaint:
                problemInput.value.trim(),

            language:
                languageInput.value,

            category:
                selectedCategory,

            location:
                locationInput.value.trim()
        };

        submitButton.disabled = true;

        try {
            const response =
                await fetch(
                    `${API_URL}/api/analyse`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Authorization":
                                `Bearer ${token}`
                        },

                        body:
                            JSON.stringify(
                                reportData
                            )
                    }
                );

            const result =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    result.message ||
                    "Unable to analyse the report."
                );
            }

            latestReport =
                result;

            showAIResult(
                result
            );

        } catch (error) {
            console.error(
                "Analysis error:",
                error
            );

            alert(
                error.message ||
                "Could not connect to the backend."
            );

        } finally {
            submitButton.disabled =
                false;
        }
    }
);

editButton.addEventListener(
    "click",
    () => {
        aiSection.classList.add(
            "hidden"
        );

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }
);

confirmButton.addEventListener(
    "click",
    async () => {
        if (!latestReport) {
            alert(
                "Please submit the report first."
            );

            return;
        }

        const token =
            localStorage.getItem("token");

        if (!token) {
            alert(
                "Please login before confirming the report."
            );

            return;
        }

        const reportData = {
            complaint:
                latestReport.original_text ||
                problemInput.value.trim(),

            language:
                languageInput.value,

            category:
                latestReport.category ||
                selectedCategory,

            location:
                latestReport.location ||
                locationInput.value.trim()
        };

        confirmButton.disabled =
            true;

        try {
            const response =
                await fetch(
                    `${API_URL}/api/complaints`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Authorization":
                                `Bearer ${token}`
                        },

                        body:
                            JSON.stringify(
                                reportData
                            )
                    }
                );

            const result =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    result.message ||
                    "Unable to register complaint."
                );
            }

            latestReport =
                result;

            requestId.textContent =
                result.complaint_id ||
                "Not available";

            aiSection.classList.add(
                "hidden"
            );

            successSection.classList.remove(
                "hidden"
            );

            successSection.scrollIntoView({
                behavior: "smooth"
            });

        } catch (error) {
            console.error(
                "Complaint submission error:",
                error
            );

            alert(
                error.message ||
                "Could not register the complaint."
            );

        } finally {
            confirmButton.disabled =
                false;
        }
    }
);

async function startRecording() {
    try {
        if (
            !navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia
        ) {
            alert(
                "Voice recording is not supported by this browser."
            );

            return;
        }

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        chunks = [];

        recorder =
            new MediaRecorder(
                stream
            );

        recorder.ondataavailable =
            (event) => {
                if (
                    event.data.size > 0
                ) {
                    chunks.push(
                        event.data
                    );
                }
            };

        recorder.onstop =
            async () => {
                stream
                    .getTracks()
                    .forEach(
                        (track) => {
                            track.stop();
                        }
                    );

                await sendAudio();
            };

        recorder.start();

        isRecording = true;

        voiceButton.classList.add(
            "recording"
        );

        voiceText.textContent =
            "Stop recording";

        recordingStatus.textContent =
            "Listening... Speak your problem";

    } catch (error) {
        console.error(
            "Microphone error:",
            error
        );

        alert(
            "Microphone permission is required for voice reporting."
        );
    }
}

function stopRecording() {
    if (
        recorder &&
        recorder.state !== "inactive"
    ) {
        recorder.stop();

        isRecording = false;

        voiceButton.classList.remove(
            "recording"
        );

        voiceText.textContent =
            "Processing voice...";

        recordingStatus.textContent =
            "Sending audio to AI...";
    }
}

async function sendAudio() {
    const token =
        localStorage.getItem(
            "token"
        );

    if (!token) {
        alert(
            "Please login before using voice reporting."
        );

        voiceText.textContent =
            "Speak your problem";

        recordingStatus.textContent =
            "Please login first.";

        return;
    }

    if (!chunks.length) {
        recordingStatus.textContent =
            "No audio was recorded.";

        voiceText.textContent =
            "Speak your problem";

        return;
    }

    const audioBlob =
        new Blob(
            chunks,
            {
                type: "audio/webm"
            }
        );

    const formData =
        new FormData();

    formData.append(
        "audio",
        audioBlob,
        "complaint.webm"
    );

    formData.append(
        "category",
        selectedCategory
    );

    formData.append(
        "location",
        locationInput.value.trim()
    );

    formData.append(
        "language",
        languageInput.value
    );

    try {
        const response =
            await fetch(
                `${API_URL}/api/voice-complaint`,
                {
                    method: "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: formData
                }
            );

        const result =
            await response.json();

        if (!response.ok) {
            throw new Error(
                result.message ||
                "Voice processing failed."
            );
        }

        if (!result.success) {
            throw new Error(
                result.message ||
                "Could not convert voice to text."
            );
        }

        problemInput.value =
            result.transcription ||
            result.text ||
            "";

        problemInput.dispatchEvent(
            new Event("input")
        );

        recordingStatus.textContent =
            "Voice converted to text ✓";

        voiceText.textContent =
            "Speak your problem";

    } catch (error) {
        console.error(
            "Voice upload error:",
            error
        );

        recordingStatus.textContent =
            "Could not process voice.";

        voiceText.textContent =
            "Speak your problem";

        alert(
            error.message ||
            "Could not connect to the voice backend."
        );
    }
}

voiceButton.addEventListener(
    "click",
    () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    }
);

async function getLocation() {
    if (!navigator.geolocation) {
        alert(
            "Location is not supported by this browser."
        );

        return;
    }

    const button =
        document.getElementById(
            "location-button"
        );

    button.textContent =
        "Detecting location...";

    button.disabled =
        true;

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;

            document.getElementById(
                "latitude"
            ).value =
                latitude;

            document.getElementById(
                "longitude"
            ).value =
                longitude;

            try {
                const response =
                    await fetch(
                        `${API_URL}/api/location`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    latitude:
                                        latitude,

                                    longitude:
                                        longitude
                                })
                        }
                    );

                const result =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        result.message ||
                        "Location lookup failed."
                    );
                }

                locationInput.value =
                    result.location ||
                    `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

                button.textContent =
                    "Location detected ✓";

            } catch (error) {
                console.error(
                    "Location API error:",
                    error
                );

                locationInput.value =
                    `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

                button.textContent =
                    "Coordinates detected ✓";
            }

            button.disabled =
                false;
        },

        (error) => {
            console.error(
                "Browser location error:",
                error.message
            );

            button.textContent =
                "Use my current location";

            button.disabled =
                false;

            alert(
                "Unable to get your location. Please allow location access and try again."
            );
        },

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }
    );
}
