function openCamera(itemId ) {
    const videoElement = document.getElementById('camera-stream');
    const cameraContainer = document.getElementById('camera-container');
    const buttonContainer = document.getElementById('button-container');
    const btnOk = document.getElementById('btn-ok');
    const btnCancel = document.getElementById('btn-cancel');
    const qrResultDiv = document.getElementById('qr-result'); // Get QR result div
    const trolleyCellId = 'trolley-' + itemId;
    
    // Clear QR result div when opening camera for a new row
    qrResultDiv.innerText = '';

     // Update camera container to display ASN and model description
     
   
    // Show camera container
   
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                videoElement.srcObject = stream;
                cameraContainer.style.display = 'flex';
                videoElement.style.display = 'block';
                buttonContainer.style.display = 'block'; // Show button container
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
                alert('Failed to access camera. Please try again.');
            });
    } else {
        alert('Your browser does not support accessing the camera.');
    }

    btnOk.addEventListener('click', function() {
        handleOkButtonClick(itemId);
    });

    btnCancel.addEventListener('click', function() {
        handleCancelButtonClick();
    });

    videoElement.addEventListener('canplay', function() {
        const canvasElement = document.getElementById('canvas');
        const canvasContext = canvasElement.getContext('2d');
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        const intervalId = setInterval(function() {
            canvasContext.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            const imageData = canvasContext.getImageData(0, 0, canvasElement.width, canvasElement.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);

            if (code) {
                canvasContext.strokeStyle = '#00FF00';
                canvasContext.lineWidth = 2;
                canvasContext.strokeRect(code.location.topLeftCorner.x, code.location.topLeftCorner.y, code.location.topRightCorner.x - code.location.topLeftCorner.x, code.location.bottomLeftCorner.y - code.location.topLeftCorner.y);

                clearInterval(intervalId);

                document.getElementById('qr-result').innerText = code.data; // Display QR code data on the page
                // Display QR code data in the table
    document.getElementById(trolleyCellId).innerHTML = code.data;
    console.log(itemId, "item id catched");
                
            }
        }, 1000);
    });
}
function sendDataToServer(qrData , itemId) {
    // Make an AJAX request to your Django backend
    $.ajax({
        url: '/getPayloadData/',
        type: 'POST',
        data: {
            qr_data: qrData,
            id: itemId
        },
        success: function(response) {
            // Handle successful response from the server
            console.log('Server response:', response);
        },
        error: function(xhr, status, error) {
            // Handle error
            console.error('Error:', error);
        }
    });
}
// Function to retrieve CSRF token from cookies
function getCookie(name) {
    const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return cookieValue ? cookieValue.pop() : '';
}

function openCameraContainer(itemId , asnNumber , modelDescription) {
    // Show the camera container
    document.getElementById('camera-container').style.display = 'block';
    document.getElementById('asn').innerText = 'Asn Number:'+ asnNumber ; 
    document.getElementById('model').innerText = 'model decription:'+ modelDescription ; 
    
    // Call the function to open the camera stream
    openCamera(itemId);
}

function handleOkButtonClick( itemId ){
    const qrResult = document.getElementById('qr-result').innerText;
    if (qrResult) {
        // QR code detected, post data
        sendDataToServer(qrResult, itemId);
    } else {
        alert('No QR code detected. Please try again.');
    }
}

function handleCancelButtonClick() {
    // Handle Cancel button click
    const videoElement = document.getElementById('camera-stream');
    const canvasElement = document.getElementById('canvas');
    const cameraContainer = document.getElementById('camera-container');

    // Stop video stream
    const streamTracks = videoElement.srcObject.getTracks();
    streamTracks.forEach(track => track.stop());

    // Clear canvas and hide button container
    canvasElement.getContext('2d').clearRect(0, 0, canvasElement.width, canvasElement.height);
    document.getElementById('button-container').style.display = 'none';

    // Clear QR result
    document.getElementById('qr-result').innerText = '';
     // Remove video element from display
     videoElement.style.display = 'none';
     cameraContainer.style.display = 'none';
}
