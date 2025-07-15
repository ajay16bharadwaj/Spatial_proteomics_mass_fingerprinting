# Spatial Mass Fingerprinting Tool

This application provides a web-based graphical user interface for performing spatial mass fingerprinting. It allows users to match peaks from a MALDI peak list file against a Peptide-Spectrum Match (PSM) file from a DDA experiment, filter the results based on specific criteria, and visualize the output.

---

## Features

- **File Upload**: Upload your peak list (`.csv`) and PSM data (`.tsv`, `.csv`, `.txt`) directly in the browser.
- **Interactive Parameters**: Set the PPM mass tolerance, Hyperscore threshold, and charge states for filtering.
- **Results Table**: View the matched peptides in a searchable and paginated table.
- **Data Visualization**: Automatically generate and display three key plots:
  - Mass Error Distribution
  - Hyperscore vs. Mass Error
  - Peptide Identifications per Mass Bin
- **Live Log**: Monitor the progress of the analysis in real-time.
- **Download Results**: Download the complete results table as a CSV file with a single click.

---

## Installation

To run this application, you will need **Python 3**. Follow these steps to set up the environment and install the necessary dependencies.

### 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies. Navigate to your project directory in the terminal and run the following commands:

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

With your virtual environment activated, install the required libraries using pip:

```bash
pip install -r requirements.txt
```

---

## How to Run the Application

The project is split into two main files:

- `spatial_mass_fingerprinter.py`: Contains the core analysis logic.
- `app.py`: Contains the NiceGUI web interface.

### Running Locally

To run the application on your local machine, execute the following command in your terminal from the project directory:

```bash
python app.py
```

The application will start, and you can access it by opening your web browser and navigating to the URL provided in the terminal (usually [http://127.0.0.1:8080](http://127.0.0.1:8080)).

---

### Running on a Local Network

To make the application accessible to other computers on the same network, modify the last line in `app.py` to include the `host` parameter:

```python
ui.run(host='0.0.0.0')
```

Then, run the app as usual:

```bash
python app.py
```

#### Find your computer's local IP address:

- **On Windows**: Open Command Prompt and type:
  ```bash
  ipconfig
  ```
  Look for the `IPv4 Address`.

- **On macOS/Linux**: Open Terminal and type:
  ```bash
  ifconfig
  ```
  or
  ```bash
  ip addr
  ```
  Look for the `inet` address.

#### Access the app:

On another computer on the same network, open a web browser and navigate to:

```
http://<YOUR_IP_ADDRESS>:8080
```

Example:

```
http://192.168.1.15:8080
```

> **Note**: You may need to configure your firewall to allow incoming connections on port `8080`.
