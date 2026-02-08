"""
Machine learning experiment support with sklearn pipelines.

This module provides the MLAnalyzer class for conducting machine learning
experiments with scikit-learn, including cross-validation, model evaluation,
and hyperparameter tuning.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import (
    train_test_split, KFold, StratifiedKFold,
    cross_val_score, cross_validate, GridSearchCV
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    mean_squared_error, mean_absolute_error, r2_score,
    explained_variance_score
)
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)


class MLAnalyzer:
    """
    Machine learning experiment analyzer with sklearn support.

    Provides methods for:
    - Train/test splitting with stratification
    - Cross-validation (k-fold, stratified k-fold)
    - Model evaluation metrics
    - Pipeline construction
    - Hyperparameter tuning
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize ML analyzer.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.results_history = []

    def train_test_split_data(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        test_size: float = 0.2,
        stratify: bool = False
    ) -> Tuple[Any, Any, Any, Any]:
        """
        Split data into train and test sets.

        Args:
            X: Features (DataFrame or array)
            y: Target variable (Series or array)
            test_size: Proportion of data for test set (default 0.2)
            stratify: If True, stratify split by target variable

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        stratify_param = y if stratify else None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=stratify_param
        )

        logger.info(f"Split data: train={len(X_train)}, test={len(X_test)} "
                   f"(test_size={test_size})")

        return X_train, X_test, y_train, y_test

    def cross_validate_model(
        self,
        model: Any,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        cv: int = 5,
        stratified: bool = False,
        scoring: Union[str, List[str]] = 'accuracy'
    ) -> Dict[str, Any]:
        """
        Perform cross-validation on a model.

        Args:
            model: sklearn estimator
            X: Features
            y: Target variable
            cv: Number of folds (default 5)
            stratified: If True, use StratifiedKFold
            scoring: Metric(s) to compute (string or list of strings)

        Returns:
            Dictionary with:
                - mean_score: Mean cross-validation score
                - std_score: Standard deviation of scores
                - fold_scores: Scores for each fold
                - scoring_metric: Name of scoring metric used
        """
        # Create cross-validation splitter
        if stratified:
            cv_splitter = StratifiedKFold(
                n_splits=cv,
                shuffle=True,
                random_state=self.random_state
            )
        else:
            cv_splitter = KFold(
                n_splits=cv,
                shuffle=True,
                random_state=self.random_state
            )

        # Handle multiple scoring metrics
        if isinstance(scoring, str):
            # Single metric
            scores = cross_val_score(
                model, X, y,
                cv=cv_splitter,
                scoring=scoring
            )

            result = {
                'mean_score': float(np.mean(scores)),
                'std_score': float(np.std(scores)),
                'fold_scores': scores.tolist(),
                'scoring_metric': scoring,
                'n_folds': cv
            }

        else:
            # Multiple metrics
            cv_results = cross_validate(
                model, X, y,
                cv=cv_splitter,
                scoring=scoring,
                return_train_score=True
            )

            result = {
                'scores': {
                    metric: {
                        'mean': float(np.mean(cv_results[f'test_{metric}'])),
                        'std': float(np.std(cv_results[f'test_{metric}'])),
                        'fold_scores': cv_results[f'test_{metric}'].tolist()
                    }
                    for metric in scoring
                },
                'scoring_metrics': scoring,
                'n_folds': cv
            }

        logger.info(f"Cross-validation complete: {cv} folds, "
                   f"stratified={stratified}")

        return result

    def evaluate_classification(
        self,
        y_true: Union[pd.Series, np.ndarray],
        y_pred: Union[pd.Series, np.ndarray],
        y_prob: Optional[np.ndarray] = None,
        average: str = 'binary'
    ) -> Dict[str, Any]:
        """
        Comprehensive classification model evaluation.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_prob: Predicted probabilities (optional, for ROC-AUC)
            average: Averaging method for multi-class ('binary', 'micro', 'macro', 'weighted')

        Returns:
            Dictionary with:
                - accuracy: Classification accuracy
                - precision: Precision score
                - recall: Recall score
                - f1_score: F1 score
                - roc_auc: ROC-AUC score (if y_prob provided)
                - confusion_matrix: Confusion matrix
                - classification_report: Detailed report string
        """
        # Auto-detect multiclass targets
        n_classes = len(np.unique(y_true))
        if average == 'binary' and n_classes > 2:
            average = 'weighted'
            logger.info(f"Auto-switched to average='weighted' for {n_classes}-class target")

        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average=average, zero_division=0)
        recall = recall_score(y_true, y_pred, average=average, zero_division=0)
        f1 = f1_score(y_true, y_pred, average=average, zero_division=0)
        conf_matrix = confusion_matrix(y_true, y_pred)
        class_report = classification_report(y_true, y_pred, zero_division=0)

        result = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': conf_matrix.tolist(),
            'classification_report': class_report,
            'n_samples': len(y_true)
        }

        # Add ROC-AUC if probabilities provided
        if y_prob is not None:
            try:
                # Handle binary and multi-class
                if y_prob.ndim == 1 or y_prob.shape[1] == 2:
                    # Binary classification
                    if y_prob.ndim == 2:
                        y_prob = y_prob[:, 1]
                    roc_auc = roc_auc_score(y_true, y_prob)
                else:
                    # Multi-class
                    roc_auc = roc_auc_score(y_true, y_prob, multi_class='ovr', average=average)

                result['roc_auc'] = float(roc_auc)
            except Exception as e:
                logger.warning(f"Could not calculate ROC-AUC: {e}")
                result['roc_auc'] = None

        logger.info(f"Classification evaluation: accuracy={accuracy:.4f}, "
                   f"f1={f1:.4f}")

        return result

    def evaluate_regression(
        self,
        y_true: Union[pd.Series, np.ndarray],
        y_pred: Union[pd.Series, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Comprehensive regression model evaluation.

        Args:
            y_true: True values
            y_pred: Predicted values

        Returns:
            Dictionary with:
                - mse: Mean squared error
                - rmse: Root mean squared error
                - mae: Mean absolute error
                - r2: R-squared score
                - explained_variance: Explained variance score
                - mean_residual: Mean of residuals
                - std_residual: Standard deviation of residuals
        """
        # Calculate metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        explained_var = explained_variance_score(y_true, y_pred)

        # Residual analysis
        residuals = np.array(y_true) - np.array(y_pred)
        mean_residual = np.mean(residuals)
        std_residual = np.std(residuals)

        result = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'explained_variance': float(explained_var),
            'mean_residual': float(mean_residual),
            'std_residual': float(std_residual),
            'n_samples': len(y_true)
        }

        logger.info(f"Regression evaluation: R²={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")

        return result

    def create_pipeline(
        self,
        model: Any,
        scaler: str = 'standard',
        include_scaler: bool = True
    ) -> Pipeline:
        """
        Create sklearn pipeline with preprocessing and model.

        Args:
            model: sklearn estimator
            scaler: Type of scaler ('standard', 'minmax', or None)
            include_scaler: If True, include scaler in pipeline

        Returns:
            sklearn Pipeline object
        """
        steps = []

        if include_scaler:
            if scaler == 'standard':
                steps.append(('scaler', StandardScaler()))
            elif scaler == 'minmax':
                steps.append(('scaler', MinMaxScaler()))
            elif scaler is not None:
                raise ValueError(f"Unknown scaler '{scaler}'. Use 'standard' or 'minmax'")

        steps.append(('model', model))

        pipeline = Pipeline(steps)

        logger.info(f"Created pipeline with {len(steps)} steps: {[s[0] for s in steps]}")

        return pipeline

    def grid_search(
        self,
        model: Any,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        param_grid: Dict[str, List],
        cv: int = 5,
        scoring: str = 'accuracy',
        stratified: bool = False
    ) -> Dict[str, Any]:
        """
        Perform grid search for hyperparameter tuning.

        Args:
            model: sklearn estimator
            X: Features
            y: Target variable
            param_grid: Dictionary of parameter names and values to try
            cv: Number of cross-validation folds
            scoring: Metric to optimize
            stratified: If True, use stratified k-fold

        Returns:
            Dictionary with:
                - best_params: Best parameters found
                - best_score: Best cross-validation score
                - best_estimator: Fitted estimator with best parameters
                - cv_results: Detailed CV results
        """
        # Create cross-validation splitter
        if stratified:
            cv_splitter = StratifiedKFold(
                n_splits=cv,
                shuffle=True,
                random_state=self.random_state
            )
        else:
            cv_splitter = KFold(
                n_splits=cv,
                shuffle=True,
                random_state=self.random_state
            )

        # Perform grid search
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=cv_splitter,
            scoring=scoring,
            n_jobs=-1,  # Use all CPU cores
            verbose=0
        )

        grid_search.fit(X, y)

        result = {
            'best_params': grid_search.best_params_,
            'best_score': float(grid_search.best_score_),
            'best_estimator': grid_search.best_estimator_,
            'cv_results': {
                'mean_test_scores': grid_search.cv_results_['mean_test_score'].tolist(),
                'std_test_scores': grid_search.cv_results_['std_test_score'].tolist(),
                'params': grid_search.cv_results_['params']
            },
            'n_combinations_tested': len(grid_search.cv_results_['params'])
        }

        logger.info(f"Grid search complete: tested {result['n_combinations_tested']} "
                   f"parameter combinations. Best score: {result['best_score']:.4f}")

        return result

    def run_experiment(
        self,
        model: Any,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        test_size: float = 0.2,
        cv: int = 5,
        stratified: bool = False,
        task_type: str = 'classification',
        scale_features: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete ML experiment with train/test split and cross-validation.

        Args:
            model: sklearn estimator
            X: Features
            y: Target variable
            test_size: Proportion for test set
            cv: Number of cross-validation folds
            stratified: If True, use stratified splits
            task_type: 'classification' or 'regression'
            scale_features: If True, scale features before modeling

        Returns:
            Dictionary with:
                - train_test_results: Evaluation on test set
                - cv_results: Cross-validation results
                - model: Fitted model on full training data
                - feature_importance: Feature importance (if available)
        """
        # Split data
        X_train, X_test, y_train, y_test = self.train_test_split_data(
            X, y, test_size=test_size, stratify=stratified
        )

        # Create pipeline if scaling requested
        if scale_features:
            pipeline = self.create_pipeline(model, scaler='standard')
        else:
            pipeline = model

        # Train model
        pipeline.fit(X_train, y_train)

        # Predictions
        y_pred = pipeline.predict(X_test)

        # Get probabilities for classification
        y_prob = None
        if task_type == 'classification' and hasattr(pipeline, 'predict_proba'):
            y_prob = pipeline.predict_proba(X_test)

        # Evaluate on test set
        if task_type == 'classification':
            test_results = self.evaluate_classification(y_test, y_pred, y_prob)
        else:
            test_results = self.evaluate_regression(y_test, y_pred)

        # Cross-validation on training data
        scoring = 'accuracy' if task_type == 'classification' else 'r2'
        cv_results = self.cross_validate_model(
            pipeline, X_train, y_train,
            cv=cv, stratified=stratified, scoring=scoring
        )

        # Feature importance (if available)
        feature_importance = None
        if hasattr(pipeline, 'feature_importances_'):
            feature_importance = pipeline.feature_importances_.tolist()
        elif hasattr(pipeline, 'coef_'):
            feature_importance = pipeline.coef_.tolist()

        result = {
            'train_test_results': test_results,
            'cv_results': cv_results,
            'model': pipeline,
            'feature_importance': feature_importance,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'n_features': X.shape[1] if hasattr(X, 'shape') else len(X[0])
        }

        # Add to history
        self.results_history.append({
            'timestamp': pd.Timestamp.now(),
            'task_type': task_type,
            'test_score': test_results.get('accuracy') or test_results.get('r2'),
            'cv_mean_score': cv_results.get('mean_score')
        })

        logger.info(f"ML experiment complete: task={task_type}, "
                   f"test_score={result['train_test_results'].get('accuracy') or result['train_test_results'].get('r2'):.4f}")

        return result


class FeatureEngineering:
    """
    Utility class for feature engineering operations.
    """

    @staticmethod
    def encode_categorical(
        df: pd.DataFrame,
        columns: List[str],
        method: str = 'label'
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Encode categorical variables.

        Args:
            df: DataFrame with categorical columns
            columns: List of categorical column names
            method: 'label' for label encoding, 'onehot' for one-hot encoding

        Returns:
            Tuple of (encoded DataFrame, encoding_info dict)
        """
        df_encoded = df.copy()
        encoding_info = {}

        if method == 'label':
            for col in columns:
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(df[col])
                encoding_info[col] = {
                    'encoder': le,
                    'classes': le.classes_.tolist()
                }

        elif method == 'onehot':
            df_encoded = pd.get_dummies(df, columns=columns, drop_first=True)
            encoding_info['method'] = 'onehot'
            encoding_info['original_columns'] = columns
            encoding_info['new_columns'] = [c for c in df_encoded.columns if c not in df.columns]

        else:
            raise ValueError(f"Unknown method '{method}'. Use 'label' or 'onehot'")

        logger.info(f"Encoded {len(columns)} categorical columns using {method} encoding")

        return df_encoded, encoding_info

    @staticmethod
    def create_polynomial_features(
        X: Union[pd.DataFrame, np.ndarray],
        degree: int = 2
    ) -> np.ndarray:
        """
        Create polynomial features.

        Args:
            X: Features
            degree: Polynomial degree

        Returns:
            Array with polynomial features
        """
        from sklearn.preprocessing import PolynomialFeatures

        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)

        logger.info(f"Created polynomial features: degree={degree}, "
                   f"features={X.shape[1]}→{X_poly.shape[1]}")

        return X_poly

    @staticmethod
    def select_k_best_features(
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        k: int = 10,
        score_func: str = 'f_classif'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Select k best features using univariate statistical tests.

        Args:
            X: Features
            y: Target variable
            k: Number of features to select
            score_func: Scoring function ('f_classif', 'f_regression', 'chi2')

        Returns:
            Tuple of (selected features, feature scores)
        """
        from sklearn.feature_selection import SelectKBest, f_classif, f_regression, chi2

        # Map score function name to function
        score_funcs = {
            'f_classif': f_classif,
            'f_regression': f_regression,
            'chi2': chi2
        }

        if score_func not in score_funcs:
            raise ValueError(f"Unknown score_func '{score_func}'. "
                           f"Use one of: {list(score_funcs.keys())}")

        selector = SelectKBest(score_func=score_funcs[score_func], k=k)
        X_selected = selector.fit_transform(X, y)
        scores = selector.scores_

        logger.info(f"Selected {k} best features using {score_func}")

        return X_selected, scores
