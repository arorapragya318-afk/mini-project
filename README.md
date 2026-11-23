# 🗳️ VoteX – Online Voting System

VoteX is a web-based online voting platform designed to make the voting process simple, secure, transparent, and efficient.

It allows voters to register, log in, view available elections, select candidates, and cast their votes online. It also provides an admin panel to manage elections, voters, and candidates.

## 🚀 Features

- **Voter Registration:** New users can create an account.
- **Secure Login:** Registered voters can log in securely.
- **Election Management:** Admin can create and manage elections.
- **Candidate Management:** Admin can add and manage candidates.
- **Online Voting:** Voters can select and submit their votes.
- **One Person, One Vote:** Prevents voters from voting more than once in an election.
- **Live Results:** Displays election results and vote counts.
- **Voice Assistant:** Supports voice-based interaction for improved accessibility.
- **Admin Dashboard:** Provides tools to manage the voting system.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| MySQL | Database management |
| HTML | Webpage structure |
| CSS | Styling and design |
| JavaScript | Interactive functionality |
| Web Speech API | Voice assistant |

## 📂 Project Structure

```text
OnlineVotingSystem/
│
├── app.py
├── templates/
│   ├── admin_login.html
│   ├── admin_voters.html
│   ├── admin_candidates.html
│   ├── admin_elections.html
│   ├── admin_dashboard.html
│   ├── candidates.html
│   ├── dashboard.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── results.html
│
├── .gitignore
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/arorapragya318-afk/mini-project.git
```

### 2. Open the Project Folder

```bash
cd mini-project
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### 5. Install Required Packages

```bash
pip install flask mysql-connector-python werkzeug
```

### 6. Configure MySQL Database

- Open MySQL Workbench.
- Create the database named `online_voting`.
- Configure your database connection in the application.
- Make sure the required tables are created.

### 7. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## 🔐 Security Features

- Password hashing.
- Session-based authentication.
- Duplicate voting prevention.
- Database-backed voter records.
- Admin authentication.

## 🎯 Project Objective

The main objective of VoteX is to reduce the limitations of traditional voting systems by providing a convenient digital platform that improves voting accessibility, simplifies vote counting, and helps prevent duplicate voting.

## 🌍 Sustainable Development Goal

**SDG 16 – Peace, Justice and Strong Institutions**

VoteX supports the idea of transparent, accountable, and inclusive institutions through a digital voting platform.

## 🔮 Future Enhancements

- OTP-based voter verification.
- Biometric authentication.
- Improved voice-based accessibility.
- Advanced election analytics.
- Enhanced security and audit mechanisms.

## 👩‍💻 Developed By

**Pragya Arora**

B.Tech – Computer Science and Engineering

Project: VoteX – Online Voting System

---

⭐ If you find this project interesting, don't forget to star the repository!
