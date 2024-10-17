# EcoClean Bot


EcoClean Bot is a CRM-style employee management system designed for small businesses (like cleaning companies) to manage daily tasks and reports through a Telegram bot interface. It uses Flask for the backend, PostgreSQL for data storage, and Docker to manage the development environment.

## Features

- Create and manage employee accounts.
- Employees can send work updates through a Telegram bot.
- Managers can receive end-of-day reports.
- REST API endpoints for account and job report management.
- Integration with PostgreSQL and Redis for queuing and processing.


## Setup

### Prerequisites

- Docker

Ensure you have the required environment variables configured in a `.env` file for Docker Compose to work correctly.

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ecoclean-bot.git
   cd ecoclean-bot
   ```


3. Build and run the application:
   ```
   docker-compose up --build
   ```
   
### Running the Application

To build and run the application locally, use Docker Compose:

4. The application should now be running and accessible at `http://localhost:5000`.

## Running Tests

To run the tests, use the following command:

```
docker-compose run test
```

This will run the test suite in a separate container.

## API Documentation

API documentation can be found in the `docs` directory. The [API.md](./docs/API.md) file provides an overview, and individual endpoint documentation is available in the `endpoints` subdirectory.

## Development

For development purposes, the application uses Flask's debug mode. Any changes made to the code in the `app` directory will be reflected immediately due to the volume mounting in the `docker-compose.yml` file.

## Database Initialization

The `initdb` directory contains scripts that are automatically run when the database container is first created. These scripts set up the necessary extensions, create the databases, set up tables, and insert initial data.

## Contributing



## License



## Contact

[Add contact information or links to where users can get help or report issues]
