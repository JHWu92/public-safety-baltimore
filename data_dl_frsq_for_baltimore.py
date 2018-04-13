from src.frsq_helper import *
polygon = 'data/cityline-baltimore.geojson'
frsq_raw_venues= 'data/foursquare/raw_venues/'
frsq_venues= 'data/foursquare/frsq_venues_baltimore.geojson'

#raw_venues_in_city(polygon, frsq_raw_venues, ngrid_1d=50)
show_grids_used(polygon, frsq_raw_venues)
frsq_venues_in_city_geojson(polygon, frsq_raw_venues, frsq_venues)
