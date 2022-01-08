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
        self.num_features = 0
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
        print(status_msg['end_read'] + str(self.raw_json_data.keys()))

    def read_json_file(self, filepath):
        with open(filepath) as f:
            self.raw_json_data = json.load(f, object_pairs_hook=OrderedDict)
        print(status_msg['end_read'] + str(self.raw_json_data.keys()))

    def extract_features(self):
        assert self.raw_json_data, error_msg['emp_json']
        self.features = self.raw_json_data['features']
        self.num_features = len(self.features)
        print(status_msg['end_extc'] + str(self.num_features))

    def simplify(self, eps = DEFAULT_RDP_EPSILON):
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

        print(status_msg['end_tsfm']) 

    def bind_data(self, data_key_name, data):
        """Binds data to the collection of GeoJSON features.

        Adds a new key-value pair to each feature's 'properties' member.
        """
        self.bound_data_key_name = data_key_name
        assert self.features, error_msg['emp_feat']
        for feature, datum in zip(self.features, data):
            feature['properties'][data_key_name] = datum
        print(status_msg['end_bind'] + str(min(self.num_features, len(data))))

    def bind_data_by_identifier(self, data_key_name, data, id_key):
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
    'end_bind' : ("SUCCESS    "
    "Finished data binding, number of features with bound data: "),
    'end_scle' : ("SUCCESS    "
    "Finished height scaling, [min, max] heights: ")
}