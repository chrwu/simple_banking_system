# Simple Banking System

## Overview
Simple Banking System is a basic banking system implemented using FastAPI, PostgreSQL, and Docker. This system allows users to create accounts, deposit and withdraw money, transfer money between accounts, and export/import the system state to/from CSV files.

## How to Run the Simple Banking System

### Prerequisites
- Docker should be installed on your machine. You can install Docker from [here](https://docs.docker.com/desktop/).

### Steps
1. Clone this repository to your local machine:

    ```bash
    git clone git@github.com:chrwu/simple_banking_system.git
    ```

2. Navigate to the root folder of the repository:

    ```bash
    cd simple_banking_system
    ```

3. Run the following command to start the containers:

    ```bash
    docker-compose up
    ```

4. Once the containers are up and running, you can check if the following two containers are active:
    - simple_banking_system-web-1
    - simple_banking_system-db-1

5. If the above two containers are running, you can access the web container by running:

    ```bash
    docker exec -it simple_banking_system-web-1 bash
    ```

6. Inside the container, you can run the unit tests with coverage using the following command:

    ```bash
    pytest --cov=sbs tests
    ```
   You'll be able to see the test results along with the coverage information.
   ```
   ---------- coverage: platform linux, python 3.10.14-final-0 ----------
   platform linux -- Python 3.10.14, pytest-8.2.0, pluggy-1.5.0
   rootdir: /app
   plugins: mock-3.14.0, anyio-4.3.0, cov-5.0.0
   collected 17 items
   
   tests/test_main.py ...........                                                                                                                                                                     [ 64%]
   tests/test_models.py .                                                                                                                                                                             [ 70%]
   tests/test_schemas.py .....
   Name              Stmts   Miss  Cover
   -------------------------------------
   sbs/__init__.py       0      0   100%
   sbs/db.py            10      4    60%
   sbs/main.py         162     33    80%
   sbs/models.py         8      0   100%
   sbs/schemas.py        4      0   100%
   -------------------------------------
   TOTAL               184     37    80%
   ========== 17 passed, 2 warnings in 1.26s ==============================================
   ```