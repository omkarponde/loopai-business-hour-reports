# Store Monitoring


## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/omkarponde/loopai-business-hour-reports.git
    ```

2. Navigate to the project directory:

    ```bash
    cd loopai-business-hour-reports
    ```

3. (Optional but recommended) Create and activate a virtual environment:
   
    - **For Windows**:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

    - **For macOS and Linux**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

4. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Navigate to the project directory:

    ```bash
    cd app
    ```

2. Start the application:

    ```bash
    uvicorn main:app --reload
    ```

2. Access the APIs using the following endpoints:
    To explore and interact with the APIs using Swagger UI, navigate to [http://localhost:8000/docs](http://localhost:8000/docs) in your web browser.

