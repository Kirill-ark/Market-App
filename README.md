# Market-App
A simple web-based market application built with Python and HTML templates.
The project demonstrates basic web development concepts such as routing, database interaction, and template rendering.
How to Run the Program
Clone the repository
git clone https://github.com/Kirill-ark/Market-App.git
cd Market-App
Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
Install dependencies
If a requirements file is available:
pip install -r requirements.txt
If not, install the required libraries manually (for example Flask, if used):
pip install flask
Initialize the database
python init_db.py
Run the application
python app.py
or
python main.py
Open in browser
Go to:
http://127.0.0.1:5000
Features Implemented
Basic web interface using HTML templates
Product or market item management
Database initialization and storage
Routing between pages
User interaction through forms
Simple backend logic using Python
How Data is Stored
The application uses a local database initialized via the init_db.py script.
Data is stored locally on the server machine.
The database structure is created automatically when running the initialization script.
Typical stored entities may include:
Products / items
Users (if authentication exists)
Orders or transactions (if implemented)
Most likely the project uses SQLite, which does not require additional setup and stores data in a file within the project directory.
Known Limitations
No authentication or advanced security features
Limited error handling and validation
Designed for learning purposes rather than production use
No deployment configuration
Minimal UI styling
No automated tests included
Author
Kirill Ark
