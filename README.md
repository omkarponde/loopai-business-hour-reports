# Store Monitoring

## Store Monitoring Setup Guide
### Installation

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
    

### Database Setup and Data Migration
This project uses a PostgreSQL database.

1. Create a .env file in the project directory and specify your database URI in it:

    ```bash
    postgresql://username:password@host:port/database

    ```

2. INavigate to the app directory:

    ```bash
    cd app
    ```

3. Create tables in the database:

    ```bash
    python init_db.py
    ```
4. Once the tables have been created, create a directory named data inside the app directory and place the appropriate CSV files from which the data is to be imported into the database.
5. Navigate to the scripts folder and run the scripts one by one:

    ```bash
    python store_activity_script.py
    ```
    
     ```bash
    python store_business_hour_script.py
    ```
     
      ```bash
    python store_timezone_script.py
    ```
6. After the data import is complete, navigate back to the 'app' directory and start the Uvicorn server:

         ```bash
    uvicorn main:app --reload

    ```

7. Access the APIs using the following endpoints:
    To explore and interact with the APIs using Swagger UI, navigate to [http://localhost:8000/docs](http://localhost:8000/docs) in your web browser.

