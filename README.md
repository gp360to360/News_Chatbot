# **RAG-Powered News Chatbot**

This repository contains the complete source code for a full-stack, Retrieval-Augmented Generation (RAG) powered chatbot. The application is designed to answer user queries based on a corpus of news articles, providing accurate, context-aware responses while preventing AI hallucinations.

### **Live Demo & Key Links**

* **Live Application:** https://chat-frontend1-g1ht.onrender.com/
* **Frontend Repository:** https://github.com/gp360to360/RAG_Frontend  
* **Backend Repository:** https://github.com/gp360to360/RAG_Backend

## **🚀 Features**

* **Accurate, Context-Aware AI:** Implements a RAG pipeline to ground responses in factual news data, preventing the AI from inventing answers.  
* **Interactive Chat Interface:** A clean and modern UI built with React for a seamless user experience.  
* **Persistent Session Management:** Automatically creates and saves chat history for each user in the browser's local storage.  
* **Scalable Backend:** A robust and well-structured API built with NestJS to handle chat logic, session management, and the AI pipeline.  
* **Automated Data Ingestion:** A Python script scrapes, chunks, and embeds news articles into a vector database to build the chatbot's knowledge base.  
* **Responsive Design:** The interface is fully responsive and works seamlessly on both desktop and mobile devices.

## **🏛️ System Architecture**

The application is architected around two distinct phases: an **Offline Ingestion Process** to build the knowledge base, and a **Real-time Query Process** to handle user interactions.

## **🛠️ Tech Stack**

| Component | Technology |
| :---- | :---- |
| **Frontend** | React, Vite, Tailwind CSS |
| **Backend** | NestJS (Node.js, Express.js), TypeScript |
| **AI Pipeline** | Python, Jina AI (Embeddings), Google Gemini API (LLM) |
| **Databases** | Qdrant (Vector DB), Redis (Cache & Session Store) |
| **DevOps** | Docker, Git & GitHub |

## **⚙️ Local Setup and Installation**

Follow these steps to get the entire application running on your local machine.

### **Prerequisites**

* Node.js (v18 or higher)  
* Python (v3.8 or higher)  
* Docker and Docker Compose  
* pnpm package manager (or npm/yarn)

### **Step 1: Clone the Repository**

Clone this repository and its submodules (if applicable) to your local machine.

git clone : https://github.com/gp360to360/News_Chatbot 
cd your-project-repo

### **Step 2: Configure Environment Variables**

You will need API keys from Google AI Studio and Jina AI.

1. Backend (chatbot-backend/.env):  
   Create a .env file inside the chatbot-backend directory and add the following:  
   PORT=8000  
   GEMINI\_API\_KEY="your\_google\_ai\_studio\_api\_key"  
   JINA\_API\_KEY="your\_jina\_api\_key"  
   QDRANT\_URL="http://localhost:6333"  
   REDIS\_URL="redis://localhost:6379"

2. Frontend (frontend/.env):  
   Create a .env file inside the frontend directory and add the following:  
   VITE\_API\_URL=http://localhost:8000/api/chat

3. Ingestion Script (rag-pipeline/.env):  
   Create a .env file inside the rag-pipeline directory and add the following:  
   JINA\_API\_KEY="your\_jina\_api\_key"  
   QDRANT\_URL="http://localhost:6333"

### **Step 3: Start Databases with Docker**

From the root of the project, start the Qdrant and Redis containers.

docker-compose up \-d

This will start both databases in the background.

### **Step 4: Install Dependencies**

Install the required packages for each part of the application.

\# Install backend dependencies  
cd chatbot-backend  
pnpm install

\# Install frontend dependencies  
cd ../frontend  
pnpm install

\# Install RAG pipeline dependencies  
cd ../rag-pipeline  
python \-m venv venv  
source venv/bin/activate  \# On Windows use \`venv\\Scripts\\activate\`  
pip install \-r requirements.txt

## **🚀 Running the Application**

1. Run the Data Ingestion Script:  
   First, you must populate the vector database with news articles.  
   cd rag-pipeline  
   source venv/bin/activate \# Activate virtual environment if not already  
   python ingest.py

2. **Start the Backend Server:**  
   cd ../chatbot-backend  
   pnpm run start:dev

   The backend API will be running on http://localhost:8000.  
3. Start the Frontend Application:  
   In a new terminal:  
   cd ../frontend  
   pnpm run dev

   The React application will be available at http://localhost:5173 (or the port specified by Vite).

## **☁️ Deployment**

This application is designed for cloud deployment on a platform like **Render**.

* **Frontend (React):** Deployed as a **Static Site**.  
* **Backend (NestJS):** Deployed as a **Web Service**.  
* **Databases (Qdrant & Redis):** Deployed as a **Private Service** (from a Docker image) and a managed **Redis Instance**.  
* **Ingestion Script (Python):** Deployed as a **Cron Job** to run on a schedule and keep the news data fresh.

For detailed instructions, please refer to the README.md files within the frontend and chatbot-backend directories.
