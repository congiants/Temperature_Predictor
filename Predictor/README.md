# Temprature_Predictor
The software part of the project that does the future temperature predictions.

## Required libraries
- pandas
- matplotlib
- scikit-learn

## Usage
To use this part of the project, follow these steps:
1. Clone the entire project: `git clone https://github.com/congiants/Temprature_Predictor.git`
2. Install the required libraries: `pip install required_library`
3. You can run the model

## Model
The model was trained using weather data from the Thessaloniki Airport "Macedonia" that was provided by [NOAA](https://www.ncei.noaa.gov/cdo-web/datasets/GHCND/locations/CITY:GR000007/detail). Using [ridge regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) from scikit-learn, the model was trained to find correlations between a given day's max temperature, min temperature, as well as the precipitation, and the next 7 day's (week) max temperature. The same logic can be applied to predict min temperatures as well. Given the required weather data of a day , the model's error is +- 1.3°C for 1 day later and +- 3.1°C for 7 days later.
