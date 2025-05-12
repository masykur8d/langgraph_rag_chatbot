audio_and_lenght_recording_utils = """
<script>
let mediaRecorder;
let mediaStream;
let chunks = [];

// Detect iOS Safari
const isIOSSafari = /iP(ad|hone|od)/.test(navigator.userAgent)
                 && /Safari/.test(navigator.userAgent)
                 && !/Chrome/.test(navigator.userAgent);

let mimeType = 'audio/webm';
if (isIOSSafari) {
    mimeType = 'audio/mp4';
}

async function startRecording() {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    let options = { mimeType };
    if (!MediaRecorder.isTypeSupported(mimeType)) {
        console.warn(`MimeType ${mimeType} not supported. Falling back to default.`);
        options = undefined; // Let browser pick
    }

    mediaRecorder = new MediaRecorder(mediaStream, options);
    chunks = [];

    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: mimeType });
        const base64 = await blobToBase64(blob);
        const duration = await getAudioDuration(blob);

        // Include the mimeType so Python knows how to decode
        emitEvent('audio_data', { audio: base64, duration, mimeType });
        console.log(`Audio data emitted. Duration: ${duration}, MIME: ${mimeType}`);
    };

    mediaRecorder.start();
    console.log(`Recording started with mimeType: ${mimeType}`);
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
        }
    }
}

async function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

async function getAudioDuration(blob) {
    return new Promise((resolve, reject) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const reader = new FileReader();
        reader.onloadend = () => {
            audioContext.decodeAudioData(reader.result, (audioBuffer) => {
                resolve(audioBuffer.duration);
            }, reject);
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(blob);
    });
}
</script>
"""