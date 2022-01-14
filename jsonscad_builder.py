"""A module to create 3D choropleth maps in OpenSCAD from GeoJSON data.

Copyright:
    Kenneth Yan 2022
License:
    MIT License; see LICENSE.txt
"""

import json
from collections import OrderedDict
from random import choice
from rdp import rdp

class JsonScadBuilder:
    """A class to represent a 3D chroropleth model.
    
    Attributes:
        raw_json_data: OrderedDict storing raw GeoJSON data.
        features: List storing features from a GeoJSON FeatureCollection.
        num_features: Integer number of features.
        bound_data_key_name: String containing the name of the statistical 
            variable that the 3D model visualizes. 
        origin: List of two elements `[lat, long]` that represents the 
            geographic coordinate corresponding to (0,0,0) in OpenSCAD.
        scale_factor: Number that represents the scaling factor in a scaling 
            transformation of the polygon geometries.
        offset_delta: Number that represents the offset distance for 
            drawing polygon geometries in OpenSCAD.
        is_colored: Boolean that indicates whether color preview mode is
            on or off.
    """

    # CONSTANTS
    DEFAULT_EXTRUDE_HEIGHT = 2
    """Default extrusion height if there does not exist a bound data value
    for a feature."""
    DEFAULT_RDP_EPSILON = 0.01
    """Default epsilon value for the Ramer-Douglas-Peucker (RDP) Algorithm."""

    COLOR_BANK = ['Red', 'Green', 'Blue', 'Brown',
                'Purple', 'Gold', 'Orange']
    """List of avaliable colors in color preview mode."""

    # CONSTRUCTOR
    def __init__(self):
        """Initializes an instance of JsonScadBuilder."""
        self.raw_json_data = OrderedDict()
        self.features = []
        self.num_features = 0
        self.bound_data_key_name = ''
        self.origin = []
        self.scale_factor = 1
        self.offset_delta = 0
        self.is_colored = False

    # HELPER FUNCTIONS
    def _transform_helper(self, pair):
        return [self.scale_factor * (pair[0]-self.origin[0]), 
        self.scale_factor * (pair[1]-self.origin[1])]
    
    # API METHODS
    def read_json(self, str):
        """Reads GeoJSON data from a string.

        Reads and parses data from a string containing a GeoJSON
        FeatureCollection. Stores the parsed data in OrderedDict
        `raw_json_data`.

        Args:
            str: String containing GeoJSON data.
        """
        self.raw_json_data = json.loads(str)
        print(status_msg['end_read'] + str(self.raw_json_data.keys()))

    def read_json_file(self, filepath):
        """Reads GeoJSON data from a file.

        Reads and parses data from any `.read()`-supporting text file or 
        binary file containing a GeoJSON FeatureCollection. Stores the parsed 
        data in OrderedDict `raw_json_data`. Conventional file extensions are 
        .geojson and .json. 

        Args:
            filepath: String containing the path to the GeoJSON file.
        """
        with open(filepath) as f:
            self.raw_json_data = json.load(f, object_pairs_hook=OrderedDict)
        print(status_msg['end_read'] + str(self.raw_json_data.keys()))

    def extract_features(self):
        """Extracts the 'features' array from raw_json_data.

        Looks up the 'features' array from the OrderedDict `raw_json_data` 
        and sets the instance attribute `features` to the array.
        """
        assert self.raw_json_data, error_msg['emp_json']
        self.features = self.raw_json_data['features']
        self.num_features = len(self.features)
        print(status_msg['end_extc'] + str(self.num_features))

    def simplify(self, eps = DEFAULT_RDP_EPSILON):
        """Simplifies the geometries for each feature.

        Applies Ramer-Douglas-Peucker (RDP) Algorithm to all polygons 
        contained in the instance attribute `features`.  

        Args:
            eps: The epsilon parameter of the RDP algorithm.
        """
        assert self.features, error_msg['emp_feat']
        print(status_msg['start_smpl'])

        # Counter for the new number of total points
        # Print once rdp is done running for all features
        num_points = 0 

        for idx, feature in enumerate(self.features):
            # Handle polygons 
            if(feature['geometry']['type'] == "Polygon"):
                # index 0 contains exterior linear ring
                coords = feature['geometry']['coordinates'][0]
                sampled_coords = rdp(coords, epsilon = eps)
                feature['geometry']['coordinates'][0] = sampled_coords
                num_points += len(sampled_coords)

            # Handle multipolygons, which store coordinate data
            # one layer deeper than polygons
            elif(feature['geometry']['type'] == "MultiPolygon"):
                for polygon in feature['geometry']['coordinates']:
                    # index 0 contains exterior linear ring
                    coords = polygon[0]
                    sampled_coords = rdp(coords, epsilon = eps)
                    polygon[0] = sampled_coords
                    num_points += len(sampled_coords)

            # Progress report
            print("           " + 
            str(idx+1) + " of " + str(self.num_features) + " complete")

        print(status_msg['end_smpl'] + str(num_points))

    def transform(self, origin, scale_factor):
        """Applies translation and scaling transformations to geometries.

        Translates all points to new positions relative to the specified 
        `origin`. The `origin` represents the longitude and latitude position
        that corresponds to (0,0,0) in OpenSCAD. Scales geometries by 
        `scale_factor`. Multiplication of coordinates by `scale_factor` occurs
        after the translation.
        
        Args:
            origin: A list of two elements `[long,lat]` in decimal form.  
            scale_factor: A real number that will multiply the x and y 
                coordinates of all points. 
        """
        self.origin = origin
        self.scale_factor = scale_factor

        assert self.features, error_msg['emp_feat']

        for feature in self.features:
            # Handle polygons 
            if(feature['geometry']['type'] == "Polygon"):
                # index 0 contains exterior linear ring
                coords = feature['geometry']['coordinates'][0] 
                feature['geometry']['coordinates'][0] = list(
                    map(self._transform_helper, coords))

            # Handle multipolygons, which store coordinate data
            # one layer deeper than polygons
            elif(feature['geometry']['type'] == "MultiPolygon"):
                for polygon in feature['geometry']['coordinates']:
                    # index 0 contains exterior linear ring
                    coords = polygon[0]
                    polygon[0] = list(map(self.transform_helper, coords))

        print(status_msg['end_tsfm']) 

    def offset(self, delta):
        """Sets the offset distance for polygon geometries.

        Sets the instance attribute `offset_delta`. A non-zero `offset_data` 
        value signals `write_scad_file()` to draw all polygon geometries
        with sides offset by `offset_delta` from the original polygon 
        geometries stored in `features`. Setting a positive `offset_delta`
        can eliminate undesirable gaps between features in the model. 

        Args:
            delta: The offset distance.
        """
        self.offset_delta = delta
        print(status_msg['end_ofst'])

    def bind_data(self, data_key_name, data):
        """Binds statistical data to GeoJSON features.

        Adds a new key-value pair to each feature's 'properties' member,
        where the key is the name of the statistical variable to visualize
        in the choropleth and the value is the value for that geographic area.
        The dataset `data` should be a list that has data points in the same 
        order as features in the list `features`.

        Args:
            data_key_name: String containing the name of the statistical 
                variable.
            data: A list containing numerical data values. 
        """
        self.bound_data_key_name = data_key_name
        assert self.features, error_msg['emp_feat']
        for feature, datum in zip(self.features, data):
            feature['properties'][data_key_name] = datum
        print(status_msg['end_bind'] + str(min(self.num_features, len(data))))

    def bind_data_by_identifier(self, data_key_name, data, id_key):
        """Binds statistical data to GeoJSON features.
        
        Similar to `bind_data`, except this method matches data points to
        features using the specified identifier `id_key`. The dataset `data` 
        should be a list containing lists of two elements `[id_value, value]`, 
        where `id_value` is the identifier value corresponding to the 
        intended feature, and `value` is the value of the statistical 
        variable at that geographic area. The identifier `id_key` should have
        unique values across all features (example identifiers include:
        county names if each feature is a county, or state abbreviations if 
        each feature is a state).

        Args:
            data_key_name: String containing the name of the statistical 
                variable.
            data: A list containing lists of two elements `[id_value, value]`.
            id_key: String containing the name of the identifier.
        """
        self.bound_data_key_name = data_key_name
        assert self.features, error_msg['emp_feat']

        # Counter for the number of datapoints with a match in the features list
        num_matches = 0 

        # Search loop
        for datum in data:
            for feature in self.features:
                if(id_key in feature['properties'] and 
                feature['properties'][id_key] == datum[0]):
                    feature['properties'][data_key_name] = datum[1]
                    num_matches += 1
                    break
        
        # Only the data that matched with a feature were bound
        # num matches == num featueres with bound data  
        print(status_msg['end_bind'] + str(num_matches))

    def scale_heights(self, domain, range):
        """Converts the bound data value for each feature into a height.

        Converts the bound data value for each feature into an extrusion 
        height for OpenSCAD. This method scales the bound data values 
        linearly according to `domain` and `range`; it scales the minimum 
        value in `domain` to the minimum height in `range`, and scales the 
        maximum value  in `domain` to the maximum height in `range`.

        Args:
            domain: A list of two numerical elements `[min, max]`
            range: A list of two numerical elements `[min, max]`
        """
        domain_diff = domain[1] - domain[0]
        range_diff = range[1] - range[0]

        assert self.features, error_msg['emp_feat']
        assert self.bound_data_key_name, error_msg['bdata_nf']

        # Keep track of min and max scaled height
        # Use range bounds as upper and lower bounds
        # for min and max heights respectively
        # Report to user once all heights have been scaled
        min_max_height = [range[1], range[0]]
        
        for feature in self.features: 
            if(self.bound_data_key_name in feature['properties']):
                scaling_ratio = (
                    feature['properties'][self.bound_data_key_name] 
                    - domain[0]) / domain_diff
                scaled_height = range[0] + (scaling_ratio * range_diff)
                feature['properties'][self.bound_data_key_name] = scaled_height
                
                # Checking for new min and max scaled heights
                min_max_height[0] = min(scaled_height, min_max_height[0])
                min_max_height[1] = max(scaled_height, min_max_height[1])

        print(status_msg['end_scle'] + str(min_max_height))

    def color_preview(self):
        """Turns on color preview mode.

        If color preview mode is on, then `write_scad_file()` will assign 
        a random color to each feature. This allows for easy identification 
        of boundaries between geographic areas when viewing the generated 
        3D model in OpenSCAD.    
        """
        self.is_colored = True

    def write_scad_file(self, filepath):
        """Generates OpenSCAD code and writes it to a file.

        Generates code that creates OpenSCAD polygons from each feature in 
        `features` and extrudes them to the height proportional to the bound 
        data value. If a bound data value does not exist for a feature, then 
        that feature is extruded to the default extrusion height, 2. This
        method then writes the OpenSCAD code to a file, which should have a 
        .scad file extension. If the file specified by `filepath` does not 
        exist, this method creates the file.

        Args:
            filepath: String containing the path to the .scad file.
        """
        # Counter so that each list of points has a unique name
        # points_0, points_1, ..., points_n where there are n-1 total polygons
        count = 0
        code = ''
        debug_num_coords = 0

        assert self.features, error_msg['emp_feat']

        for feature in self.features:
            # Handle polygons 
            if(feature['geometry']['type'] == "Polygon"):
                code += 'points_' + str(count) + '= '
                # index 0 contains exterior linear ring
                code += str(feature['geometry']['coordinates'][0])
                code += ';\n'

                if(self.is_colored):
                    code += 'color("' + str(
                        choice(self.color_bank)) + '")\n'

                if(self.bound_data_key_name != '' and 
                self.bound_data_key_name in feature['properties']):
                    code += 'linear_extrude(height=' + str(
                        feature['properties'][self.bound_data_key_name]) + ')\n'
                else:
                    code += 'linear_extrude(height=' + str(
                        self.DEFAULT_EXTRUDE_HEIGHT) + ')\n' 
                
                if(self.offset_delta != 0):
                    code += 'offset(' + str(
                        self.offset_delta) + ')\n'

                code += 'polygon(points_' + str(count) + ');\n'
                count += 1

            # Handle multipolygons, which store coordinate data
            # one layer deeper than polygons
            elif(feature['geometry']['type'] == "MultiPolygon"):
                for polygon in feature['geometry']['coordinates']:
                    code += 'points_' + str(count) + '= '
                    # index 0 contains exterior linear ring
                    code += str(polygon[0])
                    code += ';\n'

                    if(self.is_colored):
                        code += 'color("' + str(
                            choice(self.color_bank)) + '")\n'
                    
                    if(self.bound_data_key_name != '' and 
                    self.bound_data_key_name in feature['properties']):
                        code += 'linear_extrude(height=' + str(
                            feature['properties'][self.bound_data_key_name]) + ')\n'
                    else:
                        code += 'linear_extrude(height=' + str(
                            self.DEFAULT_EXTRUDE_HEIGHT) + ')\n' 

                    if(self.offset_delta != 0):
                        code += 'offset(' + str(
                            self.offset_delta) + ')\n'

                    code += 'polygon(points_' + str(count) + ');\n'
                    count += 1

        with open(filepath,'w') as f:
            char_out = f.write(code)
            
        print(status_msg['end_wrte'] + filepath + 
        ", characters written: " + str(char_out))
        
# ERROR AND STATUS MESSAGES
error_msg = {
    'emp_json' : ("raw_json_data cannot be empty. " 
    "Perhaps you forgot to read GeoJSON data?"),
    'emp_feat' : ("features list cannot be empty. "
    "Perhaps you forgot to call extract_features()?"),
    'bdata_nf' : ("bound_data_key_name cannot be empty. "
    "Perhaps you forgot to bind data to the model?") 
}

status_msg = {
    'end_read' : ("SUCCESS    "
    "Read JSON data into dictionary with keys: "),
    'end_extc' : ("SUCCESS    "
    "Extracted GeoJSON features, count: "),
    'start_smpl' : ("           "
    "Running geometry simplification..."),
    'end_smpl' : ("SUCCESS    "
    "Finished geometry simplification, new number of points: "), 
    'end_tsfm' : ("SUCCESS    "
    "Finished transformation"),
    'end_ofst' : ("SUCCESS    "
    "Finished offset"),
    'end_bind' : ("SUCCESS    "
    "Finished data binding, number of features with bound data: "),
    'end_scle' : ("SUCCESS    "
    "Finished height scaling, [min, max] heights: "),
    'end_wrte' : ("SUCCESS    "
    "Finished writing to file: ")
}