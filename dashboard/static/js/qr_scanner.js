var qr_code = '';
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
                cameraContainer.style.display = 'block';
                videoElement.style.display = 'block';
                buttonContainer.style.display = 'block'; // Show button container
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
                alert('Failed to access camera. Please try again.');
            });
    } else {
        // cameraContainer.style.display = 'none';
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
            console.log(code )
            if (code) {
                canvasContext.strokeStyle = '#00FF00';
                canvasContext.lineWidth = 2;
                canvasContext.strokeRect(code.location.topLeftCorner.x, code.location.topLeftCorner.y, code.location.topRightCorner.x - code.location.topLeftCorner.x, code.location.bottomLeftCorner.y - code.location.topLeftCorner.y);

                clearInterval(intervalId);
                qr_code = code.data;

                document.getElementById('qr-result').innerText = code.data; // Display QR code data on the page
               
                // Send code.data to your Django backend
            sendDataToServer(qr_code ,true);
            handleOkButtonClick();
            
            }
        }, 1000);
    });
}

function sendDataToServer(data, shouldSendRequest = true) {

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
      return ('' ,  false)
    });
    
}


function openCameraContainer(itemId, asnNumber, modelDescription) {
    // Show the camera container
    document.getElementById('camera-container').style.display = 'block';

    // Set ASN Number text with color
    var asnElement = document.getElementById('asn');
    asnElement.innerText = 'Asn Number: ';
    var asnNumberSpan = document.createElement('span');
    asnNumberSpan.innerText = asnNumber;
    asnNumberSpan.style.color = 'green'; // Change color here
    asnElement.appendChild(asnNumberSpan);

    // Set Model Description text with color
    var modelElement = document.getElementById('model');
    modelElement.innerText = 'Model Description: ';
    var modelDescriptionSpan = document.createElement('span');
    modelDescriptionSpan.innerText = modelDescription;
    modelDescriptionSpan.style.color = 'green'; // Change color here
    modelElement.appendChild(modelDescriptionSpan);

    // Call the function to open the camera stream
    openCamera(itemId);
}


function handleOkButtonClick(){
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
     // Check if QR code data exists
     if (qrResultDiv.innerText.trim() === '') {
        alert('No QR code data found.');
        return;
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
     // Do not send the request when canceling
    sendDataToServer('', false);
}
