# AI Request Complexity Predictor

The Complexity Predictor is a classical machine learning prototype designed for request complexity estimation within an AI Model Routing Framework. In modern multi-model AI systems, routing every request to a high-capacity model causes unnecessary latency and operational costs, while routing complex requests to smaller models leads to degraded response quality. To solve this problem, the Complexity Predictor estimates the expected workload complexity of an incoming AI request—combining the prompt text, attachment metadata, conversation context, task category, and expected output format—*before* downstream routing occurs. It categorizes each request into a discrete complexity tier (`Low`, `Medium`, `High`), assigns a continuous score (0–100), and reports a prediction confidence metric.

---

## Motivation

Modern AI systems often use multiple models with different costs and capabilities. Rather than routing every request to the largest available model, this project estimates request complexity before inference, enabling downstream routing systems to make more informed routing decisions.

---

## Features

- **Holistic AI Request Parsing**: Evaluates full request context, including user prompts, uploaded file metadata, multi-turn conversation history, task categories, and requested output formats.
- **Rich Handcrafted Feature Set**: Extracts structural, lexical, domain-complexity, scale-regex, and objective-diversity metrics using an extensive handcrafted feature engineering pipeline without external NLP packages.
- **Classical Supervised Machine Learning**: Utilizes transparent, lightweight tabular machine learning algorithms rather than resource-heavy deep learning or semantic embedding models.
- **Supervised Classifier Benchmarking**: Features an automated benchmarking suite evaluating multiple ensemble algorithms (Random Forest, Extra Trees, Gradient Boosting, XGBoost) using identical 5-fold Stratified Cross-Validation.
- **Interactive AI Request Builder CLI**: Provides a command-line interface simulating real-world request construction and non-interactive demonstration execution.
- **Automated Complexity Profile Generation**: Outputs standardized JSON response payloads containing complexity classification, numeric workload score, and model confidence.
- **Lightweight Dependency Footprint**: Operates without LLMs, neural networks, sentence transformers, TF-IDF, or external web service dependencies.

---

## Architecture

The prototype enforces an independent, 8-stage conceptual processing pipeline:

$$\text{Incoming AI Request} \longrightarrow \text{Request Analysis} \longrightarrow \text{Structured Request} \longrightarrow \text{Feature Extraction} \longrightarrow \text{Feature Vector} \longrightarrow \text{Data Preprocessing} \longrightarrow \text{Machine Learning Model} \longrightarrow \text{Complexity Profile}$$

### How It Works

1. **Incoming AI Request**: An upstream application submits a raw request dictionary containing prompt text, attachment metadata, conversation history, task category, and output preferences.
2. **Request Analyzer**: Normalizes and structures the raw input payload into an internal domain object (`StructuredRequest`) without performing feature calculations.
3. **Structured Request**: Serves as the clean internal representation of the complete AI request payload across all pipeline stages.
4. **Feature Extraction**: Computes numerical and categorical signals (e.g., domain complexity vocabulary scores, document scale regex indicators, action verb diversity, technology counts) to produce a `FeatureVector`.
5. **Data Preprocessing**: Fits and transforms feature matrices using standard numerical scaling and one-hot categorical encoding (`ColumnTransformer`).
6. **Machine Learning Model**: Processes the encoded feature matrix through a trained supervised classifier to compute class probabilities.
7. **Complexity Profile**: Formats prediction probabilities into a standardized JSON response containing the complexity label, numeric score (0–100), and confidence score.

---

## Project Structure

```text
complexity_predictor/
│
├── src/                        # Core Python source modules
│   ├── request_analyzer.py     # Structural request parser and dataclass definitions
│   ├── feature_extractor.py    # Handcrafted feature engineering module
│   ├── preprocessor.py         # Feature scaling and one-hot categorical encoder
│   ├── generator.py            # Component-based scenario dataset generator
│   └── model.py                # Supervised classifier lifecycle and inference engine
│
├── scripts/                    # Command-line entry points
│   ├── train.py                # Model training, cross-validation, and benchmarking runner
│   └── predict.py              # Interactive AI Request Builder CLI and demo interface
│
├── models/                     # Serialized production pipeline artifacts
│   └── predictor_pipeline.joblib
│
├── data/                       # Extracted feature dataset exports
│   └── dataset.csv
│
├── docs/                       # Architectural design documentation
│
├── requirements.txt            # Python dependencies (scikit-learn, pandas, numpy, joblib)
└── README.md                   # Project documentation
```

---

## Tech Stack

- **Python**: 3.10+
- **scikit-learn**: Classical machine learning algorithms, preprocessing transformers, and cross-validation metrics
- **pandas**: Tabular data manipulation and CSV feature vector storage
- **NumPy**: Matrix operations and probability score calculations
- **joblib**: Serialization and loading of fitted preprocessor and model pipeline artifacts
- **XGBoost**: *(Optional dependency used only for benchmarking)* Gradient boosting framework

---

## Setup

### Prerequisites
- Python 3.10 or higher

### Installation
Clone the repository and install required dependencies:
```bash
pip install -r requirements.txt
```

---

## Training and Benchmarking

To generate the training dataset, extract features, benchmark candidate machine learning models using 5-fold Stratified Cross-Validation, print qualitative validation matrices, automatically select the production classifier, and serialize the prediction pipeline:

```bash
python scripts/train.py
```

---

## Prediction

### Interactive CLI Mode
To build and evaluate custom AI requests interactively step-by-step:
```bash
python scripts/predict.py
```

### Non-Interactive Demo Mode
To execute a pre-configured sample request through the prediction pipeline:
```bash
python scripts/predict.py --demo
```

---

## Example Input and Output

### Constructed Raw AI Request Payload
```json
{
    "prompt": "Design and implement a FastAPI microservice using PostgreSQL, Redis, JWT authentication, Docker, and unit tests.",
    "attachments": [],
    "conversation_context": {
        "turns": 0
    },
    "metadata": {
        "task_category": "Programming"
    },
    "expected_output": {
        "format": "code"
    }
}
```

### Generated Complexity Profile Response
```json
{
    "complexity": "High",
    "complexity_score": 68,
    "confidence": 0.69
}
```

---

## Classifier Benchmarking

To select the most effective production model, multiple tree-based ensemble algorithms were benchmarked under identical 5-fold Stratified Cross-Validation on the generated tabular dataset.

### Benchmark Evaluation Summary

| Classifier | Benchmarked | Notes |
| :--- | :---: | :--- |
| **Random Forest** | ✓ | Selected production classifier |
| **Extra Trees** | ✓ | Comparable benchmark performance |
| **Gradient Boosting** | ✓ | Comparable benchmark performance |
| **XGBoost** | ✓ | Benchmarked as an optional third-party dependency |

### Qualitative Validation

To evaluate model behavior beyond quantitative metrics, a representative qualitative validation suite covering multiple enterprise request domains (software engineering, document analysis, translation, code generation, and multi-step reasoning) was executed. Model selection considered both 5-fold cross-validation performance and qualitative consistency across these benchmark scenarios.

---

## Model Selection

**Selected Classifier**: `RandomForestClassifier` (`n_estimators=200`, `random_state=42`)

### Selection Rationale
- **Technical Honesty**: Cross-validation metrics across all benchmarked algorithms on the synthetic tabular dataset are virtually identical ($\Delta \le 0.01$). Selecting a complex third-party library based on marginal synthetic deltas would be technically unjustified.
- **Qualitative Reliability**: Random Forest demonstrated the most consistent alignment with human reference judgments, correctly classifying short-but-hard systems prompts (*Linux Scheduler*, *Compiler Design*) and scale-heavy document tasks (*600-page Legal Document*, *GDPR Audit*).
- **Maintainability & Portability**: Operates natively within standard `scikit-learn` without introducing external C++ binary compilation dependencies (e.g., `xgboost` DLLs), minimizing deployment overhead.

---

## Limitations

- **Handcrafted Features**: Relies on explicit string parsing, keyword matching, and regex metrics rather than deep semantic embeddings or transformer representations.
- **Synthetic Training Data**: Trained on programmatically generated enterprise AI request scenarios designed to represent common workload patterns rather than production traffic logs.
- **Estimated Workload vs. Compute Cost**: Predicts human-perceived task complexity (`Low`, `Medium`, `High`) rather than exact GPU/CPU FLOP requirements or execution latency.
- **Current Scope**: Intended as a lightweight request complexity estimator within a broader model routing architecture rather than an end-to-end routing infrastructure.

---

## Future Work

- **Evaluation on Real Enterprise Logs**: Evaluate and fine-tune training datasets using real enterprise request traffic logs.
- **Richer Handcrafted Features**: Expand the handcrafted feature engineering pipeline to capture specialized domain metrics and structural patterns.
- **Improved Workload Heuristics**: Refine domain vocabulary and workload scale heuristics for edge-case requests.
- **Routing Gateway Integration**: Connect the complexity predictor directly into a live model routing engine gateway.
- **Optional Semantic Exploration**: Optionally explore combining lightweight handcrafted features with compact, low-overhead semantic representations.
