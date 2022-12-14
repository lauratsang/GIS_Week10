from copy import deepcopy
import datetime as dt
from IPython.display import HTML
import json
import pandas as pd
from arcgis.gis import GIS
import arcgis.network as network
import arcgis.geocoding as geocoding
from arcgis.features import FeatureLayer, FeatureSet, FeatureCollection
import arcgis.features.use_proximity as use_proximity

my_gis = GIS('https://www.arcgis.com', 'tsang.la_NU', 'XXXXXXXXXX', verify_cert=False, set_active=True)

my_gis = GIS('home')

sample_cities = my_gis.content.search('title:"USA Major Cities" type:Feature Service owner:esri*', 
                                      outside_org=True)[0]
sample_cities

stops_cities = ['San Francisco', 'San Jose', 'Los Angeles', 'San Diego',
                'Phoenix', 'El Paso', 
                'Houston', 'New Orleans', 'Orlando', 'Miami']
values = "'" + "', '".join(stops_cities) + "'"

stops_cities_fl = FeatureLayer(sample_cities.url + "/0")
type(stops_cities_fl)

stops_cities_fset = stops_cities_fl.query(where="ST in ('CA', 'NV', 'TX', 'AZ', 'LA', 'FL')  AND NAME IN ({0})".format(values), as_df=False)
stops_cities_fset

start_cities_fset = stops_cities_fl.query(where="ST='FL' AND NAME = 'Miami'", as_df=False)
start_cities_fset

print(list(map(lambda x: x.attributes['NAME'], stops_cities_fset)))

""" Used to re-order the stops to the desired order
"""
def re_order_stop_cities(fset=stops_cities_fset, start_city = "Miami", end_city = "San Francisco"):
    
    stops_cities_flist = []
    last_city = None

    for ea in fset:
        if ea.attributes['NAME'] == start_city:
            stops_cities_flist.insert(0, ea)
        elif ea.attributes['NAME'] == end_city:
            last_city = ea
        else:
            stops_cities_flist.append(ea)
    stops_cities_flist.append(last_city)
 
    return FeatureSet(stops_cities_flist)

re_ordered_stops_cities_fset = re_order_stop_cities()
re_ordered_stops_cities_fset.spatial_reference = stops_cities_fset.spatial_reference
re_ordered_stops_cities = list(map(lambda x: x.attributes['NAME'], re_ordered_stops_cities_fset))
print(re_ordered_stops_cities)

%%time

start_time = int(dt.datetime.now().timestamp() * 1000)

result = network.analysis.find_routes(re_ordered_stops_cities_fset, time_of_day=start_time, 
                                      time_zone_for_time_of_day="UTC",
                                      preserve_terminal_stops="Preserve None",
                                      reorder_stops_to_find_optimal_routes=True,
                                      save_output_na_layer=True)

print("Is the tool executed successfully?", result.solve_succeeded)

type(result)

result.output_routes, result.output_stops, result.output_directions

result.output_network_analysis_layer.url

""" Access the output directions
"""
df = result.output_directions.sdf
df = df[["RouteName", "ArriveTime", "DriveDistance", "ElapsedTime", "Text"]].loc[df["RouteName"] == "Miami - San Francisco"]
df.head()

""" Access output routes
"""
df = result.output_routes.sdf
start_times = pd.to_datetime(df["StartTime"], unit="ms")
end_times = pd.to_datetime(df["EndTime"], unit="ms")
df["StartTime"] = start_times.apply(lambda x: x.strftime("%H:%M:%S"))
df["EndTime"] = end_times.apply(lambda x: x.strftime("%H:%M:%S"))
df[["Name", "StartTime", "EndTime", "StopCount", "Total_Kilometers", "Total_Minutes"]]

""" draw the route and stops with customized styles, symbologies, and popups
"""
styles = [    
    dict(selector="td", props=[("padding", "2px")]),
    dict(selector='.row_heading, .blank', props=[('display', 'none;')]),
    dict(selector='.col_heading, .blank', props=[('display', 'none;')])]

route_symbol = {
                    "type": "esriSLS",
                    "style": "esriSLSSolid",
                    "color": [128,0,128,90],
                    "width": 4
                }

stops_symbol = {"angle":0,"xoffset":2,"yoffset":8,"type":"esriPMS",
                "url":"http://static.arcgis.com/images/Symbols/Basic/ShinyPin.png",
                "contentType":"image/png","width":24,"height":24}

start_symbol = {"angle":0,"xoffset":0,"yoffset":8.15625,"type":"esriPMS",
                "url":"http://static.arcgis.com/images/Symbols/AtoZ/redA.png",
                "contentType":"image/png","width":15.75,"height":21.75}

end_symbol = {"angle":0,"xoffset":0,"yoffset":8.15625,"type":"esriPMS",
              "url":"http://static.arcgis.com/images/Symbols/AtoZ/greenB.png",
              "contentType":"image/png","width":15.75,"height":21.75}

popup_route = {"title": "Route", 
               "content": df.style.set_table_styles(styles).render()}
popup_stop = {"title": "Stop {}", 
              "content": df.style.set_table_styles(styles).render()}

def check_curb_approach2(result):
    attributes = result.attributes
    return (attributes['ArriveCurbApproach'], attributes['DepartCurbApproach'])

map1 = my_gis.map('Texas, USA', zoomlevel=4)
map1

""" draw the route and stops with customized styles, symbologies, and popups
"""
for route in result.output_routes:
    map1.draw(route.geometry, popup_route, route_symbol)

sequence = 1
for stop in result.output_stops:
    
    stop_bool_tuple = check_curb_approach2(stop)
    if stop_bool_tuple[0] is None:
        # starting point
        symbol = start_symbol
    elif stop_bool_tuple[1] is None:
        # ending point
        symbol = end_symbol
    else:
        # by-passing point
        symbol = stops_symbol
        
    address = geocoding.reverse_geocode(stop.geometry)['address']['Match_addr']
    map1.draw(stop.geometry, 
              {"title": "Stop {}".format(sequence), 
               "content": address},
              symbol)
    sequence+=1

#save into a web map
item_properties = {
    "title": "Miami - San Francisco (2)",
    "tags" : "Routing",
    "snippet": " Route from Miami to San Francisco",
    "description": "a web map of Route from Miami to San Francisco using network.RouteLayer.solve"
}

item = map1.save(item_properties)

item


