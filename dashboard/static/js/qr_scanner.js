var qr_code = '';

function openCameraContainer(itemId, asnNumber, modelDescription) {
    const videoElement = document.getElementById('camera-stream');
    const cameraContainer = document.getElementById('camera-container');
    const buttonContainer = document.getElementById('button-container');
    const btnOk = document.getElementById('btn-ok');
    const btnCancel = document.getElementById('btn-cancel');
    const qrResultDiv = document.getElementById('qr-result');
    const manualQrCodeInput = document.getElementById('manual-qr-input');
    const btnSubmit = document.getElementById('btn-submit');

    // Clear QR result div when opening camera for a new row
    qrResultDiv.innerText = '';

    // Set ASN Number and Model Description
    var asnElement = document.getElementById('asn');
    asnElement.innerText = 'Asn Number: ' + asnNumber;
    asnElement.style.color = 'green';

    var modelElement = document.getElementById('model');
    modelElement.innerText = 'Model Description: ' + modelDescription;
    modelElement.style.color = 'green';

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                videoElement.srcObject = stream;
                cameraContainer.style.display = 'block';
                videoElement.style.display = 'block';
                buttonContainer.style.display = 'block';
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
                alert('Failed to access camera. Please try again.');
            });
    } else {
        alert('Your browser does not support accessing the camera.');
    }

    // Remove existing event listeners before adding new ones
    btnOk.removeEventListener('click', handleOkButtonClick);
    btnOk.addEventListener('click', function() {
        handleOkButtonClick(itemId);
    });

    btnCancel.removeEventListener('click', handleCancelButtonClick);
    btnCancel.addEventListener('click', handleCancelButtonClick);

    // btnSubmit.removeEventListener('click', handleSubmit);
    // btnSubmit.addEventListener('click', function() {
    //     handleSubmit(manualQrCodeInput.value);
    // });

    

    videoElement.addEventListener('canplay', function() {
        const canvasElement = document.getElementById('canvas');
        const canvasContext = canvasElement.getContext('2d');
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        const intervalId = setInterval(function() {
            canvasContext.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            const imageData = canvasContext.getImageData(0, 0, canvasElement.width, canvasElement.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            console.log(code)
            if (code) {
                canvasContext.strokeStyle = '#00FF00';
                canvasContext.lineWidth = 2;
                canvasContext.strokeRect(code.location.topLeftCorner.x, code.location.topLeftCorner.y, code.location.topRightCorner.x - code.location.topLeftCorner.x, code.location.bottomLeftCorner.y - code.location.topLeftCorner.y);

                clearInterval(intervalId);
                qr_code = code.data;

                qrResultDiv.innerText = code.data; // Display QR code data on the page
                sendDataToServer(qr_code);
                handleOkButtonClick();
            }
        }, 1000);
    });
}

function handleSubmit(manualQrCode) {
    if (manualQrCode && manualQrCode.trim() !== '') {
        qr_code = manualQrCode.trim();
        const qrResultDiv = document.getElementById('qr-result');
        qrResultDiv.innerText = qr_code; // Display QR code data on the page
        sendDataToServer(qr_code);
        handleOkButtonClick();
        // Clear the input field
        const manualQrCodeInput = document.getElementById('manual-qr-input');
        manualQrCodeInput.value = '';
    } else {
        alert('Please enter a valid QR code.');
    }
}

function sendDataToServer(data) {
    const xhr = $.ajax({
        url: '/getPayloadData/',  // URL to your Django view
        type: 'POST',
        data: {
            qr_data: data
        },
        success: function(response) {
            console.log('Server response:', response);
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
        }
    });
    console.log('Data:', data);
    const btnCancel = document.getElementById('btn-cancel');
    btnCancel.addEventListener('click', function() {
        xhr.abort(); // Abort the request on cancel button click
        console.log('AJAX request aborted.');
    });
}

function handleOkButtonClick() {
    const videoElement = document.getElementById('camera-stream');
    const row_info = document.getElementById('camera-container');
    const qrResultDiv = document.getElementById('qr-result');

    // Hide button container
    document.getElementById('button-container').style.display = 'none';

    // Stop video stream
    const streamTracks = videoElement.srcObject.getTracks();
    streamTracks.forEach(track => track.stop());
    row_info.style.display = 'none';

    // Remove video element from display
    videoElement.style.display = 'none';
    row_info.style.display = 'none';
    manual_qr =document.getElementById('manual-qr-input').value

    // Check if QR code data exists
    if (qrResultDiv.innerText.trim() === '' && manual_qr.trim() === '') {
        alert('No QR code data found.');
        return;
    }
}

function handleCancelButtonClick() {
    const videoElement = document.getElementById('camera-stream');
    const streamTracks = videoElement.srcObject.getTracks();
    streamTracks.forEach(track => track.stop());

    // Hide camera container and buttons
    document.getElementById('camera-container').style.display = 'none';
    document.getElementById('button-container').style.display = 'none';
    document.getElementById('camera-stream').style.display = 'none';
}
