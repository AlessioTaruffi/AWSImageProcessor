# Cloud Image Processing API

Progetto del corso di Cloud Computing — Sapienza Università di Roma, A.A. 2025/2026.

Sistema scalabile su AWS che espone un'API REST per il processing di immagini, con confronto tra due approcci di deployment (EC2 con Auto Scaling Group vs Lambda serverless).

## Componenti

- `processor/` — modulo Python condiviso con la logica di image processing
- `backend-ec2/` — backend Flask + Gunicorn deployato su EC2
- `backend-lambda/` — handler Lambda equivalente
- `loadgen/` — load generator custom per i benchmark
- `infra/` — script bash e AWS CLI per il provisioning dell'infrastruttura
- `results/` — output dei benchmark (CSV, grafici)
- `docs/` — documentazione

## Documentazione operativa

Vedi `docs/access.md` per la procedura di accesso al Learner Lab condiviso.
Vedi `docs/diary.md` per il diario di bordo del progetto.
