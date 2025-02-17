# EcoClean Bot

**EcoClean Bot** is a modern, CRM-style employee management system designed for small businesses to streamline daily tasks and reporting through a **Telegram bot interface**. Built with **Flask** for the backend, **PostgreSQL** for data storage, and **Docker** for seamless development and deployment, EcoClean Bot simplifies employee management and reporting for businesses.

---

## ✨ Key Features

- **User Management**: Create and manage employee accounts.
- **Email Service**: Sends verification emails with a Telegram bot link.
- **Telegram Integration**: Employees can link their Telegram accounts to receive work notifications.
- **Job Reporting**: Employees submit job reports, including location and payment details.
- **Daily Summaries**: Managers receive automated reports summarizing completed jobs.
- **REST API**: Secure API endpoints for account and job management.
- **Database & Queuing**: Uses PostgreSQL for data storage and Redis for efficient task processing.
- **Dockerized Development**: Easy setup and deployment with Docker.

## 🛠️ Setup

### Prerequisites

- **Docker** (with Docker Compose) installed on your machine.
- A `.env` file with the required environment variables.

### Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/kobs14/ecoclean-bot.git
   cd ecoclean-bot
   ```

2. **Build and Run the Application**:
   ```bash
   docker-compose up --build
   ```

3. **Access the Application**:
   - The backend will be running at `http://localhost:5000`.
   - Use the API endpoints to interact with the system.

## 🧪 Running Tests

To ensure the application works as expected, run the test suite using Docker Compose:

```bash
docker-compose run test
```

This will execute the test suite in a separate container and provide feedback on the application's functionality.

## 📚 API Documentation

The API is fully documented to help you integrate and extend the system. Check out the following resources:

- **[API.md](./docs/API.md)**: API documentation can be found in the docs directory. The [API.md](./docs/API.md) file provides an overview, and individual endpoint documentation is available in the endpoints subdirectory.

## 🖥️ Development

### Debug Mode

For development, the application runs in Flask's debug mode. Changes to the code in the `app` directory are automatically reflected thanks to volume mounting in the `docker-compose.yml` file.

### Database Initialization

The `initdb` directory contains scripts that run automatically when the database container is first created. These scripts:

- Set up necessary PostgreSQL extensions.
- Create the required databases and tables.
- Insert initial data for testing and development.


## 📝 License

See the `LICENSE` file for details.

## 💎 Contact

For questions, feedback, or support, feel free to reach out:

- **Email**: kobihorshid@gmail.com  
- **GitHub Issues**: [Open an Issue](https://github.com/kobs14/ecoclean-bot/issues)  
- **LinkedIn**: [LinkedIn Profile](https://www.linkedin.com/in/kobe-horshid-965031217)  

## 🌟 Why EcoClean Bot?

EcoClean Bot is designed to help small businesses manage their workforce efficiently. By integrating with Telegram, it provides a user-friendly interface for employees to submit updates and for managers to stay informed. The backend is built with scalability and reliability in mind, making it a great addition to your portfolio as a developer.

## 🖼️ Screenshots 




## 🏗️ Project Structure

```bash
ecoclean-bot/
├── app/                  # Flask application code
│   ├── __init__.py       # Application initialization
│   ├── routes/           # API routes
│   ├── models/           # Database models
│   ├── services/         # Business logic and services
│   └── utils/            # Utility functions
├── initdb/               # Database initialization scripts
├── tests/                # Test suite
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Dockerfile for the Flask app
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation (you are here!)
```

## 🚨 Troubleshooting

### Common Issues

#### Docker Compose Fails to Start:
- Ensure Docker is running and you have the correct permissions.
- Verify that the `.env` file is correctly configured.

#### Database Connection Issues:
- Check if the PostgreSQL container is running.
- Ensure the correct credentials are provided in the `.env` file.

#### Tests Fail:
- Make sure the test database is properly initialized.
- Run `docker-compose down -v` to clear existing volumes and restart the containers.

## 🙏 Acknowledgments

- **Flask** for providing a lightweight and flexible web framework.
- **PostgreSQL** for reliable and scalable data storage.
- **Docker** for simplifying development and deployment.

## 📜 Changelog

### v1.0.0 (Initial Release):
- Account creation and management.
- Telegram linking via verification tokens.
- Email service for sending welcome emails.

