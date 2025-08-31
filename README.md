# Advanced Receptive Field Calculator with AI Assistant

What this is
- A Flask app where you can add Conv2D, MaxPool2D, or AvgPool2D layers and see how they affect the receptive field and output dimensions.
- Supports custom input image dimensions (height, width, channels) or automatic detection via image upload.
- **NEW**: Includes an AI assistant powered by Google Gemini for answering questions about neural networks and more!
- Uses the standard 1D receptive field recurrence per spatial dimension with dilation and padding:
  - k_eff = (k - 1) * d + 1
  - rf' = rf + (k_eff - 1) * jump
  - jump' = jump * stride
  - start' = start + ((k_eff - 1)/2 - padding) * jump
- Tracks how each layer transforms the input dimensions (H×W×C) throughout the network.

Files
- `class_code/app.py` – Flask server with receptive field calculator and AI chatbot
- `class_code/templates/index.html` – Web interface
- `class_code/static/css/style.css` – Styling
- `class_code/static/js/app.js` – Frontend JavaScript
- `class_code/pyproject.toml` – Dependencies

Dependencies
- Flask (web framework)
- OpenCV (image processing)
- NumPy (numerical operations)
- Werkzeug (file handling)
- Google Generative AI (Gemini chatbot)

Setup

1. Install dependencies:
```bash
uv sync
```

2. Set up Gemini AI (optional but recommended):
   - Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Set the environment variable:
   ```bash
   # Windows
   set GEMINI_API_KEY=your_api_key_here
   
   # Linux/Mac
   export GEMINI_API_KEY=your_api_key_here
   ```

3. Run the application:
```bash
uv run app.py
```

4. Open your browser to `http://localhost:5000`

How to use
- Set input image dimensions manually or upload an image for automatic detection
- Pick a layer type (Conv2D, MaxPool2D, or AvgPool2D)
- Enter kernel size, stride, padding (per side), and dilation
- Click "Add Layer" to append it to the table
- The table shows how each layer transforms input dimensions (H×W×C) and affects the receptive field
- The "Current RF" pill shows the latest receptive field size
- **NEW**: Use the AI Assistant to ask questions about neural networks, receptive fields, or any other topic!
- Click "Reset" to clear the stack and reset to default dimensions

AI Assistant Features
- Ask questions about neural network concepts
- Get explanations about receptive field calculations
- Discuss layer parameters and their effects
- General AI/ML questions and explanations
- Any other questions you might have!

Note: The AI assistant requires a Gemini API key. Without it, the calculator will still work perfectly for receptive field calculations.



