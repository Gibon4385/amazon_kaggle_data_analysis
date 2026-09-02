[English](README.md) | [繁體中文](README-zh.md)

# Amazon Delivery Operations Analysis

> **Project Overview**  
> This project uses Kaggle's Amazon Delivery dataset to demonstrate how to convert **vague business problems** into **concrete data analysis**, **KPI metrics**, and **actionable decisions**. The focus is on business logic, hypothesis testing, data quality, and operational feasibility, rather than just building machine learning models.
> 
> 📊 **Slide Deck**: An interactive slide presentation built with **OpenSlide** is available in the [`slides/`](slides/) folder for a quick visual summary.

---

## 1. Data Source

- **Source**: [Kaggle - Amazon Delivery Dataset](https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset/data)
- **Scale**: 43,000+ delivery records including order details, agent ratings, weather, traffic conditions, and delivery duration.

---

## 2. Business Problem & Workflow

### 2.1 From Vague Problem ➡️ Concrete Analysis
* **Original Business Problem**: The operations team noticed that "some deliveries take too long." With limited operational resources, which delivery segment should we focus on first?
* **Breakdown into Analytical Questions**:
  1. **Where are long deliveries concentrated?** Compare delivery times across Area, Traffic, Pickup Period, Distance, Weather, and Category.
  2. **Are observed group differences practically meaningful?** Look at sample size, median, IQR, and the long-duration delivery rate (P75), not just p-values.
  3. **Can extreme regional differences be explained by known factors?** Focus on Semi-Urban areas and examine traffic and distance composition.
  4. **Do correlations remain stable after controlling for other factors?** Use a multivariate OLS regression model with HC3 robust standard errors to control for confounding variables.
  5. **Which factor is worth taking action on first?** Rank priorities based on effect size, data stability, and operational feasibility.

### 2.2 Analytical Thought Process
```
[Vague Business Problem] Deliveries take too long. Where should we invest resources?
       ↓
[KPI & Metrics Definition] Primary KPI: Delivery Time (Median / IQR) | Secondary: P75 Long-Duration Rate
       ↓
[Data Cleaning & Audit] Clean 43k+ records (coordinates, overnight times, rating bounds, no forced imputation)
       ↓
[Exploratory & Group Analysis] Identify Semi-Urban as the high-duration outlier area
       ↓
[Multivariate Control] OLS + HC3 Robust Errors (control for Traffic, Distance, Category)
       ↓
[Decision & Action Plan] Prioritize Semi-Urban process diagnosis with small-scale tests
```

---

## 3. KPI & Metrics Definition

To prevent extreme values from distorting results, this project uses a multi-metric approach:
* **Primary KPI: `Delivery_Time` (Total delivery time in minutes)**
  * Evaluated using the **Median**, **Interquartile Range (IQR)**, and full distribution shapes to avoid mean bias.
* **Secondary Metric: `Long-Duration Delivery Rate`**
  * Deliveries exceeding the overall 75th percentile (160 minutes) are flagged as long-duration deliveries to measure tail risk. (*Note: This is a relative threshold, not a strict SLA or promised ETA*).

---

## 4. Data Quality & Cleaning

Data cleaning logic is centralized in `src/data_preparation.py`:
* **Rating Outliers**: 53 records with ratings outside 1–5 were set to NA, while keeping their delivery records.
* **Midnight Timestamp Correction**: Fixed 828 records with pickup times crossing midnight.
* **Coordinate Validation**: Identified 3,693 records with zero-origin coordinates or sign errors. Excluded them from distance calculations to avoid bias while preserving total sample size.
* **Missing Values**: Text missing values (e.g., "NaN") were converted to true NA without forced imputation.

---

## 5. Data Analysis & Key Insights

1. **Semi-Urban Areas Suffer from Heavy Bottlenecks**
   * Semi-Urban delivery time has a median of **245 minutes** (compared to 125–126 minutes for Urban/Metropolitan), with **94.7%** of orders classified as long-duration deliveries (>160 mins).
2. **Traffic and Distance Cannot Explain the Gap**
   * Even under identical Traffic (Jam) conditions, Semi-Urban deliveries remain significantly slower.
   * In a multivariate OLS regression controlling for Distance, Traffic, Period, Weather, and Category, Semi-Urban deliveries still take about **102 minutes longer** (95% CI: 96–108 mins). This suggests unobserved operational bottlenecks (e.g., dispatch rules, pickup waiting, route design).
3. **Grocery Category Has Distinct Process Characteristics**
   * Non-grocery categories take 103–106 minutes longer than Grocery, suggesting Grocery uses a separate fast-track fulfillment process. Future analysis should stratify Grocery orders.

---

## 6. Decision & Actionable Recommendations

* **Priority Action**: Set **Semi-Urban as the first area for targeted process diagnosis**. Collect granular stage data (dispatch wait, store prep time, drive time) instead of blindly hiring more delivery drivers.
* **Avoid Ineffective Actions**: Pickup Period effects are highly sensitive to Traffic and data overlap; avoid adjusting shift schedules based on period averages alone.
* **Validation & Rollout Strategy**: Run small-scale controlled tests on Semi-Urban routes (adjusting route/pickup/dispatch logic). Track Delivery Time median, P75, and cost per delivery before scaling up.

---

## 📊 Slide Deck

This analysis includes a visual presentation (built with OpenSlide and exported as standalone HTML) for quick review:

* **How to view**: Navigate to the [`slides/`](slides/) folder and open the HTML file in any browser (Chrome, Safari, Edge):
  * English Slides: [`slides/amazon-delivery-analysis-en.html`](slides/amazon-delivery-analysis-en.html)
  * Chinese Slides: [`slides/amazon-delivery-analysis-zh.html`](slides/amazon-delivery-analysis-zh.html)

---

## 📂 Project Structure

* [`README.md`](README.md): English project overview (this file)
* [`README-zh.md`](README-zh.md): Chinese project overview
* [`amazon_delivery_revised_en.ipynb`](amazon_delivery_revised_en.ipynb): Complete English analysis Jupyter Notebook
* [`amazon_delivery_revised_zh.ipynb`](amazon_delivery_revised_zh.ipynb): Complete Chinese analysis Jupyter Notebook
* [`src/data_preparation.py`](src/data_preparation.py): Data cleaning and feature engineering module
* [`slides/`](slides/): Slide deck HTML files (English & Chinese)
