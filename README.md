# 

This project uses a Raspberry Pi, a camera, and a TensorFlow Lite model to perform real-time object detection for drone obstacle avoidance. The script detects objects, estimates their proximity, and sends `DISTANCE_SENSOR` messages to a Pixhawk flight controller (running ArduPilot) via MAVLink to trigger its built-in avoidance routines.

---

## Team Details

**Team Name:** SKYAID 

**Team Leader:** [@AaryaRatnam](https://github.com/AaryaRatnam)

**Team Members:**

- **Arya Ratnam** - 2023UME4179 - [@USERNAME](https://github.com/AaryaRatnam)
- **Vivek Goswami** - 2023UEE4605- [@USERNAME](https://github.com/VivianakaVivek)
- **Aditya Bhandari** - 2023UEE4635 - [@USERNAME](https://github.com/aditya4635)
- **Rudra Pratap Jha** - 2023UME4158 - [@USERNAME](https://github.com/Ay-2027)
- **Ayush Kumar** - 2023UME4207 - [@USERNAME](https://github.com/rpj33)
- **Pankhuri kanda** - 2023UME4212 - [@USERNAME](https://github.com/pankhuri1806)

## Project Links

- **SIH Presentation:** [Final SIH Presentation](URL TO PPT UPLOADED TO GITHUB)
- **Video Demonstration:** [Watch Video](UNLISTED YOUTUBE LINK)
- **Live Deployment:** [View Deployment](DEPLOYED LINK IF ANY)
- **Source Code:** [GitHub Repository](GITHUB LINK TO THE REPO)
- **Additional Resources:** [Other Relevant Links](ANY OTHER RELEVANT LINKS)

---

## 📋 Features

-   **MAVLink Integration**: Connects to a Pixhawk flight controller using `pymavlink` over a serial connection.
-   **Real-time Object Detection**: Uses OpenCV to capture video and a TFLite model to detect obstacles in real-time.
-   **Proximity Estimation**: A simple but effective method estimates obstacle distance based on the size of its bounding box in the camera's view.
-   **MAVLink Messaging**: Sends standardized `DISTANCE_SENSOR` messages, making it compatible with ArduPilot's proximity avoidance features.
-   **Lightweight**: Designed to run on resource-constrained hardware like a Raspberry Pi by using the `tflite-runtime`.

---

## 🛠️ Hardware Requirements

-   **Raspberry Pi**: A Raspberry Pi 4 or newer is recommended for better performance.
-   **Pixhawk Flight Controller**: Any Pixhawk or compatible flight controller running **ArduPilot** firmware (Copter, Rover, or Plane).
-   **Camera**: A Raspberry Pi Camera or a standard USB webcam compatible with OpenCV.
-   **Connection**: A physical UART (serial) connection between the Raspberry Pi's GPIO pins and one of the Pixhawk's TELEM ports.

---

## ⚙️ Setup and Installation

### 1. Hardware Connection

Connect the Raspberry Pi to the Pixhawk's telemetry port (e.g., TELEM2).

-   **Pixhawk Pin** `GND` ↔ **Raspberry Pi Pin** `GND`
-   **Pixhawk Pin** `TX (Transmit)` ↔ **Raspberry Pi Pin** `RX (Receive)`
-   **Pixhawk Pin** `RX (Receive)` ↔ **Raspberry Pi Pin** `TX (Transmit)`

**Important**: Enable the serial port on your Raspberry Pi by running `sudo raspi-config`, going to `Interface Options` -> `Serial Port`, disabling the login shell, and enabling the serial hardware. The default port is typically `/dev/serial0`.

### 2. ArduPilot Configuration

You **must** configure the ArduPilot firmware using a ground control station (e.g., Mission Planner, QGroundControl) to accept the `DISTANCE_SENSOR` messages.

Set the following parameters:

-   **Serial Port Protocol**: Set the protocol for the telemetry port you connected to the Raspberry Pi. For example, if using TELEM2:
    -   `SERIAL2_PROTOCOL = 2` (for MAVLink 2)
    -   `SERIAL2_BAUD = 921` (for 921600 baud rate)
-   **Proximity Sensor Type**: Tell ArduPilot to listen for MAVLink distance messages.
    -   `PRX_TYPE = 2` (MAVLink)
-   **Avoidance Enable**: Enable the obstacle avoidance behavior.
    -   `AVOID_ENABLE = 2` (or `3`). Use `BendyRuler` or `Dijkstra` for best results.

### 3. Software Installation

**Clone or download this repository and navigate into the directory.**

1.  **Install Python dependencies:**
    It's recommended to use a virtual environment.

    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip libatlas-base-dev
    pip3 install opencv-python numpy pymavlink tflite-runtime
    ```

2.  **Place Your Model Files:**
    Make sure your TensorFlow Lite model and labels file are in the same directory as the script:
    -   `model.tflite`
    -   `labels.txt`

---

## 🚀 How It Works

The script operates in a continuous loop:

1.  **Initialization**: It first establishes a connection with the Pixhawk, waits for a heartbeat, and then loads the TFLite model and initializes the camera.
2.  **Capture and Preprocess**: In each loop, it captures a frame from the camera, converts its color space from BGR to RGB, and resizes it to match the input dimensions required by the TFLite model.
3.  **Inference**: The preprocessed image is fed into the TFLite interpreter to perform object detection, which returns a list of potential objects, their bounding boxes, and confidence scores.
4.  **Decision Logic**: The script iterates through the detected objects.
    -   If an object is detected with a confidence score greater than a threshold (e.g., `0.6`), it calculates the area of its bounding box.
    -   **Proximity is estimated by area**: If the bounding box area exceeds a certain percentage of the total screen area (e.g., 20%), the object is considered a "close" obstacle.
5.  **Send MAVLink Message**:
    -   If a "close" obstacle is detected, the script sends a `DISTANCE_SENSOR` message with a short distance (e.g., 100 cm) to the Pixhawk. This signals an imminent obstacle.
    -   If no significant obstacles are detected, it sends a `DISTANCE_SENSOR` message with a very large distance (e.g., 1000 cm) to signal that the path ahead is clear.
    -   The Pixhawk's avoidance algorithm then uses this stream of distance data to alter its path.

---

## ▶️ Usage

To run the script, simply execute it from your terminal:

```bash
python3 your_script_name.py
