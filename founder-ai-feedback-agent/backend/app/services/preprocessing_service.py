"""
Data cleaning and preprocessing pipeline.
Handles deduplication, normalization, special character removal.
"""
import re
import hashlib
from typing import Any
import pandas as pd
import numpy as np
from loguru import logger


class PreprocessingService:
    """Cleans raw feedback text before NLP analysis."""

    SPECIAL_CHAR_PATTERN = re.compile(r"[^\w\s.,!?;:'-]", re.UNICODE)
    WHITESPACE_PATTERN = re.compile(r'\s+')
    URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
    EMAIL_PATTERN = re.compile(r'\S+@\S+\.\S+')

    def clean_text(self, text: str) -> str | None:
        """Full text cleaning pipeline."""
        if not text or not isinstance(text, str):
            return None
        # Remove URLs and emails
        text = self.URL_PATTERN.sub(' ', text)
        text = self.EMAIL_PATTERN.sub(' ', text)
        # Remove special characters (keep basic punctuation)
        text = self.SPECIAL_CHAR_PATTERN.sub(' ', text)
        # Normalize whitespace
        text = self.WHITESPACE_PATTERN.sub(' ', text).strip()
        # Minimum length check
        if len(text) < 5:
            return None
        return text

    def normalize_text(self, text: str) -> str:
        """Lowercase and normalize unicode."""
        import unicodedata
        text = unicodedata.normalize('NFKD', text)
        return text.lower().strip()

    def fingerprint(self, text: str) -> str:
        """SHA256 fingerprint for deduplication."""
        normalized = self.normalize_text(text)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def process_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Clean an entire feedback DataFrame.
        Returns cleaned df + stats dict.
        """
        original_count = len(df)
        stats = {
            'original_count': original_count,
            'empty_removed': 0,
            'duplicates_removed': 0,
            'cleaned_count': 0,
            'errors': [],
        }

        # Standardize column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        # Map common column aliases
        col_map = {
            'id': 'feedback_id',
            'text': 'feedback_text',
            'comment': 'feedback_text',
            'review': 'feedback_text',
            'score': 'rating',
            'stars': 'rating',
            'user_id': 'customer_id',
            'date': 'feedback_date',
            'timestamp': 'feedback_date',
            'created_at': 'feedback_date',
        }
        df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

        # Require feedback_text
        if 'feedback_text' not in df.columns:
            raise ValueError('Dataset must contain a feedback_text (or text/comment/review) column')

        # Drop empty feedback
        mask_empty = df['feedback_text'].isna() | (df['feedback_text'].astype(str).str.strip() == '')
        stats['empty_removed'] = int(mask_empty.sum())
        df = df[~mask_empty].copy()

        # Drop duplicates by fingerprint
        df['_fingerprint'] = df['feedback_text'].astype(str).apply(self.fingerprint)
        before_dedup = len(df)
        df.drop_duplicates(subset=['_fingerprint'], inplace=True)
        stats['duplicates_removed'] = before_dedup - len(df)
        df.drop(columns=['_fingerprint'], inplace=True)

        # Clean feedback_text
        df['cleaned_text'] = df['feedback_text'].astype(str).apply(self.clean_text)

        # Drop rows where cleaning returned None
        null_after_clean = df['cleaned_text'].isna().sum()
        df = df[df['cleaned_text'].notna()].copy()
        stats['empty_removed'] += int(null_after_clean)

        # Normalize rating
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            # Normalize to 1-5 if values > 5 (e.g. out of 10)
            max_rating = df['rating'].max()
            if pd.notna(max_rating) and max_rating > 5:
                df['rating'] = (df['rating'] / max_rating) * 5

        # Parse dates
        if 'feedback_date' in df.columns:
            df['feedback_date'] = pd.to_datetime(df['feedback_date'], errors='coerce')

        # Fill missing customer_id
        if 'customer_id' not in df.columns:
            df['customer_id'] = None
        if 'feedback_id' not in df.columns:
            df['feedback_id'] = None
        if 'feedback_date' not in df.columns:
            df['feedback_date'] = None
        if 'rating' not in df.columns:
            df['rating'] = None

        stats['cleaned_count'] = len(df)
        df.reset_index(drop=True, inplace=True)
        logger.info(f'Preprocessing done: {stats}')
        return {'dataframe': df, 'stats': stats}

    def parse_upload_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse CSV, XLSX, or JSON upload into a DataFrame."""
        import io
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(io.BytesIO(file_content))
        elif ext in ('xlsx', 'xls'):
            df = pd.read_excel(io.BytesIO(file_content))
        elif ext == 'json':
            df = pd.read_json(io.BytesIO(file_content))
        else:
            raise ValueError(f'Unsupported file format: {ext}')
        return df


preprocessing_service = PreprocessingService()
