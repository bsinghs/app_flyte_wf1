from flytekit import task, workflow, Resources, CronSchedule, LaunchPlan
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import logging
from config import CREDIT_SCORING_DATA_PATH


@task(
    requests=Resources(cpu="800m", mem="800Mi"), 
    limits=Resources(cpu="1.5", mem="1.5Gi"),
    container_image="ghcr.io/flyteorg/flytekit:py3.9-1.10.3"  # Use prebuilt flytekit image
)
def load_and_train_model(data_path: str) -> float:
    """Simple task that loads data, trains model, and returns accuracy"""
    logger = logging.getLogger(__name__)
    
    # Load data
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Clean data
    df_clean = df.dropna()
    
    # Extract features and target
    if "Status" not in df_clean.columns:
        raise ValueError("Expected column 'Status' not found in data")
    
    y = df_clean.pop("Status")
    X = pd.get_dummies(df_clean)
    
    # Train model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    
    logger.info(f"Model accuracy: {accuracy}")
    return float(accuracy)


@workflow
def simple_daily_ml_workflow() -> float:
    """Simple workflow for daily ML training and evaluation"""
    accuracy = load_and_train_model(data_path=CREDIT_SCORING_DATA_PATH)
    return accuracy


# Create scheduled launch plan - runs at 8 PM UTC daily
daily_ml_schedule = LaunchPlan.create(
    "daily_ml_at_8pm",
    simple_daily_ml_workflow,
    schedule=CronSchedule("0 20 * * ? *")  # minute hour day month dayofweek year
)


# Alternative workflow with configurable data path
@workflow
def configurable_ml_workflow(data_path: str = CREDIT_SCORING_DATA_PATH) -> float:
    """ML workflow with configurable data path"""
    accuracy = load_and_train_model(data_path=data_path)
    return accuracy


# Create another scheduled launch plan for the configurable workflow
daily_configurable_schedule = LaunchPlan.create(
    "daily_configurable_ml",
    configurable_ml_workflow,
    schedule=CronSchedule("0 20 * * ? *"),
    default_inputs={"data_path": "/path/to/your/daily/data.csv"}  # <-- Change this path
)

# Additional launch plans for different data sources
weekly_report_schedule = LaunchPlan.create(
    "weekly_report_ml",
    configurable_ml_workflow,
    schedule=CronSchedule("0 20 * * 0 *"),  # Every Sunday at 8 PM
    default_inputs={"data_path": "/path/to/weekly/report/data.csv"}
)

monthly_analysis_schedule = LaunchPlan.create(
    "monthly_analysis_ml",
    configurable_ml_workflow,
    schedule=CronSchedule("0 20 1 * ? *"),  # 1st day of every month at 8 PM
    default_inputs={"data_path": "/path/to/monthly/analysis/data.csv"}
)
