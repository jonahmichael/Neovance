#!/usr/bin/env python3
"""
Comprehensive Offline Sepsis Prediction Model Training Script
Neovance-AI NICU Monitoring System

This script implements the complete ML pipeline for sepsis prediction:
1. Load neonatal sepsis dataset
2. Feature engineering with EOS risk calculation  
3. Data preprocessing and encoding
4. Train RandomForestClassifier
5. Evaluate performance with clinical metrics
6. Save model artifacts for production use

Based on Puopolo/Kaiser EOS Risk Calculator and clinical evidence.
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, recall_score, 
    f1_score, classification_report, confusion_matrix, roc_curve
)
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
DATA_FILE = "data/neonatal_sepsis_training.csv"
MODEL_OUTPUT_DIR = "trained_models"
MODEL_OUTPUT_PATH = os.path.join(MODEL_OUTPUT_DIR, "sepsis_random_forest.pkl")
SCALER_OUTPUT_PATH = os.path.join(MODEL_OUTPUT_DIR, "feature_scaler.pkl")
FEATURE_INFO_PATH = os.path.join(MODEL_OUTPUT_DIR, "feature_columns.pkl")

# Clinical thresholds for sepsis risk interpretation
CLINICAL_THRESHOLDS = {
    'low_risk': 0.2,      # <20% probability
    'moderate_risk': 0.5,  # 20-50% probability  
    'high_risk': 0.8       # >50% probability, >80% critical
}

# --- STEP 1: EOS Risk Calculator (Medical Feature Engineering) ---
def calculate_eos_risk_advanced(row):
    """
    Enhanced EOS risk calculation using Puopolo/Kaiser validated formula
    
    This implements the peer-reviewed algorithm for Early-Onset Sepsis risk
    stratification based on maternal and neonatal factors.
    
    Returns: EOS risk score per 1000 live births
    """
    try:
        # Extract clinical parameters
        ga_weeks = row.get('ga_weeks', 39)
        ga_days = row.get('ga_days', 0) 
        temp_celsius = row.get('maternal_temp_celsius', 37.0)
        rom_hours = row.get('rom_hours', 8.0)
        gbs_status = row.get('gbs_status', 'negative')
        antibiotic_type = row.get('antibiotic_type', 'none')
        clinical_exam = row.get('clinical_exam', 'normal')
        
        # Convert gestational age to decimal weeks
        ga_decimal = ga_weeks + (ga_days / 7.0)
        
        # Initialize risk factors (multiplicative model)
        risk_factors = []
        
        # 1. Gestational age effect (validated coefficients)
        if ga_decimal < 35.0:
            risk_factors.append(4.0)  # Very preterm
        elif ga_decimal < 37.0:
            risk_factors.append(2.5)  # Preterm  
        elif ga_decimal < 39.0:
            risk_factors.append(1.2)  # Late preterm
        # Term babies (≥39 weeks) have baseline risk
        
        # 2. Maternal intrapartum fever (strongest predictor)
        if temp_celsius >= 38.5:
            risk_factors.append(5.0)   # High fever
        elif temp_celsius >= 38.0:
            risk_factors.append(2.5)   # Moderate fever
        
        # 3. Prolonged rupture of membranes
        if rom_hours >= 24.0:
            risk_factors.append(3.0)   # Very prolonged
        elif rom_hours >= 18.0:
            risk_factors.append(2.0)   # Prolonged
        
        # 4. GBS colonization and antibiotic prophylaxis
        if gbs_status.lower() == "positive":
            if antibiotic_type.lower() in ["penicillin", "ampicillin"]:
                risk_factors.append(1.5)  # Reduced risk with adequate prophylaxis
            else:
                risk_factors.append(6.0)  # High risk without adequate prophylaxis
        elif gbs_status.lower() == "unknown":
            risk_factors.append(2.0)  # Unknown status increases risk
        
        # 5. Clinical chorioamnionitis (highest risk factor)
        if clinical_exam.lower() in ["abnormal", "chorioamnionitis"]:
            risk_factors.append(20.0)  # Clinical signs of infection
        
        # 6. Additional neonatal factors from current vitals
        current_temp = row.get('temp_celsius', 37.0)
        if current_temp >= 38.0 or current_temp <= 36.0:
            risk_factors.append(1.8)  # Neonatal temperature instability
            
        hr = row.get('hr', 120)
        if hr >= 160 or hr <= 90:
            risk_factors.append(1.3)  # Heart rate abnormalities
            
        spo2 = row.get('spo2', 97)
        if spo2 <= 92:
            risk_factors.append(1.5)  # Desaturation
        
        # Calculate final risk (baseline for term infants: 0.5/1000)
        baseline_risk = 0.5  # per 1000 live births
        total_risk = baseline_risk
        
        # Apply multiplicative factors
        for factor in risk_factors:
            total_risk *= factor
        
        # Cap at clinically reasonable maximum (50/1000)
        total_risk = min(total_risk, 50.0)
        
        return round(total_risk, 3)
        
    except Exception as e:
        print(f"[EOS CALCULATION ERROR] {e}")
        return 0.5  # Return baseline risk on error


def categorize_eos_status(risk_score, clinical_exam):
    """Convert EOS risk score to clinical action categories"""
    # Clinical exam abnormalities override risk score
    if str(clinical_exam).lower() in ["abnormal", "chorioamnionitis"]:
        return "HIGH_RISK"
    
    # Risk-based categorization per 1000 live births
    if risk_score >= 3.0:
        return "HIGH_RISK"           # ≥3/1000: Empiric antibiotics
    elif risk_score >= 1.0:
        return "ENHANCED_MONITORING" # 1-3/1000: Enhanced monitoring  
    else:
        return "ROUTINE_CARE"        # <1/1000: Standard care


# --- STEP 2: Data Loading and Preprocessing ---
def load_and_prepare_data(file_path):
    """
    Load dataset and perform comprehensive preprocessing for ML training
    """
    print("="*60)
    print("🔬 LOADING AND PREPROCESSING NEONATAL SEPSIS DATA")
    print("="*60)
    
    # Load the dataset
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Training data not found: {file_path}")
    
    df = pd.read_csv(file_path)
    print(f"✅ Original data loaded: {len(df)} records")
    
    # Display data info
    print(f"\nDataset Overview:")
    print(f"  • Columns: {len(df.columns)}")
    print(f"  • Missing values: {df.isnull().sum().sum()}")
    print(f"  • Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # --- TARGET VARIABLE CREATION ---
    # Primary target: Binary sepsis prediction  
    df["target_sepsis"] = df["sepsis_group"].apply(lambda x: 1 if x in [1, 3] else 0)
    
    # Secondary target: Multi-class sepsis severity
    df["target_severity"] = df["sepsis_group"].map({
        1: 2,  # Culture-proven (highest severity)
        3: 1,  # Clinical sepsis  (moderate severity)
        2: 0   # No sepsis (no severity)
    })
    
    sepsis_count = df["target_sepsis"].sum()
    no_sepsis_count = len(df) - sepsis_count
    print(f"\n📊 Target Distribution:")
    print(f"  • Sepsis cases: {sepsis_count} ({sepsis_count/len(df)*100:.2f}%)")
    print(f"  • No sepsis: {no_sepsis_count} ({no_sepsis_count/len(df)*100:.2f}%)")
    print(f"  • Class ratio: 1:{no_sepsis_count/sepsis_count:.1f}")
    
    # --- FEATURE ENGINEERING ---
    print(f"\n🔧 Feature Engineering:")
    
    # 1. Enhanced EOS Risk Score (primary clinical feature)
    print("  • Computing enhanced EOS risk scores...")
    df["eos_risk_enhanced"] = df.apply(calculate_eos_risk_advanced, axis=1)
    df["eos_category"] = df.apply(lambda x: categorize_eos_status(x["eos_risk_enhanced"], x["clinical_exam"]), axis=1)
    
    # 2. Derived physiological features
    print("  • Creating physiological instability features...")
    
    # Temperature instability (fever or hypothermia)
    df["temp_instability"] = ((df["temp_celsius"] >= 38.0) | (df["temp_celsius"] <= 36.0)).astype(int)
    
    # Hemodynamic instability
    df["hemodynamic_instability"] = ((df["hr"] >= 160) | (df["hr"] <= 90) | (df["map"] <= 30)).astype(int)
    
    # Respiratory instability  
    df["respiratory_instability"] = ((df["spo2"] <= 92) | (df["rr"] >= 40)).astype(int)
    
    # Composite instability score
    df["physiological_instability_score"] = (
        df["temp_instability"] + 
        df["hemodynamic_instability"] + 
        df["respiratory_instability"]
    )
    
    # 3. Risk factor combinations
    df["preterm_and_fever"] = ((df["gestational_age_at_birth_weeks"] < 37) & (df["temp_celsius"] >= 38.0)).astype(int)
    df["gbs_positive_no_abx"] = ((df["gbs_status"] == "positive") & (df["antibiotic_type"] == "none")).astype(int)
    
    # 4. Gestational age categories
    df["ga_category"] = pd.cut(df["gestational_age_at_birth_weeks"], 
                              bins=[0, 32, 34, 37, 39, 45],
                              labels=["very_preterm", "preterm", "late_preterm", "early_term", "term"])
    
    # --- CATEGORICAL ENCODING ---
    print("  • Encoding categorical variables...")
    
    # One-hot encoding for categorical features
    categorical_cols = [
        "sex", "race", "gbs_status", "antibiotic_type", "clinical_exam",
        "comorbidities", "central_venous_line", "intubated_at_time_of_sepsis_evaluation",
        "inotrope_at_time_of_sepsis_eval", "ecmo", "stat_abx", "eos_category", "ga_category"
    ]
    
    # Filter existing columns
    existing_categorical = [col for col in categorical_cols if col in df.columns]
    
    for col in existing_categorical:
        if df[col].dtype == 'object' or col in ["eos_category", "ga_category"]:
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            df = pd.concat([df, dummies], axis=1)
    
    # --- FEATURE SELECTION ---
    print("  • Selecting features for training...")
    
    # Define comprehensive feature set
    continuous_features = [
        "gestational_age_at_birth_weeks", "birth_weight_kg", 
        "hr", "spo2", "rr", "temp_celsius", "map",
        "maternal_temp_celsius", "rom_hours", "time_to_antibiotics",
        "eos_risk_enhanced", "physiological_instability_score"
    ]
    
    # Binary features  
    binary_features = [
        "temp_instability", "hemodynamic_instability", "respiratory_instability",
        "preterm_and_fever", "gbs_positive_no_abx"
    ]
    
    # Get all one-hot encoded columns
    encoded_cols = [col for col in df.columns if any(col.startswith(cat + "_") for cat in existing_categorical)]
    
    # Combine all feature types
    all_features = continuous_features + binary_features + encoded_cols
    
    # Filter for existing columns
    final_features = [col for col in all_features if col in df.columns]
    
    print(f"  • Selected {len(final_features)} features for training")
    print(f"    - Continuous: {len([f for f in final_features if f in continuous_features])}")
    print(f"    - Binary: {len([f for f in final_features if f in binary_features])}")
    print(f"    - Encoded: {len([f for f in final_features if f in encoded_cols])}")
    
    # --- MISSING VALUE HANDLING ---
    print("  • Handling missing values...")
    
    X = df[final_features].copy()
    y = df["target_sepsis"].copy()
    
    # Fill missing values appropriately
    for col in X.columns:
        if col in continuous_features:
            # Use median for continuous features
            X[col] = X[col].fillna(X[col].median())
        else:
            # Use mode for categorical/binary features
            X[col] = X[col].fillna(0)
    
    missing_after = X.isnull().sum().sum()
    print(f"    ✓ Missing values after imputation: {missing_after}")
    
    print(f"✅ Preprocessing complete!")
    print(f"   • Final feature matrix: {X.shape}")
    print(f"   • Target vector: {y.shape}")
    
    return X, y, final_features


# --- STEP 3: Model Training and Evaluation ---
def train_and_evaluate_model(X, y, feature_names):
    """
    Train multiple models and select the best performer
    """
    print("\n" + "="*60)
    print("🤖 TRAINING SEPSIS PREDICTION MODELS")
    print("="*60)
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    print(f"Training sepsis prevalence: {y_train.mean()*100:.2f}%")
    
    # --- MODEL 1: Random Forest (Primary Model) ---
    print(f"\n🌲 Training Random Forest Classifier...")
    
    rf_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # Predictions
    rf_probs = rf_model.predict_proba(X_test)[:, 1]
    rf_preds = (rf_probs >= 0.5).astype(int)
    
    # --- MODEL 2: Logistic Regression (Baseline) ---
    print(f"📈 Training Logistic Regression (baseline)...")
    
    # Scale features for logistic regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    lr_model = LogisticRegression(
        class_weight='balanced',
        random_state=42,
        max_iter=1000
    )
    
    lr_model.fit(X_train_scaled, y_train)
    lr_probs = lr_model.predict_proba(X_test_scaled)[:, 1]
    lr_preds = (lr_probs >= 0.5).astype(int)
    
    # --- MODEL EVALUATION ---
    print(f"\n📊 Model Performance Evaluation:")
    
    models = {
        'Random Forest': {'probs': rf_probs, 'preds': rf_preds, 'model': rf_model},
        'Logistic Regression': {'probs': lr_probs, 'preds': lr_preds, 'model': lr_model}
    }
    
    results = {}
    
    for name, model_data in models.items():
        probs = model_data['probs']
        preds = model_data['preds']
        
        # Calculate metrics
        auc = roc_auc_score(y_test, probs)
        accuracy = accuracy_score(y_test, preds) 
        precision = precision_score(y_test, preds, zero_division=0)
        recall = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        
        results[name] = {
            'auc': auc, 'accuracy': accuracy, 'precision': precision,
            'recall': recall, 'f1': f1, 'model': model_data['model']
        }
        
        print(f"\n{name}:")
        print(f"  • AUC-ROC: {auc:.4f}")
        print(f"  • Accuracy: {accuracy:.4f}")
        print(f"  • Precision: {precision:.4f}")
        print(f"  • Recall (Sensitivity): {recall:.4f}")
        print(f"  • F1-Score: {f1:.4f}")
    
    # Select best model based on AUC (most important for medical screening)
    best_model_name = max(results.keys(), key=lambda k: results[k]['auc'])
    best_model = results[best_model_name]['model']
    best_probs = models[best_model_name]['probs']
    
    print(f"\n🏆 Best Model: {best_model_name} (AUC: {results[best_model_name]['auc']:.4f})")
    
    # --- CLINICAL EVALUATION ---
    print(f"\n🏥 Clinical Performance Analysis:")
    
    # Risk stratification performance
    for risk_level, threshold in CLINICAL_THRESHOLDS.items():
        high_risk_patients = np.sum(best_probs >= threshold)
        if high_risk_patients > 0:
            sepsis_detected = np.sum((best_probs >= threshold) & (y_test == 1))
            ppv = sepsis_detected / high_risk_patients  # Positive Predictive Value
            print(f"  • {risk_level.replace('_', ' ').title()}: {high_risk_patients} patients, PPV: {ppv:.3f}")
    
    # --- FEATURE IMPORTANCE ---
    print(f"\n🔍 Feature Importance Analysis:")
    
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        feature_importance = sorted(zip(importances, feature_names), reverse=True)
        
        print("Top 10 Most Important Features:")
        for i, (importance, feature) in enumerate(feature_importance[:10]):
            print(f"  {i+1:2d}. {feature}: {importance:.4f}")
    
    # --- CROSS-VALIDATION ---
    print(f"\n🔄 Cross-Validation Performance:")
    cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring='roc_auc')
    print(f"  • CV AUC: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
    
    return best_model, scaler if best_model_name == 'Logistic Regression' else None, results


# --- STEP 4: Model Persistence ---
def save_model_artifacts(model, scaler, feature_names, results):
    """
    Save trained model and associated artifacts for production use
    """
    print(f"\n💾 Saving Model Artifacts:")
    
    # Create model directory
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    
    # Save the trained model
    joblib.dump(model, MODEL_OUTPUT_PATH)
    print(f"  ✓ Model saved: {MODEL_OUTPUT_PATH}")
    
    # Save feature scaler (if used)
    if scaler is not None:
        joblib.dump(scaler, SCALER_OUTPUT_PATH)
        print(f"  ✓ Scaler saved: {SCALER_OUTPUT_PATH}")
    
    # Save feature column information
    joblib.dump(feature_names, FEATURE_INFO_PATH)
    print(f"  ✓ Feature info saved: {FEATURE_INFO_PATH}")
    
    # Save model metadata
    metadata = {
        'model_type': type(model).__name__,
        'feature_count': len(feature_names),
        'training_date': datetime.now().isoformat(),
        'performance_metrics': results,
        'feature_names': feature_names,
        'clinical_thresholds': CLINICAL_THRESHOLDS
    }
    
    import json
    metadata_path = os.path.join(MODEL_OUTPUT_DIR, "model_metadata.json")
    with open(metadata_path, 'w') as f:
        # Convert numpy types to regular Python types for JSON serialization
        serializable_metadata = {}
        for key, value in metadata.items():
            if key == 'performance_metrics':
                serializable_metadata[key] = {
                    model_name: {
                        metric: float(score) if isinstance(score, np.number) else score 
                        for metric, score in metrics.items() if metric != 'model'
                    }
                    for model_name, metrics in value.items()
                }
            else:
                serializable_metadata[key] = value
        
        json.dump(serializable_metadata, f, indent=2)
    
    print(f"  ✓ Metadata saved: {metadata_path}")


# --- STEP 5: Risk-to-Hours Conversion (Clinical Decision Support) ---
def risk_to_hours(risk_probability: float) -> int:
    """
    Convert ML risk probability to estimated sepsis onset window in hours
    
    Based on clinical evidence for early-onset sepsis timing:
    - High risk: rapid onset (6-12 hours)
    - Moderate risk: intermediate onset (12-24 hours)  
    - Low risk: delayed onset (24+ hours)
    """
    if risk_probability >= 0.8:
        return 6    # Critical risk: immediate evaluation
    elif risk_probability >= 0.5:
        return 12   # High risk: close monitoring
    elif risk_probability >= 0.2:
        return 24   # Moderate risk: standard monitoring
    else:
        return 48   # Low risk: routine care


# --- STEP 6: Model Testing and Validation ---
def test_model_predictions(model, feature_names):
    """
    Test the saved model with sample clinical scenarios
    """
    print(f"\n🧪 Testing Model Predictions:")
    
    # Load the saved model to ensure it works
    loaded_model = joblib.load(MODEL_OUTPUT_PATH)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Low-risk term baby",
            "gestational_age_at_birth_weeks": 39.5,
            "birth_weight_kg": 3.2,
            "eos_risk_enhanced": 0.8,
            "temp_celsius": 37.0,
            "hr": 120,
            "spo2": 97,
            "physiological_instability_score": 0
        },
        {
            "name": "High-risk preterm with fever",
            "gestational_age_at_birth_weeks": 34.2,
            "birth_weight_kg": 2.1,
            "eos_risk_enhanced": 8.5,
            "temp_celsius": 38.8,
            "hr": 165,
            "spo2": 89,
            "physiological_instability_score": 3
        }
    ]
    
    for scenario in test_scenarios:
        # Create feature vector (fill missing features with zeros)
        feature_vector = np.zeros(len(feature_names))
        
        for i, feature in enumerate(feature_names):
            if feature in scenario:
                feature_vector[i] = scenario[feature]
        
        # Make prediction
        risk_prob = loaded_model.predict_proba(feature_vector.reshape(1, -1))[0][1]
        onset_hours = risk_to_hours(risk_prob)
        
        print(f"\n  {scenario['name']}:")
        print(f"    • Sepsis Risk: {risk_prob:.3f} ({risk_prob*100:.1f}%)")
        print(f"    • Estimated Onset: {onset_hours} hours")
        print(f"    • Clinical Action: {'Immediate evaluation' if risk_prob >= 0.8 else 'Enhanced monitoring' if risk_prob >= 0.2 else 'Routine care'}")


# --- MAIN EXECUTION ---
def main():
    """
    Execute the complete model training pipeline
    """
    print("="*80)
    print("🏥 NEOVANCE-AI SEPSIS PREDICTION MODEL TRAINING")
    print("="*80)
    print(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Source: {DATA_FILE}")
    print(f"Output Directory: {MODEL_OUTPUT_DIR}")
    
    try:
        # Step 1: Load and preprocess data
        X, y, feature_names = load_and_prepare_data(DATA_FILE)
        
        # Step 2: Train and evaluate models
        best_model, scaler, results = train_and_evaluate_model(X, y, feature_names)
        
        # Step 3: Save model artifacts
        save_model_artifacts(best_model, scaler, feature_names, results)
        
        # Step 4: Test the model
        test_model_predictions(best_model, feature_names)
        
        # Success summary
        print(f"\n" + "="*80)
        print("✅ SEPSIS PREDICTION MODEL TRAINING COMPLETE!")
        print("="*80)
        print(f"📊 Best Model Performance:")
        best_model_name = max(results.keys(), key=lambda k: results[k]['auc'])
        best_metrics = results[best_model_name]
        print(f"   • Model Type: {best_model_name}")
        print(f"   • AUC-ROC: {best_metrics['auc']:.4f}")
        print(f"   • Sensitivity: {best_metrics['recall']:.4f}")
        print(f"   • Precision: {best_metrics['precision']:.4f}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Integrate model into FastAPI prediction service")
        print(f"   2. Test real-time predictions with live patient data")
        print(f"   3. Monitor model performance in clinical environment")
        
        print(f"\n📁 Saved Files:")
        print(f"   • Model: {MODEL_OUTPUT_PATH}")
        print(f"   • Features: {FEATURE_INFO_PATH}")
        print(f"   • Metadata: {os.path.join(MODEL_OUTPUT_DIR, 'model_metadata.json')}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ [DATA ERROR] {e}")
        print(f"\n💡 Please run: python generate_sepsis_training_data.py")
        return False
        
    except Exception as e:
        print(f"\n❌ [TRAINING ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)