# Temperature_Predictor
A machine learning project that can predict future temperatures given a day's temperature and precipitation.

## Project Parts
The project is meant to be a completely independent temperature predictor, consisting of the required sensors to take measurements, the software that can make future predictions, and finally a website that this information can be uploaded. Currently, there is an implementation of the first two parts. There is a README in each part with more details of each section of the project.

## Data sources
- **Training data:** daily ERA5-Land reanalysis for Thessaloniki (1950 onwards) from the
  Open-Meteo Historical Weather API, stored in `data/thessaloniki_openmeteo_raw.csv`.
  Weather data by [Open-Meteo.com](https://open-meteo.com/), licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **ERA5-Land:** Muñoz Sabater, J. (2019): ERA5-Land hourly data from 1950 to present.
  Copernicus Climate Change Service (C3S) Climate Data Store (CDS). DOI: 10.24381/cds.e2161bac.
  Contains modified Copernicus Climate Change Service information 2026.
- **Validation data:** NOAA GHCN-Daily, station MAKEDONIA, GR (`data/thessaloniki_weather_raw.csv`).
  Menne, M.J., et al. (2012): Global Historical Climatology Network - Daily (GHCN-Daily),
  Version 3. NOAA National Climatic Data Center. doi:10.7289/V5D21VHZ.

## License
MIT License Copyright (c) 2024 Constantine Giantselidis 
