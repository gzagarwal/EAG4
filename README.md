Receptive Field Calculator (Flask)

What this is
- A Flask app where you can add Conv2D, MaxPool2D, or AvgPool2D layers and see how they affect the receptive field and output dimensions.
- Supports custom input image dimensions (height, width, channels) or automatic detection via image upload.
- Uses the standard 1D receptive field recurrence per spatial dimension with dilation and padding:
  - k_eff = (k - 1) * d + 1
  - rf' = rf + (k_eff - 1) * jump
  - jump' = jump * stride
  - start' = start + ((k_eff - 1)/2 - padding) * jump
- Tracks how each layer transforms the input dimensions (H×W×C) throughout the network.

Files
- `class_code/app.py` – Flask server with Python classes
- `class_code/templates/index.html` – HTML template
- `class_code/static/css/style.css` – CSS styles
- `class_code/static/js/app.js` – JavaScript functionality

Prerequisites
- You already have `uv` installed (fast Python package manager)
- Python 3.13 (as set in `pyproject.toml`)

Install dependencies (first time)
```powershell
uv sync
```

Run the app (Windows PowerShell)
- Option 1 (run the Flask CLI):
```powershell
uv run python -m flask --app class_code.app run --host 0.0.0.0 --port 5000
```

- Option 2 (run the script directly):
```powershell
uv run python class_code/app.py
```

Open in your browser
```text
http://localhost:5000
```

How to use
- Set input image dimensions manually or upload an image for automatic detection
- Pick a layer type (Conv2D, MaxPool2D, or AvgPool2D)
- Enter kernel size, stride, padding (per side), and dilation
- Click "Add Layer" to append it to the table
- The table shows how each layer transforms input dimensions (H×W×C) and affects the receptive field
- The "Current RF" pill shows the latest receptive field size
- Click "Reset" to clear the stack and reset to default dimensions



