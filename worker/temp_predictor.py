import pandas as pd
import numpy as np
import matplotlib
import sklearn

weather = pd.read_csv("data/Thessaloniki_Weather.csv")
core_weather = weather[["DATE", "PRCP", "TMAX", "TMIN"]].copy()
core_weather.columns = ["date", "percip", "max_temp", "min_temp"]
core_weather = core_weather.set_index("date")

#We will deal with null values. 2 main tactics: 1. I put the last value of that column wherever null 2. I put zero
core_weather["percip"] = core_weather["percip"].fillna(0)
core_weather = core_weather.fillna(method="ffill")

#datetime more useful
core_weather.index = pd.to_datetime(core_weather.index)
#If x = 9999 then it means null
core_weather.apply(lambda x: (x==9999).sum())

#Duplicates in 1998, 1999, 2000, 2001, 2002, 2003, 2004   
core_weather = core_weather.reset_index()
core_weather = core_weather.drop_duplicates(subset=['date'])
core_weather = core_weather.set_index('date')


#Since we want to predict the next week, 7 targets are set to next 7 days of each day
core_weather["target1_max"] = core_weather.shift(-1)["max_temp"]
core_weather["target1_min"] = core_weather.shift(-1)["min_temp"]

core_weather["target2_max"] = core_weather.shift(-2)["max_temp"]
core_weather["target2_min"] = core_weather.shift(-2)["min_temp"]

core_weather["target3_max"] = core_weather.shift(-3)["max_temp"]
core_weather["target3_min"] = core_weather.shift(-3)["min_temp"]

core_weather["target4_max"] = core_weather.shift(-4)["max_temp"]
core_weather["target4_min"] = core_weather.shift(-4)["min_temp"]

core_weather["target5_max"] = core_weather.shift(-5)["max_temp"]
core_weather["target5_min"] = core_weather.shift(-5)["min_temp"]

core_weather["target6_max"] = core_weather.shift(-6)["max_temp"]
core_weather["target6_min"] = core_weather.shift(-6)["min_temp"]

core_weather["target7_max"] = core_weather.shift(-7)["max_temp"]
core_weather["target7_min"] = core_weather.shift(-7)["min_temp"]

core_weather = core_weather.iloc[:-7, :].copy()


core_weather["avg_max_month"] = core_weather["max_temp"].rolling(30).mean()
core_weather["avg_min_month"] = core_weather["min_temp"].rolling(30).mean()
core_weather = core_weather.iloc[30:, :].copy()

core_weather["daily_avg_offset_max"] = core_weather["avg_max_month"] / core_weather["max_temp"]
core_weather["daily_avg_offset_min"] = core_weather["avg_min_month"] / core_weather["min_temp"]

core_weather["max_min_ratio"] = core_weather["max_temp"] / core_weather["min_temp"]


#Infinity doesn't allow prediction
core_weather = core_weather.reset_index()

core_weather = core_weather.drop(core_weather[core_weather.daily_avg_offset_max == core_weather["daily_avg_offset_max"].max()].index)
core_weather = core_weather.drop(core_weather[core_weather.daily_avg_offset_max == core_weather["daily_avg_offset_max"].min()].index)

core_weather = core_weather.drop(core_weather[core_weather.daily_avg_offset_min == core_weather["daily_avg_offset_min"].max()].index)
core_weather = core_weather.drop(core_weather[core_weather.daily_avg_offset_min == core_weather["daily_avg_offset_min"].min()].index)

core_weather = core_weather.drop(core_weather[core_weather.max_min_ratio == core_weather["max_min_ratio"].max()].index)
core_weather = core_weather.drop(core_weather[core_weather.max_min_ratio == core_weather["max_min_ratio"].min()].index)

core_weather = core_weather.set_index('date')

#Ridge useful when independent variables are highly correlated 
from sklearn.linear_model import Ridge

#Minimizes ||y - Xw||^2_2 + alpha * ||w||^2_2
reg1_max = Ridge(alpha=.1)
reg1_min = Ridge(alpha=.1)

reg2_max = Ridge(alpha=.1)
reg2_min = Ridge(alpha=.1)

reg3_max = Ridge(alpha=.1)
reg3_min = Ridge(alpha=.1)

reg4_max = Ridge(alpha=.1)
reg4_min = Ridge(alpha=.1)

reg5_max = Ridge(alpha=.1)
reg5_min = Ridge(alpha=.1)

reg6_max = Ridge(alpha=.1)
reg6_min = Ridge(alpha=.1)

reg7_max = Ridge(alpha=.1)
reg7_min = Ridge(alpha=.1)

from sklearn.metrics import mean_absolute_error

#Automation1
def create_prediction_max (predictors, core_weather, reg1_max, reg2_max, reg3_max, reg4_max, reg5_max, reg6_max, reg7_max):
    train = core_weather.loc[:"2021-12-31"]
    test = core_weather.loc["2022-01-01":]

    reg1_max.fit(train[predictors], train["target1_max"])
    predictions1_max = reg1_max.predict(test[predictors])
    error1_max = mean_absolute_error(test["target1_max"], predictions1_max)
    score1_max = reg1_max.score(test[predictors], test["target1_max"])
    combined1_max = pd.concat([test["target1_max"], pd.Series(predictions1_max, index=test.index)] ,axis=1)
    combined1_max.columns = ["actual1_max", "predictions1_max"]

    reg2_max.fit(train[predictors], train["target2_max"])
    predictions2_max = reg2_max.predict(test[predictors])
    error2_max = mean_absolute_error(test["target2_max"], predictions2_max)
    score2_max = reg2_max.score(test[predictors], test["target2_max"])
    combined2_max = pd.concat([test["target2_max"], pd.Series(predictions2_max, index=test.index)] ,axis=1)
    combined2_max.columns = ["actual2_max", "predictions2_max"]

    reg3_max.fit(train[predictors], train["target3_max"])
    predictions3_max = reg3_max.predict(test[predictors])
    error3_max = mean_absolute_error(test["target3_max"], predictions3_max)
    score3_max = reg3_max.score(test[predictors], test["target3_max"])
    combined3_max = pd.concat([test["target3_max"], pd.Series(predictions3_max, index=test.index)] ,axis=1)
    combined3_max.columns = ["actual3_max", "predictions3_max"]

    reg4_max.fit(train[predictors], train["target4_max"])
    predictions4_max = reg4_max.predict(test[predictors])
    error4_max = mean_absolute_error(test["target4_max"], predictions4_max)
    score4_max = reg4_max.score(test[predictors], test["target4_max"])
    combined4_max = pd.concat([test["target4_max"], pd.Series(predictions4_max, index=test.index)] ,axis=1)
    combined4_max.columns = ["actual4_max", "predictions4_max"]

    reg5_max.fit(train[predictors], train["target5_max"])
    predictions5_max = reg5_max.predict(test[predictors])
    error5_max = mean_absolute_error(test["target5_max"], predictions5_max)
    score5_max = reg5_max.score(test[predictors], test["target5_max"])
    combined5_max = pd.concat([test["target5_max"], pd.Series(predictions5_max, index=test.index)] ,axis=1)
    combined5_max.columns = ["actual5_max", "predictions5_max"]

    reg6_max.fit(train[predictors], train["target6_max"])
    predictions6_max = reg6_max.predict(test[predictors])
    error6_max = mean_absolute_error(test["target6_max"], predictions6_max)
    score6_max = reg6_max.score(test[predictors], test["target6_max"])
    combined6_max = pd.concat([test["target6_max"], pd.Series(predictions6_max, index=test.index)] ,axis=1)
    combined6_max.columns = ["actual6_max", "predictions6_max"]

    reg7_max.fit(train[predictors], train["target7_max"])
    predictions7_max = reg7_max.predict(test[predictors])
    error7_max = mean_absolute_error(test["target7_max"], predictions7_max)
    score7_max = reg7_max.score(test[predictors], test["target7_max"])
    combined7_max = pd.concat([test["target7_max"], pd.Series(predictions7_max, index=test.index)] ,axis=1)
    combined7_max.columns = ["actual7_max", "predictions7_max"]


    return error1_max, score1_max, combined1_max, error2_max, score2_max, combined2_max, error3_max, score3_max, combined3_max, error4_max, score4_max, combined4_max, error5_max, score5_max, combined5_max, error6_max, score6_max, combined6_max, error7_max, score7_max, combined7_max

#Automation2
def create_prediction_min (predictors, core_weather, reg1_min, reg2_min, reg3_min, reg4_min, reg5_min, reg6_min, reg7_min):
    train = core_weather.loc[:"2021-12-31"]
    test = core_weather.loc["2022-01-01":]

    reg1_min.fit(train[predictors], train["target1_min"])
    predictions1_min = reg1_min.predict(test[predictors])
    error1_min = mean_absolute_error(test["target1_min"], predictions1_min)
    score1_min = reg1_min.score(test[predictors], test["target1_min"])
    combined1_min = pd.concat([test["target1_min"], pd.Series(predictions1_min, index=test.index)] ,axis=1)
    combined1_min.columns = ["actual1_min", "predictions1_min"]

    reg2_min.fit(train[predictors], train["target2_min"])
    predictions2_min = reg2_min.predict(test[predictors])
    error2_min = mean_absolute_error(test["target2_min"], predictions2_min)
    score2_min = reg2_min.score(test[predictors], test["target2_min"])
    combined2_min = pd.concat([test["target2_min"], pd.Series(predictions2_min, index=test.index)] ,axis=1)
    combined2_min.columns = ["actual2_min", "predictions2_min"]

    reg3_min.fit(train[predictors], train["target3_min"])
    predictions3_min = reg3_min.predict(test[predictors])
    error3_min = mean_absolute_error(test["target3_min"], predictions3_min)
    score3_min = reg3_min.score(test[predictors], test["target3_min"])
    combined3_min = pd.concat([test["target3_min"], pd.Series(predictions3_min, index=test.index)] ,axis=1)
    combined3_min.columns = ["actual3_min", "predictions3_min"]

    reg4_min.fit(train[predictors], train["target4_min"])
    predictions4_min = reg4_min.predict(test[predictors])
    error4_min = mean_absolute_error(test["target4_min"], predictions4_min)
    score4_min = reg4_min.score(test[predictors], test["target4_min"])
    combined4_min = pd.concat([test["target4_min"], pd.Series(predictions4_min, index=test.index)] ,axis=1)
    combined4_min.columns = ["actual4_min", "predictions4_min"]

    reg5_min.fit(train[predictors], train["target5_min"])
    predictions5_min = reg5_min.predict(test[predictors])
    error5_min = mean_absolute_error(test["target5_min"], predictions5_min)
    score5_min = reg5_min.score(test[predictors], test["target5_min"])
    combined5_min = pd.concat([test["target5_min"], pd.Series(predictions5_min, index=test.index)] ,axis=1)
    combined5_min.columns = ["actual5_min", "predictions5_min"]

    reg6_min.fit(train[predictors], train["target6_min"])
    predictions6_min = reg6_min.predict(test[predictors])
    error6_min = mean_absolute_error(test["target6_min"], predictions6_min)
    score6_min = reg6_min.score(test[predictors], test["target6_min"])
    combined6_min = pd.concat([test["target6_min"], pd.Series(predictions6_min, index=test.index)] ,axis=1)
    combined6_min.columns = ["actual6_min", "predictions6_min"]

    reg7_min.fit(train[predictors], train["target7_min"])
    predictions7_min = reg7_min.predict(test[predictors])
    error7_min = mean_absolute_error(test["target7_min"], predictions7_min)
    score7_min = reg7_min.score(test[predictors], test["target7_min"])
    combined7_min = pd.concat([test["target7_min"], pd.Series(predictions7_min, index=test.index)] ,axis=1)
    combined7_min.columns = ["actual7_min", "predictions7_min"]

    return error1_min, score1_min, combined1_min, error2_min, score2_min, combined2_min, error3_min, score3_min, combined3_min, error4_min, score4_min, combined4_min, error5_min, score5_min, combined5_min, error6_min, score6_min, combined6_min, error7_min, score7_min, combined7_min 

#Better results with these predictors
predictors = ["percip", "max_temp", "min_temp", "avg_max_month", "daily_avg_offset_max"]
error1_max, score1_max, combined1_max, error2_max, score2_max, combined2_max, error3_max, score3_max, combined3_max, error4_max, score4_max, combined4_max, error5_max, score5_max, combined5_max, error6_max, score6_max, combined6_max, error7_max, score7_max, combined7_max =create_prediction_max (predictors, core_weather, reg1_max, reg2_max, reg3_max, reg4_max, reg5_max, reg6_max, reg7_max)

#Better results with these predictors
predictors = ["percip", "max_temp", "min_temp", "avg_max_month", "daily_avg_offset_max"]
error1_min, score1_min, combined1_min, error2_min, score2_min, combined2_min, error3_min, score3_min, combined3_min, error4_min, score4_min, combined4_min, error5_min, score5_min, combined5_min, error6_min, score6_min, combined6_min, error7_min, score7_min, combined7_min =create_prediction_min (predictors, core_weather, reg1_min, reg2_min, reg3_min, reg4_min, reg5_min, reg6_min, reg7_min)

combined1_max.plot()
combined2_max.plot()
combined3_max.plot()
combined4_max.plot()
combined5_max.plot()
combined6_max.plot()
combined7_max.plot()

