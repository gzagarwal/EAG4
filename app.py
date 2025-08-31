from flask import Flask, render_template, request, jsonify
from typing import List, Dict, Any
import math
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import google.generativeai as genai
# from config import GEMINI_API_KEY  # Import from config file


class Layer:
    """Base class for neural network layers"""

    def __init__(
        self,
        name: str,
        kernel_size: int,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
    ):
        self.name = name
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation

    def get_effective_kernel_size(self) -> int:
        """Calculate effective kernel size considering dilation"""
        return (self.kernel_size - 1) * self.dilation + 1

    def compute_output_size(self, input_size: int) -> int:
        """Compute output size for a given input size"""
        effective_kernel = self.get_effective_kernel_size()
        return (
            math.floor((input_size + 2 * self.padding - effective_kernel) / self.stride)
            + 1
        )


class Conv2DLayer(Layer):
    """Convolutional layer"""

    def __init__(
        self,
        kernel_size: int,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
        groups: int = 1,
    ):
        super().__init__("Conv2D", kernel_size, stride, padding, dilation)
        self.groups = groups

    def __str__(self):
        return f"Conv2D(k={self.kernel_size}, s={self.stride}, p={self.padding}, d={self.dilation})"


class PoolingLayer(Layer):
    """Pooling layer base class"""

    def __init__(
        self, pool_type: str, kernel_size: int, stride: int = 1, padding: int = 0
    ):
        super().__init__(
            pool_type, kernel_size, stride, padding, 1
        )  # Dilation is always 1 for pooling
        self.pool_type = pool_type

    def __str__(self):
        return (
            f"{self.pool_type}(k={self.kernel_size}, s={self.stride}, p={self.padding})"
        )


class MaxPool2DLayer(PoolingLayer):
    """MaxPooling layer"""

    def __init__(self, kernel_size: int, stride: int = 1, padding: int = 0):
        super().__init__("MaxPool2D", kernel_size, stride, padding)


class AvgPool2DLayer(PoolingLayer):
    """Average pooling layer"""

    def __init__(self, kernel_size: int, stride: int = 1, padding: int = 0):
        super().__init__("AvgPool2D", kernel_size, stride, padding)


class ReceptiveFieldCalculator:
    """Calculate receptive field for a sequence of layers"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the calculator state"""
        self.rf = 1  # receptive field size
        self.jump = 1  # jump (effective stride)
        self.start = 0.5  # center of first receptive field
        self.layers: List[Layer] = []
        self.input_height = 224
        self.input_width = 224
        self.input_channels = 3

    def set_input_dimensions(self, height: int, width: int, channels: int = 3):
        """Set input image dimensions"""
        self.input_height = height
        self.input_width = width
        self.input_channels = channels

    def add_layer(self, layer: Layer) -> Dict[str, Any]:
        """Add a layer and compute new receptive field"""
        self.layers.append(layer)
        return self.compute_current_state()

    def compute_current_state(self) -> Dict[str, Any]:
        """Compute current receptive field state"""
        rf = 1
        j = 1
        start = 0.5
        results = []

        current_height = self.input_height
        current_width = self.input_width
        current_channels = self.input_channels

        for layer in self.layers:
            k_eff = layer.get_effective_kernel_size()
            p = layer.padding
            s = layer.stride

            rf_next = rf + (k_eff - 1) * j
            start_next = start + ((k_eff - 1) / 2 - p) * j
            j_next = j * s

            # Compute output dimensions
            output_height = layer.compute_output_size(current_height)
            output_width = layer.compute_output_size(current_width)

            # For pooling layers, channels remain the same
            # For conv layers, we'll assume output channels (simplified)
            if isinstance(layer, Conv2DLayer):
                output_channels = (
                    current_channels  # Simplified - in reality this depends on filters
                )
            else:
                output_channels = current_channels

            results.append(
                {
                    "name": layer.name,
                    "kernel_size": layer.kernel_size,
                    "stride": layer.stride,
                    "padding": layer.padding,
                    "dilation": layer.dilation,
                    "effective_kernel": k_eff,
                    "receptive_field": rf_next,
                    "jump": j_next,
                    "start": round(start_next, 3),
                    "input_height": current_height,
                    "input_width": current_width,
                    "input_channels": current_channels,
                    "output_height": output_height,
                    "output_width": output_width,
                    "output_channels": output_channels,
                }
            )

            rf = rf_next
            start = start_next
            j = j_next

            # Update current dimensions for next layer
            current_height = output_height
            current_width = output_width
            current_channels = output_channels

        return {
            "layers": results,
            "current_rf": rf,
            "current_jump": j,
            "current_start": round(start, 3),
            "input_dimensions": {
                "height": self.input_height,
                "width": self.input_width,
                "channels": self.input_channels,
            },
            "final_dimensions": {
                "height": current_height,
                "width": current_width,
                "channels": current_channels,
            },
        }

    def get_layer_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all layers"""
        return self.compute_current_state()["layers"]


class GeminiChatbot:
    """Gemini AI chatbot for answering questions"""

    def __init__(self, api_key: str = None):
        self.api_key = "AIzaSyDeBDiXgPfSO0BtI9U1zlu9-FJc_GqJOTY"

        if self.api_key:
            try:
                print(f"Configuring Gemini with API key: {self.api_key[:10]}...")
                genai.configure(api_key=self.api_key)

                # Debug: List available models
                try:
                    print("Attempting to list available models...")
                    models = genai.list_models()
                    print("Available models:")
                    for model in models:
                        print(f"  - {model.name}")
                except Exception as e:
                    print(f"Could not list models: {e}")
                    print(f"Error type: {type(e)}")
                    print(f"Error details: {str(e)}")

                # Try the simplest models first - these usually have better free tier quotas
                try:
                    print("Trying gemini-1.0-pro (simplest model)...")
                    self.model = genai.GenerativeModel("gemini-2.0-flash")
                    print("Successfully initialized gemini-1.0-pro")
                except Exception as e:
                    print(f"Failed to initialize gemini-1.0-pro: {e}")
                    try:
                        print("Trying gemini-pro (fallback)...")
                        self.model = genai.GenerativeModel("gemini-pro")
                        print("Successfully initialized gemini-pro")
                    except Exception as e:
                        print(f"Failed to initialize gemini-pro: {e}")
                        try:
                            print("Trying gemini-1.5-pro (last resort)...")
                            self.model = genai.GenerativeModel("gemini-1.5-pro")
                            print("Successfully initialized gemini-1.5-pro")
                        except Exception as e:
                            print(f"Failed to initialize gemini-1.5-pro: {e}")
                            self.model = None

            except Exception as e:
                print(f"Error initializing Gemini: {e}")
                self.model = None
        else:
            self.model = None

    def chat(self, message: str) -> Dict[str, Any]:
        """Send a message to Gemini and get response"""
        if not self.model:
            return {
                "error": "Gemini API key not configured or model initialization failed. Please check your API key and try again.",
                "success": False,
            }

        try:
            # Simplified context for the simplest model
            context = """
            You are a helpful AI assistant. You can answer questions about:
            - Neural networks and CNNs
            - Receptive field calculations
            - General AI/ML concepts
            - Any other questions users might have
            
            Keep responses clear and concise.
            """

            full_prompt = f"{context}\n\nUser question: {message}"

            # Simple generate_content call without complex safety settings
            response = self.model.generate_content(full_prompt)

            return {"response": response.text, "success": True}

        except Exception as e:
            error_msg = str(e)
            print(f"Gemini API error: {error_msg}")

            # Handle quota errors more gracefully
            if "quota" in error_msg.lower() or "429" in error_msg:
                return {
                    "error": "Free tier quota reached. Please wait 1-2 minutes and try again. The free tier allows 15 requests per day.",
                    "success": False,
                }
            elif "404" in error_msg and "models" in error_msg:
                return {
                    "error": "Model not found. Please check your API key.",
                    "success": False,
                }
            elif "403" in error_msg:
                return {
                    "error": "Access denied. Please check your API key permissions.",
                    "success": False,
                }
            else:
                return {
                    "error": f"API error: {error_msg}",
                    "success": False,
                }

    def test_api_key(self) -> Dict[str, Any]:
        """Test if the API key is working"""
        if not self.model:
            return {"error": "Model not initialized", "success": False}

        try:
            # Very simple test prompt
            response = self.model.generate_content("Say 'Hello'")
            return {"response": response.text, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}


class FlaskApp:
    """Main Flask application class"""

    def __init__(self):
        self.app = Flask(__name__)
        self.app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
        self.app.config["UPLOAD_FOLDER"] = "uploads"
        self.calculator = ReceptiveFieldCalculator()

        # Option 3: Pass API key when creating the chatbot
        self.chatbot = GeminiChatbot()  # Will use the key from config

        self.setup_routes()

        # Create uploads directory if it doesn't exist
        os.makedirs(self.app.config["UPLOAD_FOLDER"], exist_ok=True)

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/api/set_input_dimensions", methods=["POST"])
        def set_input_dimensions():
            """Set input image dimensions"""
            try:
                data = request.get_json()
                height = int(data.get("height", 224))
                width = int(data.get("width", 224))
                channels = int(data.get("channels", 3))

                if height <= 0 or width <= 0 or channels <= 0:
                    return jsonify(
                        {"error": "Dimensions must be positive integers"}
                    ), 400

                self.calculator.set_input_dimensions(height, width, channels)
                result = self.calculator.compute_current_state()
                return jsonify(result)

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route("/api/upload_image", methods=["POST"])
        def upload_image():
            """Upload and analyze image"""
            try:
                if "image" not in request.files:
                    return jsonify({"error": "No image file provided"}), 400

                file = request.files["image"]
                if file.filename == "":
                    return jsonify({"error": "No file selected"}), 400

                if file:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(self.app.config["UPLOAD_FOLDER"], filename)
                    file.save(filepath)

                    # Read image and get dimensions
                    img = cv2.imread(filepath)
                    if img is None:
                        return jsonify({"error": "Could not read image file"}), 400

                    height, width = img.shape[:2]
                    channels = img.shape[2] if len(img.shape) > 2 else 1

                    # Clean up uploaded file
                    os.remove(filepath)

                    # Set dimensions in calculator
                    self.calculator.set_input_dimensions(height, width, channels)
                    result = self.calculator.compute_current_state()

                    return jsonify(
                        {
                            "message": "Image uploaded successfully",
                            "dimensions": {
                                "height": height,
                                "width": width,
                                "channels": channels,
                            },
                            "calculator_state": result,
                        }
                    )

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route("/api/add_layer", methods=["POST"])
        def add_layer():
            """Add a new layer via API"""
            try:
                data = request.get_json()
                layer_type = data.get("type", "conv")
                kernel_size = int(data.get("kernel_size", 3))
                stride = int(data.get("stride", 1))
                padding = int(data.get("padding", 0))
                dilation = int(data.get("dilation", 1))

                if layer_type == "conv":
                    layer = Conv2DLayer(kernel_size, stride, padding, dilation)
                elif layer_type == "maxpool":
                    layer = MaxPool2DLayer(kernel_size, stride, padding)
                elif layer_type == "avgpool":
                    layer = AvgPool2DLayer(kernel_size, stride, padding)
                else:
                    return jsonify({"error": "Invalid layer type"}), 400

                result = self.calculator.add_layer(layer)
                return jsonify(result)

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route("/api/reset", methods=["POST"])
        def reset():
            """Reset the calculator"""
            self.calculator.reset()
            return jsonify({"message": "Reset successful"})

        @self.app.route("/api/current_state", methods=["GET"])
        def current_state():
            """Get current calculator state"""
            return jsonify(self.calculator.compute_current_state())

        @self.app.route("/api/chat", methods=["POST"])
        def chat():
            """Chat with Gemini AI"""
            try:
                data = request.get_json()
                message = data.get("message", "").strip()

                if not message:
                    return jsonify({"error": "Message cannot be empty"}), 400

                response = self.chatbot.chat(message)
                return jsonify(response)

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route("/api/test_gemini", methods=["GET"])
        def test_gemini():
            """Test Gemini API connection"""
            try:
                result = self.chatbot.test_api_key()
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

    def run(self, host="0.0.0.0", port=5000, debug=True):
        """Run the Flask application"""
        self.app.run(host=host, port=port, debug=debug)


# Create and run the application
if __name__ == "__main__":
    app_instance = FlaskApp()
    app_instance.run()
