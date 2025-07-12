# 2025 AIC Project W6

Topic C: Secure Blockchain-Based Healthcare Records Management System

## Cloud deployment

The cloud deployment using azure can be accessed on this [URL](https://w6-singlecontainer-b5g7c7eab9hnaybe.germanywestcentral-01.azurewebsites.net)

## Local deployment

To run the application locally, follow these steps:

This project uses Docker to containerize the application and its database, making it easy to set up and run on any machine.

### Prerequisites

You need to have Docker and Docker Compose installed on your system. The easiest way to get both is by installing Docker Desktop.

-   **Windows / macOS**: Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
-   **Linux**: Follow the official instructions to install the [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) for your distribution.

### Running the Application

Follow these steps to get the application running:

1.  **Navigate to Project Directory**

    Open a terminal or command prompt and navigate to the root directory of this project (the folder containing `docker-compose.yml`).

2.  **Start the Application**

    Run the following command to build and start the services in detached mode:

    ```sh
    docker-compose up -d
    ```

    This command will download the required Docker images (Postgres and the application image) and start the containers. The first time you run this, it may take a few minutes.

### Accessing the Application

Once the containers are running, you can access the services:

-   **Web Application (Flask)**: `http://localhost:5000`

### Stopping the Application

To stop the application and shut down the containers, run:

```sh
docker-compose down
```

To stop the application and remove the database volume (which will delete all data), run:

```sh
docker-compose down -v
```