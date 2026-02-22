

# 📊 Smart E-Commerce Price Tracker with AI Agent Automation

> Automate product price tracking. Track history. Set target alerts. Query with AI.

---

## 🚀 Overview

The **Smart E-Commerce Price Tracker** is a web-based system that automatically monitors product prices and stores historical data. Users can track products, set target prices, and interact with an AI assistant for intelligent insights.

This project combines:

* Web scraping
* Backend API design
* Database management
* Automation workflows
* AI agent integration

It eliminates manual price checking and supports smarter buying decisions.

---

## 🎯 Problem Statement

E-commerce prices fluctuate frequently. Users often:

* Miss discounts
* Fail to track price history
* Make impulse purchases without historical insight

Existing tools lack customization and intelligent conversational assistance.

This system solves that.

---

## ✨ Key Features

* 🔍 Product URL tracking
* 💰 Automatic price scraping
* 📈 Historical price storage
* 🎯 Target price comparison
* 📊 Personalized user dashboard
* 🤖 AI agent for natural language queries (via n8n)
* 🔄 Modular & scalable backend architecture

---

## 🏗️ System Architecture

```
User
  ↓
Web Dashboard (HTML/CSS/JS)
  ↓
FastAPI Backend
  ↓
Price Scraper (Selenium)
  ↓
SQLite Database
  ↓
Scheduler / Email / AI Agent (n8n)
```

---

## 🛠️ Tech Stack

| Layer         | Technology                |
| ------------- | ------------------------- |
| Frontend      | HTML, CSS, JavaScript     |
| Backend       | FastAPI (Python)          |
| Scraping      | Selenium                  |
| Database      | SQLite                    |
| Automation    | n8n                       |
| Future Alerts | SMTP                      |
| Scheduler     | Background Jobs (planned) |

---

## 📌 Functional Requirements

### 1️⃣ Product Tracking

User provides:

* Product URL
* Email
* Target price

System:

* Scrapes current price
* Stores data in database

---

### 2️⃣ Price History Storage

Each record stores:

* Product URL
* Email
* Current price
* Target price
* Timestamp

---

### 3️⃣ Price Comparison Logic

System compares:

* Current price
* Previous price

Status shown:

* 📉 Price Dropped
* 📈 Price Increased
* ➖ Unchanged

---

### 4️⃣ User Dashboard

* Displays only user-specific products
* Search & filter functionality
* Dynamic UI updates
* Real-time status indicators

---

### 5️⃣ AI Agent Integration (n8n)

The AI assistant can:

* Show tracked products
* Answer price-related questions
* Suggest buying decisions
* Query backend API as a tool

Example queries:

```
Show my tracked products
Has the iPhone price dropped?
Should I buy now?
```

---

## 🔄 Workflow

1. User enters product details
2. Backend scrapes current price
3. Data stored in SQLite database
4. Price compared with previous values
5. Dashboard updates dynamically
6. AI agent responds to user queries

---

## 📂 Project Structure (Suggested)

```
price-tracker/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── scraper.py
│   ├── database.py
│   └── routes.py
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
│
├── n8n-workflows/
│
├── requirements.txt
└── README.md
```

---

## 🔐 Non-Functional Requirements

* Simple and intuitive UI
* Fast API response
* Modular backend design
* Beginner-friendly architecture
* Easily extendable

---

## 🔮 Future Enhancements

* 📧 Automated email alerts
* ⏰ Scheduled price checks
* 🧠 Machine Learning price prediction model
* 📊 Advanced analytics dashboard
* 🌍 Multi-platform scraping support

---

## 🧠 Learning Outcomes

This project helps developers understand:

* FastAPI backend development
* REST API design
* Web scraping with Selenium
* Database schema design
* Automation with n8n
* AI agent integration
* System architecture planning

---

## 📜 License

For educational and learning purposes.

---

## 👨‍💻 Author

Your Name
Engineering Student | Automation Enthusiast | AI Explorer

---

Now listen carefully.

This project has the potential to:

* Become a **real SaaS**
* Be your **major resume weapon**
* Be extended into an ML-based predictive system
* Be demo-worthy in hackathons

But only if you build it cleanly.

Next step:
Do you want me to:

1. Refactor this README to a more production-level SaaS style?
2. Start backend architecture step-by-step from venv?
3. Design database schema properly first?

Choose. We build this properly.
