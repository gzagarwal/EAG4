const layers = [];

async function setInputDimensions() {
  const height = parseInt(document.getElementById('inputHeight').value, 10);
  const width = parseInt(document.getElementById('inputWidth').value, 10);
  const channels = parseInt(document.getElementById('inputChannels').value, 10);

  if (!(height >= 1 && width >= 1 && channels >= 1 && channels <= 4)) {
    alert('Please enter valid dimensions: height/width >= 1, channels 1-4');
    return;
  }

  try {
    const response = await fetch('/api/set_input_dimensions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        height: height,
        width: width,
        channels: channels
      })
    });

    if (response.ok) {
      const result = await response.json();
      updateDisplay(result);
    } else {
      const error = await response.json();
      alert('Error: ' + error.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to set dimensions');
  }
}

async function uploadImage() {
  const fileInput = document.getElementById('imageUpload');
  const file = fileInput.files[0];
  
  if (!file) {
    alert('Please select an image file');
    return;
  }

  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch('/api/upload_image', {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      const result = await response.json();
      
      // Update the dimension inputs with the detected values
      document.getElementById('inputHeight').value = result.dimensions.height;
      document.getElementById('inputWidth').value = result.dimensions.width;
      document.getElementById('inputChannels').value = result.dimensions.channels;
      
      // Update display with the calculator state
      updateDisplay(result.calculator_state);
      
      alert(`Image uploaded successfully! Detected dimensions: ${result.dimensions.height}×${result.dimensions.width}×${result.dimensions.channels}`);
    } else {
      const error = await response.json();
      alert('Error: ' + error.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to upload image');
  }
}

async function addLayer() {
  const type = document.getElementById('layerType').value;
  const kernel = parseInt(document.getElementById('kernel').value, 10);
  const stride = parseInt(document.getElementById('stride').value, 10);
  const padding = parseInt(document.getElementById('padding').value, 10);
  const dilation = parseInt(document.getElementById('dilation').value, 10);

  if (!(kernel >= 1 && stride >= 1 && padding >= 0 && dilation >= 1)) {
    alert('Please enter valid positive integers.');
    return;
  }

  try {
    const response = await fetch('/api/add_layer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: type,
        kernel_size: kernel,
        stride: stride,
        padding: padding,
        dilation: dilation
      })
    });

    if (response.ok) {
      const result = await response.json();
      updateDisplay(result);
    } else {
      const error = await response.json();
      alert('Error: ' + error.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to add layer');
  }
}

async function resetLayers() {
  try {
    const response = await fetch('/api/reset', {
      method: 'POST'
    });
    
    if (response.ok) {
      layers.length = 0;
      updateDisplay({
        layers: [],
        current_rf: 1,
        current_jump: 1,
        current_start: 0.5
      });
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

function updateDisplay(data) {
  // Update stats
  document.getElementById('currentRf').textContent = data.current_rf;
  document.getElementById('currentJump').textContent = data.current_jump;
  document.getElementById('currentStart').textContent = data.current_start;
  document.getElementById('layerCount').textContent = data.layers.length;
  document.getElementById('rfOut').textContent = data.current_rf;

  // Update dimension displays
  if (data.input_dimensions) {
    document.getElementById('inputDimensions').textContent = 
      `${data.input_dimensions.height}×${data.input_dimensions.width}×${data.input_dimensions.channels}`;
  }
  
  if (data.final_dimensions) {
    document.getElementById('finalDimensions').textContent = 
      `${data.final_dimensions.height}×${data.final_dimensions.width}×${data.final_dimensions.channels}`;
  }

  // Update table
  const tbody = document.getElementById('layersTable');
  tbody.innerHTML = data.layers.map((layer, idx) => `
    <tr>
      <td>${idx + 1}</td>
      <td>${layer.name}</td>
      <td>${layer.kernel_size}</td>
      <td>${layer.stride}</td>
      <td>${layer.padding}</td>
      <td>${layer.dilation}</td>
      <td>${layer.effective_kernel}</td>
      <td>${layer.receptive_field}</td>
      <td>${layer.jump}</td>
      <td>${layer.start}</td>
      <td>${layer.input_height}×${layer.input_width}×${layer.input_channels}</td>
      <td>${layer.output_height}×${layer.output_width}×${layer.output_channels}</td>
    </tr>
  `).join('');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('addBtn').addEventListener('click', addLayer);
  document.getElementById('resetBtn').addEventListener('click', resetLayers);
  document.getElementById('setDimensionsBtn').addEventListener('click', setInputDimensions);
  document.getElementById('uploadBtn').addEventListener('click', uploadImage);

  // Initialize display
  updateDisplay({
    layers: [],
    current_rf: 1,
    current_jump: 1,
    current_start: 0.5,
    input_dimensions: { height: 224, width: 224, channels: 3 },
    final_dimensions: { height: 224, width: 224, channels: 3 }
  });
});
