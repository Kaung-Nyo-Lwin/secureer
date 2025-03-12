# Secureer - Job Automation Risk Assessment Platform

A web-based platform that helps users assess their job automation risk and provides personalized job and skill recommendations using machine learning.

## Features

- Job automation risk assessment
- Skill-based job recommendations
- Personalized skill recommendations
- Job posting recommendations
- User skill management
- Interactive web interface

## Project Structure

```
├── admin/                  # Django admin configuration
├── ml_models/             # Machine learning model files
├── risk_check/            # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Application views
│   ├── utils.py           # Utility functions
│   ├── templates/         # HTML templates
│   └── static/           # Static files
├── Dockerfile             # Container configuration
└── docker-compose.yml     # Container orchestration
```

## Technology Stack

- **Backend Framework:** Django
- **Database:** SQLite
- **ML Libraries:**
  - scikit-learn
  - sentence-transformers
  - PyTorch
  - transformers
- **Frontend:** Bootstrap 5
- **Deployment:** Docker

## Key Components

### Models

1. **User**
   - Stores user information and skills
   - Manages user profiles and skill sets

2. **Skill**
   - Maintains skill database
   - Used for matching and recommendations

3. **Result**
   - Stores assessment results
   - Contains risk indices and recommendations

4. **Post**
   - Manages job postings
   - Tracks reach and click metrics

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone [git_url]
   cd secureer
   ```

2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone [git_url]
   cd secureer
   ```

2. Create and activate virtual environment:
   ```bash
   # Using virtualenv
   virtualenv2 --no-site-packages env
   source env/bin/activate

   # Or using conda
   conda env create -f environment.yml
   conda activate your_environment_name
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations and start server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. Navigate to `http://127.0.0.1:8000/risk_check/`

## Usage

1. Access the web interface
2. Enter your:
   - Name
   - Current position
   - Skills
3. Get personalized results:
   - Automation risk score
   - Recommended jobs
   - Suggested skills
   - Relevant job postings

## Machine Learning Components

- Job automation risk calculation
- Skill-based job matching
- Job recommendation system
- Skill gap analysis

## Documentation

- Jupyter notebook with model development: `Job_Automation_Risk_Prediction.ipynb`
- PDF documentation: `Job_Automation_Risk_Prediction_and_job_recommender_system.pdf`
- Presentation: `Job_Automation_Risk_Prediction_and_job_recommender_system_presentation.pdf`
- Video demonstration: `demo_vedio.mp4`

## Abstract

The increasing trend of computerization poses significant risks to the global job
market, particularly for roles that involve repetitive tasks. This project examines
the impact of computerization on the Myanmar job market using data sponsored
by MyJob, one of Myanmar's pioneer online job platforms, classifying job roles
based on their susceptibility to computerization. The project is grounded in Frey
and Osborne’s framework [1], which assigns probabilities to occupations based
on their likelihood of computerization. We develop a job recommender system
to assist individuals in exploring low-risk career paths and offer insights for
educational institutions and policymakers aiming to prepare the workforce for
an AI-driven economy.

## Future Improvements

1. Enhanced ML model accuracy
2. Real-time job market data integration
3. User feedback system
4. Advanced analytics dashboard
5. API endpoint development
6. Mobile application development