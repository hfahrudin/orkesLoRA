<h2 align="center">
  <img width="35%" alt="Model2Vec logo" src="assets/flowkestra.png"><br/>
  A streamlined MLflow orchestrator 
</h2>

**Status:** Early Prototype (Not Yet Usable)  

This project is an **early-stage framework** for hybrid LLM training and tuning. The goal is to allow experiments **on-premises or in the cloud** with integrated tracking, modular ETL pipelines, and simple deployment.  

> ⚠️ This project is still in the **concept / early development stage**. It is not yet usable.

---

## Goal

Enable a unified, flexible workflow for **LLM training and fine-tuning**, with focus on:

- Simplifying ETL and training pipelines
- Hybrid deployment (cloud or on-premises)
- MLflow experiment tracking
- Modular, easy-to-extend architecture

---

## Proposed Features

- **MLflow Integration**
  - Track experiments, metrics, and model artifacts
- **ETL Script Upload**
  - Modular preprocessing scripts per instance
- **Parameter & Config Upload**
  - Upload training parameters and config files
- **Model Upload & Management**
  - Support pre-trained models for fine-tuning
- **Machine Target Selection**
  - Run training locally or remotely
- **Error Log Monitoring**
  - Centralized error logging
- **Dockerized Environment**
  - Quick setup with all dependencies
- **ETL Output Preview**
  - Inspect processed data before training

---

## Conceptual Workflow

1. User provides:
   - **Configuration file** (train instance, ETL script, parameters)
   - **ETL script**
   - **Training parameters**
2. System performs:
   - ETL data processing
   - Model training/fine-tuning
   - Logging metrics and artifacts to MLflow
3. Output:
   - MLflow experiment tracking
   - Processed ETL data preview
   - Trained LLM artifacts

---

## Advantages

- **Hybrid**: Works on-premises or in the cloud
- **Developer-Friendly**: Modular design for fast iteration
- **Extensible**: Easy to add new ETL scripts or model configs
- **Tracking Built-In**: MLflow support from day one

---

## Getting Started (Early Prototype)

Currently, the project is **not usable**. Planned steps include:

1. Dockerized environment setup
2. Script-based ETL and parameter injection
3. MLflow experiment tracking

---

## Roadmap / Next Steps

- Build CLI or web interface for uploading ETL scripts and configs
- Full MLflow integration for experiments
- Multi-instance / distributed training support
- Error monitoring and auto-recovery
- Support multiple LLM frameworks (Hugging Face, OpenAI, etc.)

---

## Notes

- This project is **still in design/early implementation**.  
- Intended as a **research & development prototype** before public use.
- Contributions, feedback, and collaboration ideas are welcome.
