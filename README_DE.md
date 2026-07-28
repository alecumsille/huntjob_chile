<p align="center">
  <a href="https://cumsille.tech"><img src="assets/css_logo.png" width="160" alt="Cumsille Systems Suite Logo"></a>
  <br>
  <img src="assets/icon.png" width="90" alt="HuntJob Chile Logo">
</p>
Intelligente Job-Plattform & ATS-Audit
  <sub>Eine offizielle Entwicklung der CSS SpA <a href="https://cumsille.tech"><b>CSS SpA</b></a></sub>
</p>

<p align="center">
  <a href="https://huntjob.cumsille.me"><img src="https://img.shields.io/badge/Sitio_Web-huntjob.cumsille.me-blue?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Sitio Web"></a>
  <a href="https://cumsille.tech"><img src="https://img.shields.io/badge/Ecosistema-cumsille.tech-purple?style=for-the-badge&logo=opsgenie&logoColor=white" alt="Cumsille Tech"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License"></a>
</p>

🇩🇪 
Intelligente Job-Plattform & ATS-Prüfung
Eine offizielle Entwicklung der Cumsille Systems Suite SpA

Huntjob Chile ist die Karrierebeschleunigungs-Suite, die für Fach- und Nachwuchskräfte in Chile entwickelt wurde. Sie bündelt an einem einzigen Ort Echtzeitsuchen in den wichtigsten Portalen des Landes (Get on Board, Chiletrabajos, Trabajando, Laborum und LinkedIn), prüft Ihr Profil gegen offene Stellen mithilfe von Künstlicher Intelligenz der neuesten Generation und erstellt optimierte PDF-Lebensläufe, die darauf ausgelegt sind, ATS-Filter (Applicant Tracking Systems) zu überwinden.

🔥 Warum hebt sich Huntjob Chile von anderen Plattformen ab?

Multi-Portal-Suche: Im Gegensatz zu traditionellen Portalen (1 einziges Portal pro Tab) oder anderen KI-Apps (erfordert manuelles Kopieren von URLs) bietet Huntjob eine aggregierte Echtzeit-Indexierung.

Live ATS-Prüfung: Bietet einen Score von 0-100%, hebt Stärken hervor und identifiziert fehlende Schlüsselwörter, wodurch generische Antworten anderer KIs vermieden werden.

Unverwüstliche Verfügbarkeit: Entwickelt mit einer Hybrid-Engine Gemini + Groq (Llama 3.3 70B), die Ausfälle oder Sperrungen durch Kontingentlimits (429) verhindert.

Exekutiver Export: Bietet 4 kostenlose herunterladbare visuelle PDF-Vorlagen, im Gegensatz zu Plattformen mit Basisformaten oder Bezahlschranken.

Datenschutz & Isolierung: Verfügt über eine isolierte Sitzung im Arbeitsspeicher, ohne Ihren Lebenslauf zu speichern, und schützt so Ihre persönlichen Daten.

✨ Neuheiten & Hervorgehobene Funktionen

🔍 Multichannel-Echtzeit-Indexierung: Suchen Sie gleichzeitig in den wichtigsten Portalen Chiles, ohne Zeit mit dem Öffnen Dutzender Tabs zu verschwenden.

🎯 ATS-Kompatibilitätsprüfung: Analysieren Sie den Übereinstimmungsgrad Ihres Profils mit der Zielvakanz. Erhalten Sie eine Diagnose mit: Kompatibilitäts-Score (0-100%), erkannten Stärken in Ihrem Profil, fehlenden Schlüsselwörtern und Tools sowie taktischen Optimierungsempfehlungen.

⚡ Ausfallsicherheit & Null KI-Ausfälle: Implementiert eine Architektur mit automatischem Fallback (Google Gemini 2.0 Flash -> Groq Llama 3.3 70B). Wenn eine API ihr Kontingentlimit erreicht, übernimmt die andere nahtlos.

📄 PDF-Lebenslauf- & Anschreiben-Generator: Erstellt strukturierte, elegante und versandfertige Dokumente in 4 exekutiven Designpaletten (Pastell, Exekutiv, Dunkler Minimalismus, Smaragd).

🔒 Social Auth & Sichere Sitzung: Native Authentifizierungsintegration mit Google, GitHub und Facebook über Supabase.

🛠️ Systemanforderungen

Python 3.10+ (für lokale Ausführung oder dedizierte Server)

Docker (für Container-Bereitstellung)

Optionale API-Schlüssel: GEMINI_API_KEY, GROQ_API_KEY (konfigurierbar in Umgebungsvariablen)

🏗️ Architektur des zusammengeführten Repositories
(Traducción de comentarios para la estructura del código):

# Haupt-Weboberfläche (Streamlit)

# Wrapper für native GTK/WebKit-Desktop-App

# Bereitstellbarer Container mit CNAME

# Grafische Unternehmensressourcen + offizielle Icons

# HTML/API-Extraktion und Parsing von Jobportalen

# Aggregierter Multi-Portal-Such-Dispatcher

# ATS-Generierungs- und Prüfungs-Engine mit Gemini -> Groq Fallback

# ReportLab-Compiler für visuelle Lebenslaufvorlagen

# Isoliertes Sitzungsmodul für Benutzerprofile

# Relaitionale SQLite-Persistenz für den Verlauf

# Hintergrund-Tracking-Daemon und Job-Deduplizierung

# Multichannel-Bewerbungssynchronisator

# Systemabhängigkeiten

🚀 Lokale Installation und Ausführung

Klonen Sie das Repository.

Erstellen Sie eine virtuelle Umgebung und installieren Sie Abhängigkeiten.

Konfigurieren Sie Umgebungsschlüssel (optional).

Starten Sie die Anwendung.

🐳 Ausführung mit Docker
Wenn Sie es vorziehen, die Anwendung in einem Container auszuführen oder auf Diensten wie Render, Railway oder Koyeb bereitzustellen.

💻 Desktop-Anwendung (Linux)
Für Linux Mint / Ubuntu-Benutzer, die HuntJob Chile lieber als native Desktop-Anwendung ausführen möchten. Dadurch wird eine direkte Verknüpfung im Systemmenü mit dem nativen Fenster (GTK/WebKit) und seinem Unternehmenssymbol erstellt.

🤝 Wie kann man zum Projekt beitragen?
Jeder Beitrag ist willkommen! Wenn Sie mithelfen möchten, die Beschäftigungsfähigkeit in Chile zu fördern und die Plattform zu verbessern:

Neue Jobportale hinzufügen: Erstellen oder verbessern Sie Scraper in core/scraper_web.py.

Fehler oder Vorschläge melden: Öffnen Sie ein Issue auf GitHub mit detaillierten Angaben zur Verbesserung.

Pull Requests senden: Forken Sie das Repository, erstellen Sie Ihren Branch (git checkout -b feature/neue-funktion) und pushen Sie Ihre Änderungen.

📄 Lizenz & Danksagungen
Entwickelt mit ❤️ von Ale Cumsille als Teil des Technologie-Ökosystems der Cumsille Systems Suite SpA.
Veröffentlicht unter der MIT-Lizenz.
