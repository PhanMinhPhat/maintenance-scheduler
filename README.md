# Maintenance Scheduler System

An AI-powered maintenance planning system that uses Deep Q-Learning to optimize equipment maintenance scheduling.

## Table of Contents

1. [System Overview](#system-overview)
2. [Project Structure](#project-structure)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Data Model](#data-model)
6. [AI Model](#ai-model)
7. [Key Features](#key-features)
8. [Usage Guide](#usage-guide)
9. [API Reference](#api-reference)

## System Overview

The Maintenance Scheduler is an intelligent system that helps optimize maintenance planning by considering multiple factors including:

- Equipment condition and history
- Current issues and priorities
- Resource availability
- Cost constraints
- Risk factors

The system uses Deep Q-Learning to make optimal maintenance decisions while balancing preventive and corrective maintenance needs.

## Project Structure

```
maintenance-scheduler/
├── data/                    # Data files and templates
│   ├── data_dictionary.md   # Data field definitions
│   ├── maintenance_schedule.xlsx
│   ├── training_history.csv
│   ├── sample_data/        # Sample datasets
│   └── uploads/            # User uploaded files
├── models/                 # ML model implementations
│   ├── dqn_agent.py       # Deep Q-Network agent
│   ├── maintenance_env.py  # Maintenance environment
│   └── saved/             # Saved model weights
├── tests/                 # Test files
├── ui/                    # Frontend application
│   └── webapp/           # UI5 web application
├── utils/                # Utility functions
├── server.py            # Backend Flask server
├── train.py             # Model training script
└── requirements.txt     # Python dependencies
```

## Architecture

### Backend (Python/Flask)

The backend provides REST APIs for:

- Issue management
- Schedule generation
- Data export/import
- Model inference

Key endpoints:

- `POST /api/upload_issues`: Process new maintenance issues
- `POST /api/generate_schedule`: Create optimized schedules
- `GET /api/download_template`: Get issue reporting template
- `GET /api/download_schedule`: Export maintenance schedules

### Frontend (OpenUI5)

Web-based interface featuring:

- Issue upload interface
- Schedule visualization
- Template downloads
- Schedule exports

### ML Component

Deep Q-Learning implementation with:

- State space (8 dimensions):

  1. Days since maintenance (normalized)
  2. Equipment age
  3. Criticality score
  4. Maintenance cycle completion
  5. Cost ratio
  6. Breakdown risk
  7. Issue priority
  8. Workload factor

- Actions:
  - Schedule maintenance
  - Postpone maintenance

## Installation & Setup

1. Clone the repository
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Install UI dependencies:

```bash
cd ui/webapp
npm install
```

4. Start the backend server:

```bash
python server.py
```

5. Start the UI development server:

```bash
cd ui/webapp
ui5 serve
```

## Data Model

### Equipment Master Data

- Equipment identification and specifications
- Location and technical details
- Criticality ratings:
  - A: Critical (1.0) - Severe impact
  - B: Medium (0.6) - Moderate impact
  - C: Lower (0.3) - Lesser impact
- Cost and maintenance parameters

### Maintenance History

- Past maintenance records
- Maintenance types:
  - PM01: Regular maintenance
  - PM02: Major maintenance
  - PM03: Emergency maintenance
- Performance metrics and costs

### Current Issues

- Active maintenance notifications
- Priority levels (1-4)
- Issue types:
  - PERF: Performance
  - ELEC: Electrical
  - HYDR: Hydraulic
  - MECH: Mechanical
- Impact categories:
  - Production Stop
  - Performance Degradation
  - Quality Impact
  - Safety Risk

## AI Model

### Decision Making Process

The DQN agent makes maintenance decisions by considering:

1. Equipment condition and age
2. Historical maintenance patterns
3. Current issues and priorities
4. Resource availability
5. Cost implications

### Risk Assessment

Risk calculation incorporates:

- Equipment age and criticality
- Maintenance history
- Current issues
- Historical performance
- Cost factors

### Reward Structure

The model optimizes for:

- Timely maintenance
- Cost efficiency
- Risk minimization
- Resource utilization
- Issue priority handling

## Key Features

### Predictive Scheduling

- AI-driven maintenance timing
- Risk-based prioritization
- Balanced maintenance approach

### Resource Optimization

- Workload distribution
- Budget management
- Priority-based allocation

### Cost Management

- Budget tracking
- Cost estimation
- Optimization for efficiency

## Usage Guide

### Issue Reporting

1. Download the issue template (`/api/download_template`)
2. Fill in required information:
   - Equipment ID
   - Issue type
   - Priority
   - Description
3. Upload completed template
4. Review generated schedule

### Schedule Generation

1. Upload current issues file
2. System processes equipment states
3. AI model generates recommendations
4. Review generated schedule
5. Export schedule as Excel file

### Maintenance Types

- **PM01 (Regular)**

  - Lower priority issues
  - Preventive maintenance
  - 7-30 days scheduling window

- **PM02 (Major)**

  - Priority 2 issues
  - Mechanical/Electrical issues
  - 2-3 days scheduling window

- **PM03 (Emergency)**
  - Priority 1 issues
  - Hydraulic issues
  - Next-day maintenance

## API Reference

### POST /api/upload_issues

Upload current issues for processing

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body: CSV file

**Response:**

```json
{
  "equipment_id": "string",
  "maintenance_type": "string",
  "suggested_date": "string",
  "priority": "string",
  "confidence": "number",
  "breakdown_risk": "number"
}
```

### GET /api/download_template

Download issue reporting template

**Response:**

- Content-Type: text/csv
- File: current_issues_template.csv

### GET /api/download_schedule

Download generated maintenance schedule

**Response:**

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- File: maintenance_schedule.xlsx
