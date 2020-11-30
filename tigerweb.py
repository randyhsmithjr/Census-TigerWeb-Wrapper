import json
import ssl
import sys

import shapely
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

import geopandas

try:
    from urllib import urlencode
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode

PYTHON3 = True if sys.version_info >= (3, 0) else False
shapely.speedups.disable()


class TigerWeb(object):
    def __init__(
        self,
        geometry=[],
        geometry_type="point",
        distance=None,
        units="esriSRUnit_StatuteMile",
        return_geometry=False,
    ):
        if geometry_type == "point":
            self.geometry = "{},{}".format(geometry[0][0], geometry[0][1])
            self.geometryType = "esriGeometryPoint"
        if geometry_type == "Polygon":
            self.geometry = {"rings": []}
            self.geometryType = "esriGeometryPolygon"
            self.polygon = []
            for polygons in geometry:
                polygons.append(polygons[0])
                polygon_tuple = [
                    (xy[0], xy[1]) for xy in polygons if isinstance(xy, list)
                ]
                polygon_tuple[-1] = polygon_tuple[0]
                p = Polygon(polygon_tuple)
                self.geometry["rings"].append([[i[0], i[1]] for i in polygon_tuple])
                self.polygon.append(p)
        if geometry_type == "MultiPolygon":
            self.geometry = {"rings": []}
            self.geometryType = "esriGeometryPolygon"
            self.polygon = []
            for polygons in geometry:
                polygon = polygons[0]
                polygon.append(polygon[0])
                polygon_tuple = [
                    (xy[0], xy[1]) for xy in polygon if isinstance(xy, list)
                ]
                polygon_tuple.append((polygon[0][0], polygon[0][1]))
                p = Polygon(polygon_tuple)
                self.geometry["rings"].append(
                    [[i[0], i[1]] for i in list(p.exterior.coords)]
                )
                self.polygon.append(p)

        self.distance = distance
        self.units = units
        self.params = {
            "geometryType": self.geometryType,
            "geometry": self.geometry,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": return_geometry,
            "inSR": "4326",
            "outSR": "4326",
            "f": "geojson",
        }
        if distance:
            self.params["distance"] = distance
            self.params["units"] = "esriSRUnit_StatuteMile"

    def get_data(self, url, params={}, within_polygon=False, geojson=False):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for k, v in params.items():
            self.params[k] = v
        data = []
        if PYTHON3:
            params = urlencode(self.params).encode()
        else:
            params = urlencode(self.params)
        request = Request(url, params)
        response = urlopen(request, context=ctx)
        if response.getcode() == 200:
            r = json.loads(response.read())
            if geojson:
                data = r
            else:
                for i in r["features"]:
                    d = i["properties"]
                    if self.params["returnGeometry"]:
                        d["geometry"] = i["geometry"]
                    data.append(d)
                if within_polygon:
                    data = self.within_polygon(data)
        return data

    def within_polygon(self, data):
        polygon_in_polygon = []
        for point in data:
            p = Point(
                float(point["CENTLON"].replace("+", "")),
                float(point["CENTLAT"].replace("+", "")),
            )
            for poly in self.polygon:
                if p.within(poly):
                    polygon_in_polygon.append(point)
        return polygon_in_polygon

    def get_tracts(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/0/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_zipcodes(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/1/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_incorporated_places(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_census_designated_places(
        self, params={}, within_polygon=False, geojson=False
    ):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/5/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_place(self, params={}, within_polygon=False, geojson=False):
        data = self.get_incorporated_places(
            params=params, within_polygon=within_polygon, geojson=geojson
        )
        if len(data) == 0:
            data = self.get_census_designated_places(
                params=params, within_polygon=within_polygon, geojson=geojson
            )
        return data

    def get_counties(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_metro_area(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/CBSA/MapServer/8/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_micro_area(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/CBSA/MapServer/9/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_cbsa(self, params={}, within_polygon=False, geojson=False):
        data = self.get_metro_area(
            params=params, within_polygon=within_polygon, geojson=geojson
        )
        if len(data) == 0:
            data = self.get_micro_area(
                params=params, within_polygon=within_polygon, geojson=geojson
            )
        return data

    def get_states(self, params={}, within_polygon=False, geojson=False):
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/0/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_rural(self, params={}, within_polygon=False, geojson=False):
        url = "https://rdgdwe.sc.egov.usda.gov/arcgis/rest/services/Eligibility/Eligibility/MapServer/4/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data

    def get_fmr(self, params={}, within_polygon=False, geojson=False):
        url = "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Fair_Market_Rents/FeatureServer/0/query"
        data = self.get_data(
            url, params=params, within_polygon=within_polygon, geojson=geojson
        )
        return data
