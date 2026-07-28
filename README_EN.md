<p align="center">
  <a href="https://cumsille.tech"><img src="assets/css_logo.png" width="160" alt="Cumsille Systems Suite Logo"></a>
  <br>
  <img src="assets/icon.png" width="90" alt="HuntJob Chile Logo">
</p>

🇬🇧 English Version
Intelligent Job Platform & ATS Audit
 <sub>An official development by CSS SpA <a href="https://cumsille.tech"><b>CSS SpA</b></a></sub>
</p>

Huntjob Chile is the career acceleration suite designed for professionals and talent in Chile. It brings together in a single place real-time searches across the country's main portals (Get on Board, Chiletrabajos, Trabajando, Laborum, and LinkedIn), audits your profile against job openings using next-generation Artificial Intelligence, and generates optimized PDF resumes designed to beat ATS (Applicant Tracking Systems) filters.

🔥 Why does Huntjob Chile stand out from other platforms?

Multi-Portal Search: Unlike traditional portals (1 single portal per tab) or other AI apps (requires manual URL copying), Huntjob provides real-time aggregated indexing.

Live ATS Audit: Provides a 0-100% Score, highlights strengths, and identifies missing keywords, escaping the generic responses of other AIs.

Indestructible Availability: Built with a Hybrid Engine Gemini + Groq (Llama 3.3 70B), avoiding crashes or quota limit blocks (429).

Executive Export: Offers 4 free downloadable visual PDF templates, unlike platforms with basic formats or paywalls.

Privacy & Isolation: Features an isolated session in memory without persisting your CV, protecting your personal data.

✨ New & Highlighted Features

🔍 Real-Time Multichannel Indexing: Search simultaneously across Chile's most important portals without wasting time opening dozens of tabs.

🎯 ATS Compatibility Audit: Analyze the match level of your profile against the target vacancy. Receive a diagnostic with: Compatibility score (0-100%), detected strengths, missing keywords and tools, and tactical optimization recommendations.

⚡ Resilience & Zero AI Downtime: Implements an architecture with automatic fallback (Google Gemini 2.0 Flash -> Groq Llama 3.3 70B). If one API reaches its quota limit, the other seamlessly takes over.

📄 PDF CVs & Cover Letters Generator: Produces structured, elegant documents ready to send in 4 executive design palettes (Pastel, Executive, Dark Minimalist, Emerald).

🔒 Social Auth & Secure Session: Native authentication integration with Google, GitHub, and Facebook via Supabase.

🛠️ System Requirements

Python 3.10+ (for local execution or dedicated servers)

Docker (for containerized deployment)

Optional API Keys: GEMINI_API_KEY, GROQ_API_KEY (configurable in environment variables)

🏗️ Merged Repository Architecture
(Puedes dejar el bloque de código del árbol tal cual, ya que las carpetas no se traducen, pero aquí tienes los comentarios traducidos para que los reemplaces):

# Main web interface (Streamlit)

# Wrapper for native GTK/WebKit desktop app

# Ready-to-deploy container with CNAME

# Corporate graphic resources + official icons

# HTML/API extraction and parsing from job portals

# Multi-portal aggregated search dispatcher

# ATS generation and audit engine with Gemini -> Groq fallback

# ReportLab compiler for visual CV templates

# User profile isolated session module

# SQLite relational persistence for history

# Background tracking daemon and job deduplication

# Multichannel application synchronizer

# System dependencies

🚀 Local Installation and Execution

Clone the repository.

Create virtual environment and install dependencies.

Configure environment keys (optional).

Launch the application.

🐳 Execution with Docker
If you prefer to run the application inside a container or deploy it on services like Render, Railway, or Koyeb.

💻 Desktop Application (Linux)
For Linux Mint / Ubuntu users who prefer to run HuntJob Chile as a native desktop application. This will create a direct access in your system menu with the native window (GTK/WebKit) and its corporate icon.

🤝 How to Contribute to the Project?
Every contribution is welcome! If you want to collaborate to boost employability in Chile and improve the platform:

Add New Job Portals: Create or improve scrapers in core/scraper_web.py.

Report Bugs or Suggestions: Open an Issue on GitHub detailing the improvement.

Send Pull Requests: Fork the repository, create your branch (git checkout -b feature/new-feature), and push your changes.

📄 License & Credits
Developed with ❤️ by Ale Cumsille as part of the Cumsille Systems Suite SpA technology ecosystem.
Distributed under the MIT License.
