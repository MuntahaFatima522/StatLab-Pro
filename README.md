# StatLab Pro 📊
A professional statistical data analyzer built in Python as a full desktop
GUI application. Load any CSV or Excel dataset and instantly explore summary
statistics, run normality and hypothesis tests, detect outliers, and generate
six types of interactive charts — all in a sleek dark-themed interface.

## Overview
StatLab Pro demonstrates how scientific Python libraries come together to
build a real analysis tool. Every tab serves a purpose — the Data tab previews
your dataset, Statistics runs detailed numeric summaries, Charts renders
publication-quality plots, Distribution runs formal normality tests, and
Insights auto-generates findings the moment you load a file. The UI is built
entirely in Tkinter with custom widgets, no external UI framework needed.

## Features
- Load CSV and Excel files with automatic type detection
- Built-in sample dataset generator (200 rows, 6 columns) to explore instantly
- Summary statistics — mean, std, skewness, kurtosis, CV, percentiles
- Pearson correlation matrix with strength and direction labels
- Missing value analysis with visual bar indicators
- IQR-based outlier detection across all numeric columns
- Normality tests — Shapiro-Wilk, D'Agostino-Pearson, Kolmogorov-Smirnov
- Hypothesis testing — independent t-test, Welch t-test, Mann-Whitney U
- Group statistics — segment any numeric column by a categorical group
- Filter & Query using pandas query expressions with live row-count preview
- Normalize numeric columns to [0, 1] with one click
- Undo stack — revert any transformation or filter (up to 10 steps)
- Export filtered data to CSV or Excel
- Generate a full text report with stats and correlation matrix
- Auto-insights panel — correlations, skewed columns, and outliers flagged on load

## Charts
| Chart | Description |
|---|---|
| Histogram | Distribution with KDE overlay and box plot side-by-side |
| Box Plot | All numeric columns compared in one view |
| Scatter Plot | X vs Y with regression line, residual plot, and optional color-by-category |
| Heatmap | Correlation matrix rendered as a color-coded grid |
| Pair Plot | Grid of pairwise scatter plots and diagonal histograms |
| Time Series | Line chart with rolling average overlay |

## How to Run
1. Install dependencies:
   ```bash
   pip install numpy pandas scipy matplotlib
   ```
2. Run the app:
   ```bash
   python data_analyzer.py
   ```
3. Click **Sample Dataset** in the sidebar to load data instantly, or use
**Load CSV / Excel** to open your own file.

> Developed and tested on Python 3.10+. Requires a display environment (not headless).

## Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?style=flat&logo=scipy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=flat&logo=matplotlib&logoColor=white)

## About
Built as a personal project to explore how Python's scientific stack can power
a full desktop application. The goal was to go beyond notebooks and scripts —
building something with a real UI, real UX decisions, and enough statistical
depth to be genuinely useful for data exploration.
