const API_URL = "https://YOUR-RENDER-URL.onrender.com";

submitButton.addEventListener("click", async () => {

    if (!validateReport()) {
        return;
    }

    const reportData = {
        message: problemInput.value.trim(),
        language: languageInput.value,
        category: selectedCategory,
        location: locationInput.value.trim(),
        timestamp: new Date().toISOString()
    };

    console.log("Report data ready for backend:", reportData);

    try {

        const response = await fetch(
            `${API_URL}/api/analyse`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(reportData)
            }
        );

        if (!response.ok) {
            throw new Error(`Analysis request failed: ${response.status}`);
        }

        const result = await response.json();

        showAIResult(result);

        alert("Your report has been analysed successfully.");

    } catch (error) {

        console.error("Analysis error:", error);

        alert(
            "Could not connect to the AI backend. Please try again."
        );

    }

});

let recorder;
let chunks = [];
let isRecording = false;

async function startRecording() {

    try {

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        chunks = [];

        recorder = new MediaRecorder(stream);

        recorder.ondataavailable = function(event) {

            if (event.data.size > 0) {
                chunks.push(event.data);
            }

        };

        recorder.onstop = sendAudio;

        recorder.start();

        isRecording = true;

        voiceButton.classList.add("recording");

        voiceText.textContent = "Stop recording";

        recordingStatus.textContent =
            "Listening... Speak your problem";

    } catch (error) {

        console.error("Microphone error:", error);

        alert(
            "Microphone permission is required for voice reporting."
        );

    }

}

function stopRecording() {

    if (recorder && recorder.state !== "inactive") {

        recorder.stop();

        isRecording = false;

        voiceButton.classList.remove("recording");

        voiceText.textContent = "Processing voice...";

        recordingStatus.textContent =
            "Sending audio to AI...";

    }

}

async function sendAudio() {

    const audioBlob = new Blob(chunks, {
        type: "audio/webm"
    });

    const formData = new FormData();

    formData.append(
        "audio",
        audioBlob,
        "complaint.webm"
    );

    try {

        const response = await fetch(
            `${API_URL}/api/voice-complaint`,
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {

            throw new Error(
                `Voice API request failed: ${response.status}`
            );

        }

        const result = await response.json();

        console.log("Voice response:", result);

        if (result.success) {

            document.getElementById("problem").value =
                result.text;

            document.getElementById("problem").dispatchEvent(
                new Event("input")
            );

            recordingStatus.textContent =
                "Voice converted to text ✓";

            voiceText.textContent =
                "Speak your problem";

        } else {

            recordingStatus.textContent =
                "Could not convert voice to text.";

            alert(
                result.message ||
                "Could not convert your voice to text."
            );

        }

    } catch (error) {

        console.error(
            "Voice upload error:",
            error
        );

        recordingStatus.textContent =
            "Backend connection failed.";

        alert(
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

function getLocation() {

    if (!navigator.geolocation) {

        alert(
            "Location is not supported by this browser."
        );

        return;
    }

    const button =
        document.getElementById("location-button");

    button.textContent =
        "Detecting location...";

    button.disabled = true;

    navigator.geolocation.getCurrentPosition(

        function(position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;

            document.getElementById("latitude").value =
                latitude;

            document.getElementById("longitude").value =
                longitude;

            document.getElementById("location").value =
                `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

            button.textContent =
                "Location detected ✓";

            button.disabled = false;

            console.log(
                "Latitude:",
                latitude
            );

            console.log(
                "Longitude:",
                longitude
            );

        },

        function(error) {

            console.log(
                "Location error:",
                error.message
            );

            button.textContent =
                "Use my current location";

            button.disabled = false;

            alert(
                "Unable to get your location. Please enter it manually."
            );

        }

    );

}
