# Temprature_Predictor
The software part of the project.

## Required libraries
- pandas
- matplotlib
- scikit-learn

## Usage
To use this part of the project, follow these steps:
1. After cloning the entire project `git clone https://github.com/congiants/Temprature_Predictor.git`
2. Install the required libraries: `pip install required_library`
3. You can run the prediction

## Techniques used
Using [ridge regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) from scikit-learn, the software tries to find a correlation between a given days' max and min temperatures, as well as some other parameters with, and futures' day max temperature, with the goal of predicting the entire next weeks' daily max temperature.  

## Dataset
Dataset used from NOAA: [https://www.ncdc.noaa.gov/cdo-web/datatools/findstation](https://www.ncdc.noaa.gov/cdo-web/datatools/findstation)
