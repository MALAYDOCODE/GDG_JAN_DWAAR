
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

    const response = await fetch(
        "http://127.0.0.1:8000/api/analyse",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(reportData)
        }
    );

    const result = await response.json();

    showAIResult(result);

    alert(
        "Your report is ready to be connected with the AI backend."
    );

});
/* =========================================
   VOICE RECORDING
========================================= */

let recorder;
let chunks = [];
let isRecording = false;

async function startRecording() {

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        chunks = [];

        recorder =
            new MediaRecorder(stream);

        recorder.ondataavailable = function(event) {

            if (event.data.size > 0) {
                chunks.push(event.data);
            }

        };

        recorder.onstop = sendAudio;

        recorder.start();

        isRecording = true;

        voiceButton.classList.add("recording");

        voiceText.textContent =
            "Stop recording";

        recordingStatus.textContent =
            "Listening... Speak your problem";

    } catch (error) {

        console.error(error);

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

        voiceText.textContent =
            "Processing voice...";

        recordingStatus.textContent =
            "Sending audio to AI...";

    }

}


async function sendAudio() {

    const audioBlob =
        new Blob(chunks, {
            type: "audio/webm"
        });


    const formData =
        new FormData();


    formData.append(
        "audio",
        audioBlob,
        "complaint.webm"
    );


    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/api/voice-complaint",
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!response.ok) {

            throw new Error(
                "Voice API request failed"
            );

        }


        const result =
            await response.json();


        console.log("Voice response:", result);


        if (result.success) {

            document.getElementById(
                "problem"
            ).value = result.text;


            document.getElementById(
                "problem"
            ).dispatchEvent(
                new Event("input")
            );


            recordingStatus.textContent =
                "Voice converted to text ✓";

            voiceText.textContent =
                "Speak your problem";

        } else {

            recordingStatus.textContent =
                "Could not convert voice to text.";

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


/* =========================================
   VOICE BUTTON
========================================= */

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
        alert("Location is not supported by this browser.");
        return;
    }

    const button = document.getElementById("location-button");

    button.textContent = "Detecting location...";
    button.disabled = true;

    navigator.geolocation.getCurrentPosition(

        function(position) {

            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;

            // Store coordinates
            document.getElementById("latitude").value = latitude;
            document.getElementById("longitude").value = longitude;

            // SHOW coordinates in location input
            document.getElementById("location").value =
                `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

            button.textContent = "Location detected ✓";
            button.disabled = false;

            console.log("Latitude:", latitude);
            console.log("Longitude:", longitude);
        },

        function(error) {

            console.log("Location error:", error.message);

            button.textContent = "Use my current location";
            button.disabled = false;

            alert("Unable to get your location. Please enter it manually.");
        }
    );
}