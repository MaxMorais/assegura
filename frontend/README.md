# ERPNext Test Automation Meta-Framework - Frontend

Streamlit frontend for the ERPNext Test Automation Meta-Framework providing an intuitive UI for consultants to manage personas, activities, journeys, and test execution.

## Requirements

- Python 3.11+  
- Backend API running on http://localhost:8000 (default)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API endpoint configuration
```

3. Start the Streamlit application:
```bash
streamlit run src/main.py
```

The application will be available at http://localhost:8501

## Development

### Code Quality
- **Linting**: `ruff check .`
- **Formatting**: `black .`

### Testing  
- **Unit Tests**: `pytest tests/unit/`
- **UI Tests**: `pytest tests/ui/` (Robot Framework)
- **All Tests**: `pytest`

### Architecture

The frontend follows modular Streamlit patterns with clear separation of concerns:

- **Components** (`src/components/`): Reusable UI components organized by domain
- **Pages** (`src/pages/`): Main application pages for different workflows  
- **Services** (`src/services/`): API client services for backend communication

### Constitutional Compliance

This frontend strictly follows the [Assegura Constitution](../../.specify/memory/constitution.md):

- ✅ **Streamlit-Based UI (NON-NEGOTIABLE)**: All UI components use Streamlit framework
- ✅ **Python 3.11+**: Required development language
- ✅ **Robot Framework**: Mandatory UI testing framework
- ✅ **Modular Components**: Reusable components following Streamlit session state patterns

## Features

### Persona Management
- Create and edit test personas with ERPNext roles and permissions
- View and manage persona collections
- Validate persona configurations

### Activity Definition  
- Define business activities linked to personas
- Associate activities with ERPNext modules
- Search and filter activities

### Journey Creation
- Build test journeys using drag-and-drop action library
- Sequence validation and step ordering
- Journey preview and validation

### Test Generation & Execution
- Generate Robot Framework tests from journeys
- Monitor cloud-based test execution  
- View test results and analytics
- Download test reports

## Configuration

Create `.env` file with:
```env
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
DEBUG=false
```