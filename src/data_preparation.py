"""Data preparation helpers for the Amazon delivery analysis."""

from typing import Dict, Tuple

import numpy as np
import pandas as pd


TEXT_NULL_TOKENS = {"", "nan", "null", "none"}


def audit_raw_data(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return compact structural and missing-value audits for the raw data."""
    placeholder_counts: Dict[str, int] = {}
    for column in raw_df.select_dtypes(include="object").columns:
        normalized = raw_df[column].astype("string").str.strip().str.lower()
        placeholder_counts[column] = int(normalized.isin(TEXT_NULL_TOKENS).sum())

    audit_summary = pd.DataFrame(
        {
            "metric": [
                "Raw rows",
                "Raw columns",
                "Unique Order_ID values",
                "Duplicate Order_ID values",
                "Fully duplicated rows",
                "Minimum Delivery_Time",
                "Maximum Delivery_Time",
            ],
            "value": [
                len(raw_df),
                raw_df.shape[1],
                raw_df["Order_ID"].nunique(dropna=True),
                raw_df["Order_ID"].duplicated().sum(),
                raw_df.duplicated().sum(),
                raw_df["Delivery_Time"].min(),
                raw_df["Delivery_Time"].max(),
            ],
        }
    )

    missing_summary = pd.DataFrame(
        {
            "native_missing": raw_df.isna().sum(),
            "text_placeholder_missing": pd.Series(placeholder_counts),
        }
    ).fillna(0).astype(int)
    missing_summary = missing_summary.loc[missing_summary.sum(axis=1) > 0]

    return audit_summary, missing_summary


def clean_delivery_data(source_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Clean the delivery data conservatively and return a transformation log."""
    df = source_df.copy()
    cleaning_log: Dict[str, int] = {}

    text_columns = df.select_dtypes(include="object").columns
    text_placeholders_converted = 0
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()
        missing_token_mask = df[column].str.lower().isin(TEXT_NULL_TOKENS)
        text_placeholders_converted += int(missing_token_mask.sum())
        df.loc[missing_token_mask, column] = pd.NA

    cleaning_log["Text placeholders converted to missing"] = text_placeholders_converted
    df["Area"] = df["Area"].replace({"Metropolitian": "Metropolitan"})

    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    date_text = df["Order_Date"].dt.strftime("%Y-%m-%d")
    df["Order_Datetime"] = pd.to_datetime(
        date_text + " " + df["Order_Time"], errors="coerce"
    )
    df["Pickup_Datetime"] = pd.to_datetime(
        date_text + " " + df["Pickup_Time"], errors="coerce"
    )

    overnight_mask = (
        df["Order_Datetime"].notna()
        & df["Pickup_Datetime"].notna()
        & (df["Pickup_Datetime"] < df["Order_Datetime"])
    )
    df.loc[overnight_mask, "Pickup_Datetime"] += pd.Timedelta(days=1)
    cleaning_log["Pickup timestamps rolled into the next day"] = int(
        overnight_mask.sum()
    )

    invalid_rating_mask = (
        df["Agent_Rating"].notna() & ~df["Agent_Rating"].between(1, 5)
    )
    cleaning_log["Invalid ratings converted to missing"] = int(
        invalid_rating_mask.sum()
    )
    df.loc[invalid_rating_mask, "Agent_Rating"] = np.nan

    out_of_range_mask = (
        ~df["Store_Latitude"].between(-90, 90)
        | ~df["Drop_Latitude"].between(-90, 90)
        | ~df["Store_Longitude"].between(-180, 180)
        | ~df["Drop_Longitude"].between(-180, 180)
    )
    zero_origin_mask = df["Store_Latitude"].eq(0) & df["Store_Longitude"].eq(0)
    sign_mismatch_mask = ~zero_origin_mask & (
        (np.sign(df["Store_Latitude"]) != np.sign(df["Drop_Latitude"]))
        | (np.sign(df["Store_Longitude"]) != np.sign(df["Drop_Longitude"]))
    )
    df["Coordinate_Quality"] = np.select(
        [out_of_range_mask, zero_origin_mask, sign_mismatch_mask],
        ["out_of_range", "zero_origin_review", "sign_mismatch_review"],
        default="valid",
    )
    cleaning_log["Zero-origin coordinate records flagged"] = int(
        zero_origin_mask.sum()
    )
    cleaning_log["Coordinate sign-mismatch records flagged"] = int(
        sign_mismatch_mask.sum()
    )
    cleaning_log["Out-of-range coordinate records flagged"] = int(
        out_of_range_mask.sum()
    )

    rows_before = len(df)
    df = df.drop_duplicates().copy()
    cleaning_log["Exact duplicate rows removed"] = rows_before - len(df)

    return df, pd.Series(cleaning_log, name="record_count")


def _haversine_distance_km(
    lat1: pd.Series,
    lon1: pd.Series,
    lat2: pd.Series,
    lon2: pd.Series,
) -> np.ndarray:
    """Calculate great-circle distance with vectorized NumPy operations."""
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    latitude_delta = lat2_rad - lat1_rad
    longitude_delta = lon2_rad - lon1_rad
    a = (
        np.sin(latitude_delta / 2) ** 2
        + np.cos(lat1_rad)
        * np.cos(lat2_rad)
        * np.sin(longitude_delta / 2) ** 2
    )
    return 6_371.0088 * 2 * np.arcsin(np.sqrt(a))


def add_analysis_features(
    cleaned_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, float, pd.Series]:
    """Add distance, pickup period, and the supporting long-duration flag."""
    df = cleaned_df.copy()

    valid_coordinate_mask = df["Coordinate_Quality"].eq("valid")
    df["Distance_km"] = np.nan
    df.loc[valid_coordinate_mask, "Distance_km"] = _haversine_distance_km(
        df.loc[valid_coordinate_mask, "Store_Latitude"],
        df.loc[valid_coordinate_mask, "Store_Longitude"],
        df.loc[valid_coordinate_mask, "Drop_Latitude"],
        df.loc[valid_coordinate_mask, "Drop_Longitude"],
    )

    pickup_hour = df["Pickup_Datetime"].dt.hour
    df["Pickup_Period"] = pd.cut(
        pickup_hour,
        bins=[-1, 5, 11, 17, 23],
        labels=["Late Night", "Morning", "Afternoon", "Evening"],
    )

    long_delivery_threshold = float(df["Delivery_Time"].quantile(0.75))
    df["Long_Duration_Delivery"] = (
        df["Delivery_Time"] > long_delivery_threshold
    )

    feature_quality = pd.Series(
        {
            "Records with valid distance": df["Distance_km"].notna().sum(),
            "Records excluded from distance calculation": df["Distance_km"].isna().sum(),
            "Records with a defined pickup period": df["Pickup_Period"].notna().sum(),
            "Records without a defined pickup period": df["Pickup_Period"].isna().sum(),
        },
        name="record_count",
    )

    return df, long_delivery_threshold, feature_quality
