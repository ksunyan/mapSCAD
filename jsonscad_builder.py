import json
from collections import OrderedDict
from rdp import rdp

class JsonScadBuilder:

    # CONSTANTS
    DEFAULT_EXTRUDE_HEIGHT = 2
    DEFAULT_UNION_EPSILON = 0.02
    DEFAULT_RDP_EPSILON = 0.01

    # CONSTRUCTOR
    def __init__(self):
        self.raw_json_data = OrderedDict()
        self.features = []
        self.bound_data_key_name = ''
        self.origin = []
        self.scale_factor = 1
        self.union_eps = self.DEFAULT_UNION_EPSILON

    # HELPER FUNCTIONS
    def transform_helper(self, pair):
        return [self.scale_factor * (pair[0]-self.origin[0]) + self.union_eps, 
        self.scale_factor * (pair[1]-self.origin[1]) + self.union_eps]
    
    # METHODS
    def read_json(self, str):
        self.raw_json_data = json.loads(str)
        print(status_msg['read_json'] + str(self.raw_json_data.keys()))

    def read_json_file(self, filepath):
        with open(filepath) as f:
            self.raw_json_data = json.load(f, object_pairs_hook=OrderedDict)
        print(status_msg['read_json'] + str(self.raw_json_data.keys()))

    def extract_features(self):
        assert self.raw_json_data, error_msg['emp_json']
        self.features = self.raw_json_data['features']
        print(status_msg['extc_feat'] + str(len(self.features)))

    def sample(self, eps = DEFAULT_RDP_EPSILON):
        assert self.features, error_msg['emp_feat']

        for feature in self.features:
            # Handle polygons 
            if(feature['geometry']['type'] == "Polygon"):
                # index 0 contains exterior linear ring
                coords = feature['geometry']['coordinates'][0]
                sampled_coords = rdp(coords, epsilon = eps)
                feature['geometry']['coordinates'][0] = sampled_coords

            # Handle multipolygons, which store coordinate data
            # one layer deeper than polygons
            elif(feature['geometry']['type'] == "MultiPolygon"):
                for polygon in feature['geometry']['coordinates']:
                    # index 0 contains exterior linear ring
                    coords = polygon[0]
                    sampled_coords = rdp(coords, epsilon = eps)
                    polygon[0] = sampled_coords

    def transform(self, origin, scale_factor, eps = DEFAULT_UNION_EPSILON):
        self.origin = origin
        self.scale_factor = scale_factor
        self.union_eps = eps

        assert self.features, error_msg['emp_feat']

        for feature in self.features:
            # Handle polygons 
            if(feature['geometry']['type'] == "Polygon"):
                # index 0 contains exterior linear ring
                coords = feature['geometry']['coordinates'][0] 
                feature['geometry']['coordinates'][0] = list(
                    map(self.transform_helper, coords))

            # Handle multipolygons, which store coordinate data
            # one layer deeper than polygons
            elif(feature['geometry']['type'] == "MultiPolygon"):
                for polygon in feature['geometry']['coordinates']:
                    # index 0 contains exterior linear ring
                    coords = polygon[0]
                    polygon[0] = list(map(self.transform_helper, coords)) 

    def bind_data(self, data_key_name, data):
        """Binds data to the collection of GeoJSON features.

        Adds a new key-value pair to each feature's 'properties' member.
        """
        self.bound_data_key_name = data_key_name
        assert self.features, error_msg['emp_feat']
        for feature, datum in zip(self.features, data):
            feature['properties'][data_key_name] = datum

    def bind_data_by_identifier(self, data_key_name, data, id_key):
        self.bound_data_key_name = data_key_name
        assert self.features, error_msg['emp_feat']
        for datum in data:
            for feature in self.features:
                if(id_key in feature['properties'] and 
                feature['properties'][id_key] == datum[0]):
                    feature['properties'][data_key_name] = datum[1]
                    break


    def scale_heights(self, domain, range):
        domain_diff = domain[1] - domain[0]
        range_diff = range[1] - range[0]

        assert self.features, error_msg['emp_feat']
        assert self.bound_data_key_name, error_msg['bdata_nf']
        
        for feature in self.features: 
            if(self.bound_data_key_name in feature['properties']):
                scaling_ratio = (
                    feature['properties'][self.bound_data_key_name] 
                    - domain[0]) / domain_diff
                feature['properties'][self.bound_data_key_name] = range[0] + (
                    scaling_ratio * range_diff)

    def write_scad_file(self, filepath):
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

                if(self.bound_data_key_name != '' and 
                self.bound_data_key_name in feature['properties']):
                    code += 'linear_extrude(height=' + str(
                        feature['properties'][self.bound_data_key_name]) + ')\n'
                else:
                    code += 'linear_extrude(height=' + str(
                        self.DEFAULT_EXTRUDE_HEIGHT) + ')\n' 
                
                code += 'polygon(points_' + str(count) + ');\n'
                count += 1

                debug_num_coords += len(feature['geometry']['coordinates'][0])

            # Handle multipolygons, which store coordinate data
            # one layer deeper than polygons
            elif(feature['geometry']['type'] == "MultiPolygon"):
                for polygon in feature['geometry']['coordinates']:
                    code += 'points_' + str(count) + '= '
                    # index 0 contains exterior linear ring
                    code += str(polygon[0])
                    code += ';\n'
                    
                    if(self.bound_data_key_name != '' and 
                    self.bound_data_key_name in feature['properties']):
                        code += 'linear_extrude(height=' + str(
                            feature['properties'][self.bound_data_key_name]) + ')\n'
                    else:
                        code += 'linear_extrude(height=' + str(
                            self.DEFAULT_EXTRUDE_HEIGHT) + ')\n' 

                    code += 'polygon(points_' + str(count) + ');\n'
                    count += 1

                    debug_num_coords += len(polygon[0])

        with open(filepath,'w') as f:
            f.write(code)
            
        print(debug_num_coords)
        
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
    'read_json' : ("SUCCESS    "
    "Read JSON data into dictionary with keys: "),
    'extc_feat' : ("SUCCESS    "
    "Extracted GeoJSON features, count = ") 
}