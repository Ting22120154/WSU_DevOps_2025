# WSU_DevOps_2025 - Multi-Website Lambda Monitoring Project

## 📌 Overview
This project is part of the **DevOps 2025** coursework at Western Sydney University.  
It demonstrates how to use **AWS CDK** (Python) to deploy a scheduled Lambda function that automatically monitors the health and latency of multiple websites, with real-time dashboards and email alerts for failures.

---

## 🚀 Features

- **Multi-site Monitoring:** Easily monitor any number of websites by editing a URL list.
- **Serverless & Automated:** Uses AWS Lambda and EventBridge to check sites every 5 minutes (no server needed).
- **CloudWatch Dashboards:** Automatically creates real-time graphs for latency and uptime of each website.
- **CloudWatch Alarms:** Automatically sets up alarms for:
  - **Availability:** Alerts if a site is down for 2 consecutive checks (10 minutes).
  - **Latency:** Alerts if a site is slow (>1 second) for 3 consecutive checks (15 minutes).
- **SNS Email Alerts:** Instantly notifies you via email when a problem is detected.
- **Easy Customization:** Add/remove monitored sites and alert recipients in one file, redeploy to update.

---

## 🧰 Technologies Used

- AWS Lambda (Python 3.12+)
- AWS CDK (Python)
- AWS EventBridge (Scheduled jobs)
- AWS CloudWatch (metrics, dashboards, alarms)
- AWS SNS (notifications)
- AWS IAM (permissions)


## 📂 Project Structure
WSU_DevOps_2025/
├── lambda/
│ └── lambda_function.py # Lambda: website checking logic
├── hello_lambda_stack.py # CDK Stack: defines Lambda, alarms, dashboard, SNS
├── app.py # CDK entry point
├── requirements.txt # Python dependencies
└── README.md # This documentation

📊 How It Works

Lambda runs on a schedule (every 5 min) and checks all URLs.

Results are sent to CloudWatch as custom metrics (IsSuccess, Latency) for each website.

CloudWatch Dashboard visualizes uptime and response time for all monitored websites.

CloudWatch Alarms detect failures or high latency and trigger SNS email alerts.